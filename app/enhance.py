"""Kalite Artır: yapay zekâ ile netleştirme/büyütme (Real-ESRGAN), akıcılaştırma (RIFE), gürültü ve blok giderme.

Real-ESRGAN ve RIFE "ncnn-vulkan" sürümleri NVIDIA, AMD ve Intel ekran kartlarında çalışır.
Uzun videolar disk dolmasın diye parça parça işlenir.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import zipfile
from pathlib import Path

import core
from core import BIN, CACHE, FFMPEG, NO_WINDOW, load_settings, probe, run, safe_name, proc_pause

AI = BIN / "ai"
IS_WIN = os.name == "nt"
EXE = ".exe" if IS_WIN else ""
TOOLS = {
    "realesrgan": {
        "url": ("https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-windows.zip" if IS_WIN
                else "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-ubuntu.zip"),
        "exe": "realesrgan-ncnn-vulkan" + EXE,
    },
    "realcugan": {
        "url": ("https://github.com/nihui/realcugan-ncnn-vulkan/releases/download/20220728/realcugan-ncnn-vulkan-20220728-windows.zip" if IS_WIN
                else "https://github.com/nihui/realcugan-ncnn-vulkan/releases/download/20220728/realcugan-ncnn-vulkan-20220728-ubuntu.zip"),
        "exe": "realcugan-ncnn-vulkan" + EXE,
    },
    "waifu2x": {  # anime/manga resimleri için: çizgileri kalınlaştırmaz, gri tonları ve taramaları korur
        "url": ("https://github.com/nihui/waifu2x-ncnn-vulkan/releases/download/20220728/waifu2x-ncnn-vulkan-20220728-windows.zip" if IS_WIN
                else "https://github.com/nihui/waifu2x-ncnn-vulkan/releases/download/20220728/waifu2x-ncnn-vulkan-20220728-ubuntu.zip"),
        "exe": "waifu2x-ncnn-vulkan" + EXE,
    },
    "rife": {
        "url": ("https://github.com/nihui/rife-ncnn-vulkan/releases/download/20221029/rife-ncnn-vulkan-20221029-windows.zip" if IS_WIN
                else "https://github.com/nihui/rife-ncnn-vulkan/releases/download/20221029/rife-ncnn-vulkan-20221029-ubuntu.zip"),
        "exe": "rife-ncnn-vulkan" + EXE,
    },
}
# model -> (dosya adı, ölçek)
MODELS = {
    "gercek": ("realesrgan-x4plus", 4),          # gerçek görüntü, en iyi
    "hizli": ("realesr-animevideov3", 2),        # hızlı, videoya uygun
    "anime": ("realesrgan-x4plus-anime", 4),     # çizgi film / anime
    "anime_pro": ("realcugan", 2),               # Real-CUGAN: anime için en iyi (çizgiler temiz ve keskin)
    "ultra": ("ultrasharp-4x", 4),               # 4x-UltraSharp: gerçek görüntüde en keskin
    "dogal": ("remacri-4x", 4),                  # Remacri: keskin ama doğal doku
    "hifi": ("high-fidelity-4x", 4),             # aslına en sadık
}
EXTRA_MODELS = {"ultrasharp-4x", "remacri-4x", "high-fidelity-4x"}
EXTRA_URL = "https://raw.githubusercontent.com/upscayl/upscayl/main/resources/models/{}"


def ensure_model(name, job=None, lo=0.0, hi=0.05):
    """Ek yapay zekâ modellerini (UltraSharp, Remacri...) Real-ESRGAN'ın model klasörüne indirir."""
    if name not in EXTRA_MODELS:
        return
    exe = ensure_tool("realesrgan", job, lo, lo)
    md = exe.parent / "models"
    md.mkdir(exist_ok=True)
    for ext in ("param", "bin"):
        f = md / f"{name}.{ext}"
        if not f.exists() or f.stat().st_size < 1000:
            _download(EXTRA_URL.format(f"{name}.{ext}"), f, job, lo, hi, f"Yapay zekâ modeli indiriliyor ({name})")


def ai_tool(o):
    """Seçilen modele göre (araç adı, model, ölçek)."""
    k = float(o.get("_k") or 2)  # gereken büyütme (çıkış / kaynak)
    if o.get("model") == "anime_pro":
        if o.get("_img"):  # fotoğraf/resim: Waifu2x CUnet (en detaylı, taramaları ve gri tonları korur)
            return "waifu2x", "models-cunet", 2 if k <= 2.05 else 4
        return "realcugan", "models-pro", 2 if k <= 2.05 else 3
    name, sc = MODELS.get(o.get("model"), MODELS["hizli"])
    if o.get("model") == "hizli":
        sc = 2 if k <= 2.05 else 3 if k <= 3.05 else 4
    return "realesrgan", name, sc


def ai_cmd(o, inp, out, fmt=None):
    """Yapay zekâ büyütme komutu (Real-ESRGAN ya da Real-CUGAN). Dönen: (komut, çalışma klasörü)."""
    tool, model, sc = ai_tool(o)
    if tool != "realesrgan":
        ensure_tool(tool)
    ensure_model(model)
    exe = tool_path(tool)
    if tool == "realcugan":
        g = int(o.get("gurultu") or 0)
        # models-pro: 0 = gürültü giderme yok (en keskin), -1 = korumacı, 3 = güçlü gürültü giderme
        noise = 0 if g < 15 else -1 if g < 55 else 3
        cmd = [str(exe), "-i", str(inp), "-o", str(out), "-n", str(noise), "-s", str(sc), "-m", model]
    elif tool == "waifu2x":
        g = int(o.get("gurultu") or 0)
        # -1 = gürültü temizleme yok (taramalar korunur), 0/1/2 = hafif/orta/güçlü
        noise = -1 if g < 20 else 0 if g < 45 else 1 if g < 75 else 2
        cmd = [str(exe), "-i", str(inp), "-o", str(out), "-n", str(noise), "-s", str(sc), "-m", str(exe.parent / model)]
        if o.get("_final"):
            cmd += ["-x"]  # son kayıtta TTA: 8 yönlü işleyip birleştirir, daha temiz (biraz yavaş)
    else:
        cmd = [str(exe), "-i", str(inp), "-o", str(out), "-n", model, "-s", str(sc)]
    if fmt:
        cmd += ["-f", fmt]
    import guard
    tile = int(o.get("tile") or 0) or guard.ai_tile()
    if tile:
        cmd += ["-t", str(tile)]
    j = guard.ai_threads()
    if j:
        cmd += ["-j", j]
    return cmd, str(exe.parent)
DEFAULT = {"model": "hizli", "olcek": 2, "hedef": "x2", "keskin": 45, "gurultu": 25, "blok": True,
           "parlak": 0, "kontrast": 0, "doygun": 0, "fps": "kaynak", "fps_ai": True,
           # yüz
           "yuz": False, "yuz_guc": 70, "yuz_model": "gfpgan",
           # gelişmiş netlik
           "ai_guc": 100, "detay": 0, "yumusat": 0, "bant": False, "titreme": 0, "kayipsiz": False,
           # renk ve görüntü
           "sicaklik": 0, "golge": 0, "parlak_alan": 0, "gamma": 0, "vinyet": 0, "gren": 0, "oto_renk": False,
           # çıktı ve ses
           "kalite": "yuksek", "codec": "h264", "foto_bicim": "png", "bicim": "kaynak", "bas": 0, "bit": 0, "ses_temizle": False, "ses_dengele": False, "ses": True,
           # serbest ayar
           "ozel_w": 1920, "ozel_h": 0, "ozel_fps": 60, "crf_ozel": False, "crf": 16, "enc_hiz": "", "ses_kbps": 192, "tile": 0, "bit10": False, "supersample": False}
FACE_URLS = {"gfpgan": "https://huggingface.co/Neus/GFPGANv1.4/resolve/main/GFPGANv1.4.onnx",
             "codeformer": "https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/codeformer.onnx",
             "yunet": "https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"}
CHUNK = 240  # bir seferde işlenen kare (disk dolmasın)


def settings(s=None):
    o = dict(DEFAULT)
    o.update(load_settings().get("kalite_ayar") or {})
    o.update(s or {})
    return o


# ---------------------------------------------------------------- araçlar
def tool_path(name):
    d = AI / name
    if not d.exists():
        return None
    for p in d.rglob(TOOLS[name]["exe"]):
        return p
    return None


def ensure_tool(name, job=None, lo=0.0, hi=0.05):
    p = tool_path(name)
    if p:
        return p
    from curl_cffi import requests as creq
    AI.mkdir(parents=True, exist_ok=True)
    z = AI / (name + ".zip")
    if job:
        job.set(lo, f"Yapay zekâ aracı indiriliyor ({name}, ilk seferlik)...")
    r = creq.get(TOOLS[name]["url"], stream=True, timeout=300, allow_redirects=True)
    try:
        r.raise_for_status()
        total = int(r.headers.get("content-length") or 0)
        got = 0
        with open(z, "wb") as f:
            for chunk in r.iter_content():
                f.write(chunk)
                got += len(chunk)
                if job and total:
                    job.set(lo + (hi - lo) * got / total, f"Yapay zekâ aracı indiriliyor ({name}) %{int(got * 100 / total)}")
    finally:
        r.close()
    with zipfile.ZipFile(z) as zf:
        zf.extractall(AI / name)
    z.unlink(missing_ok=True)
    p = tool_path(name)
    if not p:
        raise RuntimeError(f"{name} kurulamadı")
    if not IS_WIN:
        p.chmod(0o755)
    return p


def _download(url, dest, job=None, lo=0.0, hi=0.05, label="indiriliyor"):
    from curl_cffi import requests as creq
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    r = creq.get(url, stream=True, timeout=600, allow_redirects=True)
    try:
        r.raise_for_status()
        total = int(r.headers.get("content-length") or 0)
        got = 0
        with open(tmp, "wb") as f:
            for chunk in r.iter_content():
                f.write(chunk)
                got += len(chunk)
                if job and total:
                    job.set(lo + (hi - lo) * got / total, f"{label} %{int(got * 100 / total)}")
    finally:
        r.close()
    if tmp.stat().st_size < 10000:
        tmp.unlink(missing_ok=True)
        raise RuntimeError("İndirme başarısız: " + url)
    tmp.replace(dest)


def _venv_python():
    exe = Path(sys.executable)
    if exe.name.lower() == "pythonw.exe" and (exe.parent / "python.exe").exists():
        return str(exe.parent / "python.exe")
    return str(exe)


def ensure_ort(job=None, lo=0.0):
    """Yapay zekâ modelleri için paketler: OpenCV + (Windows'ta) DirectML'li onnxruntime. Dönen: (python, ort_klasörü|None)."""
    ortdir = AI / "yuz" / "ort"
    py = _venv_python()
    try:
        import cv2  # noqa: F401
    except Exception:
        if job:
            job.set(lo, "Yapay zekâ paketleri kuruluyor (ilk seferlik)...")
        r = run([py, "-m", "pip", "install", "opencv-python-headless", "--disable-pip-version-check", "-q"], timeout=900)
        if r.returncode != 0:
            raise RuntimeError("Paket kurulamadı: " + (r.stderr or "")[-200:])
    if IS_WIN and not (ortdir / "onnxruntime").exists():
        if job:
            job.set(lo, "Ekran kartı (DirectML) desteği kuruluyor (ilk seferlik)...")
        r = run([py, "-m", "pip", "install", "onnxruntime-directml", "--no-deps", "--target", str(ortdir), "--disable-pip-version-check", "-q"], timeout=900)
        if r.returncode != 0:
            shutil.rmtree(ortdir, ignore_errors=True)  # yoksa işlemciyle çalışır
    if not IS_WIN:
        try:
            import onnxruntime  # noqa: F401
        except Exception:
            run([py, "-m", "pip", "install", "onnxruntime", "--disable-pip-version-check", "-q"], timeout=900)
    return py, (ortdir if (ortdir / "onnxruntime").exists() else None)


def ensure_face(job=None, lo=0.0, hi=0.06, model="gfpgan"):
    """Yüz netleştirme için model ve paketler (ilk seferde ~350 MB)."""
    d = AI / "yuz"
    gfp = d / ("codeformer.onnx" if model == "codeformer" else "GFPGANv1.4.onnx")
    yun, ortdir = d / "yunet.onnx", d / "ort"
    py = _venv_python()
    try:
        import cv2  # noqa: F401
    except Exception:
        if job:
            job.set(lo, "Yüz netleştirme paketleri kuruluyor (ilk seferlik)...")
        r = run([py, "-m", "pip", "install", "opencv-python-headless", "--disable-pip-version-check", "-q"], timeout=900)
        if r.returncode != 0:
            raise RuntimeError("Yüz paketi kurulamadı: " + (r.stderr or "")[-200:])
    if IS_WIN and not (ortdir / "onnxruntime").exists():
        if job:
            job.set(lo, "Ekran kartı (DirectML) desteği kuruluyor (ilk seferlik)...")
        r = run([py, "-m", "pip", "install", "onnxruntime-directml", "--no-deps", "--target", str(ortdir), "--disable-pip-version-check", "-q"], timeout=900)
        if r.returncode != 0:
            shutil.rmtree(ortdir, ignore_errors=True)  # yoksa işlemciyle çalışır
    if not yun.exists():
        _download(FACE_URLS["yunet"], yun, job, lo, lo + (hi - lo) * .1, "Yüz bulucu indiriliyor")
    if not gfp.exists():
        _download(FACE_URLS["codeformer" if model == "codeformer" else "gfpgan"], gfp, job, lo + (hi - lo) * .1, hi,
                  "Yüz netleştirme modeli indiriliyor (~" + ("380" if model == "codeformer" else "340") + " MB)")
    return py, gfp, yun, (ortdir if (ortdir / "onnxruntime").exists() else None)


def face_cmd(target, strength, model="gfpgan"):
    py, gfp, yun, ortdir = ensure_face(model=model)
    return [py, str(Path(__file__).with_name("face_worker.py")), str(target), str(int(strength)), str(gfp), str(yun), str(ortdir or "")]


_AI_OK = None


def ai_works(job=None):
    """Bu bilgisayarın ekran kartında yapay zekâ (Vulkan) çalışıyor mu? Bir kez dener."""
    global _AI_OK
    if _AI_OK is not None:
        return _AI_OK
    try:
        exe = ensure_tool("realesrgan", job)
        d = CACHE / "ai_test"
        d.mkdir(parents=True, exist_ok=True)
        src, out = d / "t.png", d / "o.png"
        run([FFMPEG, "-y", "-f", "lavfi", "-i", "testsrc2=s=64x64", "-frames:v", "1", str(src)])
        r = run([str(exe), "-i", str(src), "-o", str(out), "-n", "realesr-animevideov3", "-s", "2"], cwd=str(exe.parent), timeout=120)
        _AI_OK = out.exists() and out.stat().st_size > 0
        if not _AI_OK:
            print("[kalite] yapay zekâ testi başarısız:", (r.stderr or r.stdout)[-400:], file=sys.stderr, flush=True)
    except Exception as e:
        print("[kalite] yapay zekâ testi hata:", e, file=sys.stderr, flush=True)
        _AI_OK = False
    return _AI_OK


# ---------------------------------------------------------------- filtreler
def out_size(w, h, o):
    """Çıkış boyutu: biçim (Reels 9:16 vb.) seçildiyse o şekilde, yoksa videonun kendi şekli."""
    b = o.get("bicim") or "kaynak"
    if str(o.get("hedef")) == "ozel":
        return target_size(w, h, "ozel", o)
    if b == "kaynak":
        return target_size(w, h, o.get("hedef", "1080"))
    hd = str(o.get("hedef"))
    short = {"720": 720, "1080": 1080, "1440": 1440, "2160": 2160, "4320": 4320}.get(hd) or (min(w, h) * (int(hd[1]) if hd in ("x2", "x3", "x4") else 1) if hd in ("kaynak", "x2", "x3", "x4") else 1080)
    rw, rh = {"9:16k": (9, 16), "9:16b": (9, 16), "4:5k": (4, 5), "4:5b": (4, 5), "1:1k": (1, 1), "1:1b": (1, 1)}.get(b, (9, 16))
    W, H = short, round(short * rh / rw)
    return W - W % 2, H - H % 2


def target_size(w, h, hedef, o=None):
    if str(hedef) == "ozel":  # serbest çözünürlük: genişlik ya da yükseklik boşsa oran korunur
        o = o or {}
        try:
            ow, oh = int(o.get("ozel_w") or 0), int(o.get("ozel_h") or 0)
        except (TypeError, ValueError):
            ow = oh = 0
        if ow <= 0 and oh <= 0:
            return w - w % 2, h - h % 2
        if ow <= 0:
            ow = round(w * oh / h)
        if oh <= 0:
            oh = round(h * ow / w)
        ow, oh = max(64, min(16384, ow)), max(64, min(16384, oh))
        return ow - ow % 2, oh - oh % 2
    if hedef == "kaynak":
        return w - w % 2, h - h % 2
    if str(hedef) in ("x2", "x3", "x4"):
        k = int(str(hedef)[1])
        return min(16384, w * k) // 2 * 2, min(16384, h * k) // 2 * 2
    short = {"720": 720, "1080": 1080, "1440": 1440, "2160": 2160, "4320": 4320}.get(str(hedef), 1080)
    if w >= h:
        nh = short
        nw = round(w * nh / h)
    else:
        nw = short
        nh = round(h * nw / w)
    return nw - nw % 2, nh - nh % 2


def pre_filters(o):
    f = []
    if o.get("_img") and o.get("model") == "anime_pro" and o.get("model") != "klasik":
        return f  # Waifu2x JPEG gürültüsünü kendisi temizler; ek filtre taramaları ve gri tonları siler
    if o.get("blok"):
        f.append("deblock=filter=strong:block=8")
    g = int(o.get("gurultu") or 0)
    if o.get("model") == "anime_pro":
        g = g // 3  # Real-CUGAN gürültüyü kendisi temizliyor; çift temizlik çizgileri bulanıklaştırmasın
    if g > 0:
        ls = 1 + g / 100 * 7
        f.append(f"hqdn3d={ls:.1f}:{ls * .75:.1f}:{ls * 1.5:.1f}:{ls * 1.1:.1f}")
    return f


def sharpen(k, pix="yuv420p"):
    """Keskinlik (0-100): kenar maskeli, iki ölçekli keskinleştirme.
    Sadece çizgi ve kenarlar keskinleşir; düz yerlerde gürültü ve kumlanma büyümez, renklerde hale oluşmaz."""
    s = max(0, min(100, int(k))) / 100
    f = [f"cas=strength={0.25 + 0.65 * s:.2f}"]  # genel, uyarlanabilir netlik
    big, small = 0.4 + 2.6 * s, 0.2 + 1.3 * s   # orta kalınlıkta çizgiler + ince detay (sadece parlaklık kanalı)
    f.append(f"format={pix},split[ks0][ks1];[ks1]split[ks2][ks3];"
             f"[ks2]unsharp=7:7:{big:.2f}:3:3:0,unsharp=3:3:{small:.2f}:3:3:0[ksh];"
             f"[ks3]sobel=planes=1:scale={1.5 + 3.5 * s:.2f},gblur=sigma=1.2:planes=1[ksm];"
             "[ks0][ksh][ksm]maskedmerge=planes=1")
    return f


def deflicker(o):
    """Yapay zekânın kareden kareye kıpırdayan detaylarını yumuşatır (sadece zamanda, hareketi bulanıklaştırmaz)."""
    t = int(o.get("titreme") or 0)
    if t <= 0:
        return []
    v = 1 + t / 100 * 6
    return [f"hqdn3d=0:0:{v:.1f}:{v:.1f}"]


def post_filters(o, W, H):
    b = o.get("bicim") or "kaynak"
    # süper örnekleme: netleştirme hedefin 2 katı boyutta yapılır, sonra kaliteli küçültülür.
    # çizgiler pürüzsüz kalır (testere dişi / basamak olmaz), ince çizgiler kopmaz.
    ss = 1.0
    if o.get("supersample"):
        ss = min(2.0, 8192 / max(W, H), (3840 * 2160 * 2 / max(1, W * H)) ** 0.5)
        if ss < 1.25:
            ss = 1.0
    SW, SH = (int(W * ss) // 2 * 2, int(H * ss) // 2 * 2) if ss > 1 else (W, H)
    if b.endswith("k"):  # ekranı doldur (kenarlardan kırp)
        f = [f"scale={SW}:{SH}:force_original_aspect_ratio=increase:flags=lanczos,crop={SW}:{SH},setsar=1"]
    elif b.endswith("b"):  # bulanık arka plan + video ortada
        f = [f"split[kqa][kqb];[kqa]scale={SW}:{SH}:force_original_aspect_ratio=increase,crop={SW}:{SH},boxblur=24:3,eq=brightness=-0.06[kqbg];"
             f"[kqb]scale={SW}:{SH}:force_original_aspect_ratio=decrease:flags=lanczos[kqfg];[kqbg][kqfg]overlay=(W-w)/2:(H-h)/2,setsar=1"]
    else:
        f = [f"scale={SW}:{SH}:flags=lanczos"]
    y = int(o.get("yumusat") or 0)
    if y > 0:  # kenar yumuşatma (tırtıkları azaltır, kenarları korur)
        f.append(f"smartblur=lr={(0.6 + y / 100 * 2.4) * min(ss, 1.6):.2f}:ls={0.15 + y / 100 * 0.6:.2f}:lt=-2")
    dt = int(o.get("detay") or 0)
    if dt > 0:  # detay / doku güçlendirme (yerel kontrast)
        f.append(f"unsharp=13:13:{dt / 100 * 0.9:.2f}:13:13:0")
    k = int(o.get("keskin") or 0)
    if k > 0:
        f += sharpen(k, "yuv444p" if o.get("_img") else "yuv420p")
    if ss > 1:
        f.append(f"scale={W}:{H}:flags=lanczos+accurate_rnd+full_chroma_int,setsar=1")
    f += deflicker(o)
    if o.get("bant"):
        f.append("deband=1thr=0.02:2thr=0.02:3thr=0.02:range=16:blur=1")
    if o.get("oto_renk"):
        f.append("normalize=blackpt=black:whitept=white:smoothing=40:independence=0.5")
    sc = int(o.get("sicaklik") or 0)
    if sc:
        f.append(f"colortemperature=temperature={6500 - sc * 30:.0f}:mix=1:pl=1")
    b, c, s, g = float(o.get("parlak") or 0), float(o.get("kontrast") or 0), float(o.get("doygun") or 0), float(o.get("gamma") or 0)
    if b or c or s or g:
        f.append(f"eq=brightness={b / 200:.3f}:contrast={1 + c / 100:.3f}:saturation={max(0, 1 + s / 100):.3f}:gamma={max(0.3, 1 + g / 100):.3f}")
    gs, hs = float(o.get("golge") or 0), float(o.get("parlak_alan") or 0)
    if gs or hs:
        f.append(f"curves=all='0/0 0.25/{min(0.5, max(0.02, 0.25 + gs / 100 * 0.15)):.3f} 0.75/{min(0.98, max(0.5, 0.75 + hs / 100 * 0.15)):.3f} 1/1'")
    v = int(o.get("vinyet") or 0)
    if v > 0:
        f.append(f"vignette=angle={0.15 + v / 100 * 0.6:.3f}")
    gr = int(o.get("gren") or 0)
    if gr > 0:
        f.append(f"noise=alls={max(1, int(gr / 100 * 22))}:allf=t")
    return f


def audio_filters(o):
    a = []
    if o.get("ses_temizle"):
        a += ["highpass=f=70", "afftdn=nr=14:nf=-35"]
    if o.get("ses_dengele"):
        a.append("loudnorm=I=-14:TP=-1.5:LRA=11")
    return ",".join(a)


SPEED = {"hizli": "fast", "orta": "medium", "yavas": "slow", "cok_yavas": "veryslow"}


def encoder_args(o):
    import guard
    th = guard.ffmpeg_threads()
    thr = ["-threads", str(th)] if th else []
    if o.get("kalite") == "ust":  # en üst düzey: çok düşük sıkıştırma, yavaş ve özenli kodlama
        crf264, crf265, pre = 11, 12, "slow"
    else:
        q = {"yuksek": 15, "normal": 19, "kucuk": 24}.get(o.get("kalite") or "yuksek", 15)
        crf264, crf265, pre = q, q + 2, "medium"
    if o.get("crf_ozel"):  # serbest ayar: sıkıştırmayı kullanıcı seçer
        c = max(0, min(40, int(o.get("crf") or 16)))
        crf264, crf265 = c, c
    pre = SPEED.get(o.get("enc_hiz") or "", pre)
    if o.get("codec") == "h265":
        ten = o.get("kalite") == "ust" or o.get("bit10")
        return ["-c:v", "libx265", "-preset", pre, "-crf", str(crf265), "-tag:v", "hvc1", "-pix_fmt", "yuv420p10le" if ten else "yuv420p",
                "-x265-params", ("aq-mode=3:no-sao=1:deblock=-1,-1:" if o.get("kalite") == "ust" else "") + "log-level=error" + (f":pools={th}" if th else "")] + thr
    return ["-c:v", "libx264", "-preset", pre, "-crf", str(crf264)] + (["-tune", "film"] if o.get("kalite") == "ust" else []) + ["-pix_fmt", "yuv420p"] + thr


def _vf(parts):
    return ",".join(parts) if parts else "null"


# ---------------------------------------------------------------- önizleme (tek kare)
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff"}


def size_tag(W, H):
    """Dosya adı için boyut etiketi: 8K, 4K, 2K, FullHD, HD."""
    m = min(W, H)
    return "8K" if m >= 4320 else "4K" if m >= 2160 else "2K" if m >= 1440 else "FullHD" if m >= 1080 else "HD" if m >= 720 else "iyilestirilmis"


def is_image(path):
    return Path(path).suffix.lower() in IMAGE_EXT


def preview(path, t, opts, final=None):
    """Tek kareyi işler. final verilirse (fotoğraf) sonucu tam kalitede oraya yazar."""
    o = settings(opts)
    info = probe(path)
    W, H = out_size(info["width"], info["height"], o)
    key = hashlib.md5(json.dumps([str(path), round(float(t), 2), o, W, H, Path(path).stat().st_mtime], sort_keys=True).encode()).hexdigest()[:16]
    d = CACHE / "kalite" / key
    before, after = d / "once.jpg", d / "sonra.jpg"
    MW, MH = target_size(info["width"], info["height"], o["hedef"], o)
    o["_k"] = max(MW / max(1, info["width"]), MH / max(1, info["height"]))
    o["_img"], o["_final"] = is_image(path), bool(final)
    if after.exists() and not final:
        return key, W, H, bool(o["model"] != "klasik" and _AI_OK)
    d.mkdir(parents=True, exist_ok=True)
    raw = d / "kare.png"
    seek = [] if is_image(path) else ["-ss", f"{float(t):.3f}"]
    r = run([FFMPEG, "-y", *seek, "-i", str(path), "-frames:v", "1", str(raw)])
    if not raw.exists():
        raise RuntimeError("Kare alınamadı: " + (r.stderr or "")[-200:])
    if not final:
        run([FFMPEG, "-y", "-i", str(raw), "-vf", _vf(post_filters({"bicim": o.get("bicim")}, W, H)).replace("lanczos", "bicubic"), "-q:v", "2", str(before)])
    pre = d / "on.png"
    run([FFMPEG, "-y", "-i", str(raw), "-vf", _vf(pre_filters(o)), str(pre)])
    src = pre
    used_ai = False
    if o["model"] != "klasik" and ai_works():
        up = d / "ai.png"
        if ai_tool(o)[0] != "realesrgan":
            ensure_tool(ai_tool(o)[0])
        cmd, cwd = ai_cmd(o, pre, up)
        r = run(cmd, cwd=cwd, timeout=1200 if final else 300)
        if not up.exists() and ai_tool(o)[0] == "waifu2x":  # bu ekran kartında Waifu2x çalışmadıysa Real-CUGAN ile dene
            print("[kalite] waifu2x çalışmadı, Real-CUGAN deneniyor:", (r.stderr or r.stdout or "")[-300:], file=sys.stderr, flush=True)
            o2 = dict(o, _img=False)
            ensure_tool("realcugan")
            cmd, cwd = ai_cmd(o2, pre, up)
            run(cmd, cwd=cwd, timeout=600)
        if up.exists():
            src, used_ai = up, True
    if o.get("yuz"):
        fc = d / "yuz.png"
        shutil.copy(src, fc)
        r = run(face_cmd(fc, o.get("yuz_guc", 70), o.get("yuz_model") or "gfpgan"), timeout=600)
        if r.returncode != 0:
            raise RuntimeError("Yüz netleştirme çalışmadı: " + (r.stderr or "")[-250:])
        src = fc
    g = int(o.get("ai_guc", 100))
    if used_ai and g < 100:  # yapay zekâ gücü: orijinalle karıştır
        mix = d / "karisim.png"
        run([FFMPEG, "-y", "-i", str(src), "-i", str(pre), "-filter_complex",
             f"[0]scale={MW}:{MH}:flags=lanczos,setsar=1[a];[1]scale={MW}:{MH}:flags=lanczos,setsar=1[b];[b][a]blend=all_mode=normal:all_opacity={g / 100:.2f}",
             str(mix)])
        if mix.exists():
            src = mix
    if final:
        final = Path(final)
        q = ["-q:v", "1", "-qmin", "1"] if final.suffix.lower() in (".jpg", ".jpeg") else (["-quality", "95"] if final.suffix.lower() == ".webp" else [])
        gr = int(o.get("gren") or 0)
        vf = post_filters(o, W, H)
        if gr > 0:  # fotoğrafta zamana bağlı gren yerine sabit gren
            vf = [x.replace(":allf=t", "") for x in vf]
        run([FFMPEG, "-y", "-i", str(src), "-vf", _vf(vf), "-frames:v", "1", *q, str(final)])
        if not final.exists():
            raise RuntimeError("Fotoğraf kaydedilemedi")
        return key, W, H, used_ai
    run([FFMPEG, "-y", "-i", str(src), "-vf", _vf(post_filters(o, W, H)), "-q:v", "2", str(after)])
    if not after.exists():
        raise RuntimeError("Önizleme oluşturulamadı")
    return key, W, H, used_ai


def process_image(job, path, opts):
    """Fotoğraf kalitesini artırır ve çıktı klasörüne kaydeder."""
    o = settings(opts)
    o["_img"] = True
    path = Path(path)
    job.set(0.05, "Hazırlanıyor...")
    if o["model"] != "klasik":
        ensure_tool("realesrgan", job, 0.05, 0.2)
        if ai_tool(o)[0] != "realesrgan":
            ensure_tool(ai_tool(o)[0], job, 0.2, 0.3)
        if not ai_works(job):
            job.set(0.3, "Ekran kartında yapay zekâ çalışmadı, klasik mod kullanılıyor...")
    if o.get("yuz"):
        ensure_face(job, 0.3, 0.45, o.get("yuz_model") or "gfpgan")
    ext = {"png": ".png", "jpg": ".jpg", "webp": ".webp"}.get(o.get("foto_bicim") or "png", ".png")
    folder = Path(load_settings().get("cikti_klasoru") or (Path.home() / "Pictures"))
    folder.mkdir(parents=True, exist_ok=True)
    try:
        _i = probe(path)
        W, H = out_size(_i["width"], _i["height"], o)
    except Exception:
        W = H = 0
    out = folder / f"{safe_name(path.stem, 60)}_{size_tag(W, H)}{ext}"
    i = 2
    while out.exists():
        out = folder / f"{safe_name(path.stem, 60)}_{size_tag(W, H)}_{i}{ext}"
        i += 1
    job.extra = {"t0": time.time(), "parca": "Fotoğraf"}
    job.set(0.5, "Yapay zekâ fotoğrafı netleştiriyor...")
    job.extra["asama"] = job.message
    _check(job)
    preview(path, 0, opts, final=out)
    _check(job)
    job.set(1, "Hazır! " + out.name)
    return {"path": str(out), "name": out.name, "image": True}


# ---------------------------------------------------------------- tüm video
def _count(d):
    try:
        return sum(1 for _ in os.scandir(d))
    except Exception:
        return 0


def _run_watch(cmd, job, outdir, expect, lo, hi, msg, cwd=None):
    """Aracı çalıştırırken çıkan kare sayısından ilerleme göster."""
    p = _start(job, cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, cwd=cwd)
    err = []
    th = threading.Thread(target=lambda: err.append(p.stderr.read().decode("utf-8", "replace")), daemon=True)
    th.start()
    while p.poll() is None:
        if job.cancelled:
            p.kill()
            raise RuntimeError("İptal edildi")
        if not job.paused:
            n = _count(outdir)
            job.set(lo + (hi - lo) * min(1, n / max(1, expect)), msg)
        time.sleep(0.5)
    job.procs.discard(p)
    th.join(2)
    _check(job)
    return p.returncode, "".join(err)


def _start(job, cmd, **kw):
    """Alt süreci başlat ve işe kaydet (duraklat / iptal / kapanışta durdurmak için)."""
    job.wait_if_paused()
    _check(job)
    p = subprocess.Popen(cmd, creationflags=NO_WINDOW, **kw)
    job.procs.add(p)
    if job.paused:
        proc_pause(p, True)
    return p


def _check(job):
    if job.cancelled:
        raise RuntimeError("İptal edildi")
    if core.SHUTTING_DOWN:
        raise RuntimeError("Uygulama kapandı")


def _ff(cmd, job):
    p = _start(job, cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    _, e = p.communicate()
    job.procs.discard(p)
    _check(job)
    if p.returncode != 0:
        e = (e or b"").decode("utf-8", "replace")
        lines = [l for l in e.splitlines() if "rror" in l or "nvalid" in l] or (e or "hata").splitlines()
        raise RuntimeError("FFmpeg: " + lines[-1][-250:])
    return p


def _run_lines(cmd, job, lo, hi, msg):
    """'i/toplam' satırı basan işçiyi çalıştırıp ilerleme göster."""
    p = _start(job, cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
    err = []
    th = threading.Thread(target=lambda: err.append(p.stderr.read()), daemon=True)
    th.start()
    for line in p.stdout:
        if job.cancelled:
            p.kill()
            raise RuntimeError("İptal edildi")
        a, _, b = line.strip().partition("/")
        if a.isdigit() and b.isdigit():
            job.set(lo + (hi - lo) * int(a) / max(1, int(b)), msg)
    p.wait()
    job.procs.discard(p)
    th.join(2)
    _check(job)
    return p.returncode, "".join(err)


WORK = CACHE / "kalite_is"


def unfinished():
    """Uygulama kapanınca yarım kalan kalite işleri (kaldığı yerden devam edilebilir)."""
    res = []
    if not WORK.exists():
        return res
    for d in WORK.iterdir():
        f = d / "durum.json"
        if not f.exists():
            shutil.rmtree(d, ignore_errors=True)
            continue
        try:
            st = json.loads(f.read_text("utf-8"))
        except Exception:
            shutil.rmtree(d, ignore_errors=True)
            continue
        if not Path(st.get("path", "")).exists():
            shutil.rmtree(d, ignore_errors=True)
            continue
        res.append({"id": d.name, "path": st["path"], "name": Path(st["path"]).name, "progress": st.get("progress", 0),
                    "done": len(st.get("done", [])), "total": st.get("total", 0), "updated": f.stat().st_mtime})
    return sorted(res, key=lambda x: -x["updated"])


def discard(rid):
    if rid and rid.replace("_", "").isalnum():
        shutil.rmtree(WORK / rid, ignore_errors=True)


def process(job, path, opts, resume=None):
    work = WORK / (resume or job.id)
    state = {}
    if resume:
        try:
            state = json.loads((work / "durum.json").read_text("utf-8"))
            path, opts = state["path"], state["opts"]
        except Exception:
            raise RuntimeError("Yarım kalan iş bulunamadı, baştan başlat.")
    o = settings(opts)
    path = Path(path)
    info = probe(path)
    full, sfps = float(info["duration"] or 0), float(info["fps"] or 30)
    if full <= 0:
        raise RuntimeError("Video süresi okunamadı")
    t0 = max(0.0, min(float(o.get("bas") or 0), full - 0.2))
    t1 = float(o.get("bit") or 0)
    t1 = full if t1 <= t0 else min(t1, full)
    dur = t1 - t0
    W, H = out_size(info["width"], info["height"], o)
    tfps = sfps if o["fps"] == "kaynak" else max(1.0, min(240.0, float(o.get("ozel_fps") or sfps))) if o["fps"] == "ozel" else float(o["fps"])
    mult = max(1.0, tfps / sfps)
    use_ai = o["model"] != "klasik"
    if use_ai and not ai_works(job):
        use_ai = False
        job.set(0.04, "Ekran kartında yapay zekâ çalışmadı, klasik mod kullanılıyor...")
    use_rife = mult > 1.01 and o.get("fps_ai", True)
    if use_rife:
        try:
            ensure_tool("rife", job, 0.04, 0.06)
        except Exception:
            use_rife = False
    use_face = bool(o.get("yuz"))
    if use_face:
        ensure_face(job, 0.06, 0.09, o.get("yuz_model") or "gfpgan")
    folder = Path(load_settings().get("cikti_klasoru") or (Path.home() / "Videos"))
    folder.mkdir(parents=True, exist_ok=True)
    out = folder / f"{safe_name(path.stem, 60)}_{size_tag(W, H)}.mp4"
    i = 2
    while out.exists():
        out = folder / f"{safe_name(path.stem, 60)}_{size_tag(W, H)}_{i}.mp4"
        i += 1
    if not resume:
        shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)
    done = set(state.get("done") or [])
    if use_ai != state.get("use_ai", use_ai) or use_face != state.get("use_face", use_face) or use_rife != state.get("use_rife", use_rife):
        done = set()  # araçlar değiştiyse parçalar uyumsuz olur

    chunk_size = {"v": state.get("chunk")}

    def save_state(progress):
        try:
            (work / "durum.json").write_text(json.dumps({"path": str(path), "opts": opts, "done": sorted(done), "total": total_chunks, "chunk": chunk_size["v"],
                                                         "progress": round(progress, 4), "use_ai": use_ai, "use_face": use_face,
                                                         "use_rife": use_rife}), "utf-8")
        except Exception:
            pass

    enc = encoder_args(o)
    af = audio_filters(o)
    aud = (["-c:a", "aac", "-b:a", f'{int(o.get("ses_kbps") or 192)}k'] + (["-af", af] if af else [])) if o.get("ses", True) else ["-an"]
    MW, MH = target_size(info["width"], info["height"], o["hedef"], o)
    o["_k"] = max(MW / max(1, info["width"]), MH / max(1, info["height"]))  # ara adımlar videonun kendi şeklinde
    # kalan süre: duraklatmalar hariç, bu oturumda işlenen kısma göre hesaplanır
    t_start = time.time()
    job.extra = {"t0": t_start, **({"resume": resume} if resume else {})}
    _set = job.set
    base = {"p": None, "t": None}
    ok = False

    def set_eta(p=None, msg=None):
        _set(p, msg)
        p = job.progress
        if msg is not None:
            job.extra["asama"] = msg
        if base["p"] is None and p >= 0.09:
            base["p"], base["t"] = p, job.active_time(t_start)
        if base["p"] is not None and p - base["p"] > 0.004:
            el = job.active_time(t_start) - base["t"]
            rate = (p - base["p"]) / max(el, 0.1)
            rem = (1 - p) / max(rate, 1e-6)
            old = job.extra.get("eta")
            now_old = max(0, old - (time.time() - job.eta_at)) if old is not None and job.eta_at else None
            job.extra["eta"] = rem if now_old is None else now_old * 0.7 + rem * 0.3
            job.eta_at = time.time()
    job.set = set_eta
    total_chunks = 1
    try:
        # yapay zekâ, yüz ve RIFE yoksa: tek geçişte bitir (hızlı)
        if not use_ai and not use_rife and not use_face:
            save_state(0)
            vf = pre_filters(o) + post_filters(o, W, H)
            if mult > 1.01:
                vf.append(f"minterpolate=fps={tfps:g}:mi_mode=mci:mc_mode=aobmc:vsbmc=1")
            elif abs(tfps - sfps) > 0.01:  # FPS düşürme (ör. 30 -> 24)
                vf.append(f"fps={tfps:g}")
            from core import run_ffmpeg_progress
            cmd = [FFMPEG, "-y", "-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", str(path), "-map", "0:v:0", "-map", "0:a:0?",
                   "-vf", _vf(vf), *enc, *aud, "-movflags", "+faststart", str(out)]
            job.extra["parca"] = "Klasik mod (tek geçiş)"
            code, err = run_ffmpeg_progress(cmd, dur, lambda p: job.set(0.09 + 0.89 * p, "Kalite artırılıyor (klasik)"),
                                            lambda: job.cancelled or core.SHUTTING_DOWN, job=job)
            _check(job)
            if code != 0:
                raise RuntimeError("Kalite artırma başarısız: " + (err or "")[-250:])
            job.set(1, "Hazır! " + out.name)
            ok = True
            return {"path": str(out), "name": out.name}
        f0 = int(round(t0 * sfps))
        total_frames = max(1, int(dur * sfps))
        # kayıpsız modda ara kareler PNG (hiç kalite kaybı yok); disk dolmasın diye parçalar daha küçük
        X = "png" if o.get("kayipsiz") else "jpg"
        QV = [] if X == "png" else ["-q:v", "2"]
        CH = int(state.get("chunk") or (60 if X == "png" else CHUNK))
        chunk_size["v"] = CH
        chunks = list(range(0, total_frames, CH))
        total_chunks = len(chunks)
        segs = []
        if use_ai and ai_tool(o)[0] != "realesrgan":
            ensure_tool(ai_tool(o)[0], job, 0.08, 0.09)
        fexe = tool_path("rife")
        g = int(o.get("ai_guc", 100))
        save_state(0.09)
        for ci, a in enumerate(chunks):
            n = min(CH, total_frames - a)
            lo, hi = 0.09 + 0.87 * ci / len(chunks), 0.09 + 0.87 * (ci + 1) / len(chunks)
            seg = work / f"seg{ci:04d}.mp4"
            if ci in done and seg.exists() and seg.stat().st_size > 0:
                segs.append(seg)
                _set(hi, f"Parça {ci + 1}/{len(chunks)} önceden bitmişti")
                continue
            span = lambda x, y: (lo + (hi - lo) * x, lo + (hi - lo) * y)  # noqa: E731
            label = f"Parça {ci + 1}/{len(chunks)}"
            job.extra["parca"] = f"{ci + 1} / {len(chunks)}"
            d_in, d_up, d_mid, d_fps = (work / x for x in ("in", "up", "mid", "fps"))
            for d in (d_in, d_up, d_mid, d_fps):
                shutil.rmtree(d, ignore_errors=True)
                d.mkdir()
            job.set(lo, "Kareler çıkarılıyor...")
            _ff([FFMPEG, "-y", "-ss", f"{(f0 + a) / sfps:.4f}", "-i", str(path), "-frames:v", str(n), "-vf", _vf(pre_filters(o)),
                 *QV, "-start_number", "1", str(d_in / f"%08d.{X}")], job)
            n = _count(d_in) or n
            cur = d_in
            if use_ai:
                acmd, acwd = ai_cmd(o, d_in, d_up, X)
                code, err = _run_watch(acmd, job, d_up, n, *span(.05, .5), "Yapay zekâ netleştiriyor...", cwd=acwd)
                if code != 0 or _count(d_up) < n:
                    raise RuntimeError("Yapay zekâ netleştirme başarısız: " + err[-250:])
                cur = d_up
            if use_face:
                code, err = _run_lines(face_cmd(cur, o.get("yuz_guc", 70), o.get("yuz_model") or "gfpgan"), job, *span(.5, .7), "Yüzler netleştiriliyor...")
                if code != 0:
                    raise RuntimeError("Yüz netleştirme başarısız: " + err[-250:])
            if use_ai and (g < 100 or use_rife):
                if g < 100:
                    _ff([FFMPEG, "-y", "-i", str(cur / f"%08d.{X}"), "-i", str(d_in / f"%08d.{X}"), "-filter_complex",
                         f"[0]scale={MW}:{MH}:flags=lanczos,setsar=1[a];[1]scale={MW}:{MH}:flags=lanczos,setsar=1[b];[b][a]blend=all_mode=normal:all_opacity={g / 100:.2f}",
                         *QV, str(d_mid / f"%08d.{X}")], job)
                else:
                    _ff([FFMPEG, "-y", "-i", str(cur / f"%08d.{X}"), "-vf", f"scale={MW}:{MH}:flags=lanczos", *QV, str(d_mid / f"%08d.{X}")], job)
                cur = d_mid
            rate = sfps
            if use_rife:
                want = max(2, int(round(n * mult)))
                code, err = _run_watch([str(fexe), "-i", str(cur), "-o", str(d_fps), "-m", "rife-v4.6", "-n", str(want), "-f", f"%08d.{X}"],
                                       job, d_fps, want, *span(.7, .9), f"Ara kareler üretiliyor ({tfps:g} FPS)...", cwd=str(fexe.parent))
                if code != 0 or _count(d_fps) < 2:
                    raise RuntimeError("Akıcılaştırma (RIFE) başarısız: " + err[-250:])
                cur, rate = d_fps, sfps * (_count(d_fps) / n)
            job.set(lo + (hi - lo) * .92, "Video yazılıyor...")
            _ff([FFMPEG, "-y", "-framerate", f"{rate:.4f}", "-i", str(cur / f"%08d.{X}"), "-vf", _vf(post_filters(o, W, H)),
                 "-r", f"{tfps:g}", *enc, str(seg)], job)
            segs.append(seg)
            done.add(ci)
            save_state(hi)
            for d in (d_in, d_up, d_mid, d_fps):
                shutil.rmtree(d, ignore_errors=True)
            _check(job)
        lst = work / "liste.txt"
        lst.write_text("".join(f"file '{s.as_posix()}'\n" for s in segs), "utf-8")
        job.extra["parca"] = "Birleştiriliyor"
        job.set(0.97, "Parçalar birleştiriliyor...")
        _ff([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", str(path),
             "-map", "0:v", "-map", "1:a?", "-c:v", "copy", *aud, "-shortest", "-movflags", "+faststart", str(out)], job)
        job.set(1, "Hazır! " + out.name)
        ok = True
        return {"path": str(out), "name": out.name}
    except Exception:
        out.unlink(missing_ok=True)
        raise
    finally:
        job.set = _set
        job.extra.pop("eta", None)
        # uygulama kapanıyorsa bitmiş parçalar kalsın: sonra kaldığı yerden devam
        if ok or not core.SHUTTING_DOWN:
            shutil.rmtree(work, ignore_errors=True)
