"""Görsel yapay zekâ işçisi (ayrı süreçte çalışır).

  python img_worker.py arkaplan <model.onnx> <girdi> <çıktı.png> [ort_klasörü]
  python img_worker.py nesne    <model.onnx> <girdi> <maske.png> <çıktı> [ort_klasörü]
"""
import os
import sys

_ort = sys.argv[-1] if len(sys.argv) > 4 and os.path.isdir(sys.argv[-1]) else None
if _ort:
    sys.path.insert(0, _ort)  # DirectML'li onnxruntime

import cv2  # noqa: E402
import numpy as np  # noqa: E402
import onnxruntime as ort  # noqa: E402


def session(path):
    prov = [p for p in ("DmlExecutionProvider", "CUDAExecutionProvider", "CPUExecutionProvider") if p in ort.get_available_providers()]
    try:
        return ort.InferenceSession(path, providers=prov)
    except Exception:
        return ort.InferenceSession(path, providers=["CPUExecutionProvider"])


def imread(p, flags=cv2.IMREAD_UNCHANGED):
    # Türkçe karakterli yollar için (cv2.imread Windows'ta okuyamaz)
    data = np.fromfile(p, np.uint8)
    return cv2.imdecode(data, flags)


def imwrite(p, img):
    ext = os.path.splitext(p)[1] or ".png"
    ok, buf = cv2.imencode(ext, img, [cv2.IMWRITE_JPEG_QUALITY, 97] if ext.lower() in (".jpg", ".jpeg") else [])
    if not ok:
        raise RuntimeError("Kaydedilemedi")
    buf.tofile(p)


def to_bgr(img):
    if img.ndim == 2:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    if img.shape[2] == 4:
        return img[:, :, :3]
    return img


def remove_bg(model, src, dst, clean=False):
    """IS-Net (DIS) ile ön planı bulur, arka planı şeffaf yapar."""
    img = to_bgr(imread(src))
    h, w = img.shape[:2]
    net = session(model)
    inp = net.get_inputs()[0]
    S = 1024
    rgb = cv2.cvtColor(cv2.resize(img, (S, S), interpolation=cv2.INTER_LANCZOS4), cv2.COLOR_BGR2RGB).astype(np.float32)
    rgb /= max(1.0, float(rgb.max()))
    x = ((rgb - 0.5) / 1.0).transpose(2, 0, 1)[None].astype(np.float32)
    print("50/100", flush=True)
    pred = net.run(None, {inp.name: x})[0][0, 0]
    mi, ma = float(pred.min()), float(pred.max())
    pred = (pred - mi) / max(1e-6, ma - mi)
    mask = cv2.resize(pred, (w, h), interpolation=cv2.INTER_LANCZOS4).clip(0, 1)
    # kenarları biraz temizle: çok zayıf değerler tamamen şeffaf, güçlüler tamamen dolu
    mask = np.clip((mask - 0.08) / 0.84, 0, 1)
    a = (mask * 255).round().astype(np.uint8)
    if clean:
        # küçük kopuk lekeleri at: ana gövde ve ona yakın büyük parçalar kalsın
        n, lab, st, _ = cv2.connectedComponentsWithStats((a > 100).astype(np.uint8), 8)
        if n > 2:
            big = st[1:, cv2.CC_STAT_AREA].max()
            keep = np.zeros(n, bool)
            keep[1:] = st[1:, cv2.CC_STAT_AREA] >= big * 0.04
            grow = cv2.dilate(keep[lab].astype(np.uint8), np.ones((9, 9), np.uint8))
            a = (a * grow).astype(np.uint8)
    out = np.dstack([img, a])
    imwrite(dst, out)
    print("100/100", flush=True)


def inpaint(model, src, mpath, dst):
    """LaMa ile maskelenen bölgeyi siler, etrafına uygun şekilde doldurur."""
    raw = imread(src)
    alpha = raw[:, :, 3] if raw.ndim == 3 and raw.shape[2] == 4 else None
    img = to_bgr(raw)
    h, w = img.shape[:2]
    m = imread(mpath, cv2.IMREAD_GRAYSCALE)
    if m is None:
        raise RuntimeError("Maske okunamadı")
    if m.shape[:2] != (h, w):
        m = cv2.resize(m, (w, h), interpolation=cv2.INTER_NEAREST)
    m = (m > 20).astype(np.uint8)
    if not m.any():
        raise RuntimeError("Silinecek bir yer işaretlenmedi")
    m = cv2.dilate(m, np.ones((7, 7), np.uint8), iterations=2)  # kenarları da kapsasın
    net = session(model)
    names = [i.name for i in net.get_inputs()]
    S = 512
    # maskenin etrafından kare bir bölge al (büyük fotoğraflarda detay kaybolmasın)
    ys, xs = np.where(m > 0)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    side = int(max(x1 - x0, y1 - y0) * 1.8) + 64
    side = max(side, min(S, max(w, h)))
    side = min(side, max(w, h))
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    bx0 = int(np.clip(cx - side // 2, 0, max(0, w - side)))
    by0 = int(np.clip(cy - side // 2, 0, max(0, h - side)))
    bx1, by1 = min(w, bx0 + side), min(h, by0 + side)
    crop, cm = img[by0:by1, bx0:bx1], m[by0:by1, bx0:bx1]
    ch, cw = crop.shape[:2]
    ci = cv2.cvtColor(cv2.resize(crop, (S, S), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    cmm = (cv2.resize(cm, (S, S), interpolation=cv2.INTER_NEAREST) > 0).astype(np.float32)
    mname = next((n for n in names if "mask" in n.lower()), names[-1])
    iname = next((n for n in names if n != mname), names[0])
    feed = {iname: ci.transpose(2, 0, 1)[None], mname: cmm[None, None]}
    print("50/100", flush=True)
    out = net.run(None, feed)[0][0].transpose(1, 2, 0)
    if out.max() <= 1.5:
        out = out * 255.0
    out = cv2.cvtColor(out.clip(0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR)
    out = cv2.resize(out, (cw, ch), interpolation=cv2.INTER_CUBIC)
    # sadece maskelenen yere yumuşak geçişle yapıştır
    soft = cv2.GaussianBlur(cm.astype(np.float32), (0, 0), 3)[..., None]
    soft = np.maximum(soft, cm[..., None].astype(np.float32))
    res = img.copy()
    res[by0:by1, bx0:bx1] = (out.astype(np.float32) * soft + crop.astype(np.float32) * (1 - soft)).round().astype(np.uint8)
    if alpha is not None:
        res = np.dstack([res, alpha])
    imwrite(dst, res)
    print("100/100", flush=True)


def main():
    a = sys.argv[1:]
    if _ort:
        a = a[:-1]
    if a[0] == "arkaplan":
        remove_bg(a[1], a[2], a[3])
    elif a[0] == "kisi":
        remove_bg(a[1], a[2], a[3], clean=True)
    elif a[0] == "nesne":
        inpaint(a[1], a[2], a[3], a[4])
    else:
        raise SystemExit("bilinmeyen komut")


if __name__ == "__main__":
    main()
