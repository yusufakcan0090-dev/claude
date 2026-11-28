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
        return smart_search(text)
    url = text
    shorts = []
    if re.search(r"youtube\.com/(@[\w.-]+|channel/[\w-]+|c/[\w-]+|user/[\w-]+)/?$", url, re.I):
        try:
            shorts = _entries(url.rstrip("/") + "/shorts", 60)
        except Exception:
            shorts = []
        url = url.rstrip("/") + "/videos"
    if re.search(r"twitch\.tv/[\w]+/?$", url, re.I):
        url = url.rstrip("/") + "/videos?filter=archives"
    with _ydl({"extract_flat": "in_playlist", "playlistend": 60}) as ydl:
        info = ydl.extract_info(url, download=False)
    if info.get("_type") == "playlist" or info.get("entries") is not None:
        vids = [_entry(e) for e in info.get("entries") or [] if e and e.get("_type") != "playlist"]
        return {"slug": info.get("title") or url, "source": "liste", "title": info.get("title") or "",
                "videos": vids, "shorts": shorts, "clips": [], "errors": []}
    return {"single": _entry({**info, "url": info.get("webpage_url") or url})}


_KS = None


def _dbg(*a):
    """Kick sorunlarını çözebilmek için ayrıntılı kayıt (veri/kick_kayit.txt)."""
    try:
        from core import VERI
        import time as _t
        p = VERI / "kick_kayit.txt"
        if p.exists() and p.stat().st_size > 400_000:
            p.unlink()
        with open(p, "a", encoding="utf-8") as f:
            f.write(_t.strftime("%H:%M:%S ") + " ".join(str(x) for x in a) + "\n")
    except Exception:
        pass


def _kick_get(url):
    """Kick'e tarayıcı gibi doğrudan sor: önce ana sayfadan çerez al, sonra API (Cloudflare için)."""
    global _KS
    from curl_cffi import requests as creq
    hdr = {"Accept": "application/json, text/plain, */*", "Referer": "https://kick.com/", "Origin": "https://kick.com",
           "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8"}
    last = None
    for imp in ("chrome", "chrome124", "edge101", "safari17_0"):
        try:
            if _KS is None or _KS[0] != imp:
                s = creq.Session(impersonate=imp)
                try:
                    s.get("https://kick.com/", timeout=20)
                except Exception:
                    pass
                _KS = (imp, s)
            r = _KS[1].get(url, timeout=25, headers=hdr)
            body = r.text or ""
            _dbg("GET", url, imp, r.status_code, len(body), body[:160].replace("\n", " "))
            if r.status_code == 404:
                raise LookupError("Kick'te böyle bir kanal yok")
            if r.status_code == 200 and body.lstrip()[:1] in "[{":
                return r.json()
            last = RuntimeError(f"Kick {r.status_code} döndü ({'Cloudflare engeli' if r.status_code in (403, 429, 503) else 'beklenmeyen cevap'})")
        except LookupError:
            raise
        except Exception as e:
            _dbg("HATA", url, imp, repr(e)[:200])
            last = e
        _KS = None
    raise last or RuntimeError("Kick'e ulaşılamadı")


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
    for u in (f"https://kick.com/api/v2/channels/{slug}/clips?cursor=0&sort=date&time=all",
              f"https://kick.com/api/v2/channels/{slug}/clips?cursor=0&sort=view&time=all",
              f"https://kick.com/api/v2/channels/{slug}/clips?sort=view&time=month",
              f"https://kick.com/api/v2/channels/{slug}/clips"):
        try:
            d = _kick_get(u)
            got = d.get("clips") if isinstance(d, dict) else d
            if isinstance(d, dict) and not got:
                got = (d.get("data") or {}).get("clips") if isinstance(d.get("data"), dict) else d.get("data")
            raw += got or []
            if len(raw) >= 40:
                break
        except Exception as e:
            errs.append("klipler: " + _short(e))
            print("[kick] klip yolu başarısız:", u, e, file=sys.stderr, flush=True)
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


_TR_WORDS = set("ve bir bu da de çok ne için ile gibi ama ben sen o biz siz onlar var yok mi mı mu mü değil olan oldu nasıl neden kim şey en daha her kadar sonra önce şimdi bugün yeni komik kesit kesitler anlar anı türkçe türk türkiye yayın yayıncı abi hocam efsane güldüren gülme şaka röportaj sokak dizi film bölüm canlı ile nedir oyun maç gol hikaye korku kamera tepki şov".split())


def _is_turkish(text):
    t = (text or "").lower()
    if any(ch in t for ch in "çğışöüİ"):
        return True
    return any(w.strip(".,!?:;|()[]'\"") in _TR_WORDS for w in t.split())


def _non_latin(text):
    import unicodedata
    for ch in text or "":
        if ch.isalpha():
            try:
                if "LATIN" not in unicodedata.name(ch):
                    return True
            except ValueError:
                return True
    return False


def _turkish_only(vids):
    """YouTube aramasında sadece Türkçe videolar kalsın (Hint, Arap, İngilizce vb. ayıklanır)."""
    tr = [v for v in vids if not _non_latin(v.get("title")) and _is_turkish((v.get("title") or "") + " " + (v.get("channel") or ""))]
    if len(tr) >= 5:
        return tr
    return [v for v in vids if not _non_latin(v.get("title"))] or vids


def youtube_search(text):
    q = text if _is_turkish(text) else text + " türkçe"
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(2) as ex:
        fv = ex.submit(_entries, f"ytsearch60:{q}", 60)
        fs = ex.submit(_entries, f"ytsearch40:{q} shorts", 40)
        try:
            vids = _turkish_only(fv.result())
        except Exception:
            vids = []
        try:
            shorts = _turkish_only(_only_shorts(fs.result()))
        except Exception:
            shorts = []
    shorts = _merge(shorts, [v for v in vids if _is_short(v)])
    ids = {s["id"] for s in shorts}
    return [v for v in vids if v["id"] not in ids], shorts


def _norm(s):
    import unicodedata
    s = unicodedata.normalize("NFKD", (s or "").lower().replace("ı", "i"))
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in s if not unicodedata.combining(c)))


def kick_search(text):
    """Kick'te yazılana en çok benzeyen kanalları bul (yazım hatasına dayanıklı)."""
    import difflib
    import math
    q = _norm(text)
    cands = {}

    def add(slug, followers=0, live=False, name=""):
        if not slug:
            return
        c = cands.setdefault(slug, {"slug": slug, "followers": 0, "live": False, "name": name or slug})
        c["followers"] = max(c["followers"], int(followers or 0))
        c["live"] = c["live"] or bool(live)

    def walk(o):
        if isinstance(o, dict):
            slug = o.get("slug") if isinstance(o.get("slug"), str) else None
            if slug and ("followers_count" in o or "followersCount" in o or "user" in o or "is_live" in o or "isLive" in o):
                user = o.get("user") if isinstance(o.get("user"), dict) else {}
                add(slug, o.get("followers_count") or o.get("followersCount") or user.get("followers_count") or 0,
                    o.get("is_live") or o.get("isLive"), user.get("username") or o.get("username") or "")
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    from urllib.parse import quote
    for u in (f"https://kick.com/api/search?searched_word={quote(text)}", f"https://kick.com/api/v1/search?searched_word={quote(text)}"):
        try:
            walk(_kick_get(u))
            if cands:
                break
        except Exception as e:
            _dbg("arama hata", u, repr(e)[:150])
    # yazılan kelimenin kendisi de bir kanal olabilir
    if q and q not in cands:
        try:
            ch = _kick_get(f"https://kick.com/api/v2/channels/{q}")
            add(ch.get("slug") or q, ch.get("followers_count") or ch.get("followersCount") or 0, (ch.get("livestream") or {}) != {})
        except Exception:
            pass
    out = []
    for c in cands.values():
        sim = max(difflib.SequenceMatcher(None, q, _norm(c["slug"])).ratio(), difflib.SequenceMatcher(None, q, _norm(c["name"])).ratio())
        if q and (q in _norm(c["slug"]) or _norm(c["slug"]) in q):
            sim = max(sim, 0.85)
        c["sim"] = round(sim, 3)
        c["score"] = sim * 3 + math.log10(1 + c["followers"]) * 0.35 + (0.3 if c["live"] else 0)
        out.append(c)
    out.sort(key=lambda c: c["score"], reverse=True)
    _dbg(f"[arama {text}]", [(c["slug"], c["sim"], c["followers"]) for c in out[:6]])
    return out


def smart_search(text):
    """Ne yazılırsa yazılsın en uygun sonucu ver: Kick kanalı (yazım hatasına dayanıklı) + YouTube."""
    from concurrent.futures import ThreadPoolExecutor
    one_word = " " not in text.strip()
    with ThreadPoolExecutor(2) as ex:
        fk = ex.submit(kick_search, text)
        fy = ex.submit(youtube_search, text)
        try:
            kc = fk.result()
        except Exception:
            kc = []
        yv, ys = fy.result()
    res = {"slug": text, "source": "akilli", "title": text, "videos": [], "shorts": ys, "clips": [], "errors": [],
           "suggest": [c["slug"] for c in kc[:6]]}
    best = None
    for c in kc[:4]:
        if c["sim"] < (0.6 if one_word else 0.75):
            continue
        try:
            r = list_channel(c["slug"])
        except Exception:
            continue
        if r["videos"] or r["clips"]:
            best = r
            break
    if best:
        res.update(slug=best["slug"], source="kick", title=f"Kick: {best['slug']}", clips=best["clips"])
        res["videos"] = best["videos"] + yv
        res["kick"] = best["slug"]
        res["suggest"] = [s for s in res["suggest"] if s != best["slug"]]
    else:
        res["videos"] = yv
        res["title"] = f"YouTube: {text}"
        res["source"] = "youtube-arama"
    if not res["videos"] and not res["clips"] and not res["shorts"]:
        raise RuntimeError(f'"{text}" için bir şey bulunamadı. Başka bir şekilde yazmayı dene.')
    return res


def _is_short(v):
    u = (v.get("url") or "").lower()
    return "/shorts/" in u or (0 < (v.get("duration") or 0) <= 60)


def _only_shorts(vids):
    return [v for v in vids if _is_short(v) or (0 < (v.get("duration") or 0) <= 180)]


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
    _dbg(f"[{slug}] yt-dlp: {len(got['videos'])} yayın, {len(got['new'])}+{len(got['pop'])} klip", errs)
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
    res.setdefault("shorts", [])
    _dbg(f"[{slug}] sonuç: {len(res['videos'])} yayın, {len(res['clips'])} klip", errs)
    if errs:
        print(f"[kick] {slug}:", " | ".join(errs), file=sys.stderr, flush=True)
    if res["videos"] and not res["clips"]:
        errs = [f'"{slug}" kanalında izleyici klibi bulunamadı. Kanal adı doğru mu? (ör. rraenee)']
    res["errors"] = errs if (not res["clips"] or not res["videos"]) else []
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


def _download_ffmpeg(job, url, title, lo, hi, section, preview, folder, name):
    """yt-dlp'den sadece akış adreslerini alıp videoyu (ya da aralığını) doğrudan FFmpeg ile indirir."""
    import subprocess
    from core import run_ffmpeg_progress
    fmt = ("worst[ext=mp4][vcodec!=none][acodec!=none]/worst[vcodec!=none][acodec!=none]/worst" if preview
           else "b[height<=1440][vcodec!=none][acodec!=none]/bv*[height<=1440]+ba/b")
    with _ydl({"format": fmt}) as ydl:
        info = ydl.extract_info(url, download=False)
    fmts = info.get("requested_formats") or [info]
    inputs, maps = [], []
    seek = ["-ss", f"{section[0]:.3f}"] if section else []
    for i, f in enumerate(fmts[:2]):
        hdr = "".join(f"{k}: {v}\r\n" for k, v in (f.get("http_headers") or info.get("http_headers") or {}).items())
        inputs += (["-headers", hdr] if hdr else []) + seek + ["-i", f["url"]]
        maps += ["-map", f"{i}:v:0?", "-map", f"{i}:a:0?"] if len(fmts) == 1 else (["-map", f"{i}:v:0"] if i == 0 else ["-map", f"{i}:a:0"])
    dur = (section[1] - section[0]) if section else float(info.get("duration") or 0)
    out = folder / (name + f"_{info.get('id') or 'video'}.mp4")
    cmd = [FFMPEG, "-y", *inputs, *(["-t", f"{dur:.3f}"] if section else []), *maps, "-c", "copy", "-movflags", "+faststart", str(out)]
    if job:
        job.set(lo, "İndiriliyor...")
    code, err = run_ffmpeg_progress(cmd, max(1.0, dur), lambda p: job and job.set(lo + (hi - lo) * p, f"İndiriliyor %{int(p * 100)}"),
                                    lambda: bool(job and job.cancelled), job=job if job and hasattr(job, "procs") else None)
    if code != 0 or not out.exists() or out.stat().st_size < 1000:
        # kopyalama olmadıysa yeniden kodla (bazı akışlarda gerekli)
        cmd = [FFMPEG, "-y", *inputs, *(["-t", f"{dur:.3f}"] if section else []), *maps, "-c:v", "libx264", "-preset", "veryfast",
               "-crf", "18", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)]
        code, err = run_ffmpeg_progress(cmd, max(1.0, dur), lambda p: job and job.set(lo + (hi - lo) * p, f"İndiriliyor %{int(p * 100)}"),
                                        lambda: bool(job and job.cancelled))
        if code != 0 or not out.exists():
            raise RuntimeError("İndirme başarısız: " + (err or "")[-200:])
    return str(out), info


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
        "format": ("worst[ext=mp4][vcodec!=none][acodec!=none]/worst[vcodec!=none][acodec!=none]/worst" if preview
                   else "bv*[height<=1440]+ba/b[height<=1440]/bv*+ba/b"),
    }
    if section:
        import yt_dlp.utils
        opts["download_ranges"] = yt_dlp.utils.download_range_func(None, [tuple(section)])
        opts["force_keyframes_at_cuts"] = False
    try:
        with _ydl(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = info.get("requested_downloads", [{}])[0].get("filepath") or ydl.prepare_filename(info)
    except Exception as e:
        if "ffmpeg" not in str(e).lower():
            raise
        # yt-dlp bazen ffmpeg'i göremiyor: aralığı kendi ffmpeg'imizle keselim
        _dbg(f"yt-dlp ffmpeg'i göremedi, kendi ffmpeg'imizle indiriliyor: {str(e)[:150]}")
        return _download_ffmpeg(job, url, title, lo, hi, section, preview, folder, name)
    p = Path(path)
    if not p.exists():
        cands = sorted(folder.glob(name + "_*"), key=lambda x: x.stat().st_mtime, reverse=True)
        if not cands:
            raise RuntimeError("İndirilen dosya bulunamadı")
        p = cands[0]
    return str(p), info
