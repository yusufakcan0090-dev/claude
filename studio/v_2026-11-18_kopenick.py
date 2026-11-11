import os, sys, math, subprocess
import numpy as np
from PIL import Image, ImageDraw
import make as M
from make import (W, H, FPS, OUT, SCREEN_PAPER, DESK, stamp_card, paste_pop, shadow, spaced_text, font, FB, FI, INK, RED,
                  CREAM, ease, ease_out, back, clamp, finish, dust, title_band)

PAPER_DARK = Image.fromarray((np.asarray(DESK, np.float32) * 0.45).astype(np.uint8))
BG = (240, 228, 196, 240)
GOLD = (226, 170, 90)
NAVY = (36, 52, 92)

def a_(t, t0, d=0.4): return int(255 * clamp((t - t0) / d))

def note(dr, text="Temsilî çizim", col=INK):
    dr.text((W - 40, H - 250), text, font=font(FI, 30), fill=col + (150,), anchor="rb")

def gent(dr, x, y, sc=1.0, col=INK, a=255, hat=True, coat=True, cap=False):
    """19. yy. erkek silüeti (önden), y = ayak hizası."""
    c = col + (a,)
    s = sc
    dr.ellipse([x - 42 * s, y - 470 * s, x + 42 * s, y - 370 * s], fill=c)              # head
    if hat:
        dr.rectangle([x - 40 * s, y - 560 * s, x + 40 * s, y - 455 * s], fill=c)        # top hat
        dr.rounded_rectangle([x - 72 * s, y - 468 * s, x + 72 * s, y - 452 * s], 6, fill=c)
    if cap:
        dr.pieslice([x - 50 * s, y - 500 * s, x + 50 * s, y - 420 * s], 180, 360, fill=c)
    dr.rectangle([x - 18 * s, y - 380 * s, x + 18 * s, y - 350 * s], fill=c)            # neck
    w = 110 if coat else 90
    dr.polygon([(x - w * s, y - 340 * s), (x + w * s, y - 340 * s), (x + (w + 20) * s, y - 120 * s),
                (x - (w + 20) * s, y - 120 * s)], fill=c)                                  # coat
    dr.rounded_rectangle([x - w * s, y - 360 * s, x + w * s, y - 320 * s], 30, fill=c)  # shoulders
    dr.rectangle([x - 60 * s, y - 130 * s, x - 12 * s, y], fill=c)                        # legs
    dr.rectangle([x + 12 * s, y - 130 * s, x + 60 * s, y], fill=c)
    dr.rectangle([x - (w + 28) * s, y - 340 * s, x - (w - 2) * s, y - 150 * s], fill=c)  # arms
    dr.rectangle([x + (w - 2) * s, y - 340 * s, x + (w + 28) * s, y - 150 * s], fill=c)

def bars(dr, x0, x1, y0, y1, a=255, n=7, col=(40, 32, 26)):
    c = col + (a,)
    for i in range(n):
        x = x0 + (x1 - x0) * (i + 0.5) / n
        dr.rounded_rectangle([x - 12, y0, x + 12, y1], 10, fill=c)
    dr.rectangle([x0, y0, x1, y0 + 26], fill=c); dr.rectangle([x0, y1 - 26, x1, y1], fill=c)

# ---------- scenes ----------
FIELD = (40, 48, 70)  # Prussian blue coat

def soldier(dr, x, y, sc=1.0, col=FIELD, a=255, spike=True, officer=False):
    """1906 Prusya askeri silüeti (sivri miğfer / subay kasketi), y = ayak hizası."""
    s = sc; c = col + (a,)
    gent(dr, x, y, sc, col=col, a=a, hat=False, coat=True)
    if officer:
        dr.rounded_rectangle([x - 50 * s, y - 505 * s, x + 50 * s, y - 452 * s], 14 * s, fill=c)      # cap crown
        dr.pieslice([x - 58 * s, y - 470 * s, x + 30 * s, y - 440 * s], 0, 180, fill=c)            # visor
        dr.rectangle([x - 48 * s, y - 470 * s, x + 48 * s, y - 458 * s], fill=RED + (a,))           # band
        for i in range(2):  # gold buttons
            pass
        dr.rectangle([x - 112 * s, y - 352 * s, x - 70 * s, y - 336 * s], fill=GOLD + (a,))          # epaulettes
        dr.rectangle([x + 70 * s, y - 352 * s, x + 112 * s, y - 336 * s], fill=GOLD + (a,))
        for i in range(5):
            dr.ellipse([x - 7 * s, y - (320 - i * 38) * s, x + 7 * s, y - (306 - i * 38) * s], fill=GOLD + (a,))
    elif spike:
        dr.pieslice([x - 50 * s, y - 505 * s, x + 50 * s, y - 425 * s], 180, 360, fill=c)
        dr.polygon([(x - 9 * s, y - 495 * s), (x + 9 * s, y - 495 * s), (x, y - 545 * s)], fill=c)
        dr.rectangle([x - 58 * s, y - 468 * s, x + 58 * s, y - 458 * s], fill=c)

def s1(t, dur):  # hook: a shoemaker took over a town hall with a uniform
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    spaced_text(dr, (W / 2, 280), "BİR ÜNİFORMA", font(FB, 92), INK + (255,), sp=6)
    spaced_text(dr, (W / 2, 390), "BİR BELEDİYE", font(FB, 92), RED + (255,), sp=6)
    s = 0.95 + 0.05 * ease_out(t / 0.6)
    p = ease((t - 0.9) / 0.7)
    # shoemaker (brown, apron) morphs to officer
    if p < 1: gent(dr, W / 2, 1250, 1.1 * s, col=(92, 64, 40), a=int(255 * (1 - p)), hat=False)
    if p < 1:
        k = int(255 * (1 - p))
        dr.rectangle([W / 2 - 80, 1250 - 330 * 1.1 * s, W / 2 + 80, 1250 - 150 * 1.1 * s], fill=(200, 176, 130, k))
        spaced_text(dr, (W / 2, 1300), "ayakkabıcı", font(FI, 52), INK + (k,))
    if p > 0: soldier(dr, W / 2, 1250, 1.1 * s, a=int(255 * p), officer=True)
    if t > 2.6:
        paste_pop(base, stamp_card(["ELE GEÇİRDİ"], 760, 160, RED, seed=1, sizes=[88], bg=BG), W / 2, 1360, t - 2.6, rot=-3)
    note(ImageDraw.Draw(base, "RGBA"))
    return base.convert("RGB")

def mug(t):
    w, h = 640, 820
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, h], fill=(244, 232, 200, 255), outline=(120, 96, 60, 255), width=6)
    spaced_text(d, (w / 2, 70), "SABIKA KAYDI", font(FB, 56), INK + (255,), sp=6)
    d.rectangle([110, 130, w - 110, 560], fill=(214, 196, 156, 255), outline=INK + (255,), width=4)
    gent(d, w / 2, 660, 0.7, col=(70, 52, 34), hat=False)
    d.rectangle([110, 560, w - 110, 820], fill=(244, 232, 200, 255))
    d.rectangle([110, 130, w - 110, 560], outline=INK + (255,), width=4)
    spaced_text(d, (w / 2, 625), "WILHELM VOIGT", font(FB, 56), RED + (255,), sp=3)
    spaced_text(d, (w / 2, 700), "Tilsit, 1849 · ayakkabıcı", font(FI, 38), INK + (255,))
    return im

def s2(t, dur):  # Wilhelm Voigt, 57, former convict
    base = SCREEN_PAPER.copy().convert("RGBA")
    rise = ease_out(t / 0.6)
    pst = mug(t).rotate(2, expand=True, resample=Image.BICUBIC)
    cx, cy = W / 2, 660 + (1 - rise) * 120
    base.alpha_composite(shadow(pst), (int(cx - pst.width / 2 - 18), int(cy - pst.height / 2 - 14)))
    base.alpha_composite(pst, (int(cx - pst.width / 2), int(cy - pst.height / 2)))
    if t > 1.85: paste_pop(base, stamp_card(["57 YAŞINDA"], 460, 140, RED, seed=2, sizes=[58], bg=BG), 300, 1170, t - 1.85, rot=-7)
    if t > 3.0: paste_pop(base, stamp_card(["ESKİ MAHKÛM"], 480, 140, RED, seed=3, sizes=[58], bg=BG), 780, 1170, t - 3.0, rot=6)
    if t > 4.1: paste_pop(base, stamp_card(["HAYATI HAPİSTE GEÇTİ"], 900, 130, INK, seed=4, sizes=[50], bg=BG), W / 2, 1330, t - 4.1, rot=-1)
    return base.convert("RGB")

def passport(d, cx, cy, a):
    d.rounded_rectangle([cx - 190, cy - 260, cx + 190, cy + 260], 18, fill=(110, 28, 26, a), outline=(60, 14, 12, a), width=6)
    d.ellipse([cx - 70, cy - 120, cx + 70, cy + 20], outline=GOLD + (a,), width=6)
    spaced_text(d, (cx, cy + 110), "REISEPASS", font(FB, 44), GOLD + (a,), sp=4)

def s3(t, dur):  # no passport, no work
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    k = a_(t, 0.0, 0.25)
    spaced_text(dr, (W / 2, 300), "KISIR DÖNGÜ", font(FB, 84), INK + (k,), sp=6)
    passport(dr, 290, 820, k)
    # work: shoe/hammer icon
    k2 = a_(t, 1.15, 0.25)
    dr.polygon([(650, 900), (930, 900), (930, 840), (840, 820), (760, 700), (680, 700), (650, 760)], fill=(70, 52, 34, k2))
    dr.rectangle([640, 900, 940, 930], fill=(40, 30, 20, k2))
    spaced_text(dr, (790, 1010), "İŞ", font(FB, 60), INK + (k2,))
    # arrows loop
    ka = a_(t, 0.6, 0.3)
    dr.arc([200, 470, 880, 1150], 200, 340, fill=INK + (ka,), width=8)
    dr.arc([200, 470, 880, 1150], 20, 160, fill=INK + (ka,), width=8)
    if t > 0.25: paste_pop(base, stamp_card(["PASAPORT YOK"], 560, 140, RED, seed=5, sizes=[58], bg=BG), 330, 1230, t - 0.25, rot=-6)
    if t > 1.4: paste_pop(base, stamp_card(["İŞ YOK"], 400, 140, RED, seed=6, sizes=[64], bg=BG), 780, 1330, t - 1.4, rot=5)
    return base.convert("RGB")

def s4(t, dur):  # bought a captain's uniform from second-hand dealers
    base = PAPER_DARK.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    spaced_text(dr, (W / 2, 300), "ESKİCİ DÜKKÂNI", font(FB, 74), CREAM + (a_(t, 0, 0.25),), sp=6)
    dr.rectangle([140, 470, W - 140, 486], fill=(150, 120, 80, 255))  # rail
    for i, x in enumerate([260, 820]):
        dr.line([(x, 486), (x, 540)], fill=(150, 120, 80, 255), width=6)
        dr.polygon([(x - 120, 560), (x + 120, 560), (x + 140, 900), (x - 140, 900)], fill=(70, 56, 40, 255))
    sl = ease_out(t / 0.6)
    x = W / 2; y0 = 560 + (1 - sl) * 60
    dr.line([(x, 486), (x, y0 - 20)], fill=GOLD + (255,), width=6)
    dr.polygon([(x - 150, y0), (x + 150, y0), (x + 175, y0 + 420), (x - 175, y0 + 420)], fill=FIELD + (255,))
    dr.rectangle([x - 160, y0 - 6, x - 90, y0 + 14], fill=GOLD + (255,)); dr.rectangle([x + 90, y0 - 6, x + 160, y0 + 14], fill=GOLD + (255,))
    for i in range(5): dr.ellipse([x - 9, y0 + 50 + i * 70, x + 9, y0 + 68 + i * 70], fill=GOLD + (255,))
    dr.rectangle([x - 175, y0 + 330, x + 175, y0 + 350], fill=(20, 16, 12, 255))
    if t > 1.0:
        paste_pop(base, stamp_card(["YÜZBAŞI", "ÜNİFORMASI"], 760, 230, RED, seed=7, sizes=[74, 74], bg=BG), W / 2, 1270, t - 1.0, rot=-3)
    note(ImageDraw.Draw(base, "RGBA"), col=CREAM)
    return base.convert("RGB")

def s5(t, dur):  # 16 October 1906, Berlin: orders soldiers
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    p = back(t / 0.45); s = int(112 * (0.6 + 0.4 * p))
    spaced_text(dr, (W / 2, 280), "16 EKİM 1906", font(FB, max(10, s)), RED + (a_(t, 0, 0.2),), sp=6)
    spaced_text(dr, (W / 2, 400), "Berlin", font(FI, 60), INK + (a_(t, 0.4),))
    soldier(dr, 270, 1180, 0.85, officer=True)
    for i in range(3):
        k = a_(t, 2.3 + i * 0.18, 0.3)
        if k: soldier(dr, 560 + i * 175, 1180, 0.6, a=k)
    if t > 2.6:
        kb = a_(t, 2.6, 0.25)
        dr.rounded_rectangle([90, 520, 640, 640], 26, fill=(255, 250, 235, kb), outline=INK + (kb,), width=5)
        dr.polygon([(240, 638), (300, 638), (270, 690)], fill=(255, 250, 235, kb))
        spaced_text(dr, (365, 580), "“BENİ TAKİP EDİN!”", font(FB, 38), RED + (kb,))
    note(ImageDraw.Draw(base, "RGBA"))
    return base.convert("RGB")

def s6(t, dur):  # 10 soldiers followed without question
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    for i in range(10):
        r_, c_ = divmod(i, 5)
        x = 130 + c_ * 195 + (t * 15); y = 760 + r_ * 420
        k = int(255 * clamp((t - 0.05 - i * 0.07) / 0.2))
        if k: soldier(dr, x, y, 0.55, a=k)
    p = back((t - 0.0) / 0.4); s = int(120 * (0.6 + 0.4 * p))
    spaced_text(dr, (W / 2, 260), "10 ASKER", font(FB, max(10, s)), RED + (a_(t, 0, 0.2),), sp=8)
    if t > 1.0:
        paste_pop(base, stamp_card(["HİÇ SORGULAMADAN"], 860, 150, INK, seed=8, sizes=[62], bg=BG), W / 2, 1350, t - 1.0, rot=-2)
    note(ImageDraw.Draw(base, "RGBA"))
    return base.convert("RGB")

def townhall(dr, a):
    brick = (150, 62, 44, a); dark = (90, 36, 26, a)
    dr.rectangle([130, 620, 950, 1180], fill=brick)
    dr.polygon([(130, 620), (950, 620), (900, 560), (180, 560)], fill=dark)
    dr.rectangle([460, 330, 620, 620], fill=brick)                         # tower
    dr.polygon([(450, 330), (630, 330), (540, 190)], fill=dark)
    dr.ellipse([505, 380, 575, 450], fill=(240, 228, 196, a), outline=dark, width=4)  # clock
    for r_ in range(2):
        for c_ in range(6):
            x = 180 + c_ * 130; y = 680 + r_ * 200
            if 460 < x < 600 and r_ == 1: continue
            dr.rounded_rectangle([x, y, x + 70, y + 130], 30, fill=(60, 50, 40, a))
    dr.rounded_rectangle([480, 960, 600, 1180], 50, fill=(50, 34, 24, a))

def s7(t, dur):  # town hall, mayor arrested, 4000 marks
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    townhall(dr, a_(t, 0, 0.3))
    k = a_(t, 0.2, 0.3)
    dr.rounded_rectangle([250, 1200, 830, 1270], 10, fill=INK + (k,))
    spaced_text(dr, (540, 1235), "RATHAUS KÖPENICK", font(FB, 38), CREAM + (k,), sp=3)
    if t > 1.4:
        veil = Image.new("RGBA", (W, H), (20, 14, 9, int(90 * clamp((t - 1.4) / 0.3)))); base.alpha_composite(veil)
        paste_pop(base, stamp_card(["BELEDİYE BAŞKANI", "TUTUKLANDI"], 860, 230, RED, seed=9, sizes=[60, 72], bg=BG), W / 2, 820, t - 1.4, rot=-4)
    if t > 3.25:
        paste_pop(base, stamp_card(["KASADAKİ 4.000 MARK"], 900, 150, INK, seed=10, sizes=[60], bg=BG), W / 2, 1360, t - 3.25, rot=2)
    note(ImageDraw.Draw(base, "RGBA"))
    return base.convert("RGB")

def s8(t, dur):  # caught, 4 years
    base = PAPER_DARK.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    spaced_text(dr, (W / 2, 330), "YAKALANDI", font(FB, 110), CREAM + (a_(t, 0, 0.25),), sp=8)
    gent(dr, W / 2, 1150, 0.95, col=(18, 13, 9), hat=False)
    p = ease(t / 0.5)
    bars(dr, 150, W - 150, 600 - (1 - p) * 700, 1170, a=int(255 * p), n=6, col=(70, 58, 44))
    if t > 1.2:
        paste_pop(base, stamp_card(["4 YIL HAPİS"], 760, 170, RED, seed=11, sizes=[90], bg=BG), W / 2, 1330, t - 1.2, rot=-3)
    note(ImageDraw.Draw(base, "RGBA"), col=CREAM)
    return base.convert("RGB")

def crown(dr, cx, cy, sc, a):
    s = sc; c = GOLD + (a,)
    dr.polygon([(cx - 200 * s, cy + 80 * s), (cx + 200 * s, cy + 80 * s), (cx + 220 * s, cy - 90 * s), (cx + 110 * s, cy - 10 * s),
                (cx, cy - 140 * s), (cx - 110 * s, cy - 10 * s), (cx - 220 * s, cy - 90 * s)], fill=c)
    dr.rectangle([cx - 200 * s, cy + 80 * s, cx + 200 * s, cy + 130 * s], fill=c)
    for dx in (-220, 0, 220):
        dr.ellipse([cx + dx * s - 22 * s, cy - (90 if dx else 140) * s - 40 * s, cx + dx * s + 22 * s, cy - (90 if dx else 140) * s + 4 * s], fill=c)
    for dx in (-110, 0, 110):
        dr.ellipse([cx + dx * s - 18 * s, cy + 92 * s, cx + dx * s + 18 * s, cy + 118 * s], fill=RED + (a,))

def s9(t, dur):  # Kaiser laughed (reportedly), pardoned
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    p = ease_out(t / 0.6)
    crown(dr, W / 2, 720 - (1 - p) * 60, 1.4, int(255 * clamp(t / 0.4)))
    spaced_text(dr, (W / 2, 330), "KAISER WILHELM II", font(FB, 70), INK + (a_(t, 0.1),), sp=4)
    spaced_text(dr, (W / 2, 1000), "hikâyeye güldüğü anlatılır", font(FI, 54), INK + (a_(t, 1.0),))
    if t > 2.85:
        paste_pop(base, stamp_card(["AFFEDİLDİ", "1908"], 700, 240, RED, seed=12, sizes=[90, 60], bg=BG), W / 2, 1300, t - 2.85, rot=-4)
    return base.convert("RGB")

def s10(t, dur):  # ending
    base = Image.new("RGBA", (W, H), (13, 10, 7, 255)); dr = ImageDraw.Draw(base, "RGBA")
    soldier(dr, W / 2, 1700, 1.2, col=(34, 26, 19), a=int(120 * clamp(t / 1.5)), officer=True)
    spaced_text(dr, (W / 2, 640), "Bir üniformaya", font(FI, 62), CREAM + (a_(t, 0.1, 0.5),))
    spaced_text(dr, (W / 2, 730), "körü körüne itaat...", font(FI, 62), CREAM + (a_(t, 0.6, 0.5),))
    if t > 2.6:
        p = back((t - 2.6) / 0.45); s = int(104 * (0.6 + 0.4 * p))
        spaced_text(dr, (W / 2, 900), "BUGÜN DE", font(FB, max(10, s)), GOLD + (a_(t, 2.6, 0.25),), sp=8)
        spaced_text(dr, (W / 2, 1040), "İŞE YARAR MIYDI?", font(FB, max(10, int(s * 0.72))), (230, 80, 60, a_(t, 2.6, 0.25)), sp=6)
    return base.convert("RGB")

SCENES = [("s1", s1, 5.0), ("s2", s2, 5.75), ("s3", s3, 3.0), ("s4", s4, 2.7), ("s5", s5, 4.35), ("s6", s6, 2.4),
          ("s7", s7, 5.3), ("s8", s8, 3.15), ("s9", s9, 5.45), ("s10", s10, 5.3)]
XF = 0.35
STARTS = []; _a = 0.0
for _n, _f, _d in SCENES: STARTS.append(_a); _a += _d
TOTAL = _a
IMPACTS = {"s1": [2.6], "s2": [1.85, 3.0, 4.1], "s3": [0.25, 1.4], "s4": [1.0], "s5": [0.0], "s6": [1.0], "s7": [1.4, 3.25],
           "s8": [1.2], "s9": [2.85], "s10": [2.6]}
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
    out = finish(im, SCENES[k][0] != "s10").astype(np.float32)
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
    else:
        for k, sc in enumerate(SCENES):
            if sc[0] in sys.argv[2:]: render(k)
