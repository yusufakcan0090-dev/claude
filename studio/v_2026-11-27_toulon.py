"""Toulon, 27 Kasım 1942: Fransız donanması Almanların eline geçmesin diye kendi gemilerini batırdı.
Şablon: v_2026-11-24_pilecki.py. Zamanlar seslendirmenin orijinal hızına göre; ses SP ile hızlandırılır.
Nazi sembolü çizilmez; Almanlar tank siluetiyle temsil edilir."""
import os, sys, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from figures import put
from make import (W, H, FPS, OUT, SCREEN_PAPER, DESK, stamp_card, paste_pop, shadow, spaced_text, font, FB, FI, INK, RED,
                  CREAM, ease, ease_out, back, clamp, finish, dust, wave_flag)

SP = 1.05
PAPER_DARK = Image.fromarray((np.asarray(DESK, np.float32) * 0.45).astype(np.uint8))
_g = np.linspace(0.35, 0.85, H)[:, None, None]
NIGHT = Image.fromarray(np.clip(np.asarray(DESK, np.float32) * np.array([0.40, 0.48, 0.66]) * _g * 1.6, 0, 255).astype(np.uint8))
GREY = Image.fromarray(np.clip(np.asarray(SCREEN_PAPER, np.float32) * np.array([0.62, 0.62, 0.62]), 0, 255).astype(np.uint8))
BG = (240, 228, 196, 240)
GOLD = (226, 170, 90)
FBLUE = (0, 85, 164); FRED = (239, 65, 53)
SHIP = (78, 86, 100); SEA_Y = 1120

def a_(t, t0, d=0.4): return int(255 * clamp((t - t0) / d))

def note(dr, text="Temsilî çizim", col=INK):
    dr.text((W - 40, H - 250), text, font=font(FI, 30), fill=col + (150,), anchor="rb")

def tricolor(w=420, h=280, cols=(FBLUE, (255, 255, 255), FRED)):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 255)); d = ImageDraw.Draw(im)
    for i, c in enumerate(cols): d.rectangle([i * w // 3, 0, (i + 1) * w // 3, h], fill=c + (255,))
    d.rectangle([0, 0, w - 1, h - 1], outline=(150, 140, 130, 255), width=2)
    return im
FR = tricolor(); IT = tricolor(cols=((0, 146, 70), (255, 255, 255), (206, 43, 55)))

def ship_img(L=620, col=SHIP, seed=0):
    """Savaş gemisi silueti (yan görünüş), su hattı alt kenarda."""
    rng = np.random.default_rng(seed); s = 2
    w, h = int(L * s), int(L * 0.42 * s)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = col + (255,)
    wl = h - 2; hull = int(h * 0.22)
    d.polygon([(0, wl - hull), (w * 0.06, wl), (w * 0.95, wl), (w, wl - hull * 1.15), (w * 0.9, wl - hull), (w * 0.05, wl - hull)], fill=c)
    deck = wl - hull
    d.rectangle([w * 0.33, deck - h * 0.16, w * 0.66, deck], fill=c)              # superstructure
    d.rectangle([w * 0.42, deck - h * 0.32, w * 0.53, deck - h * 0.15], fill=c)    # bridge tower
    d.polygon([(w * 0.56, deck - h * 0.16), (w * 0.62, deck - h * 0.16), (w * 0.61, deck - h * 0.36), (w * 0.57, deck - h * 0.36)], fill=c)  # funnel
    d.line([(w * 0.475, deck - h * 0.32), (w * 0.475, deck - h * 0.62)], fill=c, width=int(4 * s))  # mast
    for x0, dirn in ((0.18, 1), (0.27, 1), (0.74, -1)):
        d.rounded_rectangle([w * x0 - 40 * s, deck - h * 0.09, w * x0 + 40 * s, deck], 8, fill=c)
        d.line([(w * x0, deck - h * 0.06), (w * x0 + dirn * 110 * s, deck - h * 0.09)], fill=c, width=int(7 * s))
    for k in range(int(w * 0.33 / (18 * s))):  # portholes
        x = w * 0.12 + k * 18 * s * 2.6
        if x < w * 0.88: d.ellipse([x, deck + hull * 0.35, x + 6 * s, deck + hull * 0.35 + 6 * s], fill=(200, 190, 150, 160))
    return im.resize((L, int(L * 0.42)), Image.LANCZOS)
SHIPS = [ship_img(780, seed=0), ship_img(560, (66, 72, 86), seed=1), ship_img(440, (58, 64, 76), seed=2)]

def sea(base, y=SEA_Y, t=0.0, col=(28, 40, 60), a=235):
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    d.rectangle([0, y, W, H], fill=col + (a,))
    for k in range(9):
        yy = y + 10 + k * 34
        for x in range(-60, W, 120):
            xo = x + (k % 2) * 60 + 30 * math.sin(t * 1.6 + k)
            d.line([(xo, yy), (xo + 50, yy)], fill=(170, 190, 210, 70), width=3)
    base.alpha_composite(g)

def put_ship(base, img, cx, wl, sink=0.0, tilt=0.0):
    """sink 0..1: gemi suya gömülür (su hattı altını kırp)."""
    im = img.rotate(tilt, expand=True, resample=Image.BICUBIC) if tilt else img
    dy = int(sink * im.height * 1.05)
    x = int(cx - im.width / 2); y = int(wl - im.height + dy)
    vis = max(0, min(im.height, wl - y + 6))
    if vis <= 0: return
    base.alpha_composite(im.crop((0, 0, im.width, vis)), (x, y))

GLOW = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(GLOW).ellipse([-200, SEA_Y - 520, W + 200, SEA_Y + 120], fill=(210, 150, 90, 70))
GLOW = GLOW.filter(ImageFilter.GaussianBlur(90))

def harbor(base, t, sinks=(0, 0, 0), tilts=(0, 0, 0), y=SEA_Y):
    base.alpha_composite(GLOW)
    put_ship(base, SHIPS[2], 820, y - 40, sinks[2], tilts[2])
    put_ship(base, SHIPS[1], 300, y - 20, sinks[1], tilts[1])
    sea(base, y - 30, t, a=150)
    put_ship(base, SHIPS[0], 560, y + 40, sinks[0], tilts[0])
    sea(base, y + 30, t)

def smoke(base, t, xs=(300, 560, 820), y=SEA_Y - 120, a=110):
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    for i, x in enumerate(xs):
        for k in range(7):
            r = 40 + k * 22; yy = y - k * 70 - (t * 40) % 70; xx = x + 25 * math.sin(t + k + i)
            d.ellipse([xx - r, yy - r, xx + r, yy + r], fill=(60, 56, 54, max(0, a - k * 12)))
    base.alpha_composite(g.filter(ImageFilter.GaussianBlur(16)))

def tank(L=420, col=(26, 26, 24)):
    s = 2; w, h = L * s, int(L * 0.5 * s)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = col + (255,)
    d.rounded_rectangle([0, h * 0.62, w, h], int(h * 0.19), fill=c)
    for k in range(7):
        x = w * 0.1 + k * w * 0.133; d.ellipse([x - h * 0.1, h * 0.72, x + h * 0.1, h * 0.92], fill=(70, 70, 66, 255))
    d.polygon([(w * 0.06, h * 0.62), (w * 0.15, h * 0.42), (w * 0.85, h * 0.42), (w * 0.95, h * 0.62)], fill=c)
    d.rounded_rectangle([w * 0.3, h * 0.2, w * 0.66, h * 0.44], 14, fill=c)
    d.rectangle([w * 0.64, h * 0.27, w * 1.0, h * 0.33], fill=c)
    return im.resize((L, int(L * 0.5)), Image.LANCZOS)
TANK = tank()

def gate(dr, a=255, col=(30, 26, 24), open_=0.0):
    dr.rectangle([90, 700, 190, 1400], fill=col + (a,)); dr.rectangle([890, 700, 990, 1400], fill=col + (a,))
    dr.rectangle([70, 660, 210, 720], fill=col + (a,)); dr.rectangle([870, 660, 1010, 720], fill=col + (a,))
    sw = int(350 * (1 - open_))
    for side in (0, 1):
        x0 = 190 if side == 0 else 890 - sw
        for k in range(8):
            x = x0 + 14 + k * (sw - 28) / 7
            if sw > 30: dr.line([(x, 820), (x, 1380)], fill=col + (a,), width=10)
        if sw > 30:
            dr.rectangle([x0, 820, x0 + sw, 840], fill=col + (a,)); dr.rectangle([x0, 1360, x0 + sw, 1380], fill=col + (a,))

def clock(base, cx, cy, r, hh, mm, t):
    d = ImageDraw.Draw(base, "RGBA")
    d.ellipse([cx - r - 14, cy - r - 14, cx + r + 14, cy + r + 14], fill=(60, 44, 28, 255))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(242, 232, 206, 255))
    for k in range(12):
        a = k * math.pi / 6; d.line([(cx + 0.82 * r * math.sin(a), cy - 0.82 * r * math.cos(a)), (cx + 0.94 * r * math.sin(a), cy - 0.94 * r * math.cos(a))], fill=INK + (255,), width=8)
    am = mm / 60 * 2 * math.pi; ah = (hh % 12 + mm / 60) / 12 * 2 * math.pi
    d.line([(cx, cy), (cx + 0.5 * r * math.sin(ah), cy - 0.5 * r * math.cos(ah))], fill=INK + (255,), width=16)
    d.line([(cx, cy), (cx + 0.78 * r * math.sin(am), cy - 0.78 * r * math.cos(am))], fill=INK + (255,), width=10)
    sa = t * 2 * math.pi / 3
    d.line([(cx, cy), (cx + 0.85 * r * math.sin(sa), cy - 0.85 * r * math.cos(sa))], fill=RED + (255,), width=4)
    d.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=RED + (255,))


# ---------- scenes (t = local seconds in ORIGINAL voice time) ----------
def s1(t, dur):  # hook: they sank their own fleet
    base = NIGHT.copy().convert("RGBA")
    harbor(base, t)
    dr = ImageDraw.Draw(base, "RGBA")
    p = back(t / 0.35); s = int(84 * (0.85 + 0.15 * p))
    spaced_text(dr, (W / 2, 250), "KENDİ DONANMASINI", font(FB, max(10, int(s * 0.8))), CREAM + (255,), sp=2)
    spaced_text(dr, (W / 2, 370), "BATIRDI", font(FB, max(10, int(s * 1.35))), (232, 90, 70, 255), sp=8)
    if t > 0.5: paste_pop(base, stamp_card(["27 KASIM 1942"], 560, 130, RED, seed=1, sizes=[64], bg=BG), W / 2, 530, t - 0.5, rot=-4)
    note(ImageDraw.Draw(base, "RGBA"), col=CREAM)
    return base.convert("RGB")

def s2(t, dur):  # the French, about to sink their own navy
    base = NIGHT.copy().convert("RGBA")
    f = wave_flag(FR, t, amp=12); base.alpha_composite(f, (int(W / 2 - f.width / 2), 330))
    harbor(base, t)
    dr = ImageDraw.Draw(base, "RGBA")
    spaced_text(dr, (W / 2, 220), "FRANSIZ DONANMASI", font(FB, 74), CREAM + (a_(t, 0, 0.3),), sp=3)
    if t > 1.2: paste_pop(base, stamp_card(["TOULON"], 420, 140, RED, seed=2, sizes=[84], bg=BG), W / 2, 820, t - 1.2, rot=3)
    note(ImageDraw.Draw(base, "RGBA"), col=CREAM)
    return base.convert("RGB")

def s3(t, dur):  # Hitler wanted to seize it and give it to Italy
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    spaced_text(dr, (W / 2, 220), "HİTLER'İN PLANI", font(FB, 86), RED + (a_(t, 0, 0.3),), sp=4)
    f1 = wave_flag(tricolor(330, 220), t, amp=8); base.alpha_composite(f1, (110, 420))
    k = ease(clamp((t - 2.6) / 0.5))
    if k > 0:
        f2 = wave_flag(tricolor(330, 220, ((0, 146, 70), (255, 255, 255), (206, 43, 55))), t, amp=8)
        f2.putalpha(Image.fromarray((np.asarray(f2)[..., 3] * k).astype(np.uint8))); base.alpha_composite(f2, (640, 420))
        spaced_text(dr, (805, 740), "İTALYA", font(FB, 56), INK + (int(255 * k),), sp=4)
    spaced_text(dr, (275, 740), "FRANSA", font(FB, 56), INK + (a_(t, 0, 0.3),), sp=4)
    ar = ease(clamp((t - 1.6) / 1.0))
    if ar > 0:
        x0, x1 = 300, 300 + ar * 480
        sh = SHIPS[1]; base.alpha_composite(sh, (int(x1 - sh.width / 2), 940))
        dr.line([(250, 1180), (x1 + 120, 1180)], fill=RED + (255,), width=10)
        dr.polygon([(x1 + 120, 1150), (x1 + 170, 1180), (x1 + 120, 1210)], fill=RED + (255,))
    if t > 3.0: paste_pop(base, stamp_card(["ELE GEÇİR, VER"], 640, 140, RED, seed=3, sizes=[66], bg=BG), W / 2, 1360, t - 3.0, rot=-3)
    note(ImageDraw.Draw(base, "RGBA"))
    return base.convert("RGB")

def s4(t, dur):  # Germans enter before dawn
    base = NIGHT.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    for i in range(40):
        x = (i * 263) % W; y = 120 + (i * 151) % 520; dr.ellipse([x, y, x + 4, y + 4], fill=(240, 230, 200, 120))
    dr.rectangle([0, 1250, W, H], fill=(20, 18, 18, 255))
    for i in range(3):
        x = -300 + i * 380 + ease(clamp(t / 2.4)) * 420
        base.alpha_composite(TANK, (int(x), 1260 - TANK.height + 10))
    p = back(t / 0.4); s = int(96 * (0.6 + 0.4 * p))
    spaced_text(dr, (W / 2, 260), "ŞAFAKTAN ÖNCE", font(FB, max(10, s)), CREAM + (a_(t, 0, 0.2),), sp=6)
    if t > 0.9: paste_pop(base, stamp_card(["ALMANLAR GELDİ"], 620, 140, RED, seed=4, sizes=[66], bg=BG), W / 2, 460, t - 0.9, rot=-3)
    note(ImageDraw.Draw(base, "RGBA"), col=CREAM)
    return base.convert("RGB")

def paper(w=200, h=140, rot=0):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, h], fill=(244, 236, 214, 255), outline=(120, 96, 60, 255), width=3)
    for k in range(5): d.line([(18, 24 + k * 22), (w - 18 - (k % 2) * 40, 24 + k * 22)], fill=(90, 70, 50, 200), width=4)
    return im.rotate(rot, expand=True, resample=Image.BICUBIC)

def s5(t, dur):  # sentries ask for paperwork to gain time
    base = GREY.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    gate(dr)
    put(base, "soldier", 300, 1400, 540, dark=0.15)
    spaced_text(dr, (W / 2, 230), "ÜSSÜN KAPISI", font(FB, 88), INK + (a_(t, 0, 0.3),), sp=6)
    if t > 1.6:
        for i in range(3):
            k = ease(clamp((t - 1.6 - i * 0.35) / 0.5))
            if k <= 0: continue
            p = paper(220, 150, rot=-8 + i * 7)
            base.alpha_composite(p, (int(520 + i * 60), int(820 + i * 70 - 60 * k)))
    if t > 2.6: paste_pop(base, stamp_card(["EVRAK?"], 440, 150, RED, seed=5, sizes=[92], bg=BG), W / 2 + 180, 520, t - 2.6, rot=-5)
    if t > 3.5: paste_pop(base, stamp_card(["ZAMAN KAZANDILAR"], 720, 130, INK, seed=6, sizes=[60], bg=BG), W / 2, 1300, t - 3.5, rot=3)
    note(ImageDraw.Draw(base, "RGBA"))
    return base.convert("RGB")

def s6(t, dur):  # 05:25 tanks pass the gate
    base = PAPER_DARK.copy().convert("RGBA")
    clock(base, W / 2, 620, 250, 5, 25, t)
    dr = ImageDraw.Draw(base, "RGBA")
    p = back(t / 0.4); s = int(120 * (0.6 + 0.4 * p))
    spaced_text(dr, (W / 2, 230), "05.25", font(FB, max(10, s)), CREAM + (a_(t, 0, 0.2),), sp=10)
    dr.rectangle([0, 1300, W, H], fill=(20, 18, 18, 255))
    x = W + 40 - ease(clamp((t - 1.4) / 1.6)) * 900
    base.alpha_composite(TANK.transpose(Image.FLIP_LEFT_RIGHT), (int(x), 1310 - TANK.height + 10))
    if t > 1.7: paste_pop(base, stamp_card(["TANKLAR İÇERİDE"], 640, 130, RED, seed=7, sizes=[62], bg=BG), W / 2, 980, t - 1.7, rot=-3)
    note(ImageDraw.Draw(base, "RGBA"), col=CREAM)
    return base.convert("RGB")

def s7(t, dur):  # flagship Strasbourg, one order
    base = NIGHT.copy().convert("RGBA")
    put_ship(base, ship_img(900, seed=3), W / 2, 1180)
    sea(base, 1160, t)
    dr = ImageDraw.Draw(base, "RGBA")
    if int(t * 4) % 2 == 0 and t > 1.0:  # signal lamp
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse([450, 810, 510, 870], fill=(255, 236, 170, 230))
        base.alpha_composite(g.filter(ImageFilter.GaussianBlur(10)))
    spaced_text(dr, (W / 2, 240), "AMİRAL GEMİSİ", font(FB, 84), CREAM + (a_(t, 0, 0.3),), sp=4)
    spaced_text(dr, (W / 2, 360), "STRASBOURG", font(FB, 92), GOLD + (a_(t, 0.3, 0.3),), sp=8)
    if t > 1.9: paste_pop(base, stamp_card(["TEK BİR EMİR"], 560, 130, RED, seed=8, sizes=[66], bg=BG), W / 2, 600, t - 1.9, rot=-3)
    note(ImageDraw.Draw(base, "RGBA"), col=CREAM)
    return base.convert("RGB")

B_HITS = [0.08, 0.88, 1.68]   # local times of "Batırın!" (orig 23.68, 24.48, 25.28 - scene start 23.6)

def s8(t, dur):  # SCUTTLE x3
    base = NIGHT.copy().convert("RGBA")
    k = ease(clamp((t - 0.6) / 2.6))
    harbor(base, t, sinks=(0.15 * k, 0.2 * k, 0.25 * k), tilts=(-3 * k, 4 * k, -5 * k))
    smoke(base, t, a=int(110 * k))
    for i, th in enumerate(B_HITS):
        if t > th:
            paste_pop(base, stamp_card(["BATIRIN!"], 560, 150, RED, seed=10 + i, sizes=[96], bg=BG), W / 2 + (i - 1) * 60, 300 + i * 190, t - th, rot=(-6, 4, -3)[i])
    return base.convert("RGB")

def s9(t, dur):  # 70+ ships to the bottom
    base = NIGHT.copy().convert("RGBA")
    k = ease(clamp(t / 2.4))
    harbor(base, t, sinks=(0.15 + 0.4 * k, 0.2 + 0.5 * k, 0.25 + 0.55 * k), tilts=(-3 - 5 * k, 4 + 6 * k, -5 - 6 * k))
    smoke(base, t, a=110)
    dr = ImageDraw.Draw(base, "RGBA")
    p = back(t / 0.4); s = int(96 * (0.6 + 0.4 * p))
    spaced_text(dr, (W / 2, 260), "70'TEN FAZLA", font(FB, max(10, s)), CREAM + (a_(t, 0, 0.2),), sp=6)
    spaced_text(dr, (W / 2, 380), "GEMİ", font(FB, max(10, int(s * 1.2))), (232, 90, 70, a_(t, 0, 0.2)), sp=10)
    if t > 1.0: paste_pop(base, stamp_card(["LİMANIN DİBİNE"], 620, 130, RED, seed=13, sizes=[62], bg=BG), W / 2, 560, t - 1.0, rot=-3)
    note(ImageDraw.Draw(base, "RGBA"), col=CREAM)
    return base.convert("RGB")

def s10(t, dur):  # the fleet Hitler wanted was gone
    base = PAPER_DARK.copy().convert("RGBA")
    sea(base, 1120, t, col=(24, 32, 44))
    smoke(base, t, a=70)
    dr = ImageDraw.Draw(base, "RGBA")
    spaced_text(dr, (W / 2, 420), "HİTLER'İN İSTEDİĞİ FİLO", font(FB, 64), CREAM + (a_(t, 0, 0.3),), sp=2)
    if t > 1.4: paste_pop(base, stamp_card(["ARTIK YOK"], 640, 190, RED, seed=14, sizes=[110], bg=BG), W / 2, 720, t - 1.4, rot=-5)
    return base.convert("RGB")

def s11(t, dur):  # ending question
    base = Image.new("RGBA", (W, H), (13, 10, 7, 255)); dr = ImageDraw.Draw(base, "RGBA")
    spaced_text(dr, (W / 2, 560), "Toulon, 27 Kasım 1942.", font(FI, 58), CREAM + (a_(t, 0.0, 0.4),))
    p = back(t / 0.45); s = int(80 * (0.6 + 0.4 * p))
    spaced_text(dr, (W / 2, 760), "SEN OLSAN", font(FB, max(10, s)), GOLD + (a_(t, 0.2, 0.25),), sp=6)
    spaced_text(dr, (W / 2, 880), "DÜŞMANA MI BIRAKIRDIN,", font(FB, max(10, int(s * 0.8))), GOLD + (a_(t, 0.2, 0.25),), sp=3)
    spaced_text(dr, (W / 2, 1020), "BATIRIR MIYDIN?", font(FB, max(10, s)), (230, 80, 60, a_(t, 0.2, 0.25)), sp=6)
    return base.convert("RGB")

# scene starts in ORIGINAL voice seconds (from the word transcript)
_B = [0.0, 2.6, 5.9, 10.7, 13.15, 17.45, 20.65, 23.6, 26.7, 29.3, 32.1, 36.5]
_F = [s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11]
SCENES = [(f"s{i+1}", f, (_B[i + 1] - _B[i]) / SP) for i, f in enumerate(_F)]
XF = 0.3
STARTS = []; _a = 0.0
for _n, _f, _d in SCENES: STARTS.append(_a); _a += _d
TOTAL = _a
IMPACTS = {"s1": [0.5], "s2": [1.2], "s3": [3.0], "s4": [0.9], "s5": [2.6, 3.5], "s6": [1.7], "s7": [1.9], "s8": B_HITS,
           "s9": [1.0], "s10": [1.4], "s11": [0.2]}   # local ORIGINAL seconds

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
    out = finish(im, SCENES[k][0] != "s11").astype(np.float32)
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
