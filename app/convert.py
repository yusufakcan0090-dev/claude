"""Dönüştür: herhangi bir videoyu / sesi başka biçime çevirir (toplu)."""
import json
import subprocess
from pathlib import Path

from core import FFMPEG, FFPROBE, NO_WINDOW, load_settings, run_ffmpeg_progress, safe_name

# biçim -> (uzantı, tür, açıklama)
FORMATS = {
    "mp4": (".mp4", "video", "MP4 (H.264) — her yerde açılır"),
    "mp4_h265": (".mp4", "video", "MP4 (H.265) — aynı kalite, yarı boyut"),
    "mov": (".mov", "video", "MOV — iPhone / Mac / montaj programları"),
    "mkv": (".mkv", "video", "MKV — kayıpsız taşıyıcı"),
    "webm": (".webm", "video", "WEBM (VP9) — web siteleri için"),
    "avi": (".avi", "video", "AVI — eski cihazlar"),
    "gif": (".gif", "video", "GIF — hareketli resim"),
    "mp3": (".mp3", "audio", "MP3 — sadece ses"),
    "wav": (".wav", "audio", "WAV — kayıpsız ses"),
    "m4a": (".m4a", "audio", "M4A (AAC) — sadece ses"),
    "flac": (".flac", "audio", "FLAC — kayıpsız, küçük"),
    "ogg": (".ogg", "audio", "OGG (Opus) — sadece ses"),
    # fotoğraf
    "jpg": (".jpg", "image", "JPG — her yerde açılır, küçük"),
    "png": (".png", "image", "PNG — kayıpsız, şeffaflık korunur"),
    "webp": (".webp", "image", "WEBP — çok küçük, web için"),
    "bmp": (".bmp", "image", "BMP — sıkıştırmasız"),
    "tiff": (".tiff", "image", "TIFF — baskı / arşiv"),
    "ico": (".ico", "image", "ICO — simge (en fazla 256 px)"),
}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff", ".ico", ".jfif", ".avif"}


def is_image(path):
    return Path(path).suffix.lower() in IMAGE_EXT
CRF = {"kaynak": 16, "yuksek": 19, "normal": 23, "kucuk": 28}


def streams(path):
    """Kaynağın video/ses kodekleri, boyutu, süresi."""
    r = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "stream=codec_type,codec_name,width,height,r_frame_rate:format=duration",
                        "-of", "json", str(path)], capture_output=True, text=True, encoding="utf-8", errors="replace", creationflags=NO_WINDOW)
    try:
        d = json.loads(r.stdout or "{}")
    except Exception:
        d = {}
    v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), None)
    a = next((s for s in d.get("streams", []) if s.get("codec_type") == "audio"), None)
    try:
        dur = float((d.get("format") or {}).get("duration") or 0)
    except Exception:
        dur = 0
    return {"v": v.get("codec_name") if v else None, "a": a.get("codec_name") if a else None,
            "w": (v or {}).get("width") or 0, "h": (v or {}).get("height") or 0, "dur": dur}


def _scale(o, info):
    r = str(o.get("cozunurluk") or "kaynak")
    if r == "kaynak" or not info["w"]:
        return None
    short = int(r)
    w, h = info["w"], info["h"]
    if min(w, h) <= short:
        return None  # büyütme yapma
    return f"scale={'-2:' + str(short) if w >= h else str(short) + ':-2'}:flags=lanczos"


def build(src, dst, fmt, o, info):
    """FFmpeg komutunu kurar. Mümkünse yeniden kodlamadan (kayıpsız, çok hızlı) kopyalar."""
    ext, kind, _ = FORMATS[fmt]
    q = o.get("kalite") or "yuksek"
    vf = [x for x in [_scale(o, info)] if x]
    fps = str(o.get("fps") or "kaynak")
    if fps != "kaynak":
        vf.append(f"fps={fps}")
    mute = bool(o.get("sessiz"))
    cmd = [FFMPEG, "-y", "-i", str(src)]
    if kind == "image":
        if not info["v"]:
            raise RuntimeError("Bu dosya okunamadı")
        f = [x for x in [_scale(o, info)] if x]
        qual = {"kaynak": ["-q:v", "1"], "yuksek": ["-q:v", "2"], "normal": ["-q:v", "4"], "kucuk": ["-q:v", "7"]}
        if fmt == "jpg":
            args = qual.get(q, ["-q:v", "2"]) + ["-pix_fmt", "yuvj444p" if q in ("kaynak", "yuksek") else "yuvj420p"]
            f.append("format=rgb24")  # şeffaf yerler siyaha dönüşmesin diye beyaz zemin aşağıda
            f = ["split[i0][i1];[i0]drawbox=c=white:t=fill[bg];[bg][i1]overlay=format=auto"] + f
        elif fmt == "webp":
            args = ["-quality", {"kaynak": "100", "yuksek": "92", "normal": "82", "kucuk": "70"}.get(q, "92")] + (["-lossless", "1"] if q == "kaynak" else [])
        elif fmt == "ico":
            f = ["scale='min(256,iw)':'min(256,ih)':force_original_aspect_ratio=decrease"]
            args = []
        elif fmt == "png":
            args = ["-compression_level", "6"]
        else:
            args = []
        return cmd + ["-frames:v", "1", *(["-vf", ",".join(f)] if f else []), *args, "-update", "1", str(dst)], False
    if kind == "audio":
        if not info["a"]:
            raise RuntimeError("Bu videoda ses yok")
        acodec = {"mp3": ["-c:a", "libmp3lame", "-b:a", "320k" if q in ("kaynak", "yuksek") else "192k"],
                  "wav": ["-c:a", "pcm_s16le"], "flac": ["-c:a", "flac"],
                  "m4a": ["-c:a", "aac", "-b:a", "256k" if q in ("kaynak", "yuksek") else "160k"],
                  "ogg": ["-c:a", "libopus", "-b:a", "192k" if q in ("kaynak", "yuksek") else "128k"]}[fmt]
        if fmt == "m4a" and info["a"] == "aac" and q == "kaynak":
            acodec = ["-c:a", "copy"]
        if fmt == "mp3" and info["a"] == "mp3" and q == "kaynak":
            acodec = ["-c:a", "copy"]
        return cmd + ["-vn", "-map", "0:a:0", *acodec, str(dst)], False
    if not info["v"]:
        raise RuntimeError("Bu dosyada görüntü yok")
    if fmt == "gif":
        w = {"kaynak": 640, "1080": 1080, "720": 720, "480": 480}.get(str(o.get("cozunurluk") or "kaynak"), 640)
        f = int(fps) if fps != "kaynak" else 15
        g = (f"fps={f},scale='min({w},iw)':-2:flags=lanczos,split[a][b];[a]palettegen=stats_mode=diff[p];"
             f"[b][p]paletteuse=dither=sierra2_4a:diff_mode=rectangle")
        return cmd + ["-an", "-vf", g, "-loop", "0", str(dst)], False
    # yeniden kodlamadan kopyalama: biçim değişiyor ama içerik aynı kalıyor (kayıpsız)
    copy_v = {"mp4": ("h264", "hevc", "mpeg4", "av1"), "mov": ("h264", "hevc", "prores", "mpeg4", "mjpeg"),
              "mkv": ("h264", "hevc", "vp9", "vp8", "av1", "mpeg4", "mpeg2video", "prores"), "webm": ("vp9", "vp8", "av1"),
              "avi": ("mpeg4", "h264", "mjpeg")}.get(fmt, ())
    copy_a = {"mp4": ("aac", "mp3", "ac3", "opus"), "mov": ("aac", "mp3", "pcm_s16le", "alac"), "mkv": None,
              "webm": ("opus", "vorbis"), "avi": ("mp3", "ac3", "pcm_s16le")}.get(fmt, ())
    can_copy = not vf and q == "kaynak" and info["v"] in copy_v and fmt != "mp4_h265"
    if can_copy:
        acopy = mute or not info["a"] or copy_a is None or info["a"] in copy_a
        audio = ["-an"] if mute or not info["a"] else (["-c:a", "copy"] if acopy else ["-c:a", "aac", "-b:a", "256k"])
        tag = ["-tag:v", "hvc1"] if info["v"] == "hevc" and fmt in ("mp4", "mov") else []
        fast = ["-movflags", "+faststart"] if fmt in ("mp4", "mov") else []
        return cmd + ["-map", "0:v:0", "-map", "0:a:0?", "-c:v", "copy", *tag, *audio, *fast, str(dst)], True
    crf = CRF.get(q, 19)
    v = {"mp4": ["-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p"],
         "mp4_h265": ["-c:v", "libx265", "-preset", "medium", "-crf", str(crf + 3), "-tag:v", "hvc1", "-pix_fmt", "yuv420p",
                      "-x265-params", "log-level=error"],
         "mov": ["-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p"],
         "mkv": ["-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p"],
         "webm": ["-c:v", "libvpx-vp9", "-crf", str(crf + 12), "-b:v", "0", "-row-mt", "1", "-deadline", "good", "-cpu-used", "2"],
         "avi": ["-c:v", "mpeg4", "-q:v", str(max(2, crf // 6)), "-vtag", "xvid"]}[fmt]
    a = {"webm": ["-c:a", "libopus", "-b:a", "160k"], "avi": ["-c:a", "libmp3lame", "-b:a", "256k"]}.get(fmt, ["-c:a", "aac", "-b:a", "256k"])
    audio = ["-an"] if mute or not info["a"] else a
    fast = ["-movflags", "+faststart"] if fmt in ("mp4", "mp4_h265", "mov") else []
    return cmd + ["-map", "0:v:0", "-map", "0:a:0?", *(["-vf", ",".join(vf)] if vf else []), *v, *audio, *fast, str(dst)], False


def out_path(src, ext, o):
    src = Path(src)
    folder = src.parent if (o.get("klasor") or "kaynak") == "kaynak" else Path(load_settings().get("cikti_klasoru") or (Path.home() / "Videos"))
    folder.mkdir(parents=True, exist_ok=True)
    base = safe_name(src.stem, 80)
    out = folder / f"{base}{ext}"
    i = 2
    while out.exists() or out.resolve() == src.resolve():
        out = folder / f"{base}_{i}{ext}"
        i += 1
    return out


def job_convert(job, files, fmt, o):
    if fmt not in FORMATS:
        raise RuntimeError("Bilinmeyen biçim")
    ext = FORMATS[fmt][0]
    done, fails = [], []
    n = len(files)
    for i, src in enumerate(files):
        if job.cancelled:
            raise RuntimeError("İptal edildi")
        lo, hi = i / n, (i + 1) / n
        name = Path(src).name
        job.extra = {"parca": f"{i + 1} / {n}", "dosya": name}
        try:
            if is_image(src) and FORMATS[fmt][1] != "image" and fmt != "gif":
                raise RuntimeError("Fotoğraf bu biçime çevrilemez (fotoğraf biçimi seç)")
            if not is_image(src) and FORMATS[fmt][1] == "image":
                raise RuntimeError("Video fotoğraf biçimine çevrilemez")
            info = streams(src)
            dst = out_path(src, ext, o)
            cmd, copied = build(src, dst, fmt, o, info)
            job.set(lo, f"{name} → {ext[1:].upper()}" + (" (hızlı, kayıpsız)" if copied else ""))
            code, err = run_ffmpeg_progress(cmd, max(1.0, info["dur"]),
                                            lambda p, lo=lo, hi=hi, name=name: job.set(lo + (hi - lo) * p, f"{name} %{int(p * 100)}"),
                                            lambda: job.cancelled, job=job)
            if code != 0 and copied:  # kopyalama olmadıysa yeniden kodla
                dst.unlink(missing_ok=True)
                cmd, _ = build(src, dst, fmt, {**o, "kalite": "yuksek" if (o.get("kalite") or "") == "kaynak" else o.get("kalite")}, info)
                code, err = run_ffmpeg_progress(cmd, max(1.0, info["dur"]), lambda p, lo=lo, hi=hi: job.set(lo + (hi - lo) * p), lambda: job.cancelled, job=job)
            if job.cancelled:
                dst.unlink(missing_ok=True)
                raise RuntimeError("İptal edildi")
            if code != 0 or not dst.exists():
                dst.unlink(missing_ok=True)
                lines = [x for x in (err or "").splitlines() if x.strip()]
                raise RuntimeError(lines[-1][-200:] if lines else "dönüştürülemedi")
            done.append({"path": str(dst), "name": dst.name, "src": name})
        except RuntimeError as e:
            if "İptal" in str(e):
                raise
            fails.append({"src": name, "hata": str(e)})
    if not done:
        raise RuntimeError("Hiçbir dosya dönüştürülemedi: " + (fails[0]["hata"] if fails else ""))
    job.set(1, f"{len(done)} dosya hazır" + (f", {len(fails)} hata" if fails else ""))
    return {"files": done, "fails": fails, "path": done[0]["path"], "name": done[0]["name"]}
