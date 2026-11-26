"""Proje modeli (v2): çok videolu zaman çizelgesi.

project = {
  id, title, format: dikey|yatay|kare, version: 2,
  clips: [ {id, source, name, src_dur, width, height, fps, has_audio,
            in, out, speed, layout, words: [...], captions: [...], subs_status} ],
  overlays: [ {id, source, name, src_dur, width, height, has_audio,
               s, e, in, x, y, w, opacity, volume, chroma, chroma_color, similarity} ],
  style, effects (zaman = zaman çizelgesi saniyesi), media
}
Kliplerin içindeki altyazı kelimeleri kaynak videonun zamanındadır;
geri kalan her şey (yazılar, efektler, resimler, müzik, zoom, üst videolar)
zaman çizelgesi zamanındadır."""
import copy
import hashlib
import json
from pathlib import Path

from core import CACHE, new_id, probe

FORMATS = {"dikey": (1080, 1920), "yatay": (1920, 1080), "kare": (1080, 1080)}
FORMAT_NAMES = {"dikey": "Dikey 9:16", "yatay": "Yatay 16:9", "kare": "Kare 1:1"}


def base_size(fmt):
    return FORMATS.get(fmt, FORMATS["dikey"])


def out_size(fmt, short_side):
    W, H = base_size(fmt)
    k = short_side / min(W, H)
    w, h = int(round(W * k)), int(round(H * k))
    return w - w % 2, h - h % 2


def default_layout(fmt, src_w, src_h, user_default=None):
    W, H = base_size(fmt)
    if fmt == "dikey":
        lay = {"mode": "split", "split": 0.4,
               "face": {"x": 0.0, "y": 0.0, "w": 0.3, "h": 0.3},
               "game": {"x": 0.2, "y": 0.0, "w": 0.6, "h": 1.0},
               "crop": {"x": 0.34, "y": 0.0, "w": 0.32, "h": 1.0}}
        if user_default:
            lay.update(copy.deepcopy(user_default))
    else:
        same = abs((src_w / max(1, src_h)) - (W / H)) < 0.02
        lay = {"mode": "fit" if same else ("blur" if fmt == "kare" else "fit"), "split": 0.5,
               "face": {"x": 0.0, "y": 0.0, "w": 0.3, "h": 0.3},
               "game": {"x": 0.2, "y": 0.0, "w": 0.6, "h": 1.0},
               "crop": {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0}}
    return fix_layout(lay, fmt, src_w, src_h)


def fix_layout(lay, fmt, src_w, src_h):
    """Kutuların en-boy oranını çıktı biçimine göre düzelt."""
    W, H = base_size(fmt)
    r = float(lay.get("split", 0.4))
    asp = {"face": W / (H * r), "game": W / (H * (1 - r)), "crop": W / H}
    for k, a in asp.items():
        rc = dict(lay.get(k) or {"x": 0, "y": 0, "w": 0.5, "h": 0.5})
        rc["h"] = rc["w"] * src_w / (a * src_h)
        if rc["h"] > 1:
            rc["h"] = 1.0
            rc["w"] = a * src_h / src_w
        if rc["w"] > 1:
            rc["w"] = 1.0
            rc["h"] = rc["w"] * src_w / (a * src_h)
        rc["x"] = min(max(0.0, rc["x"]), 1 - rc["w"])
        rc["y"] = min(max(0.0, rc["y"]), 1 - rc["h"])
        lay[k] = rc
    if fmt != "dikey" and lay.get("mode") == "split":
        lay["mode"] = "blur"
    return lay


def detect_content(path, duration, W, H):
    """Videonun kendi siyah kenarlarını (letterbox) bulur. Dönüş: normalize kutu ya da None."""
    import re
    import subprocess
    from core import FFMPEG, NO_WINDOW
    boxes = []
    for frac in (0.25, 0.5, 0.75):
        ss = max(0.0, duration * frac)
        try:
            r = subprocess.run([FFMPEG, "-hide_banner", "-ss", f"{ss:.2f}", "-i", str(path), "-t", "1.5",
                                "-vf", "cropdetect=limit=24:round=2:reset=0", "-an", "-f", "null", "-"],
                               capture_output=True, text=True, timeout=40, creationflags=NO_WINDOW)
            m = re.findall(r"crop=(\d+):(\d+):(\d+):(\d+)", r.stderr)
            if m:
                boxes.append(tuple(int(v) for v in m[-1]))
        except Exception:
            pass
    if not boxes:
        return None
    # en geniş görüntü alanını al (karanlık sahneler yanıltmasın)
    x0 = min(b[2] for b in boxes)
    y0 = min(b[3] for b in boxes)
    x1 = max(b[2] + b[0] for b in boxes)
    y1 = max(b[3] + b[1] for b in boxes)
    w, h = x1 - x0, y1 - y0
    if w < W * 0.3 or h < H * 0.3 or (w >= W * 0.985 and h >= H * 0.985):
        return None
    return {"x": round(x0 / W, 4), "y": round(y0 / H, 4), "w": round(w / W, 4), "h": round(h / H, 4)}


def media_info(path, detect=True):
    info = probe(path)
    out = {"source": str(path), "name": Path(path).name, "src_dur": round(info["duration"], 3),
           "width": info["width"], "height": info["height"], "fps": info["fps"],
           "has_audio": info["has_audio"]}
    if detect and info["duration"] and info["width"]:
        out["content"] = detect_content(path, info["duration"], info["width"], info["height"])
    return out


def content_size(c):
    """Siyah kenarlar atıldıktan sonraki görüntü boyutu (piksel)."""
    cb = c.get("content")
    if not cb:
        return c["width"], c["height"]
    return max(2, int(c["width"] * cb["w"])), max(2, int(c["height"] * cb["h"]))


def new_clip(path, fmt, user_layout=None, info=None):
    info = info or media_info(path)
    if not info["src_dur"]:
        raise RuntimeError("Video okunamadı: " + Path(path).name)
    cw, ch = content_size(info)
    c = {"id": new_id("c"), **info, "in": 0.0, "out": info["src_dur"], "speed": 1.0,
         "layout": default_layout(fmt, cw, ch, user_layout),
         "words": [], "captions": [], "subs_status": "yok"}
    return c


def clip_len(c):
    return max(0.0, (float(c["out"]) - float(c["in"])) / max(0.25, float(c.get("speed") or 1)))


def timeline(project):
    """Her klibin zaman çizelgesindeki başlangıcı."""
    t = 0.0
    out = []
    for c in project.get("clips") or []:
        L = clip_len(c)
        out.append((c, t, L))
        t += L
    return out, t


def total_duration(project):
    return timeline(project)[1]


def words_cache_path(source):
    p = Path(source)
    try:
        key = f"{p.resolve()}|{p.stat().st_size}|{int(p.stat().st_mtime)}"
    except Exception:
        key = str(p)
    return CACHE / ("words_" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:16] + ".json")


def cached_words(source):
    f = words_cache_path(source)
    if f.exists():
        try:
            return json.loads(f.read_text("utf-8"))
        except Exception:
            return None
    return None


def save_words(source, words):
    words_cache_path(source).write_text(json.dumps(words, ensure_ascii=False), "utf-8")


# ------------------------------------------------------------------ eski projeyi taşı
def migrate(p):
    """v1 (tek video + parçalar, katmanlar kaynak zamanında) -> v2."""
    if p.get("version") == 2:
        return p
    src = p.get("source")
    segs = sorted(p.get("segments") or [{"start": 0, "end": p.get("duration", 0)}], key=lambda s: s["start"])
    fx = dict(p.get("effects") or {})
    speed = max(0.5, min(2.0, float(fx.get("speed") or 1)))
    info = {"source": src, "name": Path(src).name if src else "video", "src_dur": p.get("duration", 0),
            "width": p.get("width", 1920), "height": p.get("height", 1080), "fps": p.get("fps", 30),
            "has_audio": p.get("has_audio", True)}
    words = p.get("words") or []
    caps = p.get("captions") or []
    clips = []
    for sg in segs:
        c = {"id": new_id("c"), **info, "in": float(sg["start"]), "out": float(sg["end"]), "speed": speed,
             "layout": copy.deepcopy(p.get("layout") or {}), "words": [w for w in words if sg["start"] - 0.5 <= w["s"] <= sg["end"] + 0.5],
             "captions": [c_ for c_ in caps if sg["start"] - 0.05 <= (c_["s"] + c_["e"]) / 2 <= sg["end"] + 0.05],
             "subs_status": p.get("subs_status", "yok")}
        c["layout"] = fix_layout(c["layout"] or default_layout("dikey", info["width"], info["height"]),
                                 "dikey", info["width"], info["height"])
        clips.append(c)

    def tl(t):  # eski kaynak zamanı -> zaman çizelgesi
        off = 0.0
        for sg in segs:
            if t <= sg["end"] + 1e-3:
                return round((off + max(0.0, min(t, sg["end"]) - sg["start"])) / speed, 3)
            off += sg["end"] - sg["start"]
        return round(off / speed, 3)
    for k in ("texts", "fxLayers"):
        for o in fx.get(k) or []:
            o["s"], o["e"] = tl(o["s"]), tl(o["e"])
    for z in fx.get("zooms") or []:
        z["t"] = tl(z["t"])
    fx["speed"] = 1
    media = dict(p.get("media") or {})
    for im in media.get("images") or []:
        im["s"], im["e"] = tl(im.get("s", 0)), tl(im.get("e", p.get("duration", 0)))
    if media.get("music"):
        media["music"]["s"] = tl(media["music"].get("s", 0))
    p.update({"version": 2, "format": "dikey", "clips": clips, "overlays": [], "effects": fx, "media": media})
    for k in ("source", "segments", "layout", "captions", "words", "duration", "width", "height", "fps", "has_audio"):
        p.pop(k, None)
    return p
