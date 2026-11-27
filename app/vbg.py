"""Video arka plan silme (yeşil perdesiz): kişi için RVM, her şey için IS-Net."""
import hashlib
import json
import time
from pathlib import Path

import enhance
import imgtools
from core import CACHE, FFMPEG, load_settings, probe, safe_name

RVM_URL = "https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_mobilenetv3_fp32.onnx"


def ensure_model(kind, job=None, lo=0.0, hi=0.3):
    if kind == "genel":
        return imgtools.ensure_model("arkaplan", job, lo, hi)
    dest = enhance.AI / "gorsel" / "rvm_mobilenetv3_fp32.onnx"
    if not dest.exists():
        enhance._download(RVM_URL, dest, job, lo, hi, "Kişi ayırma modeli indiriliyor (~15 MB)")
    return dest


def _cfg(src, o, out, **extra):
    info = probe(src)
    w, h = int(info["width"]), int(info["height"])
    w, h = w - w % 2, h - h % 2
    return {"src": str(src), "out": str(out), "w": w, "h": h, "fps": f"{float(info['fps'] or 30):.4f}",
            "frames": int(float(info["duration"] or 0) * float(info["fps"] or 30)), "kind": o.get("kind") or "insan",
            "mode": o.get("mode") or "renk", "color": o.get("color") or "#00ff00", "bg": o.get("bg") or "",
            "ratio": min(1.0, max(0.1, 512 / max(w, h))), "feather": float(o.get("feather") or 0), "shrink": int(o.get("shrink") or 0),
            "ffmpeg": FFMPEG, **extra}


def _cmd(cfg_path):
    py, ortdir = enhance.ensure_ort()
    return [py, str(Path(__file__).with_name("vmatte_worker.py")), str(cfg_path)] + ([str(ortdir)] if ortdir else [])


def preview(src, t, o):
    """Tek kare önizleme. Dönen: jpg yolu."""
    key = hashlib.md5(json.dumps([str(src), round(float(t), 2), o, Path(src).stat().st_mtime], sort_keys=True).encode()).hexdigest()[:16]
    d = CACHE / "vbg"
    d.mkdir(parents=True, exist_ok=True)
    out = d / f"{key}.jpg"
    if out.exists():
        return out
    model = ensure_model(o.get("kind") or "insan")
    cfg = _cfg(src, o, out, model=str(model), preview_t=float(t))
    cp = d / f"{key}.json"
    cp.write_text(json.dumps(cfg), "utf-8")
    from core import run
    r = run(_cmd(cp), timeout=300)
    cp.unlink(missing_ok=True)
    if not out.exists():
        line = [x for x in (r.stderr or "").splitlines() if x.strip()]
        raise RuntimeError("Önizleme yapılamadı: " + (line[-1][-200:] if line else ""))
    return out


def job_vbg(job, src, o):
    src = Path(src)
    job.extra = {"t0": time.time()}
    model = ensure_model(o.get("kind") or "insan", job, 0.01, 0.08)
    enhance.ensure_ort(job, 0.08)
    if o.get("mode") in ("resim", "video") and not (o.get("bg") and Path(o["bg"]).exists()):
        raise RuntimeError("Arka plan için resim ya da video seç")
    alpha = o.get("mode") == "seffaf"
    ext = (".webm" if (o.get("seffaf_bicim") or "webm") == "webm" else ".mov") if alpha else ".mp4"
    folder = Path(load_settings().get("cikti_klasoru") or (Path.home() / "Videos"))
    folder.mkdir(parents=True, exist_ok=True)
    base = safe_name(src.stem, 60) + "_arkaplan"
    out = folder / f"{base}{ext}"
    i = 2
    while out.exists():
        out = folder / f"{base}_{i}{ext}"
        i += 1
    cfg = _cfg(src, o, out, model=str(model))
    cp = CACHE / "vbg" / f"is_{job.id}.json"
    cp.parent.mkdir(parents=True, exist_ok=True)
    cp.write_text(json.dumps(cfg), "utf-8")
    try:
        code, err = enhance._run_lines(_cmd(cp), job, 0.1, 0.99, "Arka plan siliniyor...")
    finally:
        cp.unlink(missing_ok=True)
    if code != 0 or not out.exists() or out.stat().st_size < 1000:
        out.unlink(missing_ok=True)
        line = [x for x in (err or "").splitlines() if x.strip()]
        raise RuntimeError("Arka plan silinemedi: " + (line[-1][-200:] if line else "bilinmeyen hata"))
    job.set(1, "Hazır! " + out.name)
    return {"path": str(out), "name": out.name}
