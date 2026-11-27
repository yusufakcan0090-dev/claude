"""Kesit Stüdyosu - yerel web sunucusu (arayüz <-> motor)."""
import os
import subprocess
import time
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_file, send_from_directory

import analyzer
import exporter
import kick
import model
import transcribe
import updater
import enhance
from core import (ANALIZ, APP, CACHE, FFMPEG, FFPROBE, INDIRILEN, IS_WIN, JOBS, PROJELER, load_settings,
                  new_id, popen, probe, read_json, run, safe_name, save_settings,
                  thumbnail, write_json)

UI = APP / "ui"
WINDOW = None  # main.py pywebview penceresini buraya koyar

app = Flask(__name__, static_folder=None)


# ================================================================ projeler
_plock = __import__("threading").RLock()


def project_path(pid):
    if not pid.isalnum():
        abort(400)
    return PROJELER / pid / "proje.json"


def load_project(pid):
    p = read_json(project_path(pid))
    if not p:
        abort(404)
    changed = False
    if p.get("version") != 2:
        p = model.migrate(p)
        changed = True
    for c in (p.get("clips") or []) + (p.get("overlays") or []):
        if "content" not in c and Path(c.get("source", "")).exists():
            try:
                c["content"] = model.detect_content(c["source"], c.get("src_dur") or 0, c["width"], c["height"])
            except Exception:
                c["content"] = None
            if c in (p.get("clips") or []) and c.get("layout"):
                cw, ch = model.content_size(c)
                c["layout"] = model.fix_layout(c["layout"], p.get("format", "dikey"), cw, ch)
            changed = True
    if changed:
        save_project(p)
    return p


def save_project(p):
    p["updated"] = time.time()
    (PROJELER / p["id"]).mkdir(parents=True, exist_ok=True)
    write_json(project_path(p["id"]), p)


def default_style():
    st = dict(exporter.DEFAULT_STYLE)
    st.update(load_settings().get("varsayilan_stil") or {})
    return st


def create_project(source=None, title=None, kind="yerel", meta=None, fmt="dikey"):
    p = {"id": new_id("p"), "version": 2, "title": title or (Path(source).stem if source else "Yeni proje"),
         "kind": kind, "format": fmt if model.valid_format(fmt) else "dikey", "created": time.time(),
         "clips": [], "overlays": [], "style": default_style(), "effects": {}, "media": {},
         "exports": [], "meta": meta or {}}
    if source:
        p["clips"].append(model.new_clip(source, p["format"], load_settings().get("varsayilan_duzen")))
        model.apply_kaynak(p, p["clips"][-1])
    save_project(p)
    return p


def add_clip(pid, source, trim=None):
    """Projenin sonuna video ekle. trim=(in, out) verilirse o aralık kullanılır."""
    with _plock:
        p = load_project(pid)
        c = model.new_clip(source, p.get("format", "dikey"), load_settings().get("varsayilan_duzen"))
        if trim:
            c["in"], c["out"] = round(max(0.0, trim[0]), 3), round(min(c["src_dur"], trim[1]), 3)
        p["clips"].append(c)
        model.apply_kaynak(p, c)
        save_project(p)
    return p, c


def project_summary(p):
    clips = p.get("clips") or []
    subs = "yok"
    if clips:
        st = [c.get("subs_status", "yok") for c in clips]
        subs = "calisiyor" if "calisiyor" in st else ("hazir" if all(s == "hazir" for s in st) else ("hata" if "hata" in st else "yok"))
    return {"id": p["id"], "title": p.get("title"), "kind": p.get("kind"), "created": p.get("created"),
            "updated": p.get("updated"), "duration": model.total_duration(p), "subs_status": subs,
            "exports": p.get("exports", []), "format": p.get("format", "dikey"), "clips": len(clips)}


def all_projects():
    out = []
    for f in PROJELER.glob("*/proje.json"):
        p = read_json(f)
        if not p:
            continue
        if p.get("version") != 2:
            try:
                p = load_project(p["id"])
            except Exception:
                continue
        out.append(project_summary(p))
    out.sort(key=lambda p: p.get("updated") or p.get("created") or 0, reverse=True)
    return out


# ================================================================ işler
def job_transcribe(job, pid, clip_ids=None):
    p = load_project(pid)
    targets = [c for c in p["clips"] if (clip_ids is None and not c.get("captions")) or (clip_ids and c["id"] in clip_ids)]
    targets = [c for c in targets if c.get("has_audio")]
    if not targets:
        job.set(1, "Altyazı çıkarılacak video yok")
        return {"project": pid, "flagged": 0}
    with _plock:
        p = load_project(pid)
        for c in p["clips"]:
            if c["id"] in {t["id"] for t in targets}:
                c["subs_status"] = "calisiyor"
        save_project(p)
    flagged = total = 0
    for n, t in enumerate(targets):
        lo, hi = n / len(targets), (n + 1) / len(targets)
        try:
            words = transcribe.transcribe_range(job, t["source"], max(0.0, t["in"] - 0.3),
                                                min(t["src_dur"], t["out"] + 0.3), lo, hi)
            status = "hazir"
        except Exception:
            words, status = None, "hata"
            if len(targets) == 1:
                with _plock:
                    p = load_project(pid)
                    for c in p["clips"]:
                        if c["id"] == t["id"]:
                            c["subs_status"] = "hata"
                    save_project(p)
                raise
        with _plock:
            p = load_project(pid)
            mw = int((p.get("style") or {}).get("maxWords") or 3)
            for c in p["clips"]:
                if c["id"] == t["id"]:
                    c["subs_status"] = status
                    if words is not None:
                        c["words"] = words
                        c["captions"] = transcribe.chunk_words(words, max_words=mw)
                        flagged += sum(1 for w in words if w.get("p", 1) < 0.55)
                        total += len(words)
            save_project(p)
    job.set(1, f"Altyazı hazır · {total} kelime" + (f" · {flagged} şüpheli" if flagged else ""))
    return {"project": pid, "flagged": flagged}


def start_transcribe(pid, title, clip_ids=None):
    return JOBS.start("altyazi", "Altyazı: " + title, job_transcribe, pid, clip_ids, heavy=True)


def _after_add(p, clip=None):
    if load_settings().get("oto_altyazi"):
        if clip is None or clip.get("has_audio"):
            start_transcribe(p["id"], p["title"], [clip["id"]] if clip else None)


def _place(job, path, title, kind, meta, target=None, trim=None, fmt=None):
    """İndirilen videoyu yeni projeye ya da var olan projeye koy."""
    if target:
        try:
            p, c = add_clip(target, path, trim)
            _after_add(p, c)
            return {"project": p["id"], "added": True}
        except Exception:
            pass  # proje silinmişse yeni proje aç
    p = create_project(path, title, kind, meta, fmt or (load_settings().get("son_bicim") or "dikey"))
    if trim:
        c = p["clips"][0]
        c["in"], c["out"] = round(trim[0], 3), round(min(c["src_dur"], trim[1]), 3)
        save_project(p)
    _after_add(p)
    return {"project": p["id"], "added": False}


def job_download_clip(job, url, title, target=None):
    path, info = kick.download(job, url, title, 0, 0.95)
    job.set(0.97, "Projeye ekleniyor...")
    r = _place(job, path, title or info.get("title"), "klip", {"url": url}, target)
    job.set(1, "Projeye eklendi" if r["added"] else "İndirildi, editörde hazır")
    return r


def job_analyze(job, src, title, local, mode="orta", count=20):
    cfg = analyzer.MODES.get(mode, analyzer.MODES["orta"])
    aid = new_id("a")
    path = src if local else kick.download(job, src, title, 0, 0.55, preview=True)[0]
    info = probe(path)
    job.set(0.56 if not local else 0.02, "Ses analiz ediliyor...")
    db = analyzer.energy_curve(job, path, info["duration"], 0.56 if not local else 0.02, 0.97)
    moments, curve = analyzer.find_moments(db, info["duration"], before=cfg["before"], after=cfg["after"],
                                           max_count=int(count), max_len=cfg["max_len"], ext=cfg["ext"])
    write_json(ANALIZ / f"{aid}.json", {"id": aid, "title": title, "source": src, "local": local, "preview": path,
                                        "mode": mode, "duration": info["duration"], "moments": moments,
                                        "curve": curve, "created": time.time()})
    job.set(1, f"{len(moments)} an bulundu")
    return {"analysis": aid, "count": len(moments)}


def job_moment(job, aid, m, target=None, fmt=None):
    a = read_json(ANALIZ / f"{aid}.json")
    if not a:
        raise RuntimeError("Analiz bulunamadı")
    start, end = float(m["start"]), float(m["end"])
    title = f"{a['title']} - {m.get('label', 'An')} {int(start // 60)}.{int(start % 60):02d}"
    if a["local"]:
        # bilgisayardaki video: kopyalamaya gerek yok, aralığı direkt kullan
        r = _place(job, a["source"], title, "an", {"analysis": aid, "moment": m}, target, (start, end), fmt)
    else:
        pad = 1.5
        path, _ = kick.download(job, a["source"], title, 0, 0.95, section=(max(0, start - pad), end + pad))
        real = model.media_info(path)["src_dur"]
        extra = max(0.0, real - (end - start))
        lead = min(pad, extra / 2) if extra > 0.5 else 0.0
        r = _place(job, path, title, "an", {"analysis": aid, "moment": m}, target, (lead, lead + end - start), fmt)
    job.set(1, "Projeye eklendi" if r["added"] else "An hazır, editörde aç")
    return r


class _Sub:
    """Bir işin ilerlemesini başka bir işin lo..hi aralığına yansıtır."""
    def __init__(self, job, lo, hi, prefix=""):
        self.job, self.lo, self.hi, self.prefix = job, lo, hi, prefix

    def set(self, progress=None, message=None):
        self.job.set(None if progress is None else self.lo + (self.hi - self.lo) * max(0, min(1, progress)),
                     None if message is None else self.prefix + message)

    def __getattr__(self, k):
        return getattr(self.job, k)


def _words_text(words, every=6):
    """Kelimeleri yapay zekâ için zaman damgalı metne çevirir: '[12.3] bir iki üç ...'"""
    out, cur = [], []
    for i, w in enumerate(words):
        if i % every == 0:
            if cur:
                out.append(" ".join(cur))
            cur = [f"[{w['s']:.1f}]"]
        cur.append(w["w"])
    if cur:
        out.append(" ".join(cur))
    return " ".join(out)


def project_text(p, limit=6000):
    t = " ".join(w["w"] for c in p.get("clips") or [] for w in (c.get("words") or []) if c.get("in", 0) - .2 <= w["s"] <= c.get("out", 1e9))
    return t[:limit]


def job_autoedit(job, src, local, title, count=3, fmt="dikey", subs=True):
    """Otomatik edit: en iyi anları bul (ses + yapay zekâ), her biri için hazır bir kısa video projesi aç."""
    import ai
    count = max(1, min(10, int(count or 3)))
    use_ai = ai.enabled()
    cfg = analyzer.MODES["orta"]
    path = src if local else kick.download(_Sub(job, 0, .3, "Video alınıyor: "), src, title, 0, 1, preview=True)[0]
    base = 0.02 if local else 0.3
    info = probe(path)
    job.set(base, "Ses analiz ediliyor...")
    db = analyzer.energy_curve(job, path, info["duration"], base, base + .15)
    moments, curve = analyzer.find_moments(db, info["duration"], before=cfg["before"], after=cfg["after"],
                                           max_count=max(count * 3, 8) if use_ai else count, max_len=cfg["max_len"], ext=cfg["ext"])
    if not moments:
        raise RuntimeError("Bu videoda belirgin bir an bulunamadı.")
    aid = new_id("a")
    write_json(ANALIZ / f"{aid}.json", {"id": aid, "title": title, "source": src, "local": local, "preview": path,
                                        "mode": "orta", "duration": info["duration"], "moments": moments,
                                        "curve": curve, "created": time.time()})
    picks, words_of = [], {}
    p0 = base + .15
    if use_ai:
        cands = []
        for i, m in enumerate(moments):
            if job.cancelled:
                raise RuntimeError("İptal edildi")
            lo, hi = p0 + .35 * i / len(moments), p0 + .35 * (i + 1) / len(moments)
            job.set(lo, f"Konuşmalar dinleniyor ({i + 1}/{len(moments)})...")
            try:
                ws = transcribe.transcribe_range(_Sub(job, lo, hi), path, max(0, m["start"] - 5), min(info["duration"], m["end"] + 5), 0, 1)
            except Exception:
                ws = []
            words_of[i] = ws
            cands.append({"i": i, "start": m["start"], "end": m["end"], "score": m.get("score", 0), "text": _words_text(ws)})
        job.set(p0 + .36, "Yapay zekâ en iyi anları seçiyor...")
        try:
            sel = ai.pick_moments(cands, count, maxlen=cfg["max_len"] + 20)
        except Exception as e:
            job.set(p0 + .37, f"Yapay zekâ seçemedi ({str(e)[:60]}), ses heyecanına göre seçiliyor...")
            sel = []
        for x in sel:
            if 0 <= x["aday"] < len(moments):
                m = moments[x["aday"]]
                a, b = max(m["start"] - 5, x["bas"]), min(m["end"] + 5, x["bit"])
                if b - a < 3:
                    a, b = m["start"], m["end"]
                picks.append({**m, "start": round(max(0, a), 2), "end": round(min(info["duration"], b), 2),
                              "label": x["baslik"] or m.get("label", "An"), "neden": x["neden"], "_i": x["aday"]})
        p0 += .4
    if not picks:
        picks = [{**m, "_i": i} for i, m in sorted(enumerate(moments), key=lambda t: -t[1].get("score", 0))[:count]]
    made = []
    for k, m in enumerate(picks):
        if job.cancelled:
            raise RuntimeError("İptal edildi")
        lo, hi = p0 + (.97 - p0) * k / len(picks), p0 + (.97 - p0) * (k + 1) / len(picks)
        sub = _Sub(job, lo, hi, f"Video {k + 1}/{len(picks)}: ")
        r = job_moment(sub, aid, m, None, fmt)
        pid = r["project"]
        with _plock:
            p = load_project(pid)
            if m.get("label") and use_ai:
                p["title"] = m["label"]
            p.setdefault("meta", {})["oto_edit"] = {"neden": m.get("neden", ""), "kaynak": title}
            ws = words_of.get(m.get("_i"))
            if subs and local and ws:  # yerel videoda zaten dinlenen kelimeleri kullan (tekrar beklemesin)
                c = p["clips"][0]
                c["words"] = ws
                mw = int((p.get("style") or {}).get("maxWords") or 3)
                c["captions"] = transcribe.chunk_words([w for w in ws if c["in"] - .2 <= w["s"] <= c["out"]], max_words=mw)
                c["subs_status"] = "hazir"
            save_project(p)
        if subs and not (local and words_of.get(m.get("_i"))):
            start_transcribe(pid, p["title"])
        if use_ai:
            try:
                txt = " ".join(w["w"] for w in (words_of.get(m.get("_i")) or []) if m["start"] - .2 <= w["s"] <= m["end"])
                meta = ai.write_meta(p["title"], txt, title)
                with _plock:
                    p = load_project(pid)
                    p["paylasim"] = meta
                    save_project(p)
            except Exception:
                pass
        made.append(pid)
    job.set(1, f"{len(made)} video hazır" + (" · altyazılar çıkarılıyor" if subs and not local else ""))
    return {"projects": made, "project": made[0] if made else None, "open": True}


def job_export(job, pid, opts):
    p = load_project(pid)
    res = exporter.export(job, p, opts)
    with _plock:
        p = load_project(pid)
        p.setdefault("exports", []).append({**res, "time": time.time()})
        save_project(p)
    return res


# ================================================================ rotalar
@app.route("/")
def index():
    return send_from_directory(UI, "index.html")


@app.route("/favicon.ico")
def favicon():
    return ("", 204)


@app.route("/ui/<path:f>")
def ui_files(f):
    resp = send_from_directory(UI, f)
    resp.headers["Cache-Control"] = "no-cache"
    return resp


def _find(p, key, oid):
    o = next((x for x in p.get(key) or [] if x.get("id") == oid), None)
    if not o or not Path(o.get("source", "")).exists():
        abort(404)
    return o


@app.route("/media/clip/<pid>/<cid>")
def media_clip(pid, cid):
    return send_file(_find(load_project(pid), "clips", cid)["source"], conditional=True)


@app.route("/media/overlay/<pid>/<oid>")
def media_overlay(pid, oid):
    return send_file(_find(load_project(pid), "overlays", oid)["source"], conditional=True)


@app.route("/media/analysis/<aid>")
def media_analysis(aid):
    a = read_json(ANALIZ / f"{safe_name(aid)}.json")
    if not a:
        abort(404)
    return send_file(a["preview"], conditional=True)


@app.route("/thumb/<pid>")
def thumb(pid):
    p = load_project(pid)
    out = CACHE / f"{pid}.jpg"
    clips = p.get("clips") or []
    if not clips:
        abort(404)
    c = clips[0]
    if out.exists() and out.stat().st_mtime < (p.get("updated") or 0) - 5 and request.args.get("r"):
        out.unlink(missing_ok=True)
    thumbnail(c["source"], out, t=min(float(c["in"]) + 1, max(0, float(c["out"]) - 0.3)))
    if not out.exists():
        abort(404)
    return send_file(out)


@app.get("/api/state")
def api_state():
    return jsonify({"settings": load_settings(), "projects": all_projects(),
                    "analyses": list_analyses(), "jobs": JOBS.list()})


@app.get("/api/jobs")
def api_jobs():
    return jsonify(JOBS.list())


@app.post("/api/jobs/<jid>/cancel")
def api_cancel(jid):
    j = JOBS.get(jid)
    if j:
        j.cancel()
    return jsonify(ok=True)


@app.post("/api/jobs/<jid>/pause")
def api_pause(jid):
    j = JOBS.get(jid)
    if j:
        j.pause(bool((request.get_json(silent=True) or {}).get("pause", True)))
    return jsonify(ok=True, paused=bool(j and j.paused))


@app.get("/api/system")
def api_system():
    info = {"ffmpeg": Path(FFMPEG).exists() or bool(run([FFMPEG, "-version"]).stdout),
            "whisper_device": transcribe.current_device()}
    try:
        import yt_dlp
        info["ytdlp"] = yt_dlp.version.__version__
    except Exception:
        info["ytdlp"] = None
    info.update(transcribe.device_info())
    info["gpu_name"] = gpu_name()
    n = info["gpu_name"].lower()
    info["vendor"] = "nvidia" if ("nvidia" in n or info.get("gpu")) else "amd" if ("amd" in n or "radeon" in n) else "intel" if "intel" in n else ""
    return jsonify(info)


_GPU_NAME = None


def gpu_name():
    """Ekran kartının adı (NVIDIA / AMD / Intel)."""
    global _GPU_NAME
    if _GPU_NAME is None:
        _GPU_NAME = ""
        try:
            r = run(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_VideoController).Name -join ' | '"], timeout=15)
            _GPU_NAME = (r.stdout or "").strip()
        except Exception:
            pass
    return _GPU_NAME


@app.get("/api/update/check")
def api_update_check():
    return jsonify(updater.check(force=request.args.get("force") == "1"))


@app.post("/api/update/apply")
def api_update_apply():
    j = JOBS.start("guncelle", "Güncelleme", updater.apply)
    return jsonify(job=j.id)


@app.post("/api/restart")
def api_restart():
    updater.restart()
    return jsonify(ok=True)


@app.get("/api/version")
def api_version():
    return jsonify(updater.local_version())


@app.post("/api/settings")
def api_settings():
    data = request.get_json(force=True) or {}
    return jsonify(save_settings(data))


@app.post("/api/kick/list")
def api_kick_list():
    ch = (request.get_json(force=True) or {}).get("channel", "")
    try:
        res = kick.list_source(ch)
        if not res.get("single"):
            save_settings({"son_kanal": ch.strip()})
        return jsonify(res)
    except Exception as e:
        return jsonify(error=str(e)), 400


@app.post("/api/kick/clip")
def api_kick_clip():
    d = request.get_json(force=True) or {}
    items = d.get("items") or [{"url": d.get("url"), "title": d.get("title")}]
    target = d.get("project")
    jobs = [JOBS.start("indir", "Klip: " + (it.get("title") or "")[:40], job_download_clip,
                       it["url"], it.get("title") or "Kick klip", target).id for it in items if it.get("url")]
    return jsonify(jobs=jobs)


@app.post("/api/analyze")
def api_analyze():
    d = request.get_json(force=True) or {}
    local = bool(d.get("local"))
    src = d.get("path") if local else d.get("url")
    if not src:
        return jsonify(error="Kaynak yok"), 400
    title = d.get("title") or (Path(src).stem if local else "Video")
    mode = d.get("mode") or load_settings().get("an_modu") or "orta"
    count = int(d.get("count") if d.get("count") is not None else load_settings().get("an_sayisi", 20))
    save_settings({"an_modu": mode, "an_sayisi": count})
    j = JOBS.start("analiz", "An bul: " + title[:40], job_analyze, src, title, local, mode, count)
    return jsonify(job=j.id)


def list_analyses():
    out = []
    for f in ANALIZ.glob("*.json"):
        a = read_json(f)
        if a:
            out.append({k: a.get(k) for k in ("id", "title", "duration", "created", "local")} |
                       {"count": len(a.get("moments") or [])})
    out.sort(key=lambda a: a.get("created") or 0, reverse=True)
    return out


@app.get("/api/analysis/<aid>")
def api_analysis(aid):
    a = read_json(ANALIZ / f"{safe_name(aid)}.json")
    if not a:
        abort(404)
    return jsonify(a)


@app.delete("/api/analysis/<aid>")
def api_analysis_del(aid):
    f = ANALIZ / f"{safe_name(aid)}.json"
    a = read_json(f)
    if a:
        f.unlink(missing_ok=True)
        if not a.get("local"):
            try:
                Path(a["preview"]).unlink(missing_ok=True)
            except Exception:
                pass
    return jsonify(ok=True)


@app.post("/api/moments")
def api_moments():
    d = request.get_json(force=True) or {}
    aid, target = d.get("analysis"), d.get("project")
    jobs = [JOBS.start("an", f"An indir: {m.get('label','')} {int(float(m['start'])//60)}dk",
                       job_moment, aid, m, target).id for m in d.get("moments") or []]
    return jsonify(jobs=jobs)


@app.post("/api/local/project")
def api_local_project():
    d = request.get_json(force=True) or {}
    path = d.get("path")
    if not path or not Path(path).exists():
        return jsonify(error="Dosya bulunamadı"), 400
    if file_kind(path) != "video":
        return jsonify(error="Bu bir video dosyası değil"), 400
    if needs_mp4(path):
        # MOV, MKV, AVI vb. önce MP4'e çevrilir (editörde oynasın, her yerde açılsın)
        j = JOBS.start("indir", "MP4'e çevriliyor: " + Path(path).name[:40], job_convert_local, path,
                       d.get("project"), d.get("title") or Path(path).stem, d.get("format") or "dikey")
        return jsonify(job=j.id)
    if d.get("project"):
        p, c = add_clip(d["project"], path)
        _after_add(p, c)
        return jsonify(project=p["id"], clip=c["id"])
    p = create_project(path, d.get("title") or Path(path).stem, "yerel", fmt=d.get("format") or "dikey")
    _after_add(p)
    return jsonify(project=p["id"])


def needs_mp4(path):
    """Tarayıcının (editör önizlemesi) oynatamayacağı dosya mı? MP4 + H.264 değilse çevrilir."""
    ext = Path(path).suffix.lower()
    try:
        r = run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_name,pix_fmt",
                 "-of", "csv=p=0", str(path)], timeout=30)
        codec, _, pix = (r.stdout or "").strip().partition(",")
    except Exception:
        codec, pix = "", ""
    if ext in (".mp4", ".m4v") and codec in ("h264", "av1") and pix.startswith("yuv420p"):
        return False
    if ext == ".webm" and codec in ("vp8", "vp9", "av1"):
        return False
    return True


def job_convert_local(job, path, target, title, fmt):
    from core import run_ffmpeg_progress
    src = Path(path)
    info = probe(src)
    out = INDIRILEN / (safe_name(src.stem, 80) + ".mp4")
    i = 2
    while out.exists():
        out = INDIRILEN / f"{safe_name(src.stem, 80)}_{i}.mp4"
        i += 1
    INDIRILEN.mkdir(parents=True, exist_ok=True)
    r = run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_name,pix_fmt", "-of", "csv=p=0", str(src)], timeout=30)
    codec, _, pix = (r.stdout or "").strip().partition(",")
    tries = []
    if codec == "h264" and pix.startswith("yuv420p"):
        tries.append(["-c:v", "copy"])  # sadece kabı değiştir, anında biter
    tries += [["-c:v", "h264_nvenc", "-preset", "p5", "-cq", "17", "-pix_fmt", "yuv420p"],
              ["-c:v", "h264_amf", "-quality", "quality", "-rc", "cqp", "-qp_i", "17", "-qp_p", "17", "-pix_fmt", "yuv420p"],
              ["-c:v", "h264_qsv", "-global_quality", "18", "-pix_fmt", "nv12"],
              ["-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p"]]
    err = ""
    for v in tries:
        cmd = [FFMPEG, "-y", "-i", str(src), "-map", "0:v:0", "-map", "0:a:0?", *v, "-c:a", "aac", "-b:a", "192k",
               "-movflags", "+faststart", str(out)]
        code, err = run_ffmpeg_progress(cmd, info["duration"] or 1, lambda p: job.set(0.02 + 0.9 * p, f"MP4'e çevriliyor %{int(p * 100)}"), lambda: job.cancelled)
        if code == 0 and out.exists() and out.stat().st_size > 1000:
            break
        out.unlink(missing_ok=True)
        if job.cancelled:
            raise RuntimeError("İptal edildi")
    else:
        raise RuntimeError("MP4'e çevrilemedi: " + (err or "")[-200:])
    job.set(0.95, "Projeye ekleniyor...")
    if target:
        try:
            p, c = add_clip(target, str(out))
            _after_add(p, c)
            job.set(1, "Projeye eklendi")
            return {"project": p["id"], "added": True, "mp4": str(out)}
        except Exception:
            pass
    p = create_project(str(out), title, "yerel", fmt=fmt)
    _after_add(p)
    job.set(1, "MP4 hazır, editörde açılıyor")
    return {"project": p["id"], "added": False, "mp4": str(out), "open": True}


@app.post("/api/project/new")
def api_project_new():
    d = request.get_json(force=True) or {}
    fmt = d.get("format") if model.valid_format(d.get("format")) else "dikey"
    save_settings({"son_bicim": "kaynak" if fmt.startswith("kaynak") else fmt})
    p = create_project(None, (d.get("title") or "").strip() or "Yeni proje", "bos", fmt=fmt)
    return jsonify(project=p["id"])


@app.post("/api/project/<pid>/overlay")
def api_add_overlay(pid):
    d = request.get_json(force=True) or {}
    path = d.get("path")
    if not path or file_kind(path) != "video":
        return jsonify(error="Video dosyası değil"), 400
    info = model.media_info(path)
    with _plock:
        p = load_project(pid)
        total = model.total_duration(p) or info["src_dur"]
        s0 = min(max(0.0, float(d.get("at") or 0)), max(0.0, total - 0.5))
        green = any(k in Path(path).stem.lower() for k in ("green", "yesil", "yeşil", "chroma"))
        ov = {"id": new_id("o"), **info, "s": round(s0, 3), "e": round(min(total, s0 + info["src_dur"]), 3),
              "in": 0.0, "x": 0.55, "y": 0.06, "w": 0.4, "opacity": 1.0, "volume": 1.0 if info["has_audio"] else 0,
              "chroma": green, "chroma_color": "#00FF00", "similarity": 0.3}
        if green:
            ov.update(x=0.0, y=0.0, w=1.0)
        p.setdefault("overlays", []).append(ov)
        save_project(p)
    return jsonify(overlay=ov)


@app.get("/api/project/<pid>")
def api_project(pid):
    return jsonify(load_project(pid))


@app.post("/api/project/<pid>")
def api_project_save(pid):
    cur = load_project(pid)
    d = request.get_json(force=True) or {}
    with _plock:
        cur = load_project(pid)
        for k in ("title", "format", "clips", "overlays", "style", "effects", "media"):
            if k in d:
                cur[k] = d[k]
        if not model.valid_format(cur.get("format")):
            cur["format"] = "dikey"
        if cur.get("format") == "kaynak" and cur.get("clips"):
            c0 = cur["clips"][0]
            cur["format"] = f"kaynak:{c0['width']}x{c0['height']}"
        save_project(cur)
    return jsonify(ok=True, updated=cur["updated"], format=cur["format"])


@app.delete("/api/project/<pid>")
def api_project_delete(pid):
    import shutil
    from core import INDIRILEN
    p = load_project(pid)
    shutil.rmtree(PROJELER / pid, ignore_errors=True)
    (CACHE / f"{pid}.jpg").unlink(missing_ok=True)
    if request.args.get("dosya") == "1":
        used = set()
        for f in PROJELER.glob("*/proje.json"):
            q = read_json(f) or {}
            used |= {c.get("source") for c in q.get("clips") or []} | {o.get("source") for o in q.get("overlays") or []}
        for c in p.get("clips") or []:
            src = Path(c["source"])
            if str(src) not in used and INDIRILEN in src.parents:
                src.unlink(missing_ok=True)
    return jsonify(ok=True)


@app.post("/api/project/<pid>/transcribe")
def api_project_transcribe(pid):
    p = load_project(pid)
    ids = (request.get_json(silent=True) or {}).get("clips")
    j = start_transcribe(pid, p["title"], ids)
    return jsonify(job=j.id)


@app.post("/api/project/<pid>/rechunk")
def api_rechunk(pid):
    mw = int((request.get_json(force=True) or {}).get("maxWords") or 3)
    with _plock:
        p = load_project(pid)
        for c in p.get("clips") or []:
            words = [w for cap in c.get("captions") or [] for w in cap.get("words") or []] or c.get("words") or []
            c["captions"] = transcribe.chunk_words(words, max_words=mw)
        p.setdefault("style", {})["maxWords"] = mw
        save_project(p)
    return jsonify(clips=[{"id": c["id"], "captions": c["captions"]} for c in p["clips"]])


def parse_cube(path):
    size, data = 0, []
    for line in Path(path).read_text("utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.upper().startswith("LUT_3D_SIZE"):
            size = int(line.split()[1])
            continue
        parts = line.split()
        if len(parts) == 3:
            try:
                data.extend(float(x) for x in parts)
            except ValueError:
                pass
    if not size or len(data) != size ** 3 * 3:
        raise RuntimeError("Bu .cube dosyası okunamadı (3D LUT değil ya da bozuk)")
    return size, data


@app.post("/api/project/<pid>/lut")
def api_set_lut(pid):
    import shutil
    p = load_project(pid)
    path = (request.get_json(force=True) or {}).get("path")
    if path:
        try:
            parse_cube(path)
        except Exception as e:
            return jsonify(error=str(e)), 400
        shutil.copy2(path, PROJELER / pid / "lut.cube")
        p.setdefault("effects", {})["lut"] = {"name": Path(path).name, "mix": 100}
    else:
        (PROJELER / pid / "lut.cube").unlink(missing_ok=True)
        p.setdefault("effects", {})["lut"] = None
    save_project(p)
    return jsonify(lut=p["effects"]["lut"])


@app.get("/api/project/<pid>/lutdata")
def api_lut_data(pid):
    f = PROJELER / pid / "lut.cube"
    if not f.exists():
        return jsonify(size=0, data=[])
    size, data = parse_cube(f)
    return jsonify(size=size, data=[round(x, 4) for x in data])


@app.get("/api/project/<pid>/wave/<cid>")
def api_wave(pid, cid):
    """Klibin kaynağının dalga formu (saniyede 20 nokta), önbellekli."""
    p = load_project(pid)
    c = next((x for x in (p.get("clips") or []) + (p.get("overlays") or []) if x["id"] == cid), None)
    if not c:
        abort(404)
    f = Path(str(model.words_cache_path(c["source"])).replace("words_", "wave_"))
    w = read_json(f)
    if w is None:
        n = max(50, min(40000, int(float(c.get("src_dur") or 10) * 20)))
        w = analyzer.waveform(c["source"], n) if c.get("has_audio") else []
        write_json(f, w)
    return jsonify(w)


@app.post("/api/project/<pid>/export")
def api_export(pid):
    p = load_project(pid)
    opts = request.get_json(force=True) or {}
    save_settings({k: opts[k] for k in ("cozunurluk", "fps", "kalite", "ses_dengele") if k in opts})
    j = JOBS.start("aktar", "Dışa aktar: " + p["title"][:40], job_export, pid, opts, heavy=True)
    return jsonify(job=j.id)


@app.post("/api/fixes")
def api_fixes():
    """Düzeltme sözlüğüne ekle ve istenirse projedeki tüm eşleşmelere uygula."""
    d = request.get_json(force=True) or {}
    s = load_settings()
    fixes = dict(s.get("duzeltmeler") or {})
    for k, v in (d.get("add") or {}).items():
        if k.strip() and v.strip():
            fixes[transcribe.tr_lower(k.strip())] = v.strip()
    for k in d.get("remove") or []:
        fixes.pop(k, None)
    save_settings({"duzeltmeler": fixes})
    out = {"duzeltmeler": fixes}
    pid = d.get("project")
    if pid:
        with _plock:
            p = load_project(pid)
            for c in p.get("clips") or []:
                for cap in c.get("captions") or []:
                    cap["words"] = transcribe.apply_fixes(cap.get("words") or [], fixes)
            save_project(p)
        out["clips"] = [{"id": c["id"], "captions": c["captions"]} for c in p["clips"]]
    return jsonify(out)


@app.post("/api/defaults")
def api_defaults():
    d = request.get_json(force=True) or {}
    patch = {}
    if "style" in d:
        patch["varsayilan_stil"] = d["style"]
    if "layout" in d:
        patch["varsayilan_duzen"] = d["layout"]
    return jsonify(save_settings(patch))


@app.post("/api/pick_folder")
def api_pick_folder():
    return jsonify(path=pick_folder())


@app.post("/api/kalite/preview")
def api_kalite_preview():
    d = request.get_json(force=True) or {}
    path = d.get("path") or ""
    if not Path(path).exists():
        return jsonify(error="Video bulunamadı"), 400
    try:
        key, W, H, ai = enhance.preview(path, float(d.get("t") or 0), d.get("opts") or {})
        return jsonify(key=key, w=W, h=H, ai=ai)
    except Exception as e:
        return jsonify(error=str(e)[:300]), 400


@app.get("/media/kalite/<key>/<name>")
def media_kalite(key, name):
    if name not in ("once.jpg", "sonra.jpg") or not key.isalnum():
        return "", 404
    return send_file(CACHE / "kalite" / key / name, max_age=0)


@app.post("/api/kalite/start")
def api_kalite_start():
    d = request.get_json(force=True) or {}
    path = d.get("path") or ""
    if not Path(path).exists():
        return jsonify(error="Video bulunamadı"), 400
    opts = d.get("opts") or {}
    if enhance.is_image(path):
        save_settings({"kalite_foto_ayar": opts})
        j = JOBS.start("kalite", "Fotoğraf: " + Path(path).stem[:40], enhance.process_image, path, opts, heavy=True)
        return jsonify(job=j.id)
    save_settings({"kalite_ayar": opts})
    j = JOBS.start("kalite", "Kalite: " + Path(path).stem[:40], enhance.process, path, opts, heavy=True)
    return jsonify(job=j.id)


def _kalite_running():
    return {j.extra.get("resume") for j in JOBS.jobs.values() if j.kind == "kalite" and j.status in ("calisiyor", "bekliyor")}


@app.get("/api/kalite/yarim")
def api_kalite_yarim():
    run_ids = _kalite_running()
    return jsonify([u for u in enhance.unfinished() if u["id"] not in run_ids and not JOBS.get(u["id"])])


@app.post("/api/kalite/devam")
def api_kalite_devam():
    rid = (request.get_json(force=True) or {}).get("id") or ""
    u = next((x for x in enhance.unfinished() if x["id"] == rid), None)
    if not u:
        return jsonify(error="Yarım kalan iş bulunamadı"), 400
    if rid in _kalite_running():
        return jsonify(error="Bu iş zaten devam ediyor"), 400
    j = JOBS.start("kalite", "Kalite: " + Path(u["path"]).stem[:40], enhance.process, u["path"], {}, resume=rid, heavy=True)
    j.extra["resume"] = rid
    return jsonify(job=j.id)


@app.post("/api/kalite/sil")
def api_kalite_sil():
    enhance.discard((request.get_json(force=True) or {}).get("id") or "")
    return jsonify(ok=True)


@app.get("/api/kalite/info")
def api_kalite_info():
    p = request.args.get("path") or ""
    if not Path(p).exists():
        return jsonify(error="Video bulunamadı"), 400
    i = probe(p)
    img = enhance.is_image(p)
    opts = {**enhance.DEFAULT, "model": "gercek", "hedef": "x2", "keskin": 30, "gurultu": 15, **(load_settings().get("kalite_foto_ayar") or {})} if img else enhance.settings()
    return jsonify(path=p, name=Path(p).name, duration=0 if img else i["duration"], width=i["width"], height=i["height"], fps=i["fps"],
                   image=img, opts=opts, ai_tools=bool(enhance.tool_path("realesrgan")))


@app.get("/media/kalite_src")
def media_kalite_src():
    p = request.args.get("path") or ""
    if not Path(p).exists():
        return "", 404
    return send_file(p, conditional=True)


@app.post("/api/snapshot")
def api_snapshot():
    import base64
    d = request.get_json(force=True) or {}
    data = (d.get("data") or "").split(",", 1)[-1]
    if not data:
        return jsonify(error="Görüntü yok"), 400
    folder = Path(load_settings().get("cikti_klasoru") or str(Path.home() / "Videos"))
    folder.mkdir(parents=True, exist_ok=True)
    name = safe_name(d.get("name") or "kare", 80) + ".png"
    out = folder / name
    i = 2
    while out.exists():
        out = folder / f"{Path(name).stem}_{i}.png"
        i += 1
    out.write_bytes(base64.b64decode(data))
    return jsonify(path=str(out), name=out.name)


# ================================================================ yapay zekâ
@app.post("/api/ai/test")
def api_ai_test():
    import ai
    k = ((request.get_json(force=True) or {}).get("key") or "").strip()
    if not k:
        return jsonify(error="Anahtar boş"), 400
    try:
        ai.test(k)
    except Exception as e:
        return jsonify(error=str(e).replace("KOTA:", "").replace("MODEL:", "")), 400
    save_settings({"gemini_anahtar": k})
    ai._MODELS["pick"] = None
    try:
        m = ai.pick_model(force=True)
    except Exception:
        m = ""
    return jsonify(ok=True, model=m)


@app.get("/api/ai/chat")
def api_ai_history():
    import assistant
    import ai
    return jsonify(chat=assistant.history(), enabled=ai.enabled())


@app.post("/api/ai/chat")
def api_ai_chat():
    import assistant
    d = request.get_json(force=True) or {}
    msg = (d.get("message") or "").strip()
    if not msg:
        return jsonify(error="Mesaj boş"), 400
    try:
        return jsonify(assistant.chat(msg[:4000], d.get("ctx") or {}))
    except Exception as e:
        return jsonify(error=str(e).replace("KOTA:", "").replace("MODEL:", "")[:300]), 400


@app.post("/api/ai/reset")
def api_ai_reset():
    import assistant
    assistant.reset()
    return jsonify(ok=True)


@app.post("/api/ai/meta/<pid>")
def api_ai_meta(pid):
    import ai
    p = load_project(pid)
    if not p:
        return jsonify(error="Proje bulunamadı"), 404
    d = request.get_json(force=True) or {}
    try:
        meta = ai.write_meta(p.get("title") or "", project_text(p), (p.get("meta") or {}).get("oto_edit", {}).get("kaynak", ""), d.get("not") or "")
    except Exception as e:
        return jsonify(error=str(e).replace("KOTA:", "").replace("MODEL:", "")[:300]), 400
    with _plock:
        p = load_project(pid)
        p["paylasim"] = meta
        save_project(p)
    return jsonify(meta)


@app.post("/api/project/<pid>/paylasim")
def api_paylasim_save(pid):
    d = request.get_json(force=True) or {}
    with _plock:
        p = load_project(pid)
        if not p:
            return jsonify(error="Proje bulunamadı"), 404
        p["paylasim"] = {**(p.get("paylasim") or {}), **{k: v for k, v in d.items() if k in ("youtube", "tiktok", "instagram")}}
        save_project(p)
    return jsonify(ok=True)


@app.post("/api/autoedit")
def api_autoedit():
    d = request.get_json(force=True) or {}
    local = bool(d.get("local"))
    src = d.get("path") if local else d.get("url")
    if not src:
        return jsonify(error="Kaynak yok"), 400
    if local and not Path(src).exists():
        return jsonify(error="Dosya bulunamadı"), 400
    title = d.get("title") or (Path(src).stem if local else "Yayın")
    fmt = d.get("format") if model.valid_format(d.get("format") or "") else (load_settings().get("son_bicim") or "dikey")
    save_settings({"oto_adet": int(d.get("count") or 3), "oto_altyazi_ekle": bool(d.get("subs", True))})
    j = JOBS.start("otoedit", "Otomatik edit: " + title[:36], job_autoedit, src, local, title, int(d.get("count") or 3), fmt,
                   bool(d.get("subs", True)), heavy=True)
    return jsonify(job=j.id)


# ================================================================ görsel araçları
@app.post("/api/gorsel/arkaplan")
def api_gorsel_bg():
    import imgtools
    path = (request.get_json(force=True) or {}).get("path") or ""
    if not Path(path).exists():
        return jsonify(error="Dosya bulunamadı"), 400
    j = JOBS.start("gorsel", "Arka plan siliniyor: " + Path(path).stem[:30], imgtools.job_remove_bg, path, heavy=True)
    return jsonify(job=j.id)


@app.post("/api/gorsel/nesne")
def api_gorsel_nesne():
    import imgtools
    d = request.get_json(force=True) or {}
    path = d.get("path") or ""
    if not Path(path).exists():
        return jsonify(error="Dosya bulunamadı"), 400
    if not d.get("mask"):
        return jsonify(error="Silinecek yeri fırçayla boya"), 400
    j = JOBS.start("gorsel", "Nesne siliniyor: " + Path(path).stem[:30], imgtools.job_inpaint, path, d["mask"], heavy=True)
    return jsonify(job=j.id)


@app.get("/api/project/<pid>/frames")
def api_frames(pid):
    """Kapak için projeden aday kareler."""
    p = load_project(pid)
    if not p or not p.get("clips"):
        return jsonify(error="Projede video yok"), 400
    c = p["clips"][0]
    n = 8
    out = []
    d = CACHE / "kapak" / pid
    d.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        t = c["in"] + (c["out"] - c["in"]) * (i + .5) / n
        f = d / f"k{i}_{int(t * 1000)}.jpg"
        if not f.exists():
            run([FFMPEG, "-y", "-ss", f"{t:.3f}", "-i", c["source"], "-frames:v", "1", "-vf", "scale='min(1920,iw)':-2", "-q:v", "2", str(f)])
        if f.exists():
            out.append({"t": round(t, 2), "url": f"/media/kapak/{pid}/{f.name}"})
    return jsonify(frames=out, title=(p.get("paylasim") or {}).get("youtube", {}).get("baslik") or p.get("title"))


@app.get("/media/kapak/<pid>/<name>")
def media_kapak(pid, name):
    f = CACHE / "kapak" / safe_name(pid) / safe_name(name)
    if not f.exists():
        return "", 404
    return send_file(f)


# ================================================================ paylaşım: hazırla ve aç
UPLOAD_URLS = {"youtube": "https://www.youtube.com/upload", "tiktok": "https://www.tiktok.com/tiktokstudio/upload",
               "instagram": "https://www.instagram.com/"}


@app.post("/api/open_url")
def api_open_url():
    import webbrowser
    url = (request.get_json(force=True) or {}).get("url") or ""
    if not url.startswith(("https://", "http://")):
        return jsonify(error="Geçersiz adres"), 400
    webbrowser.open(url)
    return jsonify(ok=True)


@app.post("/api/share/open")
def api_share_open():
    import webbrowser
    d = request.get_json(force=True) or {}
    url = UPLOAD_URLS.get(d.get("platform") or "")
    if not url:
        return jsonify(error="Platform yok"), 400
    path = d.get("path") or ""
    if path and Path(path).exists() and IS_WIN:
        popen(["explorer", "/select,", str(Path(path))])
    webbrowser.open(url)
    return jsonify(ok=True)


@app.post("/api/reveal")
def api_reveal():
    path = (request.get_json(force=True) or {}).get("path", "")
    if not path or not Path(path).exists():
        return jsonify(error="Bulunamadı"), 404
    if IS_WIN:
        if Path(path).is_file():
            popen(["explorer", "/select,", str(Path(path))])
        else:
            os.startfile(path)  # noqa
    else:
        popen(["xdg-open", str(Path(path).parent if Path(path).is_file() else path)],
              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return jsonify(ok=True)


@app.post("/api/play")
def api_play():
    path = (request.get_json(force=True) or {}).get("path", "")
    if IS_WIN and Path(path).is_file():
        os.startfile(path)  # noqa
    return jsonify(ok=True)


# ================================================================ dosya ekleme
VIDEO_EXT = {".mp4", ".mkv", ".mov", ".webm", ".flv", ".ts", ".avi", ".m4v", ".wmv", ".mts"}
AUDIO_EXT = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".opus", ".wma"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}
LUT_EXT = {".cube"}
ALL_TYPES = ("Video müzik ve resim (*.mp4;*.mkv;*.mov;*.webm;*.flv;*.ts;*.avi;*.m4v;*.wmv;*.mp3;*.wav;*.m4a;*.aac;*.ogg;*.flac;*.png;*.jpg;*.jpeg;*.webp;*.gif;*.cube)",
             "Tüm dosyalar (*.*)")


def file_kind(path):
    ext = Path(path).suffix.lower()
    if ext in VIDEO_EXT:
        return "video"
    if ext in AUDIO_EXT:
        return "audio"
    if ext in IMAGE_EXT:
        return "image"
    if ext in LUT_EXT:
        return "lut"
    # uzantı tanınmazsa içine bak
    info = probe(path)
    if info["duration"] and info.get("width"):
        return "video" if info["duration"] > 0.5 else "image"
    if info["has_audio"]:
        return "audio"
    return None


def describe_file(path):
    if not path or not Path(path).exists():
        return {"error": "Dosya bulunamadı"}
    kind = file_kind(path)
    if not kind:
        return {"error": "Bu dosya türü desteklenmiyor: " + Path(path).name}
    out = {"path": str(path), "name": Path(path).name, "title": Path(path).stem, "kind": kind}
    if kind in ("video", "audio"):
        out["duration"] = probe(path)["duration"]
    return out


@app.post("/api/pick_any")
def api_pick_any():
    path = pick_file()
    if not path:
        return jsonify(path=None)
    return jsonify(describe_file(path))


@app.post("/api/describe")
def api_describe():
    return jsonify(describe_file((request.get_json(force=True) or {}).get("path")))


@app.post("/api/upload")
def api_upload():
    """Sürükle-bırak yedek yolu: dosyayı programın klasörüne kopyalar."""
    from core import VERI
    f = request.files.get("file")
    if not f:
        return jsonify(error="Dosya gelmedi"), 400
    folder = VERI / "eklenen"
    folder.mkdir(exist_ok=True)
    name = safe_name(Path(f.filename).stem, 60) + Path(f.filename).suffix.lower()
    dest = folder / name
    i = 2
    while dest.exists():
        dest = folder / f"{Path(name).stem} ({i}){Path(name).suffix}"
        i += 1
    f.save(dest)
    return jsonify(describe_file(str(dest)))


@app.route("/media/file/<pid>/<kind>")
def media_file(pid, kind):
    p = load_project(pid)
    media = p.get("media") or {}
    if kind == "img":
        iid, ipath = request.args.get("id", ""), request.args.get("v", "")
        m = next((im for im in media.get("images") or [] if im.get("id") == iid or im.get("path") == ipath), None)
    else:
        m = media.get(kind)
    if not m or not Path(m.get("path", "")).exists():
        abort(404)
    return send_file(m["path"], conditional=True)


def pick_file():
    if WINDOW is not None:
        import webview
        kind = getattr(getattr(webview, "FileDialog", None), "OPEN", None) or webview.OPEN_DIALOG
        r = WINDOW.create_file_dialog(kind, file_types=ALL_TYPES)
        return r[0] if r else None
    return _tk_dialog(False)


def pick_folder():
    if WINDOW is not None:
        import webview
        kind = getattr(getattr(webview, "FileDialog", None), "FOLDER", None) or webview.FOLDER_DIALOG
        r = WINDOW.create_file_dialog(kind)
        return (r[0] if isinstance(r, (list, tuple)) else r) if r else None
    return _tk_dialog(True)


def _tk_dialog(folder):
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        if folder:
            r = filedialog.askdirectory()
        else:
            r = filedialog.askopenfilename(filetypes=[("Video, müzik, resim", "*.mp4 *.mkv *.mov *.webm *.flv *.ts *.avi *.m4v *.mp3 *.wav *.m4a *.ogg *.flac *.png *.jpg *.jpeg *.webp *.gif *.cube"), ("Tümü", "*.*")])
        root.destroy()
        return r or None
    except Exception:
        return None
