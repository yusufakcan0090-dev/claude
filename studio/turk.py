"""'Osmanlı torunundan önce Türk'üz' videosu."""
import os, sys, math, json
import numpy as np
from PIL import Image, ImageDraw
import make as M
from make import (W, H, FPS, OUT, SCREEN_PAPER, render_map, camera, P, to_screen, city_dot, pulse, stamp_card,
                  paste_pop, wave_flag, make_flag, spaced_text, font, FB, FI, INK, RED, CREAM, ease, ease_out, back,
                  clamp, finish, dust, title_band)
import bayrak as B

TR_FLAG = make_flag(860, 573, (200, 16, 46))
OTT_SMALL = make_flag(420, 280, (200, 16, 46))
GOLD = (222, 180, 96)
T = json.load(open(os.path.join(OUT, "turk_times.json"))) if os.path.exists(os.path.join(OUT, "turk_times.json")) else {}
def e(k, d): return T.get(k, d)

def t1(t, dur):  # hook
    base = B.PAPER_DARK.copy().convert("RGBA")
    B.put_flag(base, TR_FLAG, W / 2, 900, t, amp=12, op=0.22)
    dr = ImageDraw.Draw(base, "RGBA")
    p = back(t / 0.45); s = int(110 * (0.7 + 0.3 * p))
    a = int(255 * clamp(t / 0.25))
    spaced_text(dr, (W / 2, 760), "OSMANLI", font(FB, s), CREAM + (a,), sp=10)
    spaced_text(dr, (W / 2, 900), "TORUNU?", font(FB, s), (230, 70, 60, a), sp=10)
    return base.convert("RGB")

def t2(t, dur):  # not a nation, a state/dynasty
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    a = int(255 * clamp(t / 0.3))
    spaced_text(dr, (W / 2, 280), "OSMANLI NEYDİ?", font(FB, 72), INK + (a,), sp=6)
    c1 = stamp_card(["MİLLET"], 640, 170, (120, 110, 100), seed=51, sizes=[92], bg=(240, 228, 196, 235))
    paste_pop(base, c1, W / 2, 620, t - e("millet", 0.6), rot=-3)
    tx = t - e("millet", 0.6) - 0.5
    if tx > 0:
        dr = ImageDraw.Draw(base, "RGBA"); k1 = ease(tx / 0.25); k2 = ease((tx - 0.25) / 0.25)
        L, R, T0, B0 = W / 2 - 300, W / 2 + 300, 540, 700
        dr.line([(L, T0), (L + (R - L) * k1, T0 + (B0 - T0) * k1)], fill=(200, 25, 25, 255), width=16)
        if k2 > 0: dr.line([(R, T0), (R - (R - L) * k2, T0 + (B0 - T0) * k2)], fill=(200, 25, 25, 255), width=16)
    c2 = stamp_card(["DEVLET", "VE HANEDAN"], 760, 240, RED, seed=52, sizes=[96, 56], bg=(240, 228, 196, 240))
    paste_pop(base, c2, W / 2, 960, t - e("devlet", 2.4), rot=2)
    return base.convert("RGB")

SOGUT = (30.18, 40.02)
def t3(t, dur):  # Osman Bey, Türkmen beyi
    p = ease(t / 2.0)
    cx0, cy0 = P(35, 0)[0], P(0, 39)[1]
    sx, sy = P(*SOGUT)
    cam = camera(cx0 + (sx - cx0) * p, cy0 + (sy + 80 - cy0) * p, 2200 - 1100 * p)
    base = render_map(cam).convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    x, y = to_screen(cam, *SOGUT)
    if t > 1.6: pulse(dr, x, y, t, color=RED)
    city_dot(dr, x, y, "Söğüt · 1299", t - 1.6, color=RED, labelside="u", size=56)
    title_band(base, "OSMAN BEY", t - 0.3, y=290, size=80, col=INK, sub="ANADOLU'DAKİ TÜRKMEN BEYLERİNDEN")
    paste_pop(base, stamp_card(["KURANLAR DA", "TÜRK'TÜ"], 760, 240, RED, seed=53, sizes=[60, 100], bg=(240, 228, 196, 240)),
              W / 2, 1200, t - e("turktu", 4.0), rot=-2)
    return base.convert("RGB")

ORHON = (102.5, 47.5)
def stele(base, cx, cy, t, t0):
    if t < t0: return
    k = ease_out((t - t0) / 0.6)
    w, h = 300, 560; x0, y0 = cx - w / 2, cy - h / 2 + (1 - k) * 80
    st = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(st)
    d.rounded_rectangle([0, 0, w - 1, h - 1], 40, fill=(150, 140, 125, int(255 * k)), outline=(80, 70, 60, int(255 * k)), width=6)
    rng = np.random.default_rng(4)
    for col in range(4):                       # abstract carved strokes (not a transcription)
        xx = 50 + col * 65
        yy = 50
        while yy < h - 60:
            hgt = rng.integers(18, 34)
            kind = rng.integers(0, 4)
            c = (70, 60, 50, int(230 * k))
            if kind == 0: d.line([(xx, yy), (xx, yy + hgt)], fill=c, width=5)
            elif kind == 1: d.line([(xx - 10, yy), (xx, yy + hgt), (xx + 10, yy)], fill=c, width=5)
            elif kind == 2: d.line([(xx, yy), (xx, yy + hgt)], fill=c, width=5); d.line([(xx, yy + hgt / 2), (xx + 12, yy + 4)], fill=c, width=5)
            else: d.ellipse([xx - 8, yy, xx + 8, yy + hgt], outline=c, width=5)
            yy += hgt + 16
    base.alpha_composite(M.shadow(st), (int(x0 - 30 + 10), int(y0 - 30 + 14))); base.alpha_composite(st, (int(x0), int(y0)))

def t4(t, dur):  # Göktürk 552, Orhun
    p = ease(t / 2.4)
    cx0, cy0 = P(40, 0)[0], P(0, 42)[1]
    ox, oy = P(*ORHON)
    cam = camera(cx0 + (ox - 200 - cx0) * p, cy0 + (oy + 100 - cy0) * p, 3000 - 1300 * p)
    base = render_map(cam).convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    x, y = to_screen(cam, *ORHON)
    if t < e("orhun", 4.6) - 0.2: city_dot(dr, x, y, "Orhun Vadisi", t - 1.8, color=(40, 110, 175), labelside="l", size=48)
    title_band(base, "552 · GÖKTÜRK", t - e("y552", 1.0), y=290, size=84, col=(40, 110, 175), sub="TÜRK, OSMANLI'DAN ÇOK ÖNCE VARDI")
    if t > e("orhun", 4.6) - 0.2:
        dim = Image.new("RGBA", (W, H), (20, 13, 8, int(120 * clamp((t - e("orhun", 4.6) + 0.2) / 0.4)))); base.alpha_composite(dim)
        stele(base, W / 2, 900, t, e("orhun", 4.6))
        paste_pop(base, stamp_card(["ORHUN YAZITLARI", "8. YÜZYIL"], 760, 210, INK, seed=54, sizes=[62, 46], bg=(240, 228, 196, 240)),
                  W / 2, 1290, t - e("orhun", 4.6) - 0.5, rot=-2)
    return base.convert("RGB")

ERAS = [("GÖKTÜRK", 552, 744, (40, 110, 175)), ("UYGUR", 744, 840, (70, 130, 110)), ("KARAHANLI", 840, 1212, (120, 100, 60)),
        ("SELÇUKLU", 1037, 1308, (110, 70, 120)), ("OSMANLI", 1299, 1922, (200, 16, 46)), ("CUMHURİYET", 1923, 2026, (160, 30, 40))]
def t5(t, dur):  # vertical timeline
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    a = int(255 * clamp(t / 0.3))
    spaced_text(dr, (W / 2, 230), "BİNLERCE YILLIK HİKÂYE", font(FB, 62), INK + (a,), sp=4)
    y0, y1, X = 340, 1330, 150
    def Y(yr): return y0 + (yr - 500) / (2030 - 500) * (y1 - y0)
    dr.line([(X, y0), (X, y1)], fill=INK + (a,), width=6)
    for yr in (600, 800, 1000, 1200, 1400, 1600, 1800, 2000):
        dr.line([(X - 14, Y(yr)), (X + 14, Y(yr))], fill=INK + (a,), width=4)
        dr.text((X - 26, Y(yr)), str(yr), font=font(FB, 28), fill=INK + (int(a * 0.8),), anchor="rm")
    for i, (name, a0, a1, col) in enumerate(ERAS):
        t0 = e("era%d" % i, 0.5 + i * 0.9)
        if t < t0: continue
        k = ease((t - t0) / 0.5)
        ya, yb = Y(a0), Y(a0) + (Y(a1) - Y(a0)) * k
        bx = X + 40 if i % 2 == 0 else X + 290
        hl = name == "OSMANLI" and t > e("sayfa", 6.5)
        dr.rounded_rectangle([bx, ya, bx + 230, max(ya + 4, yb)], 12, fill=col + (255,),
                             outline=(GOLD + (255,)) if hl else None, width=8 if hl else 0)
        al = int(255 * k); my = (Y(a0) + Y(a1)) / 2
        dr.line([(bx + 230, my), (X + 560, my)], fill=INK + (int(al * 0.5),), width=2)
        dr.text((X + 570, my - 4), name, font=font(FB, 40), fill=INK + (al,), anchor="lb")
        dr.text((X + 570, my + 4), f"{a0}–{a1 if a1 < 2026 else ''}", font=font(FI, 28), fill=INK + (int(al * 0.8),), anchor="lt")
    if t > e("sayfa", 6.5):
        paste_pop(base, stamp_card(["SADECE", "BİR SAYFA"], 500, 200, RED, seed=55, sizes=[48, 74], bg=(240, 228, 196, 245)),
                  X + 270, Y(1610), t - e("sayfa", 6.5), rot=-6)
    return base.convert("RGB")

def t6(t, dur):  # Biz Türk'üz
    base = SCREEN_PAPER.copy().convert("RGBA")
    rise = ease_out(t / 0.8)
    B.put_flag(base, TR_FLAG, W / 2, 760 + (1 - rise) * 160, t, amp=20)
    paste_pop(base, stamp_card(["BİZ TÜRK'ÜZ"], 820, 180, RED, seed=56, sizes=[110], bg=(240, 228, 196, 245)), W / 2, 1180, t - e("turkuz", 1.6), rot=-3)
    dr = ImageDraw.Draw(base, "RGBA")
    if t > e("bizim", 2.8):
        k = int(255 * clamp((t - e("bizim", 2.8)) / 0.4))
        spaced_text(dr, (W / 2, 1350), "Osmanlı da bizim.", font(FI, 54), INK + (k,))
    return base.convert("RGB")

def t7(t, dur):  # Ne mutlu Türküm diyene
    base = Image.new("RGBA", (W, H), (13, 10, 7, 255))
    B.put_flag(base, TR_FLAG, W / 2, 900, t, amp=12, op=0.14)
    dr = ImageDraw.Draw(base, "RGBA")
    p = back(t / 0.5); s = int(84 * (0.6 + 0.4 * p)); a = int(255 * clamp(t / 0.3))
    spaced_text(dr, (W / 2, 820), "NE MUTLU", font(FB, s), CREAM + (a,), sp=8)
    spaced_text(dr, (W / 2, 940), "TÜRKÜM DİYENE", font(FB, s), (230, 70, 60, a), sp=6)
    if t > 1.2:
        k = int(255 * clamp((t - 1.2) / 0.5))
        spaced_text(dr, (W / 2, 1060), "— Atatürk, 1933", font(FI, 40), CREAM + (k,))
    return base.convert("RGB")

DUR = T.get("durs", [3.0, 5.5, 6.0, 9.0, 9.5, 6.0, 4.0])
SCENES = [("t1", t1, DUR[0]), ("t2", t2, DUR[1]), ("t3", t3, DUR[2]), ("t4", t4, DUR[3]), ("t5", t5, DUR[4]), ("t6", t6, DUR[5]), ("t7", t7, DUR[6])]
XF = 0.4
STARTS = []; _a = 0.0
for _n, _f, _d in SCENES: STARTS.append(_a); _a += _d
TOTAL = _a
IMPACTS = {"t1": [0.05], "t2": [e("millet", 0.6), e("devlet", 2.4)], "t3": [0.3, e("turktu", 4.0)], "t4": [e("y552", 1.0), e("orhun", 4.6) + 0.5],
           "t5": [e("sayfa", 6.5)], "t6": [e("turkuz", 1.6)], "t7": [0.05]}

B.SCENES, B.XF, B.STARTS, B.TOTAL, B.IMPACTS = SCENES, XF, STARTS, TOTAL, IMPACTS

def global_frame(T_):
    k = max(i for i, s0 in enumerate(STARTS) if s0 <= T_ + 1e-9)
    out = B.global_frame(T_)
    return out

if __name__ == "__main__":
    if sys.argv[1] == "frames":
        for ts in sys.argv[2:]: Image.fromarray(B.global_frame(float(ts))).save(os.path.join(OUT, f"tf_{ts}.png"))
    else:
        for k, sc in enumerate(SCENES):
            if sc[0] in sys.argv[2:]: B.render(k)
