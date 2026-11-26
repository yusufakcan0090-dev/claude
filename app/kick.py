"""Video kaynakları: Kick kanalları, YouTube/Twitch/her link, YouTube arama ve indirme (yt-dlp)."""
import re
import shutil
import sys
from pathlib import Path

from core import FFMPEG, INDIRILEN, ONIZLEME, safe_name


def _ydl(opts=None):
    import yt_dlp
    base = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "ffmpeg_location": str(Path(FFMPEG).parent) if Path(FFMPEG).exists() else None,
        "retries": 5,
        "fragment_retries": 10,
        "concurrent_fragment_downloads": 6,
        "socket_timeout": 30,
    }
    deno = _deno()
    if deno:
        base["js_runtimes"] = {"deno": {"path": deno}}
    if opts:
        base.update(opts)
    if not base["ffmpeg_location"]:
        base.pop("ffmpeg_location")
    return yt_dlp.YoutubeDL(base)


def _deno():
    """YouTube için gereken JavaScript motoru (pip ile kurulan deno)."""
    exe = "deno.exe" if sys.platform.startswith("win") else "deno"
    for c in (Path(sys.executable).parent / exe, Path(sys.executable).parent / "Scripts" / exe):
        if c.exists():
            return str(c)
    return shutil.which("deno")


def channel_slug(text):
    text = (text or "").strip()
    m = re.search(r"kick\.com/([\w-]+)", text)
    if m:
        return m.group(1).lower()
    return re.sub(r"[^\w-]", "", text).lower()


def _entry(e):
    thumb = e.get("thumbnail")
    if not thumb and e.get("thumbnails"):
        thumb = e["thumbnails"][-1].get("url")
    url = e.get("url") or e.get("webpage_url")
    if url and not url.startswith("http") and e.get("ie_key") == "Youtube":
        url = "https://www.youtube.com/watch?v=" + url
    return {
        "id": e.get("id"),
        "url": url,
        "title": e.get("title") or e.get("id"),
        "duration": e.get("duration") or 0,
        "thumbnail": thumb,
        "views": e.get("view_count") or 0,
        "timestamp": e.get("timestamp") or 0,
        "availability": e.get("availability") or "public",
        "channel": e.get("channel") or e.get("uploader") or "",
    }


def _entries(url, limit=60):
    with _ydl({"extract_flat": "in_playlist", "playlistend": limit}) as ydl:
        info = ydl.extract_info(url, download=False)
    out = []
    for e in (info or {}).get("entries") or []:
        if not e:
            continue
        if e.get("_type") == "playlist" or (e.get("url") or "").endswith(("/shorts", "/streams")):
            continue
        out.append(_entry(e))
    return out


def list_source(text):
    """Arama kutusuna yazılan her şeyi anlar:
    - Kick kanal adı / linki -> yayın kayıtları + izleyici klipleri
    - YouTube / Twitch kanal, oynatma listesi linki -> videolar
    - Tek video linki -> {"single": ...}
    - Boşluklu yazı -> YouTube'da arama"""
    text = (text or "").strip()
    is_url = bool(re.match(r"^https?://", text, re.I)) or "." in text.split("/")[0]
    if is_url and not text.lower().startswith("http"):
        text = "https://" + text
    if re.search(r"kick\.com/[\w-]+/?(\?.*)?$", text, re.I) and "clip=" not in text:
        return list_channel(text)
    if not is_url:
        if " " not in text:
            return list_channel(text)  # tek kelime: Kick kanal adı
        vids = _entries(f"ytsearch40:{text}", 40)
        return {"slug": text, "source": "youtube-arama", "title": f"YouTube: {text}", "videos": vids, "clips": [], "errors": []}
    url = text
    if re.search(r"youtube\.com/(@[\w.-]+|channel/[\w-]+|c/[\w-]+|user/[\w-]+)/?$", url, re.I):
        url = url.rstrip("/") + "/videos"
    if re.search(r"twitch\.tv/[\w]+/?$", url, re.I):
        url = url.rstrip("/") + "/videos?filter=archives"
    with _ydl({"extract_flat": "in_playlist", "playlistend": 60}) as ydl:
        info = ydl.extract_info(url, download=False)
    if info.get("_type") == "playlist" or info.get("entries") is not None:
        vids = [_entry(e) for e in info.get("entries") or [] if e and e.get("_type") != "playlist"]
        return {"slug": info.get("title") or url, "source": "liste", "title": info.get("title") or "",
                "videos": vids, "clips": [], "errors": []}
    return {"single": _entry({**info, "url": info.get("webpage_url") or url})}


def _kick_get(url):
    """Kick'e tarayıcı gibi doğrudan sor (yt-dlp boş dönerse yedek yol)."""
    from curl_cffi import requests as creq
    r = creq.get(url, impersonate="chrome", timeout=25,
                 headers={"Accept": "application/json", "Referer": "https://kick.com/"})
    if r.status_code == 404:
        raise LookupError("Kick'te böyle bir kanal yok")
    r.raise_for_status()
    return r.json()


def _ms_or_s(v):
    try:
        v = float(v or 0)
    except (TypeError, ValueError):
        return 0
    return v / 1000 if v > 36000 else v  # Kick süreyi bazen milisaniye verir


def _ts(v):
    if not v:
        return 0
    try:
        from datetime import datetime
        return int(datetime.fromisoformat(str(v).replace("Z", "+00:00").replace(" ", "T")).timestamp())
    except Exception:
        return 0


def _kick_direct(slug):
    vids, clips, errs = [], [], []
    try:
        ch = _kick_get(f"https://kick.com/api/v2/channels/{slug}")
    except LookupError as e:
        raise RuntimeError(f'"{slug}" adında bir Kick kanalı bulunamadı. Adı kanal linkindeki gibi yaz (kick.com/...).') from e
    except Exception as e:
        ch = None
        errs.append("kanal: " + _short(e))
    lst = []
    for u in (f"https://kick.com/api/v2/channels/{slug}/videos", f"https://kick.com/api/v1/channels/{slug}"):
        try:
            d = _kick_get(u)
            lst = d if isinstance(d, list) else (d.get("previous_livestreams") or d.get("data") or [])
            if lst:
                break
        except Exception as e:
            errs.append("videolar: " + _short(e))
    for v in lst:
        vid = (v.get("video") or {}).get("uuid") or v.get("uuid")
        if not vid:
            continue
        th = v.get("thumbnail")
        th = (th.get("src") or th.get("url")) if isinstance(th, dict) else th
        vids.append({"id": vid, "url": f"https://kick.com/{slug}/videos/{vid}",
                     "title": v.get("session_title") or v.get("title") or "Yayın",
                     "duration": _ms_or_s(v.get("duration")), "thumbnail": th,
                     "views": v.get("views") or v.get("viewer_count") or 0,
                     "timestamp": _ts(v.get("start_time") or v.get("created_at")),
                     "availability": "public", "channel": slug})
    raw = []
    for srt in ("date", "view"):
        try:
            d = _kick_get(f"https://kick.com/api/v2/channels/{slug}/clips?sort={srt}&time=all")
            raw += d.get("clips") or (d.get("data") or {}).get("clips") or []
        except Exception as e:
            errs.append("klipler: " + _short(e))
    seen = set()
    try:
        for c in raw:
            cid = c.get("id")
            if not cid or cid in seen:
                continue
            seen.add(cid)
            clips.append({"id": cid, "url": f"https://kick.com/{slug}/clips/{cid}",
                          "title": c.get("title") or "Klip", "duration": _ms_or_s(c.get("duration")),
                          "thumbnail": c.get("thumbnail_url"),
                          "views": c.get("views") or c.get("view_count") or 0,
                          "timestamp": _ts(c.get("created_at")), "availability": "public", "channel": slug})
    except Exception as e:
        errs.append("klipler: " + _short(e))
    return vids, clips, errs, ch


def _merge(*lists):
    out, seen = [], set()
    for lst in lists:
        for c in lst or []:
            key = c.get("id") or c.get("url")
            if key in seen:
                continue
            seen.add(key)
            out.append(c)
    return out


def list_channel(text):
    slug = channel_slug(text)
    if not slug:
        raise ValueError("Kanal adı boş")
    res = {"slug": slug, "source": "kick", "title": slug, "videos": [], "clips": [], "errors": []}
    errs = []
    from concurrent.futures import ThreadPoolExecutor
    urls = {"videos": f"https://kick.com/{slug}/videos",
            "pop": f"https://kick.com/{slug}/clips?sort=view&range=all",
            "new": f"https://kick.com/{slug}/clips?sort=date&range=all"}
    got = {}
    with ThreadPoolExecutor(3) as ex:
        futs = {k: ex.submit(_entries, u) for k, u in urls.items()}
        for k, f in futs.items():
            try:
                got[k] = f.result()
            except Exception as e:
                got[k] = []
                errs.append(("Yayın kayıtları: " if k == "videos" else "Klipler: ") + _short(e))
    res["videos"] = got["videos"]
    res["clips"] = _merge(got["new"], got["pop"])
    if res["clips"]:
        errs = [x for x in errs if not x.startswith("Klipler")]
    if not res["videos"] or not res["clips"]:
        try:
            v2, c2, e2, _ = _kick_direct(slug)
            if not res["videos"]:
                res["videos"] = v2
            if not res["clips"]:
                res["clips"] = c2
            errs += e2
        except RuntimeError:
            if not res["videos"] and not res["clips"]:
                raise
    res["clips"].sort(key=lambda c: c.get("timestamp") or 0, reverse=True)
    if not res["videos"] and not res["clips"]:
        detail = (" Ayrıntı: " + " | ".join(errs)) if errs else ""
        raise RuntimeError(f'"{slug}" kanalında video ya da klip bulunamadı. Kanal yayın kayıtlarını '
                           f'kapatmış olabilir. Bir yayın/klip linkini direkt yapıştırmayı dene ya da '
                           f'GUNCELLE.bat çalıştır.' + detail)
    return res


def _short(e):
    s = str(e)
    s = re.sub(r"\x1b\[[0-9;]*m", "", s)
    return s.replace("ERROR: ", "")[:200]


def _hook(job, lo, hi, label):
    def h(d):
        if job.cancelled:
            raise RuntimeError("İptal edildi")
        if d.get("status") == "downloading":
            tot = d.get("total_bytes") or d.get("total_bytes_estimate")
            frac = None
            if tot:
                frac = d.get("downloaded_bytes", 0) / tot
            elif d.get("fragment_count"):
                frac = (d.get("fragment_index") or 0) / d["fragment_count"]
            spd = d.get("speed")
            sp = f" · {spd/1e6:.1f} MB/sn" if spd else ""
            if frac is not None:
                job.set(lo + (hi - lo) * min(1, frac), f"{label} %{int(frac*100)}{sp}")
            else:
                job.set(None, f"{label}{sp}")
    return h


def download(job, url, title, lo=0.0, hi=1.0, section=None, preview=False):
    """Videoyu indirir, dosya yolunu döndürür.
    section=(start, end) verilirse sadece o aralık indirilir.
    preview=True ise en düşük kalite (an bulmak için hızlı) indirilir."""
    folder = ONIZLEME if preview else INDIRILEN
    name = safe_name(title, 50)
    if section:
        name += f"_{int(section[0])}-{int(section[1])}"
    outtmpl = str(folder / (name + "_%(id)s.%(ext)s"))
    opts = {
        "outtmpl": outtmpl,
        "progress_hooks": [_hook(job, lo, hi, "Düşük kalitede indiriliyor (analiz için)" if preview else "İndiriliyor")],
        "merge_output_format": "mp4",
        "format": ("worst[vcodec!=none][acodec!=none]/worst" if preview
                   else "bv*[height<=1440]+ba/b[height<=1440]/bv*+ba/b"),
    }
    if section:
        import yt_dlp.utils
        opts["download_ranges"] = yt_dlp.utils.download_range_func(None, [tuple(section)])
        opts["force_keyframes_at_cuts"] = False
    with _ydl(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        path = info.get("requested_downloads", [{}])[0].get("filepath") or ydl.prepare_filename(info)
    p = Path(path)
    if not p.exists():
        cands = sorted(folder.glob(name + "_*"), key=lambda x: x.stat().st_mtime, reverse=True)
        if not cands:
            raise RuntimeError("İndirilen dosya bulunamadı")
        p = cands[0]
    return str(p), info
