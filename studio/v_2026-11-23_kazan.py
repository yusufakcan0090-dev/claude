"""Tataristan (halklar sırası #1): Aziz Vasil Katedrali Kazan'ın düşüşü (1552) için yapıldı; Kul Şerif; Tatarlar bugün
Rusya'nın 2. büyük halkı; Kul Şerif Camii 2005'te Kazan Kremlini'nde, Müjde Katedrali ile aynı surların içinde yeniden açıldı.
Kaynaklar: Encyclopedia of Russian History (encyclopedia.com) 'Cathedral of St. Basil'; Macalester College 'St. Basil's';
Wikipedia 'Kul Sharif', 'Kul Sharif Mosque', 'Kazan Kremlin'; kazan-kremlin.ru; Wikipedia 'Ethnic groups in Russia' (2021);
Wikipedia 'Flag of Tatarstan' + kitaphane.tatarstan.ru (29 Kasım 1991).
Şablon: v_2026-11-21_balon.py."""
import os, sys, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from make import (W, H, FPS, OUT, SCREEN_PAPER, DESK, stamp_card, paste_pop, shadow, spaced_text, font, FB, FI, INK, RED,
                  CREAM, ease, ease_out, back, clamp, finish, dust)
import bayrak as B

SP = 1.0
PAPER_DARK = Image.fromarray((np.asarray(DESK, np.float32) * 0.45).astype(np.uint8))
NIGHT = Image.fromarray(np.clip(np.asarray(DESK, np.float32) * np.array([0.22, 0.25, 0.36]), 0, 255).astype(np.uint8))
SKY = Image.fromarray(np.clip(np.asarray(SCREEN_PAPER, np.float32) * np.array([0.8, 0.9, 1.04]), 0, 255).astype(np.uint8))
BG = (240, 228, 196, 240)
GOLD = (226, 170, 90)
MBLUE = (40, 110, 175)
WALL = (236, 230, 214)
FLAG = Image.open(os.path.join(OUT, "flags_ru_png", "ta.png")).convert("RGBA")
_fc = {}
def flag(w):
    if w not in _fc:
        h = int(FLAG.height * w / FLAG.width); im = FLAG.resize((w, h), Image.LANCZOS)
        bd = Image.new("RGBA", (w + 4, h + 4), (40, 30, 20, 255)); bd.alpha_composite(im, (2, 2)); _fc[w] = bd
    return _fc[w]

def a_(t, t0, d=0.4): return int(255 * clamp((t - t0) / d))

def note(dr, text="Temsilî çizim", col=INK):
    dr.text((W - 40, H - 250), text, font=font(FI, 30), fill=col + (150,), anchor="rb")

def onion(dr, cx, by, w, h, col, a=255, stripes=None):
    """Soğan kubbe: tabanı (cx, by), genişlik w, yükseklik h."""
    pts = []
    for s in np.linspace(0, 1, 30):
        y = by - s * h
        r = w / 2 * (math.sin(math.pi * min(1, s * 1.35)) ** 0.8) * (1 - s) ** 0.35 if s < 0.999 else 0
        if s < 0.12: r = max(r, w * 0.32)
        pts.append((cx + r, y))
    pts = pts + [(2 * cx - x, y) for x, y in reversed(pts)]
    dr.polygon(pts, fill=col + (a,))
    if stripes:
        for i in range(-2, 3):
            dr.line([(cx + i * w * 0.14, by), (cx + i * w * 0.05, by - h * 0.9)], fill=stripes + (a,), width=max(2, int(w * 0.05)))
    dr.line([(cx, by - h), (cx, by - h - h * 0.25)], fill=GOLD + (a,), width=max(2, int(w * 0.05)))

def cathedral(dr, cx, by, s, a=255):
    """Stilize Aziz Vasil Katedrali silueti (renkli soğan kubbeler, ortada sivri kule)."""
    body = (176, 62, 48)
    dr.rectangle([cx - 380 * s, by - 260 * s, cx + 380 * s, by], fill=body + (a,))
    for i in range(-3, 4):  # arches
        x = cx + i * 105 * s
        dr.rounded_rectangle([x - 30 * s, by - 150 * s, x + 30 * s, by], int(28 * s), fill=(110, 36, 28, a))
    # central tent tower
    dr.rectangle([cx - 70 * s, by - 560 * s, cx + 70 * s, by - 260 * s], fill=(196, 84, 60, a))
    dr.polygon([(cx - 80 * s, by - 560 * s), (cx + 80 * s, by - 560 * s), (cx, by - 900 * s)], fill=(214, 170, 90, a))
    for k in range(5):
        y = by - (600 + k * 55) * s; hw = 80 * s * (1 - (k * 55 + 40) / 340)
        dr.line([(cx - hw, y), (cx + hw, y)], fill=(150, 110, 50, a), width=max(2, int(6 * s)))
    onion(dr, cx, by - 900 * s, 50 * s, 70 * s, GOLD, a)
    # side towers with onion domes
    spec = [(-290, 360, (40, 130, 90), (230, 220, 190)), (-160, 470, (220, 160, 40), (176, 62, 48)), (160, 470, (40, 100, 170), (235, 225, 200)),
            (290, 360, (200, 60, 50), (240, 200, 90))]
    for dx, hh, col, st in spec:
        x = cx + dx * s
        dr.rectangle([x - 48 * s, by - hh * s, x + 48 * s, by - 200 * s], fill=(200, 92, 66, a))
        dr.rectangle([x - 52 * s, by - hh * s - 10 * s, x + 52 * s, by - hh * s + 6 * s], fill=(240, 226, 196, a))
        onion(dr, x, by - hh * s - 8 * s, 150 * s, 170 * s, col, a, stripes=st)

def walls(dr, y, a=255, col=WALL, towers=True):
    dr.rectangle([0, y, W, y + 520], fill=col + (a,))
    for x in range(0, W, 60): dr.rectangle([x, y - 34, x + 34, y], fill=col + (a,))
    if towers:
        for x in (90, W - 150):
            dr.rectangle([x, y - 170, x + 120, y + 520], fill=(222, 214, 196, a))
            dr.polygon([(x - 10, y - 170), (x + 130, y - 170), (x + 60, y - 300)], fill=(70, 110, 80, a))
    dr.line([(0, y + 4), (W, y + 4)], fill=(160, 150, 130, a), width=3)

def old_mosque(dr, cx, by, s, a=255, col=(120, 100, 80), crumble=0.0):
    rng = np.random.default_rng(7)
    dr.rectangle([cx - 260 * s, by - 220 * s, cx + 260 * s, by], fill=col + (a,))
    dr.pieslice([cx - 170 * s, by - 390 * s, cx + 170 * s, by - 50 * s], 180, 360, fill=col + (a,))
    for dx in (-330, -200, 200, 330):
        h = 620 * s * (1 - crumble * rng.uniform(0.3, 0.8))
        x = cx + dx * s
        dr.rectangle([x - 22 * s, by - h, x + 22 * s, by], fill=col + (a,))
        if crumble < 0.3: dr.polygon([(x - 30 * s, by - h), (x + 30 * s, by - h), (x, by - h - 90 * s)], fill=col + (a,))

def kul_sharif_mosque(dr, cx, by, s, a=255):
    white = (244, 242, 236)
    dr.rectangle([cx - 230 * s, by - 260 * s, cx + 230 * s, by], fill=white + (a,))
    for i in range(-2, 3):
        x = cx + i * 85 * s
        dr.rounded_rectangle([x - 22 * s, by - 210 * s, x + 22 * s, by - 40 * s], int(20 * s), fill=(90, 150, 200, a))
    dr.pieslice([cx - 150 * s, by - 520 * s, cx + 150 * s, by - 220 * s], 180, 360, fill=MBLUE + (a,))
    dr.rectangle([cx - 150 * s, by - 372 * s, cx + 150 * s, by - 260 * s], fill=white + (a,))
    dr.pieslice([cx - 150 * s, by - 520 * s, cx + 150 * s, by - 260 * s], 180, 360, fill=MBLUE + (a,))
    dr.line([(cx, by - 520 * s), (cx, by - 580 * s)], fill=GOLD + (a,), width=max(2, int(8 * s)))
    for dx in (-300, 300, -200, 200):
        x = cx + dx * s; h = (760 if abs(dx) == 300 else 600) * s
        dr.rectangle([x - 20 * s, by - h, x + 20 * s, by], fill=white + (a,))
        for k in (0.45, 0.75): dr.rectangle([x - 28 * s, by - h * k - 8 * s, x + 28 * s, by - h * k + 8 * s], fill=white + (a,))
        dr.polygon([(x - 24 * s, by - h), (x + 24 * s, by - h), (x, by - h - 120 * s)], fill=MBLUE + (a,))

def annunciation(dr, cx, by, s, a=255):
    white = (246, 244, 238)
    dr.rectangle([cx - 170 * s, by - 300 * s, cx + 170 * s, by], fill=white + (a,))
    for dx, w, hh in ((0, 120, 300), (-110, 70, 300), (110, 70, 300)):
        x = cx + dx * s
        dr.rectangle([x - w * 0.4 * s, by - (hh + 90) * s, x + w * 0.4 * s, by - hh * s], fill=white + (a,))
        onion(dr, x, by - (hh + 88) * s, w * s, w * 1.2 * s, (50, 80, 150), a)

def s1(t, dur):  # hook: this cathedral -> fall of a Turkic city
    base = SKY.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    z = 1.0 + 0.04 * ease(t / 5.6)
    cathedral(dr, W / 2, 1320, 0.8 * z)
    dr.rectangle([0, 1320, W, H], fill=(150, 140, 128, 255))
    p = back(t / 0.3); s = int(96 * (0.85 + 0.15 * p))
    spaced_text(dr, (W / 2, 210), "BU KATEDRAL", font(FB, max(10, s)), INK + (255,), sp=6, stroke=3, sfill=(245, 235, 211))
    spaced_text(dr, (W / 2, 320), "BİR TÜRK ŞEHRİNİN", font(FB, max(10, int(s * 0.62))), RED + (255,), sp=2, stroke=3, sfill=(245, 235, 211))
    spaced_text(dr, (W / 2, 395), "DÜŞÜŞÜ İÇİN", font(FB, max(10, int(s * 0.62))), RED + (255,), sp=2, stroke=3, sfill=(245, 235, 211))
    if t > 2.6:
        paste_pop(base, stamp_card(["MOSKOVA", "1555–1561"], 520, 200, RED, seed=1, sizes=[70, 52], bg=BG), W / 2, 1180, t - 2.6, rot=-4)
    note(ImageDraw.Draw(base, "RGBA"))
    return base.convert("RGB")

def s2(t, dur):  # 1552 siege of Kazan
    base = PAPER_DARK.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    old_mosque(dr, W / 2, 1010, 0.8, col=(170, 150, 120))
    walls(dr, 1010, col=(214, 206, 186))
    # encircling red arrows
    k = ease(clamp((t - 1.6) / 2.5))
    for i in range(10):
        ang = math.pi * (1.05 + i * 0.09)
        if i / 10 > k: break
        r = 470; x = W / 2 + r * math.cos(ang) * 1.05; y = 980 + r * math.sin(ang) * 0.55 + 200
        dr.ellipse([x - 16, y - 16, x + 16, y + 16], fill=RED + (230,))
    for i in range(10):
        if i / 10 > k: break
        x = 60 + i * 106; dr.polygon([(x, 1420), (x + 60, 1395), (x + 60, 1445)], fill=RED + (230,))
    p = back(t / 0.4); s = int(150 * (0.6 + 0.4 * p))
    spaced_text(dr, (W / 2, 250), "1552", font(FB, max(10, s)), CREAM + (a_(t, 0.1, 0.2),), sp=10)
    if t > 1.7: spaced_text(dr, (W / 2, 400), "KORKUNÇ İVAN", font(FB, 72), (232, 90, 70, a_(t, 1.7, 0.3)), sp=4)
    if t > 2.7: paste_pop(base, stamp_card(["KAZAN", "KUŞATILDI"], 560, 210, RED, seed=2, sizes=[80, 56], bg=BG), W / 2, 1220, t - 2.7, rot=3)
    note(ImageDraw.Draw(base, "RGBA"), col=CREAM)
    return base.convert("RGB")

def person(dr, x, yfeet, h, col, a=255, imam=False):
    hw = h * 0.17
    dr.polygon([(x - hw, yfeet), (x + hw, yfeet), (x + hw * 0.7, yfeet - h * 0.75), (x - hw * 0.7, yfeet - h * 0.75)], fill=col + (a,))
    r = h * 0.11; dr.ellipse([x - r, yfeet - h * 0.75 - 2 * r, x + r, yfeet - h * 0.75], fill=col + (a,))
    if imam:
        dr.ellipse([x - r * 1.35, yfeet - h * 0.75 - 2.5 * r, x + r * 1.35, yfeet - h * 0.75 - 1.1 * r], fill=(236, 230, 214, a))

def s3(t, dur):  # Kul Sharif and his students defend the palace
    base = NIGHT.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    gd.ellipse([W / 2 - 500, 500, W / 2 + 500, 1300], fill=(255, 150, 60, 70))
    base.alpha_composite(glow.filter(ImageFilter.GaussianBlur(80))); dr = ImageDraw.Draw(base, "RGBA")
    old_mosque(dr, W / 2, 1000, 0.85, col=(70, 62, 66))
    dr.rectangle([0, 1000, W, H], fill=(46, 40, 44, 255))
    k = ease(clamp(t / 1.2))
    person(dr, W / 2, 1180, 330 * k + 1, (24, 20, 22), imam=True)
    for i, dx in enumerate((-330, -220, 220, 330, -420, 420)):
        kk = ease(clamp((t - 1.0 - i * 0.12) / 0.5))
        if kk > 0: person(dr, W / 2 + dx, 1180, 230 * kk + 1, (34, 28, 30))
    p = back(t / 0.4); s = int(92 * (0.6 + 0.4 * p))
    spaced_text(dr, (W / 2, 240), "İMAM KUL ŞERİF", font(FB, max(10, s)), CREAM + (a_(t, 0, 0.2),), sp=4)
    if t > 1.1: spaced_text(dr, (W / 2, 350), "ve öğrencileri", font(FI, 64), GOLD + (a_(t, 1.1, 0.3),))
    if t > 4.3: paste_pop(base, stamp_card(["HAN SARAYINI", "SAVUNDU"], 600, 200, RED, seed=3, sizes=[70, 70], bg=BG), W / 2, 1300, t - 4.3, rot=-3)
    note(ImageDraw.Draw(base, "RGBA"), col=CREAM)
    return base.convert("RGB")

def s4(t, dur):  # mosque destroyed
    base = NIGHT.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    c = ease(clamp(t / 1.0))
    old_mosque(dr, W / 2, 1000 + c * 40, 0.85, col=(70, 62, 66), a=int(255 * (1 - 0.55 * c)), crumble=c)
    rng = np.random.default_rng(11)
    for i in range(40):
        x = W / 2 + rng.uniform(-380, 380); y0 = rng.uniform(450, 900); v = rng.uniform(250, 600)
        y = min(995, y0 + v * t * t); sz = rng.uniform(8, 22)
        dr.rectangle([x - sz, y - sz * 0.6, x + sz, y + sz * 0.6], fill=(90, 80, 84, 230))
    dr.rectangle([0, 1000, W, H], fill=(46, 40, 44, 255))
    if t > 0.25: paste_pop(base, stamp_card(["CAMİSİ", "YIKILDI"], 520, 210, RED, seed=4, sizes=[80, 80], bg=BG), W / 2, 1230, t - 0.25, rot=4)
    return base.convert("RGB")

def s5(t, dur):  # but Tatars survived: flag + 2nd largest people
    base = SCREEN_PAPER.copy().convert("RGBA")
    B.put_flag(base, flag(900), W / 2, 860, t, amp=14)
    dr = ImageDraw.Draw(base, "RGBA")
    p = back(t / 0.4); s = int(96 * (0.6 + 0.4 * p))
    spaced_text(dr, (W / 2, 230), "AMA TATARLAR", font(FB, max(10, s)), INK + (a_(t, 0, 0.2),), sp=4)
    spaced_text(dr, (W / 2, 350), "YOK OLMADI", font(FB, max(10, s)), RED + (a_(t, 0, 0.2),), sp=6)
    if t > 0.6: dr.text((W / 2, 1150), "Tataristan bayrağı (1991)", font=font(FI, 44), fill=INK + (a_(t, 0.6, 0.3),), anchor="mm")
    if t > 2.0: paste_pop(base, stamp_card(["RUSYA'NIN", "2. BÜYÜK HALKI"], 680, 210, RED, seed=5, sizes=[62, 66], bg=BG), W / 2, 1300, t - 2.0, rot=-3)
    return base.convert("RGB")

def s6(t, dur):  # Kazan Kremlin today: mosque + cathedral, same walls
    base = SKY.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    pan = ease(clamp(t / 7.0))
    off = 120 - pan * 240
    kul_sharif_mosque(dr, 330 + off, 1080, 0.78)
    annunciation(dr, 830 + off, 1080, 0.85)
    walls(dr, 1080)
    p = back(t / 0.4); s = int(92 * (0.6 + 0.4 * p))
    spaced_text(dr, (W / 2, 210), "KAZAN KREMLİNİ", font(FB, max(10, s)), INK + (a_(t, 0, 0.2),), sp=4, stroke=3, sfill=(245, 235, 211))
    spaced_text(dr, (W / 2, 315), "bugün", font(FI, 60), RED + (a_(t, 0.2, 0.3),), stroke=2, sfill=(245, 235, 211))
    if t > 1.5:
        dr.text((330 + off, 1130), "Kul Şerif Camii", font=font(FB, 40), fill=INK + (a_(t, 1.5, 0.3),), anchor="mm")
    if t > 5.9:
        dr.text((830 + off, 1130), "Müjde Katedrali", font=font(FB, 40), fill=INK + (a_(t, 5.9, 0.3),), anchor="mm")
    if 3.3 < t < 6.0:
        paste_pop(base, stamp_card(["2005"], 340, 150, RED, seed=6, sizes=[96], bg=BG), W / 2, 1290, t - 3.3, rot=-4)
    if t > 6.3:
        paste_pop(base, stamp_card(["AYNI SURLARIN", "İÇİNDE"], 640, 200, RED, seed=7, sizes=[64, 64], bg=BG), W / 2, 1290, t - 6.3, rot=3)
    note(ImageDraw.Draw(base, "RGBA"))
    return base.convert("RGB")

def s7(t, dur):  # ending question
    base = Image.new("RGBA", (W, H), (13, 10, 7, 255))
    if t > 0:
        f = flag(700); f2 = f.copy(); a = np.asarray(f2).copy(); a[..., 3] = (a[..., 3] * 0.22 * clamp(t / 1.2)).astype(np.uint8)
        base.alpha_composite(Image.fromarray(a), (int(W / 2 - f.width / 2), 1030))
    dr = ImageDraw.Draw(base, "RGBA")
    spaced_text(dr, (W / 2, 520), "Bir şehir düştü.", font(FI, 62), CREAM + (a_(t, 0.0, 0.4),))
    spaced_text(dr, (W / 2, 610), "Bir halk ise yaşıyor.", font(FI, 62), CREAM + (a_(t, 0.3, 0.4),))
    if t > 1.0:
        p = back((t - 1.0) / 0.45); s = int(96 * (0.6 + 0.4 * p))
        spaced_text(dr, (W / 2, 790), "SENCE BİR HALK", font(FB, max(10, s)), GOLD + (a_(t, 1.0, 0.25),), sp=6)
        spaced_text(dr, (W / 2, 920), "AYAKTA KALABİLİR Mİ?", font(FB, max(10, int(s * 0.7))), (230, 80, 60, a_(t, 1.0, 0.25)), sp=4)
    return base.convert("RGB")

_B = [0.0, 5.6, 11.12, 16.45, 17.95, 22.6, 30.5, 35.2]
_F = [s1, s2, s3, s4, s5, s6, s7]
SCENES = [(f"s{i+1}", f, (_B[i + 1] - _B[i]) / SP) for i, f in enumerate(_F)]
XF = 0.3
STARTS = []; _a = 0.0
for _n, _f, _d in SCENES: STARTS.append(_a); _a += _d
TOTAL = _a
IMPACTS = {"s1": [2.6], "s2": [2.7], "s3": [4.3], "s4": [0.25], "s5": [2.0], "s6": [3.3, 6.3], "s7": [1.0]}

def shake(img, name, t):
    amp = 0.0
    for t0 in IMPACTS.get(name, []):
        dt = t - t0 - 0.06
        if 0 <= dt < 0.45: amp += 12 * math.exp(-dt * 9)
    if amp < 0.5: return img
    dx = amp * math.sin(t * 91); dy = amp * math.cos(t * 77)
    return img.transform((W, H), Image.AFFINE, (1, 0, -dx, 0, 1, -dy), Image.BILINEAR, fillcolor=(20, 14, 9))

def scene_frame(k, T):
    name, fn, dur = SCENES[k]; t = (T - STARTS[k]) * SP
    return np.asarray(shake(fn(t, dur * SP), name, t), np.float32)

def global_frame(T):
    k = max(i for i, s0 in enumerate(STARTS) if s0 <= T + 1e-9)
    a = scene_frame(k, T)
    if k > 0 and T - STARTS[k] < XF:
        b = scene_frame(k - 1, T); w = ease((T - STARTS[k]) / XF); a = a * w + b * (1 - w)
    im = dust(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)), T)
    out = finish(im, SCENES[k][0] != "s7").astype(np.float32)
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
