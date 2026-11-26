"""Kesit Stüdyosu - yerel web sunucusu (arayüz <-> motor)."""
import os
import subprocess
import time
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_file, send_from_directory

import analyzer
import exporter
import kick
import transcribe
import updater
from core import (ANALIZ, APP, CACHE, FFMPEG, IS_WIN, JOBS, PROJELER, load_settings,
                  new_id, popen, probe, read_json, run, safe_name, save_settings,
                  thumbnail, write_json)

UI = APP / "ui"
WINDOW = None  # main.py pywebview penceresini buraya koyar

app = Flask(__name__, static_folder=None)


# ================================================================ projeler
def project_path(pid):
    if not pid.isalnum():
        abort(400)
    return PROJELER / pid / "proje.json"


def load_project(pid):
    p = read_json(project_path(pid))
    if not p:
        abort(404)
    return p


def save_project(p):
    p["updated"] = time.time()
    (PROJELER / p["id"]).mkdir(parents=True, exist_ok=True)
    write_json(project_path(p["id"]), p)


def create_project(source, title, kind, meta=None):
    info = probe(source)
    if not info["duration"]:
        raise RuntimeError("Video okunamadı: " + str(source))
    s = load_settings()
    pid = new_id("p")
    layout = dict(exporter.DEFAULT_LAYOUT)
    layout.update(s.get("varsayilan_duzen") or {})
    style = dict(exporter.DEFAULT_STYLE)
    style.update(s.get("varsayilan_stil") or {})
    p = {
        "id": pid, "title": title or Path(source).stem, "kind": kind, "source": str(source),
        "created": time.time(), "duration": info["duration"], "width": info["width"],
        "height": info["height"], "fps": info["fps"], "has_audio": info["has_audio"],
        "segments": [{"start": 0.0, "end": round(info["duration"], 3)}],
        "layout": layout, "style": style, "words": [], "captions": [],
        "subs_status": "yok", "exports": [], "meta": meta or {},
    }
    save_project(p)
    return p


def project_summary(p):
    return {k: p.get(k) for k in ("id", "title", "kind", "created", "updated", "duration",
                                  "subs_status", "exports", "width", "height")}


def all_projects():
    out = []
    for f in PROJELER.glob("*/proje.json"):
        p = read_json(f)
        if p:
            out.append(project_summary(p))
    out.sort(key=lambda p: p.get("created") or 0, reverse=True)
    return out


# ================================================================ işler
def job_transcribe(job, pid):
    p = load_project(pid)
    p["subs_status"] = "calisiyor"
    save_project(p)
    try:
        words = transcribe.transcribe(job, p["source"], p["duration"])
    except Exception:
        p = load_project(pid)
        p["subs_status"] = "hata"
        save_project(p)
        raise
    p = load_project(pid)
    p["words"] = words
    mw = int((p.get("style") or {}).get("maxWords") or 3)
    p["captions"] = transcribe.chunk_words(words, max_words=mw)
    p["subs_status"] = "hazir"
    save_project(p)
    flagged = sum(1 for w in words if w.get("p", 1) < 0.55)
    job.set(1, f"Altyazı hazır · {len(words)} kelime" + (f" · {flagged} şüpheli" if flagged else ""))
    return {"project": pid, "flagged": flagged}


def start_transcribe(pid, title):
    return JOBS.start("altyazi", "Altyazı: " + title, job_transcribe, pid, heavy=True)


def _after_project(p):
    if load_settings().get("oto_altyazi") and p.get("has_audio"):
        start_transcribe(p["id"], p["title"])


def job_download_clip(job, url, title):
    path, info = kick.download(job, url, title, 0, 0.95)
    job.set(0.97, "Proje hazırlanıyor...")
    p = create_project(path, title or info.get("title"), "klip", {"url": url})
    _after_project(p)
    job.set(1, "İndirildi, editörde hazır")
    return {"project": p["id"]}


def job_analyze(job, src, title, local, mode="orta", count=20):
    s = load_settings()
    cfg = analyzer.MODES.get(mode, analyzer.MODES["orta"])
    aid = new_id("a")
    if local:
        path = src
    else:
        path, _ = kick.download(job, src, title, 0, 0.55, preview=True)
    info = probe(path)
    job.set(0.56 if not local else 0.02, "Ses analiz ediliyor...")
    db = analyzer.energy_curve(job, path, info["duration"], 0.56 if not local else 0.02, 0.97)
    moments, curve = analyzer.find_moments(db, info["duration"], before=cfg["before"], after=cfg["after"],
                                           max_count=int(count), max_len=cfg["max_len"], ext=cfg["ext"])
    data = {"id": aid, "title": title, "source": src, "local": local, "preview": path, "mode": mode,
            "duration": info["duration"], "moments": moments, "curve": curve,
            "created": time.time()}
    write_json(ANALIZ / f"{aid}.json", data)
    job.set(1, f"{len(moments)} an bulundu")
    return {"analysis": aid, "count": len(moments)}


def job_moment(job, aid, m):
    a = read_json(ANALIZ / f"{aid}.json")
    if not a:
        raise RuntimeError("Analiz bulunamadı")
    start, end = float(m["start"]), float(m["end"])
    title = f"{a['title']} - {m.get('label', 'An')} {int(start//60)}.{int(start%60):02d}"
    pad = 1.5
    if a["local"]:
        from core import INDIRILEN
        out = INDIRILEN / f"{safe_name(a['title'], 40)}_{int(start)}-{int(end)}_{new_id()}.mp4"
        job.set(0.1, "Parça kesiliyor...")
        r = run([FFMPEG, "-y", "-ss", f"{max(0, start - pad):.2f}", "-i", a["source"],
                 "-t", f"{end - start + 2 * pad:.2f}", "-map", "0:v:0", "-map", "0:a?",
                 "-c", "copy", "-avoid_negative_ts", "make_zero", str(out)])
        if r.returncode != 0 or not out.exists():
            raise RuntimeError("Parça kesilemedi: " + r.stderr[-300:])
        path = str(out)
    else:
        path, _ = kick.download(job, a["source"], title, 0, 0.95,
                                section=(max(0, start - pad), end + pad))
    p = create_project(path, title, "an", {"analysis": aid, "moment": m})
    # baştaki/sondaki fazlalığı kırp (indirme anahtar kareden başlayabilir)
    real = p["duration"]
    extra = max(0.0, real - (end - start))
    lead = min(pad, extra / 2) if extra > 0.5 else 0.0
    p["segments"] = [{"start": round(lead, 3), "end": round(min(real, lead + end - start), 3)}]
    save_project(p)
    _after_project(p)
    job.set(1, "An hazır, editörde aç")
    return {"project": p["id"]}


def job_export(job, pid, opts):
    p = load_project(pid)
    res = exporter.export(job, p, opts)
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


@app.route("/media/project/<pid>")
def media_project(pid):
    p = load_project(pid)
    return send_file(p["source"], conditional=True)


@app.route("/media/analysis/<aid>")
def media_analysis(aid):
    a = read_json(ANALIZ / f"{safe_name(aid)}.json")
    if not a:
        abort(404)
    return send_file(a["preview"], conditional=True)


@app.route("/media/export")
def media_export():
    path = request.args.get("path", "")
    pid = request.args.get("pid", "")
    p = load_project(pid)
    if not any(e.get("path") == path for e in p.get("exports", [])) or not Path(path).exists():
        abort(404)
    return send_file(path, conditional=True)


@app.route("/thumb/<pid>")
def thumb(pid):
    p = load_project(pid)
    out = CACHE / f"{pid}.jpg"
    t = (p.get("segments") or [{"start": 0}])[0]["start"] + 1
    thumbnail(p["source"], out, t=min(t, max(0, p["duration"] - 0.5)))
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
        j.cancelled = True
    return jsonify(ok=True)


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
    return jsonify(info)


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
    jobs = [JOBS.start("indir", "Klip: " + (it.get("title") or "")[:40], job_download_clip,
                       it["url"], it.get("title") or "Kick klip").id for it in items if it.get("url")]
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
    aid = d.get("analysis")
    jobs = [JOBS.start("an", f"An indir: {m.get('label','')} {int(float(m['start'])//60)}dk",
                       job_moment, aid, m).id for m in d.get("moments") or []]
    return jsonify(jobs=jobs)


@app.post("/api/local/project")
def api_local_project():
    d = request.get_json(force=True) or {}
    path = d.get("path")
    if not path or not Path(path).exists():
        return jsonify(error="Dosya bulunamadı"), 400
    if file_kind(path) != "video":
        return jsonify(error="Bu bir video dosyası değil"), 400
    p = create_project(path, d.get("title") or Path(path).stem, "yerel")
    _after_project(p)
    return jsonify(project=p["id"])


@app.get("/api/project/<pid>")
def api_project(pid):
    return jsonify(load_project(pid))


@app.post("/api/project/<pid>")
def api_project_save(pid):
    cur = load_project(pid)
    d = request.get_json(force=True) or {}
    for k in ("title", "segments", "layout", "style", "captions", "effects", "media"):
        if k in d:
            cur[k] = d[k]
    save_project(cur)
    return jsonify(ok=True, updated=cur["updated"])


@app.delete("/api/project/<pid>")
def api_project_delete(pid):
    p = load_project(pid)
    import shutil
    shutil.rmtree(PROJELER / pid, ignore_errors=True)
    (CACHE / f"{pid}.jpg").unlink(missing_ok=True)
    if d := request.args.get("dosya"):
        if d == "1" and p.get("kind") in ("klip", "an"):
            Path(p["source"]).unlink(missing_ok=True)
    return jsonify(ok=True)


@app.post("/api/project/<pid>/transcribe")
def api_project_transcribe(pid):
    p = load_project(pid)
    j = start_transcribe(pid, p["title"])
    return jsonify(job=j.id)


@app.post("/api/project/<pid>/rechunk")
def api_rechunk(pid):
    p = load_project(pid)
    mw = int((request.get_json(force=True) or {}).get("maxWords") or 3)
    words = [w for c in p.get("captions") or [] for w in c.get("words") or []] or p.get("words") or []
    p["captions"] = transcribe.chunk_words(words, max_words=mw)
    p.setdefault("style", {})["maxWords"] = mw
    save_project(p)
    return jsonify(captions=p["captions"])


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


@app.get("/api/project/<pid>/wave")
def api_wave(pid):
    p = load_project(pid)
    f = PROJELER / pid / "wave.json"
    w = read_json(f)
    if w is None:
        w = analyzer.waveform(p["source"]) if p.get("has_audio") else []
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
        p = load_project(pid)
        for c in p.get("captions") or []:
            c["words"] = transcribe.apply_fixes(c.get("words") or [], fixes)
        save_project(p)
        out["captions"] = p["captions"]
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
