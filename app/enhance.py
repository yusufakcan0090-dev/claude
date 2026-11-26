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

from core import BIN, CACHE, FFMPEG, NO_WINDOW, load_settings, probe, run, safe_name

AI = BIN / "ai"
IS_WIN = os.name == "nt"
EXE = ".exe" if IS_WIN else ""
TOOLS = {
    "realesrgan": {
        "url": ("https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-windows.zip" if IS_WIN
                else "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-ubuntu.zip"),
        "exe": "realesrgan-ncnn-vulkan" + EXE,
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
}
DEFAULT = {"model": "hizli", "olcek": 2, "hedef": "1080", "keskin": 45, "gurultu": 25, "blok": True,
           "parlak": 0, "kontrast": 0, "doygun": 0, "fps": "kaynak", "fps_ai": True}
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
def target_size(w, h, hedef):
    if hedef == "kaynak":
        return w - w % 2, h - h % 2
    short = {"720": 720, "1080": 1080, "1440": 1440, "2160": 2160}.get(str(hedef), 1080)
    if w >= h:
        nh = short
        nw = round(w * nh / h)
    else:
        nw = short
        nh = round(h * nw / w)
    return nw - nw % 2, nh - nh % 2


def pre_filters(o):
    f = []
    if o.get("blok"):
        f.append("deblock=filter=strong:block=8")
    g = int(o.get("gurultu") or 0)
    if g > 0:
        ls = 1 + g / 100 * 7
        f.append(f"hqdn3d={ls:.1f}:{ls * .75:.1f}:{ls * 1.5:.1f}:{ls * 1.1:.1f}")
    return f


def post_filters(o, W, H):
    f = [f"scale={W}:{H}:flags=lanczos"]
    k = int(o.get("keskin") or 0)
    if k > 0:
        f.append(f"cas=strength={min(1.0, k / 100 * 0.9):.2f}")
        if k > 60:  # çizgileri daha da belirginleştir
            f.append(f"unsharp=5:5:{(k - 60) / 40 * 0.8:.2f}:5:5:0")
    b, c, s = float(o.get("parlak") or 0), float(o.get("kontrast") or 0), float(o.get("doygun") or 0)
    if b or c or s:
        f.append(f"eq=brightness={b / 200:.3f}:contrast={1 + c / 100:.3f}:saturation={max(0, 1 + s / 100):.3f}")
    return f


def _vf(parts):
    return ",".join(parts) if parts else "null"


# ---------------------------------------------------------------- önizleme (tek kare)
def preview(path, t, opts):
    o = settings(opts)
    info = probe(path)
    W, H = target_size(info["width"], info["height"], o["hedef"])
    key = hashlib.md5(json.dumps([str(path), round(float(t), 2), o, W, H], sort_keys=True).encode()).hexdigest()[:16]
    d = CACHE / "kalite" / key
    before, after = d / "once.jpg", d / "sonra.jpg"
    if after.exists():
        return key, W, H, bool(o["model"] != "klasik" and _AI_OK)
    d.mkdir(parents=True, exist_ok=True)
    raw = d / "kare.png"
    r = run([FFMPEG, "-y", "-ss", f"{float(t):.3f}", "-i", str(path), "-frames:v", "1", str(raw)])
    if not raw.exists():
        raise RuntimeError("Kare alınamadı: " + (r.stderr or "")[-200:])
    run([FFMPEG, "-y", "-i", str(raw), "-vf", f"scale={W}:{H}:flags=bicubic", "-q:v", "2", str(before)])
    pre = d / "on.png"
    run([FFMPEG, "-y", "-i", str(raw), "-vf", _vf(pre_filters(o)), str(pre)])
    src = pre
    used_ai = False
    if o["model"] != "klasik" and ai_works():
        name, sc = MODELS.get(o["model"], MODELS["hizli"])
        if o["model"] == "hizli":
            sc = int(o.get("olcek") or 2)
        up = d / "ai.png"
        exe = tool_path("realesrgan")
        run([str(exe), "-i", str(pre), "-o", str(up), "-n", name, "-s", str(sc)], cwd=str(exe.parent), timeout=300)
        if up.exists():
            src, used_ai = up, True
    run([FFMPEG, "-y", "-i", str(src), "-vf", _vf(post_filters(o, W, H)), "-q:v", "2", str(after)])
    if not after.exists():
        raise RuntimeError("Önizleme oluşturulamadı")
    return key, W, H, used_ai


# ---------------------------------------------------------------- tüm video
def _count(d):
    try:
        return sum(1 for _ in os.scandir(d))
    except Exception:
        return 0


def _run_watch(cmd, job, outdir, expect, lo, hi, msg, cwd=None):
    """Aracı çalıştırırken çıkan kare sayısından ilerleme göster."""
    p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, cwd=cwd, creationflags=NO_WINDOW)
    err = []
    th = threading.Thread(target=lambda: err.append(p.stderr.read().decode("utf-8", "replace")), daemon=True)
    th.start()
    while p.poll() is None:
        if job.cancelled:
            p.kill()
            raise RuntimeError("İptal edildi")
        n = _count(outdir)
        job.set(lo + (hi - lo) * min(1, n / max(1, expect)), msg)
        time.sleep(0.5)
    th.join(2)
    return p.returncode, "".join(err)


def _ff(cmd, job):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", creationflags=NO_WINDOW)
    if r.returncode != 0:
        lines = [l for l in (r.stderr or "").splitlines() if "rror" in l or "nvalid" in l] or (r.stderr or "hata").splitlines()
        raise RuntimeError("FFmpeg: " + lines[-1][-250:])
    return r


def process(job, path, opts):
    o = settings(opts)
    path = Path(path)
    info = probe(path)
    dur, sfps = float(info["duration"] or 0), float(info["fps"] or 30)
    if dur <= 0:
        raise RuntimeError("Video süresi okunamadı")
    W, H = target_size(info["width"], info["height"], o["hedef"])
    tfps = sfps if o["fps"] == "kaynak" else float(o["fps"])
    mult = max(1.0, tfps / sfps)
    use_ai = o["model"] != "klasik"
    if use_ai and not ai_works(job):
        use_ai = False
        job.set(0.05, "Ekran kartında yapay zekâ çalışmadı, klasik mod kullanılıyor...")
    use_rife = mult > 1.01 and o.get("fps_ai", True)
    if use_rife:
        try:
            ensure_tool("rife", job, 0.05, 0.08)
        except Exception:
            use_rife = False
    folder = Path(load_settings().get("cikti_klasoru") or (Path.home() / "Videos"))
    folder.mkdir(parents=True, exist_ok=True)
    out = folder / f"{safe_name(path.stem, 60)}_HD.mp4"
    i = 2
    while out.exists():
        out = folder / f"{safe_name(path.stem, 60)}_HD_{i}.mp4"
        i += 1
    work = CACHE / "kalite_is" / job.id
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)
    enc = ["-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p"]
    try:
        # yapay zekâ ve RIFE yoksa: tek geçişte bitir (hızlı)
        if not use_ai and not use_rife:
            vf = pre_filters(o) + post_filters(o, W, H)
            if mult > 1.01:
                vf.append(f"minterpolate=fps={tfps:g}:mi_mode=mci:mc_mode=aobmc:vsbmc=1")
            from core import run_ffmpeg_progress
            cmd = [FFMPEG, "-y", "-i", str(path), "-vf", _vf(vf), *enc, "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)]
            code, err = run_ffmpeg_progress(cmd, dur, lambda p: job.set(0.08 + 0.9 * p, f"Kalite artırılıyor (klasik) %{int(p * 100)}"), lambda: job.cancelled)
            if code != 0:
                raise RuntimeError("Kalite artırma başarısız: " + (err or "")[-250:])
            job.set(1, "Hazır! " + out.name)
            return {"path": str(out), "name": out.name}
        total_frames = max(1, int(dur * sfps))
        chunks = list(range(0, total_frames, CHUNK))
        segs = []
        model, sc = MODELS.get(o["model"], MODELS["hizli"])
        if o["model"] == "hizli":
            sc = int(o.get("olcek") or 2)
        rexe, fexe = tool_path("realesrgan"), tool_path("rife")
        for ci, a in enumerate(chunks):
            n = min(CHUNK, total_frames - a)
            lo, hi = 0.08 + 0.88 * ci / len(chunks), 0.08 + 0.88 * (ci + 1) / len(chunks)
            label = f"Parça {ci + 1}/{len(chunks)}"
            d_in, d_up, d_mid, d_fps = (work / x for x in ("in", "up", "mid", "fps"))
            for d in (d_in, d_up, d_mid, d_fps):
                shutil.rmtree(d, ignore_errors=True)
                d.mkdir()
            job.set(lo, f"{label}: kareler çıkarılıyor...")
            _ff([FFMPEG, "-y", "-ss", f"{a / sfps:.4f}", "-i", str(path), "-frames:v", str(n), "-vf", _vf(pre_filters(o)),
                 "-q:v", "2", "-start_number", "1", str(d_in / "%08d.jpg")], job)
            n = _count(d_in) or n
            cur = d_in
            if use_ai:
                code, err = _run_watch([str(rexe), "-i", str(d_in), "-o", str(d_up), "-n", model, "-s", str(sc), "-f", "jpg"],
                                       job, d_up, n, lo + (hi - lo) * .05, lo + (hi - lo) * (.6 if use_rife else .9),
                                       f"{label}: yapay zekâ netleştiriyor...", cwd=str(rexe.parent))
                if code != 0 or _count(d_up) < n:
                    raise RuntimeError("Yapay zekâ netleştirme başarısız: " + err[-250:])
                cur = d_up
            if use_rife:
                # RIFE'ı hedef boyutta çalıştır (4K karelerde çok yavaşlamasın)
                _ff([FFMPEG, "-y", "-i", str(cur / "%08d.jpg"), "-vf", f"scale={W}:{H}:flags=lanczos", "-q:v", "2", str(d_mid / "%08d.jpg")], job)
                want = max(2, int(round(n * mult)))
                code, err = _run_watch([str(fexe), "-i", str(d_mid), "-o", str(d_fps), "-m", "rife-v4.6", "-n", str(want), "-f", "%08d.jpg"],
                                       job, d_fps, want, lo + (hi - lo) * .6, lo + (hi - lo) * .9,
                                       f"{label}: ara kareler üretiliyor ({tfps:g} FPS)...", cwd=str(fexe.parent))
                if code != 0 or _count(d_fps) < 2:
                    raise RuntimeError("Akıcılaştırma (RIFE) başarısız: " + err[-250:])
                cur, rate = d_fps, sfps * (_count(d_fps) / n)
            else:
                rate = sfps
            seg = work / f"seg{ci:04d}.mp4"
            job.set(lo + (hi - lo) * .92, f"{label}: video yazılıyor...")
            _ff([FFMPEG, "-y", "-framerate", f"{rate:.4f}", "-i", str(cur / "%08d.jpg"), "-vf", _vf(post_filters(o, W, H)),
                 "-r", f"{tfps:g}", *enc, str(seg)], job)
            segs.append(seg)
            for d in (d_in, d_up, d_mid, d_fps):
                shutil.rmtree(d, ignore_errors=True)
            if job.cancelled:
                raise RuntimeError("İptal edildi")
        lst = work / "liste.txt"
        lst.write_text("".join(f"file '{s.as_posix()}'\n" for s in segs), "utf-8")
        job.set(0.97, "Parçalar birleştiriliyor...")
        _ff([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-i", str(path), "-map", "0:v", "-map", "1:a?",
             "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out)], job)
        job.set(1, "Hazır! " + out.name)
        return {"path": str(out), "name": out.name}
    except Exception:
        out.unlink(missing_ok=True)
        raise
    finally:
        shutil.rmtree(work, ignore_errors=True)
