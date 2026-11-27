"""Görsel araçları: arka plan silme, nesne silme (bilgisayarda, ücretsiz yapay zekâ)."""
import base64
from pathlib import Path

import enhance
from core import load_settings, safe_name

MODELS = {
    "arkaplan": ("isnet-general-use.onnx", "https://github.com/danielgatis/rembg/releases/download/v0.0.0/isnet-general-use.onnx", "Arka plan modeli (~170 MB)"),
    "nesne": ("lama_fp32.onnx", "https://huggingface.co/Carve/LaMa-ONNX/resolve/main/lama_fp32.onnx", "Nesne silme modeli (~200 MB)"),
}


def ensure_model(kind, job=None, lo=0.0, hi=0.4):
    name, url, label = MODELS[kind]
    dest = enhance.AI / "gorsel" / name
    if not dest.exists():
        enhance._download(url, dest, job, lo, hi, label + " indiriliyor")
    return dest


def _out(src, suffix, ext):
    folder = Path(load_settings().get("cikti_klasoru") or (Path.home() / "Pictures"))
    folder.mkdir(parents=True, exist_ok=True)
    base = safe_name(Path(src).stem, 60)
    out = folder / f"{base}_{suffix}{ext}"
    i = 2
    while out.exists():
        out = folder / f"{base}_{suffix}_{i}{ext}"
        i += 1
    return out


def _run(job, args, lo, msg):
    py, ortdir = enhance.ensure_ort(job, lo)
    cmd = [py, str(Path(__file__).with_name("img_worker.py")), *map(str, args)] + ([str(ortdir)] if ortdir else [])
    code, err = enhance._run_lines(cmd, job, lo, 0.98, msg)
    if code != 0:
        line = [x for x in (err or "").strip().splitlines() if x.strip()]
        raise RuntimeError("Görsel işlenemedi: " + (line[-1][-250:] if line else "bilinmeyen hata"))


def job_remove_bg(job, src):
    job.extra = {"parca": "Fotoğraf"}
    model = ensure_model("arkaplan", job, 0.02, 0.5)
    out = _out(src, "arkaplansiz", ".png")
    _run(job, ["arkaplan", model, src, out], 0.5, "Arka plan siliniyor...")
    if not out.exists():
        raise RuntimeError("Arka plan silinemedi")
    job.set(1, "Hazır! " + out.name)
    return {"path": str(out), "name": out.name, "image": True}


def job_inpaint(job, src, mask_data):
    job.extra = {"parca": "Fotoğraf"}
    model = ensure_model("nesne", job, 0.02, 0.5)
    tmp = enhance.CACHE / "gorsel"
    tmp.mkdir(parents=True, exist_ok=True)
    mpath = tmp / f"maske_{job.id}.png"
    mpath.write_bytes(base64.b64decode(mask_data.split(",", 1)[-1]))
    ext = Path(src).suffix.lower() if Path(src).suffix.lower() in (".png", ".jpg", ".jpeg", ".webp") else ".png"
    out = _out(src, "temiz", ext)
    try:
        _run(job, ["nesne", model, src, mpath, out], 0.5, "Nesne siliniyor...")
    finally:
        mpath.unlink(missing_ok=True)
    if not out.exists():
        raise RuntimeError("Nesne silinemedi")
    job.set(1, "Hazır! " + out.name)
    return {"path": str(out), "name": out.name, "image": True}


def job_cutout(job, src):
    """Kapak Stüdyosu: kişiyi kes (önbellekli, çıktı klasörüne yazmaz)."""
    import hashlib
    job.extra = {"parca": "Kişi"}
    st = Path(src).stat()
    key = hashlib.md5(f"{src}|{st.st_mtime}|{st.st_size}".encode()).hexdigest()[:16]
    d = enhance.CACHE / "kapak" / "kes"
    d.mkdir(parents=True, exist_ok=True)
    out = d / f"{key}_v2.png"
    if not out.exists():
        model = ensure_model("arkaplan", job, 0.02, 0.6)
        tmp = d / f"{key}_yaz.png"
        _run(job, ["kisi", model, src, tmp], 0.6, "Kişi kesiliyor...")
        if not tmp.exists():
            raise RuntimeError("Kişi kesilemedi")
        tmp.replace(out)
    job.set(1, "Kişi kesildi")
    return {"path": str(out)}
