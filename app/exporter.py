"""Dikey video dışa aktarma: kesme + kadraj + altyazı (ASS) + kodlama."""
from pathlib import Path

import fxlib
from core import (FFMPEG, PROJELER, ROOT, load_settings, run_ffmpeg_progress,
                  safe_name, tr_upper)

FONT_FAMILY = {
    "anton": "Anton",
    "poppins": "Poppins ExtraBold",
    "poppins-black": "Poppins Black",
    "bangers": "Bangers",
}

DEFAULT_STYLE = {
    "font": "poppins-black", "size": 88, "color": "#FFFFFF", "hl": "#FFE14D",
    "outline": "#000000", "outlineW": 9, "shadow": True, "y": 68, "upper": True,
    "karaoke": True, "anim": True, "maxWords": 3,
}

DEFAULT_LAYOUT = {
    "mode": "split", "split": 0.4,
    "face": {"x": 0.0, "y": 0.0, "w": 0.3, "h": 0.3},
    "game": {"x": 0.2, "y": 0.0, "w": 0.6, "h": 1.0},
    "crop": {"x": 0.34, "y": 0.0, "w": 0.32, "h": 1.0},
}

RES = {720: (720, 1280), 1080: (1080, 1920), 1440: (1440, 2560)}


# ------------------------------------------------------------------ zaman
def kept_segments(project):
    segs = sorted([s for s in project.get("segments") or [] if s["end"] - s["start"] > 0.05],
                  key=lambda s: s["start"])
    if not segs:
        segs = [{"start": 0.0, "end": project["duration"]}]
    return segs


def map_time(t, segs):
    off = 0.0
    for s in segs:
        if s["start"] - 1e-3 <= t <= s["end"] + 1e-3:
            return off + min(max(t, s["start"]), s["end"]) - s["start"]
        off += s["end"] - s["start"]
    return None


def map_clamp(t, segs):
    """Silinmiş bölgeye denk gelen zamanı bir sonraki parçanın başına taşır."""
    off = 0.0
    for s in segs:
        if t <= s["end"] + 1e-3:
            return off + max(0.0, min(t, s["end"]) - s["start"])
        off += s["end"] - s["start"]
    return off


def out_duration(segs):
    return sum(s["end"] - s["start"] for s in segs)


# ------------------------------------------------------------------ ASS
def _ass_color(hexc, alpha=0):
    h = (hexc or "#FFFFFF").lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = h[0:2], h[2:4], h[4:6]
    return f"&H{alpha:02X}{b}{g}{r}".upper()


def _ts(t):
    t = max(0.0, t)
    cs = int(round(t * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _esc(text):
    return text.replace("\\", "＼").replace("{", "(").replace("}", ")").replace("\n", " ")


def build_ass(project, segs, speed=1.0):
    st = dict(DEFAULT_STYLE)
    st.update(project.get("style") or {})
    fam = FONT_FAMILY.get(st["font"], "Poppins Black")
    base_c = _ass_color(st["color"])
    hl_c = _ass_color(st["hl"])
    out_c = _ass_color(st["outline"])
    shadow = 4 if st.get("shadow") else 0
    y = int(1920 * float(st["y"]) / 100)
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: K,{fam},{int(st['size'])},{base_c},{hl_c},{out_c},&H96000000,0,0,0,0,100,100,1,0,1,{float(st['outlineW']):.1f},{shadow},5,70,70,0,1
Style: T,Poppins Black,80,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,7,3,5,60,60,0,1
Style: TB,Poppins Black,80,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,3,18,0,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    # altyazı parçalarını çıktı zamanına taşı
    chunks = []
    for c in project.get("captions") or []:
        ws = []
        for w in c.get("words") or []:
            mid = (w["s"] + w["e"]) / 2
            t0 = map_time(mid, segs)
            if t0 is None:
                continue
            s = map_time(w["s"], segs)
            e = map_time(w["e"], segs)
            s = t0 - 0.05 if s is None else s
            e = t0 + 0.05 if e is None else e
            s, e = s / speed, e / speed
            txt = w["w"].strip()
            if not txt:
                continue
            ws.append({"w": tr_upper(txt) if st.get("upper") else txt, "s": s, "e": max(e, s + 0.05)})
        if ws:
            chunks.append(ws)
    chunks.sort(key=lambda ws: ws[0]["s"])
    for i, ws in enumerate(chunks):
        start = ws[0]["s"]
        end = ws[-1]["e"] + 0.35
        if i + 1 < len(chunks):
            end = min(end, chunks[i + 1][0]["s"])
            if chunks[i + 1][0]["s"] - ws[-1]["e"] < 0.35:
                end = chunks[i + 1][0]["s"]
        end = max(end, start + 0.2)
        pos = f"\\pos(540,{y})"
        pop = "\\fscx72\\fscy72\\t(0,110,\\fscx104\\fscy104)\\t(110,170,\\fscx100\\fscy100)" if st.get("anim") else ""
        if st.get("karaoke") and len(ws) > 1:
            for k, w in enumerate(ws):
                es = start if k == 0 else w["s"]
                ee = ws[k + 1]["s"] if k + 1 < len(ws) else end
                if ee - es < 0.02:
                    continue
                parts = []
                for j, x in enumerate(ws):
                    t = _esc(x["w"])
                    parts.append(f"{{\\1c{hl_c}}}{t}{{\\1c{base_c}}}" if j == k else t)
                tag = "{" + pos + (pop if k == 0 else "") + "}"
                lines.append(f"Dialogue: 0,{_ts(es)},{_ts(ee)},K,,0,0,0,,{tag}{' '.join(parts)}")
        else:
            text = " ".join(_esc(x["w"]) for x in ws)
            lines.append(f"Dialogue: 0,{_ts(start)},{_ts(end)},K,,0,0,0,,{{{pos}{pop}}}{text}")
    lines += text_events(project, segs, speed)
    return head + "\n".join(lines) + "\n"


def text_events(project, segs, speed):
    """Yazı katmanları (başlık vb.)."""
    out = []
    total = out_duration(segs) / speed
    for tx in (project.get("effects") or {}).get("texts") or []:
        raw = (tx.get("text") or "").strip()
        if not raw:
            continue
        s = map_clamp(float(tx["s"]), segs) / speed
        e = map_clamp(float(tx["e"]), segs) / speed
        e = min(e, total)
        if e - s < 0.1:
            continue
        txt = _esc(tr_upper(raw) if tx.get("upper", True) else raw)
        fam = FONT_FAMILY.get(tx.get("font") or "poppins-black", "Poppins Black")
        y = int(1920 * float(tx.get("y", 18)) / 100)
        size = int(tx.get("size", 80))
        col = _ass_color(tx.get("color") or "#FFFFFF")
        box = bool(tx.get("box", True))
        bc = _ass_color(tx.get("boxColor") or "#FF3D8B")
        style = "TB" if box else "T"
        base = f"\\fn{fam}\\fs{size}\\1c{col}" + (f"\\3c{bc}" if box else "")
        anim = tx.get("anim") or "pop"
        if anim == "type":
            n = len(txt)
            step = min(0.06, max(0.02, (e - s) * 0.4 / max(1, n)))
            for k in range(1, n + 1):
                es = s + (k - 1) * step
                ee = s + k * step if k < n else e
                if ee <= es:
                    continue
                vis = txt[:k] + "{\\alpha&HFF&}" + txt[k:]
                out.append(f"Dialogue: 1,{_ts(es)},{_ts(ee)},{style},,0,0,0,,{{\\pos(540,{y}){base}}}{vis}")
            continue
        if anim == "slide":
            mv = f"\\move(-700,{y},540,{y},0,260)\\fad(0,180)"
        elif anim == "fade":
            mv = f"\\pos(540,{y})\\fad(300,300)"
        else:
            mv = f"\\pos(540,{y})\\fscx60\\fscy60\\t(0,140,\\fscx108\\fscy108)\\t(140,220,\\fscx100\\fscy100)\\fad(0,150)"
        out.append(f"Dialogue: 1,{_ts(s)},{_ts(e)},{style},,0,0,0,,{{{mv}{base}}}{txt}")
    return out


# ------------------------------------------------------------------ kadraj
def _rect(r, W, H):
    x = max(0, min(W - 2, int(r["x"] * W)))
    y = max(0, min(H - 2, int(r["y"] * H)))
    w = max(2, min(W - x, int(r["w"] * W)))
    h = max(2, min(H - y, int(r["h"] * H)))
    w -= w % 2
    h -= h % 2
    x -= x % 2
    y -= y % 2
    return f"crop={w}:{h}:{x}:{y}"


def layout_filter(src_label, project, OW, OH):
    lay = dict(DEFAULT_LAYOUT)
    lay.update(project.get("layout") or {})
    W, H = project["width"], project["height"]
    mode = lay.get("mode", "split")
    if mode == "crop":
        return f"[{src_label}]{_rect(lay['crop'], W, H)},scale={OW}:{OH}:flags=lanczos,setsar=1[vl]"
    if mode == "blur":
        return (f"[{src_label}]split[b1][b2];"
                f"[b1]scale={OW}:{OH}:force_original_aspect_ratio=increase,crop={OW}:{OH},"
                f"gblur=sigma=28,eq=brightness=-0.10:saturation=1.15[bg];"
                f"[b2]scale={OW}:-2:flags=lanczos[fg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1[vl]")
    # yüz + oyun
    r = float(lay.get("split", 0.4))
    top = int(OH * r)
    top -= top % 2
    bot = OH - top
    return (f"[{src_label}]split[s1][s2];"
            f"[s1]{_rect(lay['face'], W, H)},scale={OW}:{top}:flags=lanczos,setsar=1[top];"
            f"[s2]{_rect(lay['game'], W, H)},scale={OW}:{bot}:flags=lanczos,setsar=1[bot];"
            f"[top][bot]vstack[vl]")




# ------------------------------------------------------------------ efektler
DEFAULT_EFFECTS = {
    "preset": "none", "bright": 0, "contrast": 0, "sat": 0, "temp": 0,
    "vignette": False, "grain": False, "glow": False, "rgb": False, "sharpen": False,
    "mirror": False, "speed": 1.0, "fadeIn": False, "fadeOut": False,
    "zooms": [], "texts": [], "fxLayers": [], "transition": {"type": "none", "d": 0.4},
    "lut": None, "hide": {},
}

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


def effects_of(project):
    fx = dict(DEFAULT_EFFECTS)
    fx.update(project.get("effects") or {})
    return fx


def color_chain(fx):
    parts = []
    if PRESETS.get(fx["preset"]):
        parts.append(PRESETS[fx["preset"]])
    b, c, s_ = float(fx["bright"]), float(fx["contrast"]), float(fx["sat"])
    if b or c or s_:
        parts.append(f"eq=brightness={b/250:.3f}:contrast={1+c/100:.3f}:saturation={max(0,1+s_/100):.3f}")
    if float(fx["temp"]):
        parts.append(f"colortemperature=temperature={int(6500 - float(fx['temp'])*30)}")
    return ",".join(parts)


def zoom_expr(fx, segs, speed):
    zs = []
    for z in fx.get("zooms") or []:
        t = map_time(float(z["t"]), segs)
        if t is None:
            continue
        a = t / speed
        d = float(z.get("d", 0.8))
        zs.append((a, a + d, float(z.get("z", 1.25)), bool(z.get("shake"))))
    if not zs:
        return None, None, None
    zterm, sh = [], []
    for a, b, zz, shake in zs:
        env = f"if(between(it,{a:.3f},{b:.3f}),min(1,min((it-{a:.3f})/0.12,({b:.3f}-it)/0.2)),0)"
        amp = max(zz - 1, 0.06 if shake else 0)
        zterm.append(f"{amp:.3f}*{env}")
        if shake:
            sh.append(f"if(between(it,{a:.3f},{b:.3f}),1,0)")
    z = "1+" + "+".join(zterm)
    shake = "+".join(sh) if sh else "0"
    x = f"iw/2-(iw/zoom/2)+({shake})*sin(it*53)*iw*0.012"
    y = f"ih/2-(ih/zoom/2)+({shake})*cos(it*47)*ih*0.008"
    return z, x, y


# ------------------------------------------------------------------ aktar
def unique_path(folder, name):
    folder.mkdir(parents=True, exist_ok=True)
    p = folder / f"{name}.mp4"
    i = 2
    while p.exists():
        p = folder / f"{name} ({i}).mp4"
        i += 1
    return p


LOGO_POS = {"tl": "40:40", "tr": "W-w-40:40", "bl": "40:H-h-40", "br": "W-w-40:H-h-40", "c": "(W-w)/2:(H-h)/2"}


def apply_hidden(project):
    """Göz ikonuyla gizlenen katmanları dışa aktarmaya katma."""
    hide = ((project.get("effects") or {}).get("hide") or {})
    if not any(hide.values()):
        return project
    p = dict(project)
    fx = dict(p.get("effects") or {})
    media = dict(p.get("media") or {})
    if hide.get("cap"):
        p["captions"] = []
    if hide.get("text"):
        fx["texts"] = []
    if hide.get("zoom"):
        fx["zooms"] = []
    if hide.get("fx"):
        fx["fxLayers"] = []
        fx["transition"] = {"type": "none"}
    if hide.get("image"):
        media["images"] = []
    if hide.get("music"):
        media["music"] = None
    p["effects"], p["media"] = fx, media
    return p


def build_command(project, opts, s, out, encoder):
    project = apply_hidden(project)
    res = int(opts.get("cozunurluk") or s.get("cozunurluk") or 1080)
    OW, OH = RES.get(res, RES[1080])
    fps_opt = str(opts.get("fps") or s.get("fps") or "kaynak")
    kalite = opts.get("kalite") or s.get("kalite") or "yuksek"
    ses_dengele = opts.get("ses_dengele", s.get("ses_dengele", True))
    fx = effects_of(project)
    speed = max(0.5, min(2.0, float(fx.get("speed") or 1)))
    segs = kept_segments(project)
    total = out_duration(segs) / speed
    media = project.get("media") or {}
    music = media.get("music") if media.get("music") and Path(media["music"].get("path", "")).exists() else None
    images = [im for im in media.get("images") or [] if Path(im.get("path", "")).exists()]

    inputs = ["-i", project["source"]]
    n_in = 1
    mi = None
    if music:
        mi = n_in
        inputs += ["-stream_loop", "-1", "-i", music["path"]]
        n_in += 1
    img_idx = []
    for im in images:
        img_idx.append(n_in)
        if Path(im["path"]).suffix.lower() == ".gif":
            inputs += ["-ignore_loop", "0", "-i", im["path"]]
        else:
            inputs += ["-loop", "1", "-i", im["path"]]
        n_in += 1

    has_a = project.get("has_audio", True)
    fc = []
    # parçaları tek akışta seç (trim+concat bellekte kare biriktirir, select biriktirmez)
    sel = "+".join(f"between(t,{sg['start']:.3f},{sg['end'] - 0.0005:.3f})" for sg in segs)
    src_fps0 = float(project.get("fps") or 30)
    fc.append(f"[0:v]select='{sel}',setpts=N/({src_fps0:g})/TB[vc]")
    if has_a:
        fc.append(f"[0:a]aselect='{sel}',asetpts=N/SR/TB[ac]")
    cur = "vc"

    def add(filt, label):
        nonlocal cur
        fc.append(f"[{cur}]{filt}[{label}]")
        cur = label

    if speed != 1.0:
        add(f"setpts=PTS/{speed:.3f}", "vsp")
    src_fps = float(project.get("fps") or 30)
    out_fps = src_fps
    if fps_opt != "kaynak":
        tf = int(fps_opt)
        out_fps = tf
        if tf > src_fps + 1:
            add(f"minterpolate=fps={tf}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1", "vf")
        else:
            add(f"fps={tf}", "vf")
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
            fc.append(f"[{cur}]split[lu1][lu2];[lu2]lut3d=file={lut_rel}[lu3];"
                      f"[lu1][lu3]blend=all_mode=normal:all_opacity={mix:.2f}[vlut]")
            cur = "vlut"
    fc.append(layout_filter(cur, project, OW, OH))
    cur = "vl"
    if fx.get("mirror"):
        add("hflip", "vmir")
    z, zx, zy = zoom_expr(fx, segs, speed)
    if z:
        add(f"zoompan=z='{z}':x='{zx}':y='{zy}':d=1:s={OW}x{OH}:fps={out_fps:g}", "vz")
    if fx.get("glow"):
        fc.append(f"[{cur}]format=gbrp,split[gl1][gl2];[gl2]gblur=sigma={OW/60:.1f}[gl3];"
                  f"[gl1][gl3]blend=all_mode=screen:all_opacity=0.38,format=yuv420p[vg]")
        cur = "vg"
    if fx.get("rgb"):
        sh = max(2, OW // 220)
        add(f"rgbashift=rh=-{sh}:bh={sh}", "vrgb")
    if fx.get("sharpen"):
        add("unsharp=5:5:0.7", "vsh")
    if fx.get("vignette"):
        add("vignette=PI/4.5", "vvig")
    if fx.get("grain"):
        add("noise=alls=9:allf=t", "vgr")
    # zamanlı efektler ve geçişler
    def add_input(path, loop):
        nonlocal n_in
        inputs.extend((["-loop", "1"] if loop else []) + ["-i", path])
        n_in += 1
        return n_in - 1
    fctx = fxlib.Ctx(OW, OH, out_fps, add_input)
    jobs = []
    for L in fx.get("fxLayers") or []:
        if L.get("kind") not in fxlib.EFFECTS:
            continue
        a = map_clamp(float(L["s"]), segs) / speed
        b = min(total, map_clamp(float(L["e"]), segs) / speed)
        if b - a > 0.04:
            jobs.append((a, b, L["kind"], float(L.get("i", 70)) / 100, L.get("params") or {}))
    tr = fx.get("transition") or {}
    if tr.get("type") and tr["type"] != "none" and len(segs) > 1:
        d = max(0.15, min(1.5, float(tr.get("d", 0.4))))
        acc = 0.0
        for sg in segs[:-1]:
            acc += sg["end"] - sg["start"]
            T = acc / speed
            jobs.append((max(0.0, T - d / 2), min(total, T + d / 2), "tr_" + tr["type"], 1.0, {}))
    for k, (a, b, kind, inten, params) in enumerate(jobs):
        parts, cur = fxlib.timed(cur, k, a, b, kind, inten, params, fctx)
        fc.extend(parts)

    for k, (im, idx) in enumerate(zip(images, img_idx)):
        size = float(im.get("size", 22)) / 100
        op = float(im.get("opacity", 1))
        a = map_clamp(float(im.get("s", 0)), segs) / speed
        b = map_clamp(float(im.get("e", project["duration"])), segs) / speed
        fc.append(f"[{idx}:v]scale={max(2, int(OW*size))}:-2,format=rgba,colorchannelmixer=aa={op:.2f}[im{k}]")
        fc.append(f"[{cur}][im{k}]overlay={LOGO_POS.get(im.get('pos','tr'), LOGO_POS['tr'])}"
                  f":enable='between(t,{a:.3f},{b:.3f})':eof_action=pass:shortest=0[vim{k}]")
        cur = f"vim{k}"
    has_subs = bool(project.get("captions")) or bool(fx.get("texts"))
    ass_rel = f"veri/projeler/{project['id']}/altyazi.ass"
    if has_subs:
        (ROOT / ass_rel).write_text(build_ass(project, segs, speed), "utf-8")
        add(f"ass=filename={ass_rel}:fontsdir=app/ui/fonts", "vs")
    if fx.get("fadeIn"):
        add("fade=t=in:st=0:d=0.5", "vfi")
    if fx.get("fadeOut"):
        add(f"fade=t=out:st={max(0, total-0.6):.3f}:d=0.6", "vfo")
    add("format=yuv420p", "vo")

    # ses
    amap = None
    if has_a:
        a = "ac"
        if speed != 1.0:
            fc.append(f"[ac]atempo={speed:.3f}[asp]")
            a = "asp"
        if music:
            vol = float(music.get("vol", 0.25))
            ms = int(map_clamp(float(music.get("s", 0)), segs) / speed * 1000)
            fc.append(f"[{mi}:a]volume={vol:.2f},atrim=0:{max(0.1, total - ms/1000):.3f},adelay={ms}|{ms},apad[mus]")
            fc.append(f"[{a}][mus]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[amx]")
            a = "amx"
        chain = []
        if ses_dengele:
            chain.append("loudnorm=I=-14:TP=-1.5:LRA=11")
        if fx.get("fadeIn"):
            chain.append("afade=t=in:st=0:d=0.5")
        if fx.get("fadeOut"):
            chain.append(f"afade=t=out:st={max(0, total-0.6):.3f}:d=0.6")
        chain.append("aresample=48000")
        fc.append(f"[{a}]" + ",".join(chain) + "[ao]")
        amap = "[ao]"
    elif music:
        vol = float(music.get("vol", 0.25))
        ms = int(map_clamp(float(music.get("s", 0)), segs) / speed * 1000)
        fc.append(f"[{mi}:a]volume={vol:.2f},atrim=0:{max(0.1, total - ms/1000):.3f},adelay={ms}|{ms},apad,aresample=48000[ao]")
        amap = "[ao]"

    c = [FFMPEG, "-y"] + inputs + ["-filter_complex", ";".join(fc), "-map", "[vo]"]
    if amap:
        c += ["-map", amap, "-c:a", "aac", "-b:a", "192k"]
    if encoder == "nvenc":
        cq = "18" if kalite == "yuksek" else "23"
        c += ["-c:v", "h264_nvenc", "-preset", "p5", "-tune", "hq", "-rc", "vbr",
              "-cq", cq, "-b:v", "0", "-profile:v", "high"]
        if res >= 1440:
            c += ["-maxrate", "60M", "-bufsize", "120M"]
    else:
        crf = "18" if kalite == "yuksek" else "22"
        c += ["-c:v", "libx264", "-preset", "medium", "-crf", crf, "-profile:v", "high"]
    c += ["-t", f"{total:.3f}", "-movflags", "+faststart", str(out)]
    label = f"{OW}x{OH}" + ("" if fps_opt == "kaynak" else f" · {fps_opt} FPS")
    return c, total, label


def export(job, project, opts=None):
    s = load_settings()
    opts = opts or {}
    out_dir = Path(opts.get("klasor") or s.get("cikti_klasoru"))
    out = unique_path(out_dir, safe_name(project.get("title") or "kesit", 60))
    cancel = lambda: job.cancelled  # noqa

    def run_with(enc):
        cmd, total, label = build_command(project, opts, s, out, enc)

        def prog(f):
            job.set(f, f"Dışa aktarılıyor %{int(f*100)} · {label}")
        return run_ffmpeg_progress(cmd, total, prog, cancel, cwd=str(ROOT))

    job.set(0.01, "Dışa aktarma başlıyor (NVIDIA)...")
    code, err = run_with("nvenc")
    if code != 0:
        if job.cancelled:
            out.unlink(missing_ok=True)
            raise RuntimeError("İptal edildi")
        job.set(0.01, "NVIDIA kodlayıcı açılmadı, işlemci ile aktarılıyor...")
        code, err = run_with("x264")
        if code != 0:
            out.unlink(missing_ok=True)
            last = err.strip().splitlines()[-1] if err.strip() else "bilinmeyen hata"
            raise RuntimeError("Dışa aktarma başarısız: " + last)
    job.set(1, "Hazır! " + out.name)
    return {"path": str(out), "name": out.name, "folder": str(out.parent)}
