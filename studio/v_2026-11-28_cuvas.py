"""Çuvaşistan (halklar sırası #3): bayrak 29 Nisan 1992 (hayat ağacı + 3 güneş); Çuvaşça bugün yaşayan tek Oğur Türkçesi,
diğer Türkler anlayamaz; Çuvaşlar Volga Bulgarlarının torunları olarak bilinir; Ortak Türkçe z ~ Çuvaşça r (kız ~ хӗр),
ş ~ l (kış ~ хӗл); Çuvaşların çoğu Ortodoks Hristiyan.
Kaynaklar: Wikipedia 'Flag of Chuvashia', 'Chuvash language', 'Chuvash people'; FOTW ru-21; flaggenlexikon.de;
Britannica 'Chuvash language', 'Chuvash'; TDV İslâm Ansiklopedisi 'Çuvaşlar' (N. Yüce); F. Ersoy (2013) 'Çuvaşçaya Özgü
Bazı Özellikler Üzerine', Turkish Studies 8/9.
Şablon: v_2026-11-25_saha.py."""
import os, sys, math, subprocess
import numpy as np
from PIL import Image, ImageDraw
from make import (W, H, FPS, OUT, SCREEN_PAPER, DESK, stamp_card, paste_pop, spaced_text, font, FB, FI, INK, RED,
                  CREAM, ease, back, clamp, finish, dust)
import bayrak as B

SP = 1.0
PAPER_DARK = Image.fromarray((np.asarray(DESK, np.float32) * 0.45).astype(np.uint8))
WARM = Image.fromarray(np.clip(np.asarray(SCREEN_PAPER, np.float32) * np.array([1.03, 0.98, 0.86]), 0, 255).astype(np.uint8))
BG = (240, 228, 196, 240)
GOLD = (226, 170, 90)
CRED = (160, 38, 14)
FLAG = Image.open(os.path.join(OUT, "flags_ru_png", "cu.png")).convert("RGBA")
_fc = {}
def flag(w):
    if w not in _fc:
        h = int(FLAG.height * w / FLAG.width); im = FLAG.resize((w, h), Image.LANCZOS)
        bd = Image.new("RGBA", (w + 4, h + 4), (40, 30, 20, 255)); bd.alpha_composite(im, (2, 2)); _fc[w] = bd
    return _fc[w]

def a_(t, t0, d=0.4): return int(255 * clamp((t - t0) / d))

def ring(dr, cx, cy, r, k, t):
    r = r + 12 * math.sin(t * 5)
    dr.arc([cx - r, cy - r, cx + r, cy + r], -90, -90 + 360 * k, fill=RED + (255,), width=10)

def s1(t, dur):  # hook
    base = WARM.copy().convert("RGBA")
    B.put_flag(base, flag(940), W / 2, 880, t, amp=12)
    dr = ImageDraw.Draw(base, "RGBA")
    p = back(t / 0.3); s = int(80 * (0.85 + 0.15 * p))
    spaced_text(dr, (W / 2, 240), "BİR TÜRK HALKI…", font(FB, max(10, s)), INK + (255,), sp=4, stroke=3, sfill=(245, 235, 211))
    spaced_text(dr, (W / 2, 360), "AMA DİLİNİ", font(FB, max(10, s)), RED + (255,), sp=4, stroke=3, sfill=(245, 235, 211))
    spaced_text(dr, (W / 2, 470), "TÜRKLER ANLAMIYOR", font(FB, max(10, int(s * 0.82))), RED + (255,), sp=3, stroke=3, sfill=(245, 235, 211))
    if t > 0.6: dr.text((W / 2, 1210), "Çuvaşistan bayrağı, 1992", font=font(FI, 46), fill=INK + (a_(t, 0.6, 0.3),), anchor="mm")
    return base.convert("RGB")

def s2(t, dur):  # Chuvashia: tree of life + 3 suns
    base = SCREEN_PAPER.copy().convert("RGBA")
    fw = 900; cx0, cy0 = W / 2, 820
    B.put_flag(base, flag(fw), cx0, cy0, t, amp=10)
    dr = ImageDraw.Draw(base, "RGBA")
    p = back(t / 0.4); s = int(96 * (0.6 + 0.4 * p))
    spaced_text(dr, (W / 2, 230), "ÇUVAŞİSTAN", font(FB, max(10, s)), INK + (a_(t, 0, 0.2),), sp=8)
    if t > 0.3: dr.text((W / 2, 340), "Rusya Federasyonu içinde", font=font(FI, 44), fill=INK + (a_(t, 0.3, 0.3),), anchor="mm")
    fh = fw * 563 / 900; x0 = cx0 - fw / 2; y0 = cy0 - fh / 2
    if t > 1.1: ring(dr, x0 + fw * 0.5, y0 + fh * 0.47, 150, ease(clamp((t - 1.1) / 0.5)), t)
    if 1.1 < t < 2.5: paste_pop(base, stamp_card(["HAYAT AĞACI"], 560, 130, RED, seed=1, sizes=[70], bg=BG), W / 2, 1240, t - 1.1, rot=-3)
    if t > 2.5: paste_pop(base, stamp_card(["3 GÜNEŞ"], 460, 130, RED, seed=2, sizes=[74], bg=BG), W / 2, 1240, t - 2.5, rot=3)
    return base.convert("RGB")

def box(dr, cx, cy, w, h, txt, sub, col, a, fill=BG, fs=42):
    dr.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], 22, fill=fill[:3] + (int(fill[3] * a / 255),),
                         outline=col + (a,), width=5)
    dr.text((cx, cy - (18 if sub else 0)), txt, font=font(FB, fs), fill=col + (a,), anchor="mm")
    if sub: dr.text((cx, cy + 32), sub, font=font(FI, 30), fill=INK + (a,), anchor="mm")

def s3(t, dur):  # family tree: the only living Oghur language; Volga Bulgar descent
    base = WARM.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    spaced_text(dr, (W / 2, 210), "TÜRK DİLLERİ", font(FB, 84), INK + (a_(t, 0, 0.25),), sp=6)
    a1 = a_(t, 0.2, 0.3); a2 = a_(t, 0.6, 0.3)
    dr.line([(W / 2, 270), (W / 2, 330)], fill=INK + (a1,), width=6)
    dr.line([(285, 330), (790, 330)], fill=INK + (a1,), width=6)
    dr.line([(285, 330), (285, 400)], fill=INK + (a1,), width=6); dr.line([(790, 330), (790, 400)], fill=INK + (a1,), width=6)
    box(dr, 285, 470, 470, 140, "ORTAK TÜRKÇE", "Türkçe, Azerice, Kazakça…", INK, a1)
    box(dr, 790, 470, 420, 140, "OĞUR KOLU", "iki ana koldan biri", RED, a1)
    dr.line([(790, 540), (790, 620)], fill=RED + (a2,), width=6)
    dr.line([(640, 620), (900, 620)], fill=RED + (a2,), width=6)
    dr.line([(640, 620), (640, 680)], fill=RED + (a2,), width=6); dr.line([(900, 620), (900, 680)], fill=RED + (a2,), width=6)
    box(dr, 610, 750, 260, 130, "Bulgarca", "soyu tükendi", (120, 104, 90), a2, fill=(225, 215, 190, 230))
    k = clamp((t - 1.6) / 0.3)
    if t > 1.6:
        box(dr, 905, 750, 270, 130, "ÇUVAŞÇA", "yaşıyor", RED, int(255 * k))
        if t > 1.9:
            r = 160 + 6 * math.sin(t * 5); cx, cy = 905, 750
            dr.ellipse([cx - r, cy - r * 0.62, cx + r, cy + r * 0.62], outline=RED + (255,), width=8)
    if t > 2.9: paste_pop(base, stamp_card(["BUGÜN YAŞAYAN", "TEK OĞUR TÜRKÇESİ"], 700, 210, RED, seed=3, sizes=[60, 60], bg=BG),
                          W / 2, 990, t - 2.9, rot=-3)
    if t > 3.6:
        dr = ImageDraw.Draw(base, "RGBA")
        dr.text((W / 2, 1180), "Çuvaşlar: Volga Bulgarlarının", font=font(FI, 56), fill=INK + (a_(t, 3.6, 0.3),), anchor="mm")
        dr.text((W / 2, 1260), "torunları olarak bilinir", font=font(FI, 56), fill=INK + (a_(t, 3.8, 0.3),), anchor="mm")
    return base.convert("RGB")

def pair(base, cy, tr, cv, lat, t1, t2, t):
    dr = ImageDraw.Draw(base, "RGBA")
    if t > t1:
        k = back(clamp((t - t1) / 0.3)); s = int(120 * (0.6 + 0.4 * k))
        spaced_text(dr, (270, cy), tr, font(FB, max(10, s)), CREAM + (a_(t, t1, 0.15),), sp=4, stroke=3, sfill=(20, 14, 9))
        dr.text((270, cy + 100), "Türkçe", font=font(FI, 42), fill=CREAM + (a_(t, t1, 0.3),), anchor="mm")
    if t > t2 - 0.4:
        k = clamp((t - t2 + 0.4) / 0.4)
        x1 = 450; x2 = 450 + 170 * k
        dr.line([(x1, cy), (x2, cy)], fill=GOLD + (255,), width=10)
        if k > 0.95: dr.polygon([(x2 + 30, cy), (x2 - 6, cy - 24), (x2 - 6, cy + 24)], fill=GOLD + (255,))
    if t > t2:
        k = back(clamp((t - t2) / 0.3)); s = int(120 * (0.6 + 0.4 * k))
        spaced_text(dr, (830, cy), cv, font(FB, max(10, s)), (240, 90, 60, a_(t, t2, 0.15)), sp=4, stroke=3, sfill=(20, 14, 9))
        dr.text((830, cy + 100), f"Çuvaşça ({lat})", font=font(FI, 42), fill=CREAM + (a_(t, t2, 0.3),), anchor="mm")

def s4(t, dur):  # kız ~ хӗр, kış ~ хӗл
    base = PAPER_DARK.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    spaced_text(dr, (W / 2, 220), "AYNI KÖK, FARKLI SES", font(FB, 64), CREAM + (a_(t, 0, 0.25),), sp=3)
    dr.text((W / 2, 310), "Türkçedeki z → r,  ş → l olur", font=font(FI, 48), fill=GOLD + (a_(t, 0.3, 0.3),), anchor="mm")
    pair(base, 560, "KIZ", "ХӖР", "hĕr", 0.36, 1.84, t)
    pair(base, 900, "KIŞ", "ХӖЛ", "hĕl", 3.0, 4.56, t)
    return base.convert("RGB")

def church(dr, cx, by, s, a=255):
    col = (70, 52, 40, a)
    dr.rectangle([cx - 150 * s, by - 260 * s, cx + 150 * s, by], fill=col)
    dr.rectangle([cx - 60 * s, by - 420 * s, cx + 60 * s, by - 260 * s], fill=col)
    dr.ellipse([cx - 80 * s, by - 540 * s, cx + 80 * s, by - 400 * s], fill=(200, 150, 60, a))
    dr.polygon([(cx - 40 * s, by - 520 * s), (cx + 40 * s, by - 520 * s), (cx, by - 600 * s)], fill=(200, 150, 60, a))
    dr.line([(cx, by - 600 * s), (cx, by - 700 * s)], fill=(200, 150, 60, a), width=max(2, int(10 * s)))
    dr.line([(cx - 30 * s, by - 670 * s), (cx + 30 * s, by - 670 * s)], fill=(200, 150, 60, a), width=max(2, int(10 * s)))
    dr.rounded_rectangle([cx - 36 * s, by - 150 * s, cx + 36 * s, by], int(30 * s), fill=(250, 210, 120, a))
    for dx in (-100, 100):
        dr.rounded_rectangle([cx + dx * s - 20 * s, by - 210 * s, cx + dx * s + 20 * s, by - 130 * s], int(16 * s), fill=(250, 210, 120, a))

def s5(t, dur):  # most Chuvash are Orthodox Christians
    base = WARM.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    p = back(t / 0.4); s = int(76 * (0.6 + 0.4 * p))
    spaced_text(dr, (W / 2, 230), "ÇUVAŞLARIN ÇOĞU", font(FB, max(10, s)), INK + (a_(t, 0, 0.2),), sp=4)
    dr.rectangle([0, 1080, W, 1400], fill=(196, 178, 140, 255))
    church(dr, W / 2, 1100, 0.9 * (0.9 + 0.1 * ease(clamp(t / 1.0))), a_(t, 0, 0.4))
    f = flag(300); base.alpha_composite(f, (W - f.width - 60, 1150))
    if t > 1.2: paste_pop(base, stamp_card(["ORTODOKS", "HRİSTİYAN"], 560, 200, RED, seed=6, sizes=[70, 70], bg=BG),
                          W / 2 - 150, 1250, t - 1.2, rot=-3)
    dr = ImageDraw.Draw(base, "RGBA")
    dr.text((60, H - 260), "Temsilî çizim", font=font(FI, 30), fill=INK + (150,), anchor="lb")
    return base.convert("RGB")

def s6(t, dur):  # ending question
    base = Image.new("RGBA", (W, H), (13, 10, 7, 255))
    f = flag(700); a = np.asarray(f).copy(); a[..., 3] = (a[..., 3] * 0.22 * clamp(t / 1.2)).astype(np.uint8)
    base.alpha_composite(Image.fromarray(a), (int(W / 2 - f.width / 2), 1060))
    dr = ImageDraw.Draw(base, "RGBA")
    spaced_text(dr, (W / 2, 500), "BİR HALKI", font(FB, 72), (200, 190, 170, a_(t, 0.3, 0.3)), sp=4)
    spaced_text(dr, (W / 2, 600), "HALK YAPAN NE?", font(FB, 72), (200, 190, 170, a_(t, 1.6, 0.3)), sp=4)
    if t > 3.3:
        p = back((t - 3.3) / 0.45); s = int(120 * (0.6 + 0.4 * p))
        spaced_text(dr, (W / 2, 790), "DİLİ Mİ,", font(FB, max(10, s)), GOLD + (a_(t, 3.3, 0.2),), sp=5)
    if t > 4.1:
        p = back((t - 4.1) / 0.45); s = int(120 * (0.6 + 0.4 * p))
        spaced_text(dr, (W / 2, 930), "DİNİ Mİ?", font(FB, max(10, s)), (230, 80, 60, a_(t, 4.1, 0.2)), sp=5)
    return base.convert("RGB")

_B = [0.0, 5.78, 9.92, 16.16, 21.1, 24.32, 30.4]
_F = [s1, s2, s3, s4, s5, s6]
SCENES = [(f"s{i+1}", f, (_B[i + 1] - _B[i]) / SP) for i, f in enumerate(_F)]
XF = 0.3
STARTS = []; _a = 0.0
for _n, _f, _d in SCENES: STARTS.append(_a); _a += _d
TOTAL = _a
IMPACTS = {"s2": [1.1, 2.5], "s3": [1.6, 2.9], "s4": [1.84, 4.56], "s5": [1.2], "s6": [3.3, 4.1]}

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
    out = finish(im, SCENES[k][0] != "s6").astype(np.float32)
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
