"""Video arka plan silme işçisi (ayrı süreç).

  python vmatte_worker.py <ayarlar.json> [ort_klasörü]
ayarlar: {src, out, w, h, fps, frames, model, kind(insan|genel), mode(renk|bulanik|resim|video|seffaf),
          color, bg, ratio, feather, shrink, preview_t (tek kare önizleme için), ffmpeg}
"""
import json
import os
import subprocess
import sys

_ort = sys.argv[2] if len(sys.argv) > 2 and os.path.isdir(sys.argv[2]) else None
if _ort:
    sys.path.insert(0, _ort)

import cv2  # noqa: E402
import numpy as np  # noqa: E402
import onnxruntime as ort  # noqa: E402

NOWIN = 0x08000000 if os.name == "nt" else 0


def session(path):
    prov = [p for p in ("DmlExecutionProvider", "CUDAExecutionProvider", "CPUExecutionProvider") if p in ort.get_available_providers()]
    try:
        return ort.InferenceSession(path, providers=prov)
    except Exception:
        return ort.InferenceSession(path, providers=["CPUExecutionProvider"])


def cover(img, w, h):
    ih, iw = img.shape[:2]
    k = max(w / iw, h / ih)
    r = cv2.resize(img, (max(w, int(iw * k + .5)), max(h, int(ih * k + .5))), interpolation=cv2.INTER_AREA if k < 1 else cv2.INTER_CUBIC)
    y, x = (r.shape[0] - h) // 2, (r.shape[1] - w) // 2
    return r[y:y + h, x:x + w]


def hex_rgb(c):
    c = (c or "#00ff00").lstrip("#")
    return np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


class Matter:
    """Kişi: RVM (zamanda tutarlı, saç telleri dahil). Genel: IS-Net (her nesne) + zamanda yumuşatma."""

    def __init__(self, cfg):
        self.kind = cfg.get("kind") or "insan"
        self.net = session(cfg["model"])
        self.names = [i.name for i in self.net.get_inputs()]
        self.ratio = float(cfg.get("ratio") or 0.25)
        self.rec = None
        self.prev = None

    def __call__(self, rgb):
        h, w = rgb.shape[:2]
        if self.kind == "insan":
            x = (rgb.astype(np.float32) / 255.0).transpose(2, 0, 1)[None]
            if self.rec is None:
                self.rec = [np.zeros((1, 1, 1, 1), np.float32)] * 4
            feed = {"src": x, "r1i": self.rec[0], "r2i": self.rec[1], "r3i": self.rec[2], "r4i": self.rec[3],
                    "downsample_ratio": np.array([self.ratio], np.float32)}
            fgr, pha, *self.rec = self.net.run(None, feed)
            return pha[0, 0], (fgr[0].transpose(1, 2, 0) * 255.0)
        S = 1024
        im = cv2.resize(rgb, (S, S), interpolation=cv2.INTER_AREA).astype(np.float32)
        im /= max(1.0, float(im.max()))
        pred = self.net.run(None, {self.names[0]: ((im - 0.5) / 1.0).transpose(2, 0, 1)[None].astype(np.float32)})[0][0, 0]
        mi, ma = float(pred.min()), float(pred.max())
        pred = (pred - mi) / max(1e-6, ma - mi)
        a = cv2.resize(pred, (w, h), interpolation=cv2.INTER_LINEAR)
        if self.prev is not None:  # kareler arası titremeyi azalt
            a = a * 0.65 + self.prev * 0.35
        self.prev = a
        return a, None


def refine(a, feather, shrink):
    a = np.clip(a, 0, 1).astype(np.float32)
    if shrink:
        k = int(abs(shrink)) * 2 + 1
        a = cv2.erode(a, np.ones((k, k), np.uint8)) if shrink > 0 else cv2.dilate(a, np.ones((k, k), np.uint8))
    if feather > 0:
        a = cv2.GaussianBlur(a, (0, 0), feather)
    return a


def compose(rgb, a, fg, mode, bg, color, blur_k):
    if mode == "seffaf":
        out = np.dstack([(fg if fg is not None else rgb.astype(np.float32)), a * 255.0])
        return np.clip(out, 0, 255).astype(np.uint8)
    h, w = rgb.shape[:2]
    if mode == "renk":
        back = np.broadcast_to(color, (h, w, 3))
    elif mode == "bulanik":
        small = cv2.resize(rgb, (max(2, w // 8), max(2, h // 8)), interpolation=cv2.INTER_AREA)
        back = cv2.resize(cv2.GaussianBlur(small, (0, 0), blur_k), (w, h), interpolation=cv2.INTER_LINEAR).astype(np.float32)
    else:
        back = bg.astype(np.float32)
    f = fg if fg is not None else rgb.astype(np.float32)
    # RVM'nin ön plan rengi saç kenarlarında yeşil/arka plan sızmasını önler
    out = f * a[..., None] + back * (1 - a[..., None])
    return np.clip(out, 0, 255).astype(np.uint8)


def main():
    cfg = json.load(open(sys.argv[1], encoding="utf-8"))
    ff, W, H = cfg["ffmpeg"], int(cfg["w"]), int(cfg["h"])
    mode = cfg.get("mode") or "renk"
    color = hex_rgb(cfg.get("color"))
    feather, shrink = float(cfg.get("feather") or 0), int(cfg.get("shrink") or 0)
    m = Matter(cfg)
    bg_img = None
    if mode == "resim":
        bg_img = cv2.cvtColor(cv2.imdecode(np.fromfile(cfg["bg"], np.uint8), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
        bg_img = cover(bg_img, W, H)

    if cfg.get("preview_t") is not None:  # tek kare önizleme (RVM'yi birkaç kare ısıtarak)
        t = float(cfg["preview_t"])
        frames = []
        for dt in (0.4, 0.27, 0.13, 0.0):
            p = subprocess.run([ff, "-v", "error", "-ss", f"{max(0, t - dt):.3f}", "-i", cfg["src"], "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24",
                                "-s", f"{W}x{H}", "-"], capture_output=True, creationflags=NOWIN)
            if len(p.stdout) == W * H * 3:
                frames.append(np.frombuffer(p.stdout, np.uint8).reshape(H, W, 3))
        if not frames:
            raise SystemExit("kare okunamadı")
        for fr in frames:
            a, fg = m(fr)
        a = refine(a, feather, shrink)
        if mode == "video":
            p = subprocess.run([ff, "-v", "error", "-i", cfg["bg"], "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-vf",
                                f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}", "-"], capture_output=True, creationflags=NOWIN)
            bg_img = np.frombuffer(p.stdout, np.uint8).reshape(H, W, 3)
        out = compose(frames[-1], a, fg, "renk" if mode == "seffaf" else mode, bg_img, np.array([40, 40, 40], np.float32) if mode == "seffaf" else color, 12)
        if mode == "seffaf":  # dama tahtası göster
            ii = np.indices((H, W)) // 24
            cb = ((ii[0] + ii[1]) % 2 * 40 + 180).astype(np.float32)[..., None].repeat(3, 2)
            out = np.clip((fg if fg is not None else frames[-1]) * a[..., None] + cb * (1 - a[..., None]), 0, 255).astype(np.uint8)
        cv2.imwrite(cfg["out"], cv2.cvtColor(out, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 92])
        print("1/1", flush=True)
        return

    total = int(cfg.get("frames") or 0)
    fps = str(cfg.get("fps") or "30")
    dec = subprocess.Popen([ff, "-v", "error", "-i", cfg["src"], "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-"],
                           stdout=subprocess.PIPE, creationflags=NOWIN)
    bgdec = None
    if mode == "video":
        bgdec = subprocess.Popen([ff, "-v", "error", "-stream_loop", "-1", "-i", cfg["bg"], "-f", "rawvideo", "-pix_fmt", "rgb24", "-r", fps, "-vf",
                                  f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}", "-"], stdout=subprocess.PIPE, creationflags=NOWIN)
    alpha = mode == "seffaf"
    ext = os.path.splitext(cfg["out"])[1].lower()
    if alpha and ext == ".webm":
        venc = ["-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-crf", "20", "-b:v", "0", "-row-mt", "1", "-auto-alt-ref", "0"]
        aenc = ["-c:a", "libopus", "-b:a", "160k"]
    elif alpha:
        venc = ["-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le"]
        aenc = ["-c:a", "pcm_s16le"]
    else:
        venc = ["-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p"]
        aenc = ["-c:a", "aac", "-b:a", "192k"]
    enc = subprocess.Popen([ff, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba" if alpha else "rgb24", "-s", f"{W}x{H}", "-r", fps, "-i", "-",
                            "-i", cfg["src"], "-map", "0:v", "-map", "1:a?", *venc, *aenc, "-shortest",
                            *(["-movflags", "+faststart"] if ext in (".mp4", ".mov") and not alpha else []), cfg["out"]],
                           stdin=subprocess.PIPE, creationflags=NOWIN)
    n = W * H * 3
    i = 0
    try:
        while True:
            buf = dec.stdout.read(n)
            if len(buf) < n:
                break
            fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
            a, fg = m(fr)
            a = refine(a, feather, shrink)
            back = None
            if bgdec:
                bb = bgdec.stdout.read(n)
                back = np.frombuffer(bb, np.uint8).reshape(H, W, 3) if len(bb) == n else np.zeros((H, W, 3), np.uint8)
            elif bg_img is not None:
                back = bg_img
            enc.stdin.write(compose(fr, a, fg, mode, back, color, 12).tobytes())
            i += 1
            if i % 5 == 0:
                print(f"{i}/{max(total, i)}", flush=True)
    finally:
        try:
            enc.stdin.close()
        except Exception:
            pass
        enc.wait()
        dec.kill()
        if bgdec:
            bgdec.kill()
    if enc.returncode != 0:
        raise SystemExit("kodlama başarısız")
    print(f"{i}/{i}", flush=True)


if __name__ == "__main__":
    main()
