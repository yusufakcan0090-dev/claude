"""Dışa aktarma (v2): çok klip + biçim (dikey/yatay/kare) + katmanlar + efektler + altyazı."""
import json
from pathlib import Path

import anim
import fxlib
import model
from core import FFMPEG, ROOT, load_settings, run_ffmpeg_progress, safe_name, tr_upper

# libass yazı boyutunu (Win yükseliş+iniş)/em oranına göre küçültür; önizlemedeki px boyutu tutsun diye çarpılır
FONT_RATIO = {"anton": 1.7334, "poppins": 1.762, "poppins-black": 1.762, "bangers": 1.757}
_FM = None


def text_width(text, font, size):
    """Yazının piksel genişliği (önizlemedeki ölçümle aynı yazı tipi verisiyle)."""
    global _FM
    if _FM is None:
        try:
            _FM = json.loads((Path(__file__).parent / "fontmetrics.json").read_text("utf-8"))
        except Exception:
            _FM = {}
    m = _FM.get(font) or _FM.get("poppins-black") or {}
    d = m.get("_default", 0.6)
    return sum(m.get(ch, d) for ch in text) * size


FONT_FAMILY = {"anton": "Anton", "poppins": "Poppins ExtraBold", "poppins-black": "Poppins Black", "bangers": "Bangers"}
DEFAULT_STYLE = {"font": "poppins-black", "size": 88, "color": "#FFFFFF", "hl": "#FFE14D", "outline": "#000000",
                 "outlineW": 9, "shadow": True, "y": 68, "upper": True, "karaoke": True, "anim": True, "maxWords": 3}
DEFAULT_EFFECTS = {"preset": "none", "bright": 0, "contrast": 0, "sat": 0, "temp": 0, "vignette": False,
                   "grain": False, "glow": False, "rgb": False, "sharpen": False, "mirror": False,
                   "fadeIn": False, "fadeOut": False, "zooms": [], "texts": [], "fxLayers": [],
                   "transition": {"type": "none", "d": 0.4}, "lut": None, "hide": {}}
PRESETS = {
    "none": "",
    "sinematik": "eq=contrast=1.12:saturation=0.88:brightness=-0.02,colorbalance=rs=-0.04:bs=0.07:rh=0.07:bh=-0.05",
    "canli": "eq=saturation=1.45:contrast=1.08",
    "sb": "hue=s=0,eq=contrast=1.22",
    "vintage": "curves=preset=vintage,eq=saturation=0.85",
    "soguk": "colortemperature=temperature=9000,eq=saturation=1.05",
    "sicak": "colortemperature=temperature=4300,eq=saturation=1.12",
    "neon": "eq=saturation=1.6:contrast=1.15,colorbalance=rs=0.08:bs=0.12:gm=-0.08",
}
LOGO_POS = {"tl": "40:40", "tr": "W-w-40:40", "bl": "40:H-h-40", "br": "W-w-40:H-h-40", "c": "(W-w)/2:(H-h)/2"}


# ------------------------------------------------------------------ yardımcılar
def _ass_color(hexc, alpha=0):
    h = (hexc or "#FFFFFF").lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return f"&H{alpha:02X}{h[4:6]}{h[2:4]}{h[0:2]}".upper()


def _ts(t):
    cs = int(round(max(0.0, t) * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _esc(text):
    return text.replace("\\", "＼").replace("{", "(").replace("}", ")").replace("\n", " ")


def effects_of(project):
    fx = dict(DEFAULT_EFFECTS)
    fx.update(project.get("effects") or {})
    return fx


def color_chain(fx):
    parts = []
    if PRESETS.get(fx.get("preset")):
        parts.append(PRESETS[fx["preset"]])
    b, c, s_ = float(fx.get("bright") or 0), float(fx.get("contrast") or 0), float(fx.get("sat") or 0)
    if b or c or s_:
        parts.append(f"eq=brightness={b / 250:.3f}:contrast={1 + c / 100:.3f}:saturation={max(0, 1 + s_ / 100):.3f}")
    if float(fx.get("temp") or 0):
        parts.append(f"colortemperature=temperature={int(6500 - float(fx['temp']) * 30)}")
    return ",".join(parts)


def apply_hidden(project):
    """Gizli (göz kapalı) ve solo katmanları uygula."""
    p = dict(project)
    fx0 = dict(p.get("effects") or {})
    md0 = dict(p.get("media") or {})
    groups = [(fx0, "texts"), (fx0, "shapes"), (fx0, "fxLayers"), (md0, "images"), (p, "overlays")]
    solo = any(o.get("solo") for d, k in groups for o in d.get(k) or [])
    for d, k in groups:
        d[k] = [o for o in d.get(k) or [] if not o.get("hidden") and (not solo or o.get("solo"))]
    p["effects"], p["media"] = fx0, md0
    project = p
    hide = (project.get("effects") or {}).get("hide") or {}
    if not any(hide.values()):
        return project
    p = dict(project)
    fx = dict(p.get("effects") or {})
    media = dict(p.get("media") or {})
    if hide.get("cap"):
        p["clips"] = [dict(c, captions=[]) for c in p.get("clips") or []]
    if hide.get("text"):
        fx["texts"] = []
        fx["shapes"] = []
    if hide.get("zoom"):
        fx["zooms"] = []
    if hide.get("fx"):
        fx["fxLayers"] = []
        fx["transition"] = {"type": "none"}
    if hide.get("image"):
        media["images"] = []
    if hide.get("music"):
        media["music"] = None
    if hide.get("pip"):
        p["overlays"] = []
    p["effects"], p["media"] = fx, media
    return p


# ------------------------------------------------------------------ altyazı (ASS)
def timeline_captions(project):
    """Kliplerdeki altyazıları zaman çizelgesine taşı: [[{w,s,e},...], ...]"""
    tl, _ = model.timeline(project)
    chunks = []
    for c, start, L in tl:
        sp = max(0.25, float(c.get("speed") or 1))
        for cap in c.get("captions") or []:
            ws = []
            for w in cap.get("words") or []:
                mid = (w["s"] + w["e"]) / 2
                if not (c["in"] - 1e-3 <= mid <= c["out"] + 1e-3):
                    continue
                s = start + (max(w["s"], c["in"]) - c["in"]) / sp
                e = start + (min(w["e"], c["out"]) - c["in"]) / sp
                txt = (w.get("w") or "").strip()
                if txt:
                    ws.append({"w": txt, "s": s, "e": max(e, s + 0.05)})
            if ws:
                chunks.append(ws)
    chunks.sort(key=lambda ws: ws[0]["s"])
    return chunks


def build_ass(project):
    BW, BH = model.base_size(project.get("format"))
    st = dict(DEFAULT_STYLE)
    st.update(project.get("style") or {})
    fam = FONT_FAMILY.get(st["font"], "Poppins Black")
    base_c, hl_c, out_c = _ass_color(st["color"]), _ass_color(st["hl"]), _ass_color(st["outline"])
    y = int(BH * float(st["y"]) / 100)
    cx = BW // 2
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {BW}
PlayResY: {BH}
WrapStyle: 1
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: K,{fam},{float(st['size']) * FONT_RATIO.get(st['font'], 1.762):.1f},{base_c},{hl_c},{out_c},&H96000000,0,0,0,0,100,100,0,0,1,{float(st['outlineW']):.1f},{4 if st.get('shadow') else 0},5,70,70,0,1
Style: T,Poppins Black,80,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,7,3,5,60,60,0,1
Style: TB,Poppins Black,80,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,3,18,0,5,60,60,0,1
Style: S,Arial,20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    chunks = timeline_captions(project)
    if st.get("upper"):
        for ws in chunks:
            for w in ws:
                w["w"] = tr_upper(w["w"])
    size = float(st["size"])
    lh = size * 1.12  # önizlemedeki satır aralığı
    maxw = BW - 140

    def wrap(ws):
        out, cur = [], []
        for w in ws:
            if cur and text_width(" ".join(x["w"] for x in cur + [w]), st["font"], size) > maxw:
                out.append(cur)
                cur = [w]
            else:
                cur.append(w)
        if cur:
            out.append(cur)
        return out

    for i, ws in enumerate(chunks):
        start, end = ws[0]["s"], ws[-1]["e"] + 0.35
        if i + 1 < len(chunks):
            nxt = chunks[i + 1][0]["s"]
            end = min(end, nxt)
            if nxt - ws[-1]["e"] < 0.35:
                end = nxt
        end = max(end, start + 0.2)
        rows = wrap(ws)
        tot = len(rows) * lh
        # her satır ayrı olay: satır aralığı önizlemeyle birebir aynı olsun
        centers = [y - tot / 2 + lh * k + lh / 2 for k in range(len(rows))]
        pop = "\\fscx72\\fscy72\\t(0,110,\\fscx104\\fscy104)\\t(110,170,\\fscx100\\fscy100)" if st.get("anim") else ""
        segs = []
        if st.get("karaoke") and len(ws) > 1:
            for k, w in enumerate(ws):
                es = start if k == 0 else w["s"]
                ee = ws[k + 1]["s"] if k + 1 < len(ws) else end
                if ee - es >= 0.02:
                    segs.append((es, ee, w))
        else:
            segs.append((start, end, None))
        for si, (es, ee, act) in enumerate(segs):
            for row, cy in zip(rows, centers):
                parts = [f"{{\\1c{hl_c}}}{_esc(x['w'])}{{\\1c{base_c}}}" if x is act else _esc(x["w"]) for x in row]
                lines.append(f"Dialogue: 0,{_ts(es)},{_ts(ee)},K,,0,0,0,,{{\\an5\\pos({cx},{cy:.1f}){pop if si == 0 else ''}}}{' '.join(parts)}")
    lines += text_events(project, BW, BH)
    return head + "\n".join(lines) + "\n"


def _tags(x, y, sc, rot, op):
    return f"\\pos({x:.1f},{y:.1f})\\fscx{sc:.1f}\\fscy{sc:.1f}\\frz{-rot:.2f}\\alpha&H{int(255 * (1 - max(0, min(1, op / 100)))):02X}&"


def _anim_events(obj, s, e, BW, BH, style, body, defaults, layer=1):
    """Keyframe'li katmanı 1/15 sn parçalara bölüp \\move ve \\t ile pürüzsüz canlandırır."""
    out = []
    if not anim.animated(obj):
        v = {p: anim.value(obj, p, 0, defaults) for p in anim.PROPS}
        out.append(f"Dialogue: {layer},{_ts(s)},{_ts(e)},{style},,0,0,0,,{{\\an5{_tags(v['x'] * BW, v['y'] * BH, v['scale'], v['rot'], v['op'])}{body[0]}}}{body[1]}")
        return out
    step = 1 / 15
    t = s
    while t < e - 1e-4:
        t1 = min(e, t + step)
        v0 = {p: anim.value(obj, p, t - s, defaults) for p in anim.PROPS}
        v1 = {p: anim.value(obj, p, t1 - s, defaults) for p in anim.PROPS}
        d = int(round((t1 - t) * 1000))
        a0 = int(255 * (1 - max(0, min(1, v0['op'] / 100))))
        a1 = int(255 * (1 - max(0, min(1, v1['op'] / 100))))
        tag = (f"\\an5\\move({v0['x'] * BW:.1f},{v0['y'] * BH:.1f},{v1['x'] * BW:.1f},{v1['y'] * BH:.1f},0,{d})"
               f"\\fscx{v0['scale']:.1f}\\fscy{v0['scale']:.1f}\\frz{-v0['rot']:.2f}\\alpha&H{a0:02X}&"
               f"\\t(0,{d},\\fscx{v1['scale']:.1f}\\fscy{v1['scale']:.1f}\\frz{-v1['rot']:.2f}\\alpha&H{a1:02X}&)")
        out.append(f"Dialogue: {layer},{_ts(t)},{_ts(t1)},{style},,0,0,0,,{{{tag}{body[0]}}}{body[1]}")
        t = t1
    return out


def text_defaults(tx):
    return {"x": 0.5, "y": float(tx.get("y", 18)) / 100}


def text_events(project, BW, BH):
    out = []
    total = model.total_duration(project)
    fx = project.get("effects") or {}
    hide = fx.get("hide") or {}
    for tx in fx.get("texts") or []:
        raw = (tx.get("text") or "").strip()
        if not raw or tx.get("hidden"):
            continue
        s, e = float(tx["s"]), min(float(tx["e"]), total)
        if e - s < 0.1:
            continue
        txt = _esc(tr_upper(raw) if tx.get("upper", True) else raw)
        fam = FONT_FAMILY.get(tx.get("font") or "poppins-black", "Poppins Black")
        box = tx.get("box", True) is not False
        style = "TB" if box else "T"
        base = f"\\fn{fam}\\fs{float(tx.get('size', 80)) * FONT_RATIO.get(tx.get('font') or 'poppins-black', 1.762):.1f}\\1c{_ass_color(tx.get('color') or '#FFFFFF')}" + \
               (f"\\3c{_ass_color(tx.get('boxColor') or '#FF3D8B')}" if box else "")
        dfl = text_defaults(tx)
        if anim.animated(tx) or anim.has_rotation(tx, dfl) or anim.tf_of(tx, dfl)["scale"] != 100 or anim.tf_of(tx, dfl)["op"] < 100:
            out += _anim_events(tx, s, e, BW, BH, style, (base, txt), dfl)
            continue
        x, y = anim.tf_of(tx, dfl)["x"] * BW, anim.tf_of(tx, dfl)["y"] * BH
        anim_k = tx.get("anim") or "pop"
        if anim_k == "type":
            n = len(txt)
            step = min(0.06, max(0.02, (e - s) * 0.4 / max(1, n)))
            for k in range(1, n + 1):
                es, ee = s + (k - 1) * step, (s + k * step if k < n else e)
                if ee > es:
                    out.append(f"Dialogue: 1,{_ts(es)},{_ts(ee)},{style},,0,0,0,,{{\\an5\\pos({x:.0f},{y:.0f}){base}}}{txt[:k]}{{\\alpha&HFF&}}{txt[k:]}")
            continue
        if anim_k == "slide":
            mv = f"\\move({-BW // 2 - 200},{y:.0f},{x:.0f},{y:.0f},0,260)\\fad(0,180)"
        elif anim_k == "fade":
            mv = f"\\pos({x:.0f},{y:.0f})\\fad(300,300)"
        elif anim_k == "none":
            mv = f"\\pos({x:.0f},{y:.0f})"
        else:
            mv = f"\\pos({x:.0f},{y:.0f})\\fscx60\\fscy60\\t(0,140,\\fscx108\\fscy108)\\t(140,220,\\fscx100\\fscy100)\\fad(0,150)"
        out.append(f"Dialogue: 1,{_ts(s)},{_ts(e)},{style},,0,0,0,,{{\\an5{mv}{base}}}{txt}")
    # şekiller ve düz renk katmanları (alttakiler önce çizilir)
    for sh in reversed(fx.get("shapes") or []):
        if sh.get("hidden"):
            continue
        s, e = float(sh["s"]), min(float(sh["e"]), total)
        if e - s < 0.05:
            continue
        w, h = float(sh.get("w", 0.4)) * BW, float(sh.get("h", 0.2)) * BH
        path = shape_path(sh.get("kind", "rect"), w, h, float(sh.get("radius", 0)) * min(w, h) / 2)
        sw = float(sh.get("strokeW", 0))
        body = (f"\\1c{_ass_color(sh.get('fill') or '#FF3D8B')}\\3c{_ass_color(sh.get('stroke') or '#FFFFFF')}"
                f"\\bord{sw:.1f}\\shad0\\p1" + ("\\1a&HFF&" if sh.get("noFill") else ""), path + "{\\p0}")
        out += _anim_events(sh, s, e, BW, BH, "S", body, {"x": 0.5, "y": 0.5}, layer=0)
    return out


def shape_path(kind, w, h, r=0):
    if kind == "ellipse":
        k = 0.5523
        cx, cy, rx, ry = w / 2, h / 2, w / 2, h / 2
        return (f"m {cx - rx:.1f} {cy:.1f} b {cx - rx:.1f} {cy - k * ry:.1f} {cx - k * rx:.1f} {cy - ry:.1f} {cx:.1f} {cy - ry:.1f} "
                f"b {cx + k * rx:.1f} {cy - ry:.1f} {cx + rx:.1f} {cy - k * ry:.1f} {cx + rx:.1f} {cy:.1f} "
                f"b {cx + rx:.1f} {cy + k * ry:.1f} {cx + k * rx:.1f} {cy + ry:.1f} {cx:.1f} {cy + ry:.1f} "
                f"b {cx - k * rx:.1f} {cy + ry:.1f} {cx - rx:.1f} {cy + k * ry:.1f} {cx - rx:.1f} {cy:.1f}")
    r = max(0.0, min(r, w / 2, h / 2))
    if r < 0.5:
        return f"m 0 0 l {w:.1f} 0 {w:.1f} {h:.1f} 0 {h:.1f}"
    k = r * 0.4477
    return (f"m {r:.1f} 0 l {w - r:.1f} 0 b {w - k:.1f} 0 {w:.1f} {k:.1f} {w:.1f} {r:.1f} l {w:.1f} {h - r:.1f} "
            f"b {w:.1f} {h - k:.1f} {w - k:.1f} {h:.1f} {w - r:.1f} {h:.1f} l {r:.1f} {h:.1f} "
            f"b {k:.1f} {h:.1f} 0 {h - k:.1f} 0 {h - r:.1f} l 0 {r:.1f} b 0 {k:.1f} {k:.1f} 0 {r:.1f} 0")


def OV_DEF(ov):
    """Eski üst video ayarlarından (x,y sol-üst) dönüştürme varsayılanı."""
    w = float(ov.get("w", 0.4))
    return {"x": float(ov.get("x", 0.55)) + w / 2, "y": float(ov.get("y", 0.06)) + 0.15, "op": 100 * float(ov.get("opacity", 1))}


IMG_POS = {"tl": (0.18, 0.1), "tr": (0.82, 0.1), "bl": (0.18, 0.9), "br": (0.82, 0.9), "c": (0.5, 0.5)}


def IMG_DEF(im, OW=1080, OH=1920):
    x, y = IMG_POS.get(im.get("pos", "tr"), IMG_POS["tr"])
    return {"x": x, "y": y, "op": 100 * float(im.get("opacity", 1))}


# ------------------------------------------------------------------ kadraj
def _rect(r, W, H):
    x = max(0, min(W - 2, int(r["x"] * W)))
    y = max(0, min(H - 2, int(r["y"] * H)))
    w = max(2, min(W - x, int(r["w"] * W)))
    h = max(2, min(H - y, int(r["h"] * H)))
    return f"crop={w - w % 2}:{h - h % 2}:{x - x % 2}:{y - y % 2}"


def layout_chain(inp, out, clip, fmt, OW, OH):
    W, H = model.content_size(clip)
    lay = model.fix_layout(dict(clip.get("layout") or model.default_layout(fmt, W, H)), fmt, W, H)
    mode = lay.get("mode", "fit")
    k = inp + "_"
    cb = clip.get("content")
    if cb:  # videonun kendi siyah kenarlarını at
        cx, cy = int(clip["width"] * cb["x"]) // 2 * 2, int(clip["height"] * cb["y"]) // 2 * 2
        pre = [f"[{inp}]crop={W - W % 2}:{H - H % 2}:{cx}:{cy}[{k}c]"]
        inp = f"{k}c"
        W, H = W - W % 2, H - H % 2
    else:
        pre = []
    return pre + _layout_modes(inp, out, k, lay, mode, fmt, W, H, OW, OH)


def _layout_modes(inp, out, k, lay, mode, fmt, W, H, OW, OH):
    if mode == "crop":
        return [f"[{inp}]{_rect(lay['crop'], W, H)},scale={OW}:{OH}:flags=lanczos,setsar=1[{out}]"]
    if mode == "split" and fmt == "dikey":
        top = int(OH * float(lay.get("split", 0.4)))
        top -= top % 2
        return [f"[{inp}]split[{k}a][{k}b]",
                f"[{k}a]{_rect(lay['face'], W, H)},scale={OW}:{top}:flags=lanczos,setsar=1[{k}t]",
                f"[{k}b]{_rect(lay['game'], W, H)},scale={OW}:{OH - top}:flags=lanczos,setsar=1[{k}u]",
                f"[{k}t][{k}u]vstack[{out}]"]
    if mode == "blur":
        return [f"[{inp}]split[{k}a][{k}b]",
                f"[{k}a]scale={OW}:{OH}:force_original_aspect_ratio=increase,crop={OW}:{OH},gblur=sigma=28,eq=brightness=-0.10:saturation=1.15[{k}bg]",
                f"[{k}b]scale={OW}:{OH}:force_original_aspect_ratio=decrease:flags=lanczos[{k}fg]",
                f"[{k}bg][{k}fg]overlay=(W-w)/2:(H-h)/2,setsar=1[{out}]"]
    return [f"[{inp}]scale={OW}:{OH}:force_original_aspect_ratio=decrease:flags=lanczos,"
            f"pad={OW}:{OH}:(ow-iw)/2:(oh-ih)/2:black,setsar=1[{out}]"]


def _atempo(sp):
    parts = []
    while sp > 2.0:
        parts.append("atempo=2.0")
        sp /= 2.0
    while sp < 0.5:
        parts.append("atempo=0.5")
        sp /= 0.5
    if abs(sp - 1) > 1e-3:
        parts.append(f"atempo={sp:.4f}")
    return ",".join(parts)


def zoom_expr(fx):
    zs = [(float(z["t"]), float(z["t"]) + float(z.get("d", 0.8)), float(z.get("z", 1.25)), bool(z.get("shake")))
          for z in fx.get("zooms") or []]
    if not zs:
        return None, None, None
    zt, sh = [], []
    for a, b, zz, shake in zs:
        env = f"if(between(it,{a:.3f},{b:.3f}),min(1,min((it-{a:.3f})/0.12,({b:.3f}-it)/0.2)),0)"
        zt.append(f"{max(zz - 1, 0.06 if shake else 0):.3f}*{env}")
        if shake:
            sh.append(f"if(between(it,{a:.3f},{b:.3f}),1,0)")
    shake = "+".join(sh) if sh else "0"
    return ("1+" + "+".join(zt), f"iw/2-(iw/zoom/2)+({shake})*sin(it*53)*iw*0.012",
            f"ih/2-(ih/zoom/2)+({shake})*cos(it*47)*ih*0.008")


# ------------------------------------------------------------------ komut
def unique_path(folder, name):
    folder.mkdir(parents=True, exist_ok=True)
    p = folder / f"{name}.mp4"
    i = 2
    while p.exists():
        p = folder / f"{name} ({i}).mp4"
        i += 1
    return p


def build_command(project, opts, s, out, encoder):
    project = apply_hidden(project)
    clips = [c for c in project.get("clips") or [] if model.clip_len(c) > 0.04 and Path(c["source"]).exists()]
    if not clips:
        raise RuntimeError("Projede video yok. Önce bir video ekle.")
    fmt = project.get("format") or "dikey"
    res = int(opts.get("cozunurluk") or s.get("cozunurluk") or 1080)
    OW, OH = model.out_size(fmt, res)
    fps_opt = str(opts.get("fps") or s.get("fps") or "kaynak")
    kalite = opts.get("kalite") or s.get("kalite") or "yuksek"
    ses_dengele = opts.get("ses_dengele", s.get("ses_dengele", True))
    fx = effects_of(project)
    media = project.get("media") or {}
    src_fps = max(float(c.get("fps") or 30) for c in clips)
    base_fps = round(src_fps) if abs(src_fps - round(src_fps)) < 0.05 else src_fps
    out_fps = base_fps if fps_opt == "kaynak" else int(fps_opt)
    total = sum(model.clip_len(c) for c in clips)

    inputs, fc = [], []

    def add_input(path, loop=False, ss=None, t=None):
        if loop:
            inputs.extend(["-loop", "1"])
        if ss is not None:
            inputs.extend(["-ss", f"{ss:.3f}"])
        if t is not None:
            inputs.extend(["-t", f"{t:.3f}"])
        inputs.extend(["-i", str(path)])
        return sum(1 for x in inputs if x == "-i") - 1

    # 1) klipler: her biri ayrı giriş (bellekte kare birikmez), hız, kadraj
    cat = ""
    cfps = min(out_fps, base_fps)
    for i, c in enumerate(clips):
        sp = max(0.25, float(c.get("speed") or 1))
        dur = float(c["out"]) - float(c["in"])
        idx = add_input(c["source"], ss=float(c["in"]), t=dur)
        fc.append(f"[{idx}:v]setpts=(PTS-STARTPTS)/{sp:.4f},fps={cfps:g}[r{i}]")
        fc += layout_chain(f"r{i}", f"l{i}", c, fmt, OW, OH)
        fc.append(f"[l{i}]format=yuv420p" + (",drawbox=c=black:t=fill" if c.get("hidden") else "") + f"[v{i}]")
        L = dur / sp
        if c.get("has_audio"):
            at = _atempo(sp)
            vol = float(c.get("volume", 1) if c.get("volume") is not None else 1)
            fc.append(f"[{idx}:a]asetpts=PTS-STARTPTS{(',' + at) if at else ''},volume={vol:.2f},aresample=48000,"
                      f"aformat=sample_fmts=fltp:channel_layouts=stereo,apad,atrim=0:{L:.3f}[a{i}]")
        else:
            fc.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{L:.3f},aformat=sample_fmts=fltp[a{i}]")
        cat += f"[v{i}][a{i}]"
    fc.append(f"{cat}concat=n={len(clips)}:v=1:a=1[vc][ac]")
    cur = "vc"

    def add(filt, label):
        nonlocal cur
        fc.append(f"[{cur}]{filt}[{label}]")
        cur = label

    if out_fps > base_fps + 1:
        add(f"minterpolate=fps={out_fps}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1", "vmi")
    cc = color_chain(fx)
    if cc:
        add(cc, "vcol")
    lut = fx.get("lut") or {}
    lut_rel = f"veri/projeler/{project['id']}/lut.cube"
    if lut and (ROOT / lut_rel).exists():
        mix = max(0.0, min(1.0, float(lut.get("mix", 100)) / 100))
        if mix >= 0.99:
            add(f"lut3d=file={lut_rel}", "vlut")
        else:
            fc.append(f"[{cur}]split[lu1][lu2];[lu2]lut3d=file={lut_rel}[lu3];[lu1][lu3]blend=all_mode=normal:all_opacity={mix:.2f}[vlut]")
            cur = "vlut"
    if fx.get("mirror"):
        add("hflip", "vmir")
    z, zx, zy = zoom_expr(fx)
    if z:
        add(f"zoompan=z='{z}':x='{zx}':y='{zy}':d=1:s={OW}x{OH}:fps={out_fps:g}", "vz")
    if fx.get("glow"):
        fc.append(f"[{cur}]format=gbrp,split[gl1][gl2];[gl2]gblur=sigma={OW / 60:.1f}[gl3];"
                  f"[gl1][gl3]blend=all_mode=screen:all_opacity=0.38,format=yuv420p[vg]")
        cur = "vg"
    if fx.get("rgb"):
        add(f"rgbashift=rh=-{max(2, OW // 220)}:bh={max(2, OW // 220)}", "vrgb")
    if fx.get("sharpen"):
        add("unsharp=5:5:0.7", "vsh")
    if fx.get("vignette"):
        add("vignette=PI/4.5", "vvig")
    if fx.get("grain"):
        add("noise=alls=9:allf=t", "vgr")

    # 3) video üstüne video (köşede tepki videosu, yeşil ekran)
    pip_audio = []
    for k, ov in enumerate(project.get("overlays") or []):
        if not Path(ov.get("source", "")).exists():
            continue
        a, b = max(0.0, float(ov["s"])), min(total, float(ov["e"]))
        if b - a < 0.05:
            continue
        idx = add_input(ov["source"], ss=float(ov.get("in", 0)), t=b - a)
        pre = f"[{idx}:v]setpts=PTS-STARTPTS,fps={out_fps:g}"
        if ov.get("chroma"):
            col = (ov.get("chroma_color") or "#00FF00").lstrip("#")
            pre += f",format=rgba,colorkey=0x{col}:{float(ov.get('similarity', 0.3)):.2f}:0.08"
        fc.append(pre + f"[pr{k}]")
        base_w = OW * float(ov.get("w", 0.4))
        parts, xe, ye = anim.visual_chain(f"pr{k}", f"pt{k}", ov, base_w, OW, OH, 0.0, a, OV_DEF(ov))
        fc += parts
        pad = f"tpad=start_duration={a:.3f}:color=black@0" if a > 0.001 else "null"
        fc.append(f"[pt{k}]{pad}[pv{k}]")
        fc.append(f"[{cur}][pv{k}]overlay=x='{xe}':y='{ye}':eval=frame:"
                  f"eof_action=pass:repeatlast=0:enable='between(t,{a:.3f},{b - 0.001:.3f})'[vp{k}]")
        cur = f"vp{k}"
        vol = float(ov.get("volume", 1))
        if ov.get("has_audio") and vol > 0.01:
            ms = int(a * 1000)
            fc.append(f"[{idx}:a]asetpts=PTS-STARTPTS,volume={vol:.2f},aresample=48000,"
                      f"aformat=sample_fmts=fltp:channel_layouts=stereo,adelay={ms}|{ms},apad,atrim=0:{total:.3f}[pa{k}]")
            pip_audio.append(f"[pa{k}]")

    # 4) resimler
    for k, im in enumerate([im for im in media.get("images") or [] if Path(im.get("path", "")).exists()]):
        if Path(im["path"]).suffix.lower() == ".gif":
            inputs.extend(["-ignore_loop", "0"])
            idx = add_input(im["path"])
        else:
            idx = add_input(im["path"], loop=True)
        a, b = float(im.get("s", 0)), float(im.get("e", total))
        base_w = OW * float(im.get("size", 22)) / 100
        parts, xe, ye = anim.visual_chain(f"{idx}:v", f"im{k}", im, base_w, OW, OH, a, a, IMG_DEF(im, OW, OH))
        fc += parts
        fc.append(f"[{cur}][im{k}]overlay=x='{xe}':y='{ye}':eval=frame"
                  f":enable='between(t,{a:.3f},{b:.3f})':eof_action=pass:shortest=0[vim{k}]")
        cur = f"vim{k}"

    # 4b) ayar katmanları (zamanlı efektler) + geçişler: altındaki her şeye etki eder
    fctx = fxlib.Ctx(OW, OH, out_fps, lambda p, loop: add_input(p, loop))
    jobs = []
    for L in fx.get("fxLayers") or []:
        if L.get("kind") in fxlib.EFFECTS:
            a, b = max(0.0, float(L["s"])), min(total, float(L["e"]))
            if b - a > 0.04:
                jobs.append((a, b, L["kind"], float(L.get("i", 70)) / 100, L.get("params") or {}))
    tr = fx.get("transition") or {}
    if tr.get("type") and tr["type"] != "none" and len(clips) > 1:
        d = max(0.15, min(1.5, float(tr.get("d", 0.4))))
        acc = 0.0
        for c in clips[:-1]:
            acc += model.clip_len(c)
            jobs.append((max(0.0, acc - d / 2), min(total, acc + d / 2), "tr_" + tr["type"], 1.0, {}))
    for k, (a, b, kind, inten, params) in enumerate(jobs):
        parts, cur = fxlib.timed(cur, k, a, b, kind, inten, params, fctx)
        fc.extend(parts)

    # 5) altyazı + yazılar
    if any(c.get("captions") for c in clips) or fx.get("texts") or fx.get("shapes"):
        ass_rel = f"veri/projeler/{project['id']}/altyazi.ass"
        (ROOT / ass_rel).write_text(build_ass(project), "utf-8")
        add(f"ass=filename={ass_rel}:fontsdir=app/ui/fonts", "vs")
    if fx.get("fadeIn"):
        add("fade=t=in:st=0:d=0.5", "vfi")
    if fx.get("fadeOut"):
        add(f"fade=t=out:st={max(0, total - 0.6):.3f}:d=0.6", "vfo")
    add("format=yuv420p", "vo")

    # 6) ses
    mixes = ["[ac]"] + pip_audio
    music = media.get("music") if media.get("music") and Path(media["music"].get("path", "")).exists() else None
    if music:
        inputs.extend(["-stream_loop", "-1"])
        mi = add_input(music["path"])
        ms = int(float(music.get("s", 0)) * 1000)
        fc.append(f"[{mi}:a]volume={float(music.get('vol', 0.25)):.2f},aresample=48000,"
                  f"aformat=sample_fmts=fltp:channel_layouts=stereo,atrim=0:{max(0.1, total - ms / 1000):.3f},"
                  f"adelay={ms}|{ms},apad,atrim=0:{total:.3f}[mus]")
        mixes.append("[mus]")
    a = "ac"
    if len(mixes) > 1:
        fc.append("".join(mixes) + f"amix=inputs={len(mixes)}:duration=first:dropout_transition=0:normalize=0[amx]")
        a = "amx"
    chain = ["loudnorm=I=-14:TP=-1.5:LRA=11"] if ses_dengele else []
    if fx.get("fadeIn"):
        chain.append("afade=t=in:st=0:d=0.5")
    if fx.get("fadeOut"):
        chain.append(f"afade=t=out:st={max(0, total - 0.6):.3f}:d=0.6")
    chain.append("aresample=48000")
    work = opts.get("work") or None
    if work and float(work.get("b", 0)) - float(work.get("a", 0)) > 0.1:
        wa, wb = max(0.0, float(work["a"])), min(total, float(work["b"]))
        fc.append(f"[{a}]" + ",".join(chain) + f",atrim={wa:.3f}:{wb:.3f},asetpts=PTS-STARTPTS[ao]")
        fc.append(f"[vo]trim={wa:.3f}:{wb:.3f},setpts=PTS-STARTPTS[vow]")
        vmap, total = "[vow]", wb - wa
    else:
        fc.append(f"[{a}]" + ",".join(chain) + "[ao]")
        vmap = "[vo]"

    c = [FFMPEG, "-y"] + inputs + ["-filter_complex", ";".join(fc), "-map", vmap, "-map", "[ao]",
                                   "-c:a", "aac", "-b:a", "192k"]
    if encoder == "nvenc":
        c += ["-c:v", "h264_nvenc", "-preset", "p5", "-tune", "hq", "-rc", "vbr",
              "-cq", "18" if kalite == "yuksek" else "23", "-b:v", "0", "-profile:v", "high"]
        if max(OW, OH) >= 2500:
            c += ["-maxrate", "60M", "-bufsize", "120M"]
    elif encoder == "amf":  # AMD ekran kartı
        q = "18" if kalite == "yuksek" else "23"
        c += ["-c:v", "h264_amf", "-quality", "quality", "-rc", "cqp", "-qp_i", q, "-qp_p", q, "-qp_b", q, "-profile:v", "high"]
    elif encoder == "qsv":  # Intel ekran kartı
        c += ["-c:v", "h264_qsv", "-preset", "slower", "-global_quality", "20" if kalite == "yuksek" else "25", "-profile:v", "high"]
    else:
        c += ["-c:v", "libx264", "-preset", "medium", "-crf", "18" if kalite == "yuksek" else "22", "-profile:v", "high"]
    c += ["-r", f"{out_fps:g}", "-t", f"{total:.3f}", "-movflags", "+faststart", str(out)]
    label = f"{OW}x{OH}" + ("" if fps_opt == "kaynak" else f" · {fps_opt} FPS")
    return c, total, label


_ENC_OK = None  # bu bilgisayarda çalışan kodlayıcı (NVIDIA / AMD / Intel / işlemci)


def export(job, project, opts=None):
    s = load_settings()
    opts = opts or {}
    out = unique_path(Path(opts.get("klasor") or s.get("cikti_klasoru")), safe_name(project.get("title") or "kesit", 60))
    cancel = lambda: job.cancelled  # noqa

    def run_with(enc):
        cmd, total, label = build_command(project, opts, s, out, enc)
        return run_ffmpeg_progress(cmd, total, lambda f: job.set(f, f"Dışa aktarılıyor %{int(f * 100)} · {label}"),
                                   cancel, cwd=str(ROOT))

    global _ENC_OK
    names = {"nvenc": "NVIDIA", "amf": "AMD", "qsv": "Intel", "x264": "işlemci"}
    order = ([_ENC_OK] if _ENC_OK else []) + [e for e in ("nvenc", "amf", "qsv", "x264") if e != _ENC_OK]
    code, err = 1, ""
    for enc in order:
        job.set(0.01, f"Dışa aktarma başlıyor ({names[enc]})...")
        code, err = run_with(enc)
        if code == 0:
            _ENC_OK = enc
            break
        if job.cancelled:
            out.unlink(missing_ok=True)
            raise RuntimeError("İptal edildi")
        out.unlink(missing_ok=True)
        if enc == _ENC_OK:
            _ENC_OK = None
    if code != 0:
        lines = [l for l in err.strip().splitlines() if "rror" in l or "nvalid" in l] or err.strip().splitlines() or ["bilinmeyen hata"]
        raise RuntimeError("Dışa aktarma başarısız: " + lines[-1][-300:])
    job.set(1, "Hazır! " + out.name)
    return {"path": str(out), "name": out.name, "folder": str(out.parent)}
