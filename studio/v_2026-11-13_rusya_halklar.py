"""Reels: Rusya'nın halkları ve 21 cumhuriyetin bayrakları.
Kaynaklar: Wikipedia 'Ethnic groups in Russia' (2021 sayımı, 190+ halk; Tatar 2., Çeçen 3.), 'Republics of Russia' (21 tanınmış),
'Dagestan' (30+ halk, 14 resmî dil), 'Kalmykia' (Avrupa'da Budist çoğunluklu tek bölge, Oirat Moğolları ~1630 Volga),
'Sakha Republic' (3.083.523 km², Arjantin'den büyük). Bayraklar: github.com/russian-flags/regions (MIT) SVG → PNG."""
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw
from make import (W, H, OUT, SCREEN_PAPER, stamp_card, paste_pop, spaced_text, font, FB, FI, INK, RED, CREAM,
                  ease, ease_out, back, clamp, title_band, shadow)
import bayrak as B

FD = os.path.join(OUT, "flags_ru_png")
NAMES = {"ad": "Adigey", "al": "Altay", "ba": "Başkurdistan", "bu": "Buryatya", "ce": "Çeçenistan", "cu": "Çuvaşistan",
         "da": "Dağıstan", "in": "İnguşetya", "kb": "Kabardey-Balkar", "kc": "Karaçay-Çerkes", "kk": "Hakasya",
         "kl": "Kalmukya", "ko": "Komi", "kr": "Karelya", "me": "Mari El", "mo": "Mordovya", "se": "Kuzey Osetya",
         "sa": "Saha", "ta": "Tataristan", "ty": "Tuva", "ud": "Udmurtya"}
ORDER = ["ta", "ba", "ce", "cu", "da", "sa", "kl", "bu", "ty", "kk", "al", "kc", "kb", "in", "se", "ad", "kr", "ko", "ud", "me", "mo"]
_cache = {}
def flag(code, w):
    k = (code, w)
    if k not in _cache:
        im = Image.open(os.path.join(FD, code + ".png")).convert("RGBA")
        h = int(im.height * w / im.width); im = im.resize((w, h), Image.LANCZOS)
        bd = Image.new("RGBA", (w + 4, h + 4), (40, 30, 20, 255)); bd.alpha_composite(im, (2, 2)); _cache[k] = bd
    return _cache[k]

def flag_h(code, h):
    """Bayrağı sabit YÜKSEKLİĞE ölçekle (farklı oranlı bayraklar aynı hizada dursun)."""
    k = ("h", code, h)
    if k not in _cache:
        im = Image.open(os.path.join(FD, code + ".png")).convert("RGBA")
        w = int(im.width * h / im.height); im = im.resize((w, h), Image.LANCZOS)
        bd = Image.new("RGBA", (w + 4, h + 4), (40, 30, 20, 255)); bd.alpha_composite(im, (2, 2)); _cache[k] = bd
    return _cache[k]

def grid(base, t, t0, step, names=False, top=250, fh=120, rowh=148, colw=330):
    """3 sütun x 7 satır; her hücrede bayrak ortalı, hepsi aynı yükseklikte, isimler tek hizada."""
    cols = 3; cx0 = W / 2 - colw
    dr = ImageDraw.Draw(base, "RGBA")
    for i, c in enumerate(ORDER):
        ti = t0 + i * step
        if t < ti: continue
        k = ease_out(clamp((t - ti) / 0.25)); r, q = divmod(i, cols)
        im = flag_h(c, fh)
        cx = cx0 + q * colw; y = top + r * rowh + (1 - k) * 24
        if k < 1:
            a = np.asarray(im).copy(); a[..., 3] = (a[..., 3] * k).astype(np.uint8); im = Image.fromarray(a)
        base.alpha_composite(shadow(im, op=int(90 * k)), (int(cx - im.width / 2 - 18), int(y - 14)))
        base.alpha_composite(im, (int(cx - im.width / 2), int(y)))
        if names:
            spaced_text(dr, (cx, top + r * rowh + fh + 26), NAMES[c], font(FB, 27), INK + (int(255 * k),), sp=1)

def big_flag(base, code, t, cy=820, w=840):
    im = flag(code, w)
    B.put_flag(base, im, W / 2, cy + (1 - ease_out(clamp(t / 0.5))) * 50, t, amp=14)

def s1(t, dur):
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    if t < 3.7:
        a = int(255 * clamp(t / 0.15)); p = back(t / 0.45); s = int(96 * (0.75 + 0.25 * p))
        spaced_text(dr, (W / 2, 700), "RUSYA'DA", font(FB, s), INK + (a,), sp=8)
        spaced_text(dr, (W / 2, 830), "SADECE RUSLAR", font(FB, s), INK + (a,), sp=6)
        spaced_text(dr, (W / 2, 960), "MI YAŞIYOR?", font(FB, s), RED + (a,), sp=6)
        return base.convert("RGB")
    paste_pop(base, stamp_card(["190+", "HALK"], 520, 260, RED, seed=81, sizes=[120, 70], bg=(240, 228, 196, 245)),
              W / 2, 860 if t < 6.6 else -999, t - 4.4, rot=-4)
    if t >= 6.6:
        grid(base, t, 6.6, 0.1, top=250, fh=120, rowh=148)
        title_band(base, "21 CUMHURİYET · 21 BAYRAK", t - 8.7, y=150, size=58, col=RED)
    return base.convert("RGB")

def card(code, title, sub, stamps):
    def f(t, dur):
        base = SCREEN_PAPER.copy().convert("RGBA")
        big_flag(base, code, t, cy=720)
        title_band(base, title, t - 0.05, y=300, size=92, col=INK, sub=sub)
        for i, (lines, sizes, tt, y, col, rot, seed) in enumerate(stamps):
            nxt = stamps[i + 1][2] if i + 1 < len(stamps) else 1e9
            if t >= nxt: continue          # bir sonraki mühür gelince öncekini kaldır (altyazıya binmesin)
            paste_pop(base, stamp_card(lines, 760, 90 + 80 * len(lines), col, seed=seed, sizes=sizes, bg=(240, 228, 196, 245)),
                      W / 2, 1140, t - tt, rot=rot)
        return base.convert("RGB")
    return f

s2 = card("ta", "TATARİSTAN", "TATARLAR · 4,7 MİLYON", [(["RUSYA'NIN", "2. BÜYÜK HALKI"], [62, 72], 1.8, 1290, RED, -3, 82)])
s3 = card("ce", "ÇEÇENİSTAN", "ÇEÇENLER · 1,7 MİLYON", [(["3. SIRADA"], [96], 1.7, 1280, RED, 3, 83)])
s4 = card("da", "DAĞISTAN", "RUSYA'NIN EN KARMA CUMHURİYETİ", [(["30'DAN FAZLA", "HALK"], [64, 80], 2.3, 1240, RED, -3, 84),
                                                              (["14 RESMÎ DİL"], [80], 3.8, 1450, INK, 4, 85)])
s5 = card("kl", "KALMUKYA", "OİRAT MOĞOLLARI · 1600'LER", [(["AVRUPA'NIN TEK", "BUDİST BÖLGESİ"], [62, 66], 1.1, 1260, RED, -3, 86),
                                                         (["MOĞOL KÖKENLİ"], [72], 6.2, 1470, INK, 3, 87)])
s6 = card("sa", "SAHA (YAKUTİSTAN)", "3.083.523 KM²", [(["ARJANTİN'DEN", "BÜYÜK"], [66, 90], 1.5, 1280, RED, -4, 88)])

TURK = [("ba", 1.35), ("cu", 2.27), ("ty", 3.07), ("kk", 3.79), ("al", 4.67), ("kc", 5.55), ("kb", 6.51)]
def s7(t, dur):
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    title_band(base, "TÜRK HALKLARI", t - 0.1, y=250, size=96, col=RED)
    pos = [(W / 2 - 240, 540), (W / 2 + 240, 540), (W / 2 - 240, 830), (W / 2 + 240, 830), (W / 2 - 240, 1120), (W / 2 + 240, 1120), (W / 2, 1410)]
    for (c, tt), (x, y) in zip(TURK, pos):
        if t < tt: continue
        k = back(clamp((t - tt) / 0.35)); w = int(330 * max(0.2, k))
        im = flag(c, w)
        base.alpha_composite(shadow(im, op=90), (int(x - im.width / 2 - 18), int(y - im.height / 2 - 14)))
        base.alpha_composite(im, (int(x - im.width / 2), int(y - im.height / 2)))
        lbl = {"kc": "Karaçay", "kb": "Balkar"}.get(c, NAMES[c])
        spaced_text(dr, (x, y + 138), lbl, font(FB, 36), INK + (int(255 * clamp((t - tt) / 0.3)),), sp=2)
    return base.convert("RGB")

def s8(t, dur):
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    grid(base, t, 0.0, 0.04, names=True, top=250, fh=112, rowh=172)
    title_band(base, "BİR HALKLAR HARİTASI", t - 0.1, y=150, size=66, col=INK)
    if t > 3.0:
        k = clamp((t - 3.0) / 0.3); a = int(255 * k); p = back(clamp((t - 3.0) / 0.45))
        box = Image.new("RGBA", (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
        bd.rounded_rectangle([90, 1475, W - 90, 1690], 30, fill=(24, 16, 10, int(235 * k)), outline=(200, 160, 90, a), width=4)
        base.alpha_composite(box)
        dr = ImageDraw.Draw(base, "RGBA"); s_ = 0.8 + 0.2 * p
        spaced_text(dr, (W / 2, 1545), "SEN KAÇINI", font(FB, int(68 * s_)), (250, 240, 220, a), sp=6)
        spaced_text(dr, (W / 2, 1635), "TANIDIN?", font(FB, int(84 * s_)), (255, 196, 60, a), sp=8)
    return base.convert("RGB")

SCENES = [("r1", s1, 10.4), ("r2", s2, 4.2), ("r3", s3, 2.8), ("r4", s4, 5.2), ("r5", s5, 7.7), ("r6", s6, 2.95), ("r7", s7, 8.15), ("r8", s8, 7.4)]
XF = 0.35
STARTS = []; _a = 0.0
for _n, _f, _d in SCENES: STARTS.append(_a); _a += _d
TOTAL = _a
IMPACTS = {"r1": [0.05, 4.4, 8.7], "r2": [1.8], "r3": [1.7], "r4": [2.3, 3.8], "r5": [1.1, 6.2], "r6": [1.5],
           "r7": [x for _, x in TURK], "r8": [3.0]}
B.SCENES, B.XF, B.STARTS, B.TOTAL, B.IMPACTS = SCENES, XF, STARTS, TOTAL, IMPACTS

if __name__ == "__main__":
    if sys.argv[1] == "frames":
        for ts in sys.argv[2:]: Image.fromarray(B.global_frame(float(ts))).save(os.path.join(OUT, f"rf_{ts}.png"))
    else:
        for k, sc in enumerate(SCENES):
            if sc[0] in sys.argv[2:]: B.render(k)
