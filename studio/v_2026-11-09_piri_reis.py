import os, sys, math, subprocess, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import make as M
from make import (W, H, FPS, OUT, SCREEN_PAPER, DESK, stamp_card, paste_pop, shadow, spaced_text, font, FB, FI, INK, RED,
                  CREAM, ease, ease_out, back, clamp, finish, dust, title_band, parchment, grunge, noise_img)

# ---------- Atlantic map (real coastlines from geo/land.geojson, drawn in a portolan style) ----------
LONA, LONB, LATA, LATB = -105.0, 45.0, -60.0, 64.0
S = 16
AW, AH = int((LONB - LONA) * S), int((LATB - LATA) * S)
def AP(lon, lat): return ((lon - LONA) * S, (LATB - lat) * S)
SEA = (226, 208, 166)
LAND_C = (204, 170, 118)

def _rings():
    d = json.load(open(os.path.join(OUT, "geo", "land.geojson")))
    out = []
    for f in d["features"]:
        g = f["geometry"]; polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for p in polys:
            r = p[0]
            xs = [c[0] for c in r]; ys = [c[1] for c in r]
            if max(xs) < LONA or min(xs) > LONB or max(ys) < LATA or min(ys) > LATB: continue
            if len(r) < 8: continue
            out.append(r)
    return out

def _layer(rings, fill):
    im = Image.new("RGBA", (AW, AH), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    for r in rings:
        pts = [AP(x, y) for x, y in r]
        dr.polygon(pts, fill=fill + (255,))
    for r in rings:
        pts = [AP(x, y) for x, y in r]
        dr.line(pts + [pts[0]], fill=INK + (255,), width=3)
    return im

AMAP = os.path.join(OUT, "atlas_piri.npz")
def build():
    rings = _rings()
    amer = [r for r in rings if np.mean([c[0] for c in r]) < -28]
    old = [r for r in rings if np.mean([c[0] for c in r]) >= -28]
    base = Image.fromarray(parchment(AW, AH, SEA, 21).astype(np.uint8)).convert("RGBA")
    dr = ImageDraw.Draw(base, "RGBA")
    # portolan rhumb lines from two wind roses
    for (lo, la, col) in [(-38, 18, (158, 30, 28)), (-20, -22, (40, 90, 60)), (-62, 38, (52, 36, 22))]:
        cx, cy = AP(lo, la)
        for i in range(32):
            a = i * math.pi / 16
            c = col if i % 4 == 0 else INK
            dr.line([(cx, cy), (cx + math.cos(a) * 3000, cy + math.sin(a) * 3000)], fill=c + (70 if i % 4 == 0 else 38,), width=2)
        for i in range(8):
            a = i * math.pi / 4; r1 = 70 if i % 2 == 0 else 40
            p1 = (cx + math.cos(a) * r1, cy + math.sin(a) * r1)
            pl = (cx + math.cos(a + 0.35) * 14, cy + math.sin(a + 0.35) * 14)
            pr = (cx + math.cos(a - 0.35) * 14, cy + math.sin(a - 0.35) * 14)
            dr.polygon([pl, p1, pr, (cx, cy)], fill=(col if i % 2 == 0 else INK) + (220,))
        dr.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], fill=(240, 228, 196, 255), outline=INK + (255,), width=2)
    old_l = _layer(old, LAND_C); am_l = _layer(amer, LAND_C)
    np.savez_compressed(AMAP, base=np.asarray(base), old=np.asarray(old_l), am=np.asarray(am_l))

if not os.path.exists(AMAP): build()
_z = np.load(AMAP)
A_BASE = Image.fromarray(_z["base"]); A_OLD = Image.fromarray(_z["old"]); A_AM = Image.fromarray(_z["am"])

def with_alpha(im, k):
    if k >= 1: return im
    a = np.asarray(im).copy(); a[..., 3] = (a[..., 3] * k).astype(np.uint8); return Image.fromarray(a)

def atlas(ko=1.0, ka=1.0):
    im = A_BASE.copy()
    if ko > 0: im.alpha_composite(with_alpha(A_OLD, ko))
    if ka > 0: im.alpha_composite(with_alpha(A_AM, ka))
    return im

FULL = atlas()

def cam_at(lon, lat, vh_deg):
    cx, cy = AP(lon, lat); vh = vh_deg * S; vw = vh * W / H
    return (cx - vw / 2, cy - vh / 2, vw, vh)

def view(src, cam):
    x0, y0, vw, vh = cam
    return src.transform((W, H), Image.EXTENT, (x0, y0, x0 + vw, y0 + vh), Image.BILINEAR, fillcolor=SEA + (255,))

def scr(cam, lon, lat):
    x0, y0, vw, vh = cam; mx, my = AP(lon, lat)
    return ((mx - x0) * W / vw, (my - y0) * H / vh)

def label(dr, xy, text, k, size=54, col=INK):
    if k <= 0: return
    a = int(255 * clamp(k))
    spaced_text(dr, xy, text, font(FB, size), col + (a,), sp=5, stroke=6, sfill=(245, 235, 211, a))

def note(dr, text="Temsilî çizim"):
    dr.text((W - 40, H - 250), text, font=font(FI, 30), fill=INK + (150,), anchor="rb")

# torn fragment of the map (for 1517 / 1929 scenes)
def make_fragment(w=560, h=700):
    cam = cam_at(-35, 8, 92)
    x0, y0, vw, vh = cam
    vw2 = vh * w / h
    im = FULL.transform((w, h), Image.EXTENT, (x0 + (vw - vw2) / 2, y0, x0 + (vw + vw2) / 2, y0 + vh), Image.BILINEAR)
    m = Image.new("L", (w, h), 0); d = ImageDraw.Draw(m)
    rng = np.random.default_rng(5)
    right = [(w - 30 - rng.uniform(0, 70) - 60 * math.sin(i / 3), i * h / 24) for i in range(25)]
    pts = [(14, 10), (w * 0.6, 4)] + right + [(w * 0.5, h - 8), (10, h - 14)]
    d.polygon(pts, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(1.2))
    im.putalpha(m)
    # darken the edges like old skin
    a = np.asarray(im).astype(np.float32)
    e = np.asarray(m.filter(ImageFilter.GaussianBlur(18)), np.float32) / 255
    a[..., :3] *= (0.72 + 0.28 * e[..., None])
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

FRAG = make_fragment()
PAPER_DARK = Image.fromarray((np.asarray(DESK, np.float32) * 0.45).astype(np.uint8))

def put(base, img, cx, cy, op=1.0, rot=0.0, sc=1.0):
    im = img
    if sc != 1.0: im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BILINEAR)
    if rot: im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    im = with_alpha(im, op)
    sh = shadow(im, op=int(120 * op))
    base.alpha_composite(sh, (int(cx - im.width / 2 - 30 + 12), int(cy - im.height / 2 - 30 + 16)))
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

def quill_line(dr, t, t0, d, pts, col=INK, width=6):
    p = clamp((t - t0) / d)
    if p <= 0: return
    n = max(2, int(len(pts) * p))
    dr.line(pts[:n], fill=col + (255,), width=width)

# ---------- scenes ----------
def p1(t, dur):  # hook: 1513
    cam = cam_at(-30, 2 + 2 * t / dur, 118 - 14 * t / dur)
    base = view(FULL, cam)
    veil = Image.new("RGBA", (W, H), (236, 222, 186, int(150 + 40 * (1 - clamp((t - 5.5) / 1.5))))); base.alpha_composite(veil)
    dr = ImageDraw.Draw(base, "RGBA")
    paste_pop(base, stamp_card(["1513"], 620, 250, RED, seed=1, sizes=[170], bg=(240, 228, 196, 240)), W / 2, 520, t - 0.15, rot=-4)
    if t > 2.3:
        k = int(255 * clamp((t - 2.3) / 0.4))
        spaced_text(dr, (W / 2, 790), "Kolomb Amerika'ya: 1492", font(FI, 50), INK + (k,))
    if t > 4.3:
        paste_pop(base, stamp_card(["SADECE 21 YIL SONRA"], 860, 150, INK, seed=2, sizes=[66], bg=(240, 228, 196, 240)),
                  W / 2, 950, t - 4.3, rot=2)
    if t > 5.6:
        k = int(255 * clamp((t - 5.6) / 0.4))
        spaced_text(dr, (W / 2, 1150), "BİR OSMANLI DENİZCİSİ", font(FB, 60), INK + (k,), sp=5, stroke=6, sfill=(245, 235, 211, k))
    if t > 6.9:
        paste_pop(base, stamp_card(["DÜNYAYI ÇİZDİ"], 760, 170, RED, seed=3, sizes=[84], bg=(240, 228, 196, 240)),
                  W / 2, 1320, t - 6.9, rot=-3)
    return base.convert("RGB")

def p2(t, dur):  # name card
    cam = cam_at(-38, 18, 34 - 3 * t / dur)
    base = view(FULL, cam)
    veil = Image.new("RGBA", (W, H), (236, 222, 186, 120)); base.alpha_composite(veil)
    dr = ImageDraw.Draw(base, "RGBA")
    a = int(255 * clamp((t - 0.05) / 0.3))
    spaced_text(dr, (W / 2, 640), "ADI", font(FB, 64), INK + (a,), sp=12, stroke=6, sfill=(245, 235, 211, a))
    paste_pop(base, stamp_card(["PÎRÎ REİS"], 820, 220, RED, seed=4, sizes=[120], bg=(240, 228, 196, 245)), W / 2, 860, t - 1.0, rot=-3)
    if t > 1.3:
        k = int(255 * clamp((t - 1.3) / 0.4))
        spaced_text(dr, (W / 2, 1060), "Osmanlı denizcisi ve haritacı", font(FI, 50), INK + (k,), stroke=5, sfill=(245, 235, 211, k))
    return base.convert("RGB")

def p3(t, dur):  # the map appears
    ko = ease((t - 2.5) / 0.9); ka = ease((t - 4.1) / 0.9)
    cam = cam_at(-24, 2, 122 - 4 * ease(t / dur))
    base = view(atlas(ko, ka), cam)
    dr = ImageDraw.Draw(base, "RGBA")
    label(dr, scr(cam, -4, 40.5), "AVRUPA", (t - 2.9) / 0.35, 52)
    label(dr, scr(cam, 0, 12), "AFRİKA", (t - 3.6) / 0.35, 58)
    label(dr, scr(cam, -45, -8), "GÜNEY", (t - 4.4) / 0.35, 54)
    label(dr, scr(cam, -45, -8 - 6.5), "AMERİKA", (t - 4.4) / 0.35, 54)
    paste_pop(base, stamp_card(["CEYLAN DERİSİ", "ÜZERİNE"], 620, 190, RED, seed=5, sizes=[62, 38], bg=(240, 228, 196, 240)),
              370, 250, t - 0.3, rot=-2)
    note(dr)
    return base.convert("RGB")

def p4(t, dur):  # lost Columbus map
    z = ease(t / 1.6)
    lon = -30 + (-72 + 30) * z; lat = 4 + (19 - 4) * z; vh = 106 + (46 - 106) * z
    cam = cam_at(lon, lat, vh)
    base = view(FULL, cam)
    dr = ImageDraw.Draw(base, "RGBA")
    if t > 1.0:
        k = clamp((t - 1.0) / 0.5)
        x0, y0 = scr(cam, -88, 26); x1, y1 = scr(cam, -60, 10)
        for i in range(0, 200):
            # dashed rectangle
            pass
        segs = [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]
        for (a, b) in segs:
            L = math.hypot(b[0] - a[0], b[1] - a[1]); n = int(L / 28)
            for j in range(0, n, 2):
                u0, u1 = j / n, min(1, (j + 1) / n)
                dr.line([(a[0] + (b[0] - a[0]) * u0, a[1] + (b[1] - a[1]) * u0), (a[0] + (b[0] - a[0]) * u1, a[1] + (b[1] - a[1]) * u1)],
                        fill=RED + (int(255 * k),), width=7)
        label(dr, ((x0 + x1) / 2, y1 + 60), "KARAYİPLER", k, 46, RED)
    paste_pop(base, stamp_card(["KAYIP", "KOLOMB HARİTASI"], 820, 230, INK, seed=6, sizes=[60, 64], bg=(240, 228, 196, 245)),
              W / 2, 470, t - 2.2, rot=-3)
    a = int(255 * clamp((t - 0.1) / 0.4))
    spaced_text(dr, (W / 2, 250), "KAYNAKLARI ARASINDA", font(FB, 58), INK + (a,), sp=5, stroke=6, sfill=(245, 235, 211, a))
    note(dr)
    return base.convert("RGB")

def p5(t, dur):  # 1517 Cairo, then forgotten
    base = SCREEN_PAPER.copy().convert("RGBA")
    fade = ease((t - 3.9) / 1.4)
    fr = FRAG
    if fade > 0:
        g = fr.convert("LA").convert("RGBA"); g.putalpha(fr.getchannel("A")); fr = Image.blend(fr, g, 0.8 * fade)
        a = np.asarray(fr).astype(np.float32); a[..., :3] *= (1 - 0.35 * fade); fr = Image.fromarray(a.astype(np.uint8))
    rise = ease_out((t - 0.2) / 0.9)
    put(base, fr, W / 2, 800 + (1 - rise) * 260 + 60 * fade, op=clamp(rise * 1.2), rot=-3 + 5 * fade, sc=0.95 - 0.12 * fade)
    if fade > 0:
        dk = Image.new("RGBA", (W, H), (20, 14, 9, int(130 * fade))); base.alpha_composite(dk)
    title_band(base, "1517 · KAHİRE", t - 0.3, y=290, size=80, col=RED)
    paste_pop(base, stamp_card(["YAVUZ SULTAN SELİM'E", "SUNULDU"], 860, 220, INK, seed=7, sizes=[56, 50], bg=(240, 228, 196, 245)),
              W / 2, 1290, t - 1.6, rot=2)
    paste_pop(base, stamp_card(["YÜZYILLARCA", "UNUTULDU"], 760, 240, (110, 90, 70), seed=8, sizes=[64, 76], bg=(225, 212, 180, 245)),
              W / 2, 800, t - 4.0, rot=-6)
    return base.convert("RGB")

def pile(base, t, top=1120):
    rng = np.random.default_rng(9)
    dr = ImageDraw.Draw(base, "RGBA")
    for i in range(14):
        w = rng.uniform(380, 620); h = rng.uniform(60, 110)
        cx = W / 2 + rng.uniform(-260, 260); cy = top + 360 - i * 26 + rng.uniform(-10, 10)
        ang = rng.uniform(-0.12, 0.12)
        c, s = math.cos(ang), math.sin(ang)
        pts = [(cx + dx * c - dy * s, cy + dx * s + dy * c) for dx, dy in [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]]
        col = tuple(int(v) for v in rng.uniform([170, 145, 100], [215, 190, 145]))
        dr.polygon(pts, fill=col + (255,), outline=(70, 50, 30, 255))

def p6(t, dur):  # 1929 Topkapı
    base = PAPER_DARK.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    paste_pop(base, stamp_card(["1929"], 560, 230, (200, 60, 40), seed=10, sizes=[160], bg=(240, 228, 196, 240)),
              W / 2, 420 if t < 2.6 else 420 - 140 * ease((t - 2.6) / 0.5), t - 0.3, rot=-4)
    if t > 1.0:
        k = int(255 * clamp((t - 1.0) / 0.4) * (1 - clamp((t - 2.6) / 0.3)))
        spaced_text(dr, (W / 2, 640), "Ta ki...", font(FI, 64), CREAM + (k,))
    if t > 2.9:
        k = int(255 * clamp((t - 2.9) / 0.4))
        spaced_text(dr, (W / 2, 520), "TOPKAPI SARAYI", font(FB, 74), CREAM + (k,), sp=6)
        spaced_text(dr, (W / 2, 610), "müzeye dönüştürülürken", font(FI, 50), CREAM + (k,))
    # the pile and the fragment rising out of it
    if t > 3.3:
        k = clamp((t - 3.3) / 0.5)
        up = ease_out((t - 4.6) / 1.2)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); pile(lay, t); lay = with_alpha(lay, k)
        def fr(): put(base, FRAG, W / 2, 1400 - 420 * up, op=clamp(k * 1.5), rot=4 - 6 * up, sc=0.7 + 0.12 * up)
        if up < 0.5: fr(); base.alpha_composite(lay)
        else: base.alpha_composite(lay); fr()
    if t > 6.0:
        paste_pop(base, stamp_card(["BİR PARÇASI", "BULUNDU"], 680, 220, RED, seed=11, sizes=[66, 66], bg=(240, 228, 196, 245)),
                  W / 2, 1320, t - 6.0, rot=-3)
    return base.convert("RGB")

def p7(t, dur):  # ending
    base = Image.new("RGBA", (W, H), (13, 10, 7, 255))
    put(base, FRAG, W / 2, 1000, op=0.22 + 0.12 * clamp((t - 2.1) / 1.5), rot=-2, sc=1.25)
    dr = ImageDraw.Draw(base, "RGBA")
    def a(t0, d=0.5): return int(255 * clamp((t - t0) / d))
    spaced_text(dr, (W / 2, 720), "Bugün hâlâ orada:", font(FI, 62), CREAM + (a(0.3),))
    if t > 2.1:
        p = back((t - 2.1) / 0.45); s = int(96 * (0.6 + 0.4 * p))
        spaced_text(dr, (W / 2, 900), "TOPKAPI", font(FB, max(10, s)), (226, 170, 90, a(2.1, 0.25)), sp=10)
        spaced_text(dr, (W / 2, 1020), "SARAYI", font(FB, max(10, s)), (226, 170, 90, a(2.1, 0.25)), sp=10)
    if t > 3.0:
        spaced_text(dr, (W / 2, 1160), "İstanbul", font(FI, 48), CREAM + (a(3.0),))
    return base.convert("RGB")

SCENES = [("p1", p1, 8.6), ("p2", p2, 2.0), ("p3", p3, 6.1), ("p4", p4, 4.2), ("p5", p5, 6.5), ("p6", p6, 8.0), ("p7", p7, 5.0)]
XF = 0.4
STARTS = []; _a = 0.0
for _n, _f, _d in SCENES: STARTS.append(_a); _a += _d
TOTAL = _a
IMPACTS = {"p1": [0.15, 4.3, 6.9], "p2": [1.0], "p4": [2.2], "p5": [0.3, 4.0], "p6": [0.3, 6.0], "p7": [2.1]}

def shake(img, name, t):
    amp = 0.0
    for t0 in IMPACTS.get(name, []):
        dt = t - t0 - 0.06
        if 0 <= dt < 0.45: amp += 12 * math.exp(-dt * 9)
    if amp < 0.5: return img
    dx = amp * math.sin(t * 91); dy = amp * math.cos(t * 77)
    return img.transform((W, H), Image.AFFINE, (1, 0, -dx, 0, 1, -dy), Image.BILINEAR, fillcolor=(20, 14, 9))

def scene_frame(k, T):
    name, fn, dur = SCENES[k]; t = T - STARTS[k]
    return np.asarray(shake(fn(t, dur + XF), name, t), np.float32)

def global_frame(T):
    k = max(i for i, s0 in enumerate(STARTS) if s0 <= T + 1e-9)
    a = scene_frame(k, T)
    if k > 0 and T - STARTS[k] < XF:
        b = scene_frame(k - 1, T); w = ease((T - STARTS[k]) / XF); a = a * w + b * (1 - w)
    im = dust(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)), T)
    out = finish(im, SCENES[k][0] != "p7").astype(np.float32)
    if T < 0.15: out *= T / 0.15
    if T > TOTAL - 0.6: out *= max(0, (TOTAL - T) / 0.6)
    return np.clip(out, 0, 255).astype(np.uint8)

def render(k):
    name = SCENES[k][0]
    t0 = STARTS[k]; t1 = STARTS[k + 1] if k + 1 < len(SCENES) else TOTAL
    n0, n1 = int(round(t0 * FPS)), int(round(t1 * FPS))
    tmp = os.path.join(OUT, f"{name}.tmp.mp4"); fin = os.path.join(OUT, f"{name}.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), tmp],
                         stdin=subprocess.PIPE)
    for i in range(n0, n1): p.stdin.write(global_frame(i / FPS).tobytes())
    p.stdin.close(); rc = p.wait()
    if rc == 0: os.replace(tmp, fin)
    print(name, "done", rc, flush=True)

if __name__ == "__main__":
    if sys.argv[1] == "frames":
        for ts in sys.argv[2:]: Image.fromarray(global_frame(float(ts))).save(os.path.join(OUT, f"pf_{ts}.png"))
    else:
        for k, sc in enumerate(SCENES):
            if sc[0] in sys.argv[2:]: render(k)
