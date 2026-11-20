"""Pilâtre de Rozier: ilk serbest balon uçuşu (21 Kasım 1783) ve ilk hava kazası (15 Haziran 1785).
Şablon: v_2026-11-20_tolstoy.py. Zamanlar seslendirmenin orijinal hızına göre; ses SP ile hızlandırılır."""
import os, sys, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from figures import put
from make import (W, H, FPS, OUT, SCREEN_PAPER, DESK, stamp_card, paste_pop, shadow, spaced_text, font, FB, FI, INK, RED,
                  CREAM, ease, ease_out, back, clamp, finish, dust)

SP = 1.05
PAPER_DARK = Image.fromarray((np.asarray(DESK, np.float32) * 0.45).astype(np.uint8))
NIGHT = Image.fromarray(np.clip(np.asarray(DESK, np.float32) * np.array([0.22, 0.25, 0.36]), 0, 255).astype(np.uint8))
SKY = Image.fromarray(np.clip(np.asarray(SCREEN_PAPER, np.float32) * np.array([0.78, 0.9, 1.05]), 0, 255).astype(np.uint8))
BG = (240, 228, 196, 240)
GOLD = (226, 170, 90)
BBLUE = (38, 70, 140)
SEA = (150, 178, 196)

def a_(t, t0, d=0.4): return int(255 * clamp((t - t0) / d))

def note(dr, text="Temsilî çizim", col=INK):
    dr.text((W - 40, H - 250), text, font=font(FI, 30), fill=col + (150,), anchor="rb")

def balloon(dr, cx, cy, s, a=255, fire=0.0, people=True, sag=0.0):
    """Montgolfier tipi balon. (cx, cy) = gövdenin merkezi, s = ölçek (1 -> ~560 px yükseklik)."""
    R = 200 * s
    top = cy - R * 1.05
    # envelope: circle + tapered neck
    sq = 1 - 0.35 * sag
    dr.ellipse([cx - R, cy - R * sq, cx + R, cy + R * sq], fill=BBLUE + (a,))
    neck = [(cx - R * 0.93, cy + R * 0.25 * sq), (cx + R * 0.93, cy + R * 0.25 * sq), (cx + R * 0.42, cy + R * 1.25), (cx - R * 0.42, cy + R * 1.25)]
    dr.polygon(neck, fill=BBLUE + (a,))
    # gold bands & ornaments
    for k in (-0.45, 0.1, 0.62):
        y = cy + R * k * sq; hw = math.sqrt(max(0, 1 - k * k)) * R * (1 if k < 0.3 else 0.85)
        dr.line([(cx - hw, y), (cx + hw, y)], fill=GOLD + (a,), width=max(2, int(10 * s)))
    for i in range(-2, 3):
        x = cx + i * R * 0.34; y = cy - R * 0.17 * sq
        dr.ellipse([x - 14 * s, y - 14 * s, x + 14 * s, y + 14 * s], fill=GOLD + (a,))
    dr.ellipse([cx - 34 * s, top + 8 * s, cx + 34 * s, top + 50 * s], fill=GOLD + (a,))
    dr.rectangle([cx - R * 0.42, cy + R * 1.18, cx + R * 0.42, cy + R * 1.28], fill=GOLD + (a,))
    # gallery (ring) under the neck
    gy = cy + R * 1.42
    for sx in (-1, 1):
        dr.line([(cx + sx * R * 0.42, cy + R * 1.28), (cx + sx * R * 0.55, gy)], fill=INK + (a,), width=max(2, int(5 * s)))
    dr.rounded_rectangle([cx - R * 0.62, gy, cx + R * 0.62, gy + R * 0.16], 6, fill=(120, 84, 50, a))
    if people:
        for sx in (-0.4, 0.4):
            px = cx + sx * R; dr.ellipse([px - 13 * s, gy - 34 * s, px + 13 * s, gy - 8 * s], fill=(60, 40, 30, a))
            dr.rectangle([px - 12 * s, gy - 12 * s, px + 12 * s, gy + 4 * s], fill=(60, 40, 30, a))
    if fire > 0:
        rng = np.random.default_rng(int(fire * 37) + 3)
        for i in range(26):
            ang = rng.uniform(-2.6, -0.5); rr = R * rng.uniform(0.3, 1.0)
            x = cx + rr * math.cos(ang); y = cy + rr * math.sin(ang) * sq
            fl = R * 0.35 * fire * rng.uniform(0.5, 1.2)
            col = (240, int(rng.uniform(110, 190)), 40, int(a * 0.85))
            dr.polygon([(x - fl * 0.35, y), (x + fl * 0.35, y), (x + rng.uniform(-0.2, 0.2) * fl, y - fl)], fill=col)

def clouds(dr, t, a=170, y0=0):
    for i in range(5):
        x = ((i * 290 + t * 30) % (W + 400)) - 200; y = y0 + 160 + (i * 173) % 700
        for j in range(3):
            dr.ellipse([x + j * 70, y - 30 - (j % 2) * 20, x + j * 70 + 150, y + 50], fill=(250, 246, 236, a))


# ---------- scenes (t = local seconds in ORIGINAL voice time) ----------
def s1(t, dur):  # hook: first flight -> condemned prisoners
    base = NIGHT.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    for i in range(40):
        x = (i * 263) % W; y = 120 + (i * 151) % 520; dr.ellipse([x, y, x + 4, y + 4], fill=(240, 230, 200, 120))
    rise = ease(t / 4.0)
    balloon(dr, W / 2, 760 - rise * 60, 1.0, people=False)
    # prison bars over the lower part
    for i in range(7):
        x = 120 + i * 140; dr.rectangle([x, 1090, x + 18, 1300], fill=(40, 36, 34, 230))
    dr.rectangle([100, 1080, 980, 1100], fill=(40, 36, 34, 230))
    p = back(t / 0.35); s = int(104 * (0.85 + 0.15 * p))
    spaced_text(dr, (W / 2, 250), "İLK UÇUŞA", font(FB, max(10, s)), CREAM + (255,), sp=6)
    spaced_text(dr, (W / 2, 370), "İDAM MAHKÛMLARI", font(FB, max(10, int(s * 0.7))), (232, 90, 70, 255), sp=2)
    if t > 2.0:
        paste_pop(base, stamp_card(["1783"], 360, 140, RED, seed=1, sizes=[84], bg=BG), W / 2, 1230, t - 2.0, rot=-4)
    note(ImageDraw.Draw(base, "RGBA"), col=CREAM)
    return base.convert("RGB")

def card_portrait():
    w, h = 620, 800
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, h], fill=(244, 232, 200, 255), outline=(120, 96, 60, 255), width=6)
    d.rectangle([90, 60, w - 90, 560], fill=(214, 196, 156, 255))
    put(im, "civilian", w / 2, 1180, 1100, shadow=False)
    d.rectangle([0, 562, w, h], fill=(244, 232, 200, 255)); d.rectangle([0, 0, w, h], outline=(120, 96, 60, 255), width=6)
    d.rectangle([90, 60, w - 90, 560], outline=INK + (255,), width=4)
    spaced_text(d, (w / 2, 630), "PİLÂTRE DE ROZIER", font(FB, 46), RED + (255,), sp=2)
    spaced_text(d, (w / 2, 710), "genç bir bilim insanı", font(FI, 38), INK + (255,))
    return im

def s2(t, dur):  # young scientist claims the honour
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    p = back(t / 0.45); s = int(110 * (0.6 + 0.4 * p))
    spaced_text(dr, (W / 2, 240), "AMA...", font(FB, max(10, s)), RED + (a_(t, 0, 0.2),), sp=10)
    if t > 0.4:
        rise = ease_out((t - 0.4) / 0.6)
        c = card_portrait().rotate(-2, expand=True, resample=Image.BICUBIC)
        cx, cy = W / 2, 760 + (1 - rise) * 120
        k = clamp((t - 0.4) / 0.3)
        c.putalpha(Image.fromarray((np.asarray(c)[..., 3] * k).astype(np.uint8)))
        base.alpha_composite(shadow(c), (int(cx - c.width / 2 - 18), int(cy - c.height / 2 - 14)))
        base.alpha_composite(c, (int(cx - c.width / 2), int(cy - c.height / 2)))
    if t > 1.9: paste_pop(base, stamp_card(["BU ŞEREF BENİM"], 700, 140, RED, seed=2, sizes=[62], bg=BG), W / 2, 1250, t - 1.9, rot=-5)
    note(ImageDraw.Draw(base, "RGBA"))
    return base.convert("RGB")

def rooftops(dr, a=255, y=1150, col=(70, 60, 56)):
    rng = np.random.default_rng(5); x = 0
    while x < W:
        w = int(rng.integers(90, 180)); h = int(rng.integers(120, 300))
        dr.rectangle([x, y - h, x + w, y + 400], fill=col + (a,))
        dr.polygon([(x - 6, y - h), (x + w + 6, y - h), (x + w / 2, y - h - 60)], fill=(50, 42, 40, a))
        for j in range(2):
            dr.rectangle([x + 20 + j * 50, y - h + 50, x + 44 + j * 50, y - h + 90], fill=(236, 210, 150, a))
        x += w + 6

def s3(t, dur):  # 21 Nov 1783, Paris
    base = SKY.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    clouds(dr, t, 150)
    rooftops(dr)
    balloon(dr, W / 2, 760, 0.9)
    p = back(t / 0.45); s = int(100 * (0.6 + 0.4 * p))
    spaced_text(dr, (W / 2, 250), "21 KASIM 1783", font(FB, max(10, s)), RED + (a_(t, 0, 0.2),), sp=6, stroke=3, sfill=(245, 235, 211))
    if t > 2.05: paste_pop(base, stamp_card(["PARİS"], 420, 150, INK, seed=3, sizes=[88], bg=BG), W / 2, 1260, t - 2.05, rot=3)
    note(ImageDraw.Draw(base, "RGBA"))
    return base.convert("RGB")

def s4(t, dur):  # the balloon rises, free, 25 minutes
    base = SKY.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    up = ease(clamp(t / 5.0))
    clouds(dr, t * 2, 170, y0=int(up * 300))
    rooftops(dr, y=int(1150 + up * 650))
    balloon(dr, W / 2 + 40 * math.sin(t * 0.8), 820 - up * 140, 0.9 - 0.2 * up)
    spaced_text(dr, (W / 2, 250), "İLK SERBEST UÇUŞ", font(FB, 70), INK + (a_(t, 0, 0.3),), sp=4, stroke=3, sfill=(245, 235, 211))
    if t > 3.6:
        mins = int(min(25, (t - 3.6) / 0.8 * 25))
        paste_pop(base, stamp_card([f"{mins} DAKİKA"], 560, 150, RED, seed=4, sizes=[80], bg=BG), W / 2, 1250, t - 3.6, rot=-3)
    note(ImageDraw.Draw(base, "RGBA"))
    return base.convert("RGB")

# Channel map: simple lon/lat box
LON0, LON1, LAT0, LAT1 = -2.2, 3.4, 49.2, 52.0
def mp(lon, lat): return (60 + (lon - LON0) / (LON1 - LON0) * 960, 520 + (LAT1 - lat) / (LAT1 - LAT0) * 820)
ENG = [(-2.2, 50.65), (-1.6, 50.72), (-1.1, 50.78), (-0.6, 50.78), (0.0, 50.78), (0.25, 50.74), (0.6, 50.86), (0.98, 50.92), (1.38, 51.15),
       (1.42, 51.36), (1.0, 51.42), (0.6, 51.48), (0.95, 51.6), (0.9, 51.8), (1.3, 51.95), (1.6, 52.0), (-2.2, 52.0)]
FRA = [(-2.2, 49.2), (-1.95, 49.72), (-1.6, 49.65), (-1.25, 49.7), (-1.1, 49.36), (-0.2, 49.3), (0.2, 49.45), (0.1, 49.7), (0.6, 49.86),
       (1.2, 49.98), (1.5, 50.2), (1.58, 50.6), (1.62, 50.85), (1.85, 50.95), (2.35, 51.05), (2.9, 51.2), (3.4, 51.37), (3.4, 49.2)]

def s5(t, dur):  # 1.5 years later: Channel crossing attempt
    base = Image.new("RGBA", (W, H), SEA + (255,))
    dr = ImageDraw.Draw(base, "RGBA")
    pap = SCREEN_PAPER.convert("RGBA")
    for poly in (ENG, FRA):
        m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).polygon([mp(*q) for q in poly], fill=255)
        base.paste(pap, (0, 0), m)
    dr = ImageDraw.Draw(base, "RGBA")
    for poly in (ENG, FRA): dr.line([mp(*q) for q in poly], fill=INK + (255,), width=4)
    dr.rectangle([0, 0, W, 470], fill=(236, 222, 186, 255)); dr.rectangle([0, 1380, W, H], fill=(236, 222, 186, 255))
    spaced_text(dr, mp(-0.7, 50.25), "MANŞ DENİZİ", font(FI, 52), (40, 70, 100, 230), sp=6)
    spaced_text(dr, mp(-1.0, 51.45), "İNGİLTERE", font(FB, 52), INK + (255,), sp=4)
    spaced_text(dr, mp(2.5, 49.75), "FRANSA", font(FB, 52), INK + (255,), sp=4)
    p = back(t / 0.45); s = int(104 * (0.6 + 0.4 * p))
    spaced_text(dr, (W / 2, 220), "1,5 YIL SONRA", font(FB, max(10, s)), RED + (a_(t, 0, 0.2),), sp=6)
    bx, by = mp(1.61, 50.73)
    dr.ellipse([bx - 14, by - 14, bx + 14, by + 14], fill=RED + (255,))
    dr.text((bx + 24, by + 10), "Boulogne", font=font(FB, 40), fill=RED + (255,), anchor="lm")
    if t > 1.8:
        k = ease(clamp((t - 1.8) / 2.0)); tx, ty = mp(0.4, 51.1)
        n = 14
        for i in range(int(n * k)):
            x0 = bx + (tx - bx) * i / n; y0 = by + (ty - by) * i / n
            x1 = bx + (tx - bx) * (i + 0.5) / n; y1 = by + (ty - by) * (i + 0.5) / n
            dr.line([(x0, y0), (x1, y1)], fill=RED + (255,), width=8)
        hx = bx + (tx - bx) * k * 0.55; hy = by + (ty - by) * k * 0.55
        balloon(dr, hx, hy - 90, 0.22)
    if t > 1.9: paste_pop(base, stamp_card(["BALONLA GEÇMEK"], 720, 130, RED, seed=5, sizes=[60], bg=BG), W / 2, 395, t - 1.9, rot=-2)
    return base.convert("RGB")

def s6(t, dur):  # balloon caught fire
    base = NIGHT.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    fire = clamp(t / 0.8)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    gd.ellipse([W / 2 - 420, 360, W / 2 + 420, 1180], fill=(255, 140, 40, int(110 * fire)))
    base.alpha_composite(glow.filter(ImageFilter.GaussianBlur(60)))
    dr = ImageDraw.Draw(base, "RGBA")
    balloon(dr, W / 2, 760 + t * 30, 0.95, fire=fire + 0.001 * t)
    p = back(t / 0.4); s = int(110 * (0.6 + 0.4 * p))
    spaced_text(dr, (W / 2, 250), "HAVADA", font(FB, max(10, s)), CREAM + (a_(t, 0, 0.2),), sp=8)
    if t > 0.9: paste_pop(base, stamp_card(["ALEV ALDI"], 560, 160, RED, seed=6, sizes=[86], bg=BG), W / 2, 1250, t - 0.9, rot=-4)
    note(ImageDraw.Draw(base, "RGBA"), col=CREAM)
    return base.convert("RGB")

def s7(t, dur):  # first known air-crash deaths
    base = PAPER_DARK.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    fall = ease(clamp(t / 2.5))
    balloon(dr, W / 2 + 60 * fall, 560 + fall * 330, 0.75, a=int(255 * (1 - 0.5 * fall)), sag=fall, people=False)
    spaced_text(dr, (W / 2, 250), "15 HAZİRAN 1785", font(FB, 92), CREAM + (a_(t, 0, 0.25),), sp=6)
    if t > 2.9:
        paste_pop(base, stamp_card(["BİLİNEN İLK", "HAVA KAZASI"], 740, 230, RED, seed=7, sizes=[70, 70], bg=BG), W / 2, 1200, t - 2.9, rot=-3)
    note(ImageDraw.Draw(base, "RGBA"), col=CREAM)
    return base.convert("RGB")

def s8(t, dur):  # ending question
    base = Image.new("RGBA", (W, H), (13, 10, 7, 255)); dr = ImageDraw.Draw(base, "RGBA")
    balloon(dr, W / 2, 1450, 0.8, a=int(110 * clamp(t / 1.5)), people=False)
    spaced_text(dr, (W / 2, 520), "Gökyüzüne ilk çıkanlardan biri,", font(FI, 58), CREAM + (a_(t, 0.0, 0.4),))
    spaced_text(dr, (W / 2, 610), "ilk hava kazasında öldü.", font(FI, 58), CREAM + (a_(t, 0.3, 0.4),))
    if t > 0.75:
        p = back((t - 0.75) / 0.45); s = int(100 * (0.6 + 0.4 * p))
        spaced_text(dr, (W / 2, 790), "O ŞEREFE", font(FB, max(10, s)), GOLD + (a_(t, 0.75, 0.25),), sp=8)
        spaced_text(dr, (W / 2, 930), "DEĞER MİYDİ?", font(FB, max(10, s)), (230, 80, 60, a_(t, 0.75, 0.25)), sp=8)
    return base.convert("RGB")

# durations in ORIGINAL voice seconds (sentence starts from the transcript)
_B = [0.0, 4.08, 9.52, 12.56, 19.04, 23.28, 25.15, 30.0, 34.6]
_F = [s1, s2, s3, s4, s5, s6, s7, s8]
SCENES = [(f"s{i+1}", f, (_B[i + 1] - _B[i]) / SP) for i, f in enumerate(_F)]
XF = 0.3
STARTS = []; _a = 0.0
for _n, _f, _d in SCENES: STARTS.append(_a); _a += _d
TOTAL = _a
IMPACTS = {"s1": [2.0], "s2": [1.9], "s3": [2.05], "s4": [3.6], "s5": [1.9], "s6": [0.9], "s7": [2.9], "s8": [0.75]}   # local ORIGINAL seconds

def shake(img, name, t):
    amp = 0.0
    for t0 in IMPACTS.get(name, []):
        dt = t - t0 - 0.06
        if 0 <= dt < 0.45: amp += 12 * math.exp(-dt * 9)
    if amp < 0.5: return img
    dx = amp * math.sin(t * 91); dy = amp * math.cos(t * 77)
    return img.transform((W, H), Image.AFFINE, (1, 0, -dx, 0, 1, -dy), Image.BILINEAR, fillcolor=(20, 14, 9))

def scene_frame(k, T):
    name, fn, dur = SCENES[k]; t = (T - STARTS[k]) * SP   # local time in original voice seconds
    return np.asarray(shake(fn(t, dur * SP), name, t), np.float32)

def global_frame(T):
    k = max(i for i, s0 in enumerate(STARTS) if s0 <= T + 1e-9)
    a = scene_frame(k, T)
    if k > 0 and T - STARTS[k] < XF:
        b = scene_frame(k - 1, T); w = ease((T - STARTS[k]) / XF); a = a * w + b * (1 - w)
    im = dust(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)), T)
    out = finish(im, SCENES[k][0] != "s8").astype(np.float32)
    if T > TOTAL - 0.5: out *= max(0, (TOTAL - T) / 0.5)
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
        for ts in sys.argv[2:]: Image.fromarray(global_frame(float(ts))).save(os.path.join(OUT, f"sf_{ts}.png"))
    elif sys.argv[1] == "info":
        print(TOTAL, [round(s, 3) for s in STARTS])
    else:
        for k, sc in enumerate(SCENES):
            if sc[0] in sys.argv[2:]: render(k)
