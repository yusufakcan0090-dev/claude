"""Yüz netleştirme (GFPGAN) işçisi: ayrı süreçte çalışır.

Kullanım: python face_worker.py <klasör_ya_da_resim> <güç 0-100> <gfpgan.onnx> <yunet.onnx> [ort_klasörü]
Klasördeki her .jpg/.png dosyasında yüzleri bulur, netleştirir ve yerine yazar.
"""
import os
import sys

if len(sys.argv) > 5 and sys.argv[5] and os.path.isdir(sys.argv[5]):
    sys.path.insert(0, sys.argv[5])  # DirectML'li onnxruntime (her ekran kartında)

import cv2  # noqa: E402
import numpy as np  # noqa: E402
import onnxruntime as ort  # noqa: E402

# GFPGAN'in 512x512 yüz şablonu (göz, göz, burun, ağız, ağız)
TEMPLATE = np.array([[192.98138, 239.94708], [318.90277, 240.1936], [256.63416, 314.01935],
                     [201.26117, 371.41043], [313.08905, 371.15118]], np.float32)


def session(path):
    prov = [p for p in ("DmlExecutionProvider", "CUDAExecutionProvider", "CPUExecutionProvider") if p in ort.get_available_providers()]
    try:
        return ort.InferenceSession(path, providers=prov)
    except Exception:
        return ort.InferenceSession(path, providers=["CPUExecutionProvider"])


def detect(det, img):
    h, w = img.shape[:2]
    k = min(1.0, 960 / max(h, w))
    small = cv2.resize(img, (int(w * k), int(h * k))) if k < 1 else img
    det.setInputSize((small.shape[1], small.shape[0]))
    _, faces = det.detect(small)
    out = []
    if faces is None:
        return out
    for f in faces:
        if f[-1] < 0.6 or f[2] / k < 40:  # çok küçük ya da emin değilse dokunma
            continue
        out.append(f[4:14].reshape(5, 2) / k)
    return out


def restore(net, inp_name, img, lm, strength):
    M, _ = cv2.estimateAffinePartial2D(lm.astype(np.float32), TEMPLATE, method=cv2.LMEDS)
    if M is None:
        return img
    face = cv2.warpAffine(img, M, (512, 512), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT101)
    x = cv2.cvtColor(face, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    x = ((x - 0.5) / 0.5).transpose(2, 0, 1)[None]
    y = net.run(None, {inp_name: x})[0][0]
    y = ((np.clip(y, -1, 1) + 1) / 2 * 255).transpose(1, 2, 0).round().astype(np.uint8)
    y = cv2.cvtColor(y, cv2.COLOR_RGB2BGR)
    if strength < 1:
        y = cv2.addWeighted(y, strength, face, 1 - strength, 0)
    h, w = img.shape[:2]
    Mi = cv2.invertAffineTransform(M)
    back = cv2.warpAffine(y, Mi, (w, h), flags=cv2.INTER_LANCZOS4)
    mask = np.zeros((512, 512), np.float32)
    cv2.rectangle(mask, (24, 24), (488, 488), 1.0, -1)
    mask = cv2.GaussianBlur(mask, (0, 0), 14)
    m = cv2.warpAffine(mask, Mi, (w, h))[..., None]
    return (back.astype(np.float32) * m + img.astype(np.float32) * (1 - m)).round().clip(0, 255).astype(np.uint8)


def main():
    target, strength, gfp, yun = sys.argv[1], int(sys.argv[2]) / 100, sys.argv[3], sys.argv[4]
    net = session(gfp)
    inp = net.get_inputs()[0].name
    det = cv2.FaceDetectorYN.create(yun, "", (320, 320), 0.6, 0.3, 50)
    files = [os.path.join(target, f) for f in sorted(os.listdir(target)) if f.lower().endswith((".jpg", ".png"))] if os.path.isdir(target) else [target]
    total = len(files)
    for i, fp in enumerate(files):
        img = cv2.imread(fp)
        if img is None:
            continue
        faces = detect(det, img)
        for lm in faces:
            img = restore(net, inp, img, lm, strength)
        if faces:
            if fp.lower().endswith(".png"):
                cv2.imwrite(fp, img)
            else:
                cv2.imwrite(fp, img, [cv2.IMWRITE_JPEG_QUALITY, 96])
        print(f"{i + 1}/{total}", flush=True)


if __name__ == "__main__":
    main()
