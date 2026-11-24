"""Saha / Yakutistan (halklar sırası #2): bayraktaki beyaz güneş (14 Ekim 1992, 'Kuzey'in güneşi'); Oymyakon 6 Şubat 1933
-67,7 °C, insanların sürekli yaşadığı en soğuk yer; Sahalar Türk halkı, dilleri Saha Türkçesi; 'Yakut' adı Rusların kullandığı,
Tunguzların verdiği 'Yako' adından; kendilerine 'Saha' derler.
Kaynaklar: Wikipedia 'Flag of the Sakha Republic'; FOTW ru-14; WMO Weather & Climate Extremes (Asia lowest temp);
Guinness WR 'Lowest temperature inhabited'; Wikipedia 'Yakuts'; Britannica 'Sakha'; Küre Ansiklopedisi 'Yakutlar' (A. Taşağıl).
Şablon: v_2026-11-23_kazan.py."""
import os, sys, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from make import (W, H, FPS, OUT, SCREEN_PAPER, DESK, stamp_card, paste_pop, shadow, spaced_text, font, FB, FI, INK, RED,
                  CREAM, ease, ease_out, back, clamp, finish, dust)
import bayrak as B

SP = 1.0
PAPER_DARK = Image.fromarray((np.asarray(DESK, np.float32) * 0.45).astype(np.uint8))
NIGHT = Image.fromarray(np.clip(np.asarray(DESK, np.float32) * np.array([0.22, 0.27, 0.40]), 0, 255).astype(np.uint8))
SKY = Image.fromarray(np.clip(np.asarray(SCREEN_PAPER, np.float32) * np.array([0.8, 0.9, 1.04]), 0, 255).astype(np.uint8))
BG = (240, 228, 196, 240)
GOLD = (226, 170, 90)
ICE = (200, 228, 245)
SBLUE = (60, 150, 215)
FLAG = Image.open(os.path.join(OUT, "flags_ru_png", "sa.png")).convert("RGBA")
_fc = {}
def flag(w):
    if w not in _fc:
        h = int(FLAG.height * w / FLAG.width); im = FLAG.resize((w, h), Image.LANCZOS)
        bd = Image.new("RGBA", (w + 4, h + 4), (40, 30, 20, 255)); bd.alpha_composite(im, (2, 2)); _fc[w] = bd
    return _fc[w]

def a_(t, t0, d=0.4): return int(255 * clamp((t - t0) / d))

def note(dr, text="Temsilî çizim", col=INK):
    dr.text((W - 40, H - 250), text, font=font(FI, 30), fill=col + (150,), anchor="rb")

_SN = np.random.default_rng(3)
FLAKES = np.stack([_SN.uniform(0, W, 160), _SN.uniform(0, H, 160), _SN.uniform(2, 7, 160), _SN.uniform(60, 220, 160)], 1)
def snow(dr, t, a=220):
    for x, y, r, v in FLAKES:
        yy = (y + v * t) % H; xx = (x + 30 * math.sin(t * 0.8 + y)) % W
        dr.ellipse([xx - r, yy - r, xx + r, yy + r], fill=(240, 246, 255, a))

def hut(dr, x, by, s, t):
    dr.rectangle([x - 90 * s, by - 120 * s, x + 90 * s, by], fill=(70, 50, 38, 255))
    dr.polygon([(x - 110 * s, by - 120 * s), (x + 110 * s, by - 120 * s), (x, by - 210 * s)], fill=(235, 242, 250, 255))
    dr.rectangle([x - 30 * s, by - 80 * s, x + 10 * s, by - 40 * s], fill=(255, 200, 110, 255))
    for k in range(6):  # smoke column
        ph = (t * 0.6 + k / 6) % 1
        r = (14 + 40 * ph) * s; yy = by - 210 * s - 40 * s - ph * 420 * s; xx = x + 50 * s + 40 * s * math.sin(ph * 4 + x)
        dr.ellipse([xx - r, yy - r, xx + r, yy + r], fill=(210, 220, 232, int(150 * (1 - ph))))

def thermo(dr, x, y0, h, level, a=255):
    """Termometre: level 0 (üst) .. 1 (alt-en soğuk)."""
    dr.rounded_rectangle([x - 34, y0, x + 34, y0 + h], 34, fill=(240, 244, 250, a), outline=(40, 50, 70, a), width=5)
    dr.ellipse([x - 62, y0 + h - 40, x + 62, y0 + h + 84], fill=(240, 244, 250, a), outline=(40, 50, 70, a), width=5)
    dr.ellipse([x - 46, y0 + h - 24, x + 46, y0 + h + 68], fill=(40, 120, 210, a))
    top = y0 + 30 + (h - 60) * level
    dr.rectangle([x - 14, top, x + 14, y0 + h], fill=(40, 120, 210, a))
    for i in range(9):
        yy = y0 + 40 + i * (h - 80) / 8
        dr.line([(x + 40, yy), (x + 70, yy)], fill=(230, 236, 245, a), width=4)

def s1(t, dur):  # hook: white sun on the flag
    base = SKY.copy().convert("RGBA")
    B.put_flag(base, flag(940), W / 2, 900, t, amp=12)
    dr = ImageDraw.Draw(base, "RGBA")
    p = back(t / 0.3); s = int(104 * (0.85 + 0.15 * p))
    spaced_text(dr, (W / 2, 250), "BU GÜNEŞ", font(FB, max(10, s)), INK + (255,), sp=6, stroke=3, sfill=(245, 235, 211))
    spaced_text(dr, (W / 2, 380), "NEDEN BEYAZ?", font(FB, max(10, s)), RED + (255,), sp=6, stroke=3, sfill=(245, 235, 211))
    # ring around sun (sun is left-center of flag)
    if t > 0.9:
        k = ease(clamp((t - 0.9) / 0.6)); cx, cy = W / 2 - 470 + 940 * 0.5, 900 - 235 + 470 * 0.375
        r = 150 + 30 * math.sin(t * 5)
        dr.arc([cx - r, cy - r, cx + r, cy + r], -90, -90 + 360 * k, fill=RED + (255,), width=10)
    if t > 0.6: dr.text((W / 2, 1180), "Saha (Yakutistan) bayrağı, 1992", font=font(FI, 44), fill=INK + (a_(t, 0.6, 0.3),), anchor="mm")
    return base.convert("RGB")

def s2(t, dur):  # coldest inhabited place: Oymyakon, 1933, -67.7
    base = NIGHT.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    dr.polygon([(0, 1100), (260, 900), (520, 1080), (760, 860), (1080, 1060), (1080, 1400), (0, 1400)], fill=(150, 170, 200, 255))
    dr.rectangle([0, 1180, W, H], fill=(225, 234, 244, 255))
    hut(dr, 230, 1250, 0.9, t); hut(dr, 470, 1230, 0.6, t + 0.3)
    lvl = 0.15 + 0.8 * ease(clamp((t - 6.0) / 2.6))
    thermo(dr, 840, 560, 560, lvl)
    snow(dr, t)
    p = back(t / 0.4); s = int(60 * (0.6 + 0.4 * p))
    spaced_text(dr, (W / 2, 200), "İNSANLARIN YAŞADIĞI", font(FB, max(10, s)), CREAM + (a_(t, 0, 0.2),), sp=3, stroke=3, sfill=(20, 26, 40))
    spaced_text(dr, (W / 2, 300), "EN SOĞUK YER", font(FB, max(10, int(s * 1.5))), ICE + (a_(t, 0, 0.2),), sp=5, stroke=3, sfill=(20, 26, 40))
    if t > 4.3: paste_pop(base, stamp_card(["OYMYAKON"], 470, 140, RED, seed=1, sizes=[74], bg=BG), 330, 560, t - 4.3, rot=-4)
    if t > 5.4: paste_pop(base, stamp_card(["6 ŞUBAT 1933"], 470, 120, RED, seed=2, sizes=[56], bg=BG), 330, 720, t - 5.4, rot=3)
    if t > 7.9:
        k = clamp((t - 7.9) / 0.25)
        dr = ImageDraw.Draw(base, "RGBA")
        spaced_text(dr, (W / 2 - 90, 950), "−67,7 °C", font(FB, int(120 * (0.7 + 0.3 * back(k)))), (40, 120, 210, int(255 * k)), sp=2,
                    stroke=6, sfill=(245, 248, 252))
    return base.convert("RGB")

def s3(t, dur):  # Saha Republic: a Turkic people
    base = SCREEN_PAPER.copy().convert("RGBA")
    B.put_flag(base, flag(820), W / 2, 830, t, amp=14)
    dr = ImageDraw.Draw(base, "RGBA")
    p = back(t / 0.4); s = int(92 * (0.6 + 0.4 * p))
    spaced_text(dr, (W / 2, 230), "SAHA", font(FB, max(10, int(s * 1.4))), INK + (a_(t, 0, 0.2),), sp=10)
    spaced_text(dr, (W / 2, 360), "CUMHURİYETİ", font(FB, max(10, s)), RED + (a_(t, 0, 0.2),), sp=6)
    if t > 0.5: dr.text((W / 2, 1100), "Rusya Federasyonu içinde", font=font(FI, 44), fill=INK + (a_(t, 0.5, 0.3),), anchor="mm")
    if 3.6 < t < 5.9: paste_pop(base, stamp_card(["BİR TÜRK", "HALKI"], 520, 210, RED, seed=3, sizes=[76, 76], bg=BG), W / 2, 1240, t - 3.6, rot=-3)
    if t > 5.9: paste_pop(base, stamp_card(["SAHA", "TÜRKÇESİ"], 520, 210, RED, seed=4, sizes=[76, 76], bg=BG), W / 2, 1240, t - 5.9, rot=3)
    return base.convert("RGB")

def label(base, txt, sub, cx, cy, t, col, crossed=0.0):
    dr = ImageDraw.Draw(base, "RGBA")
    k = back(clamp(t / 0.35)); s = int(150 * (0.6 + 0.4 * k))
    spaced_text(dr, (cx, cy), txt, font(FB, max(10, s)), col + (a_(t, 0, 0.15),), sp=8, stroke=4, sfill=(245, 235, 211))
    if sub: dr.text((cx, cy + 120), sub, font=font(FI, 52), fill=INK + (a_(t, 0.2, 0.3),), anchor="mm")
    if crossed > 0:
        w = font(FB, 150).getlength(txt) + 8 * len(txt) + 40
        dr.line([(cx - w / 2, cy + 10), (cx - w / 2 + w * crossed, cy - 10)], fill=RED + (230,), width=14)

def s4(t, dur):  # Russians call them Yakut, from Tungus 'Yako'
    base = PAPER_DARK.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    spaced_text(dr, (W / 2, 230), "RUSLAR DER Kİ:", font(FB, 70), CREAM + (a_(t, 0, 0.25),), sp=4)
    if t > 0.95:
        dr.rounded_rectangle([110, 470, W - 110, 860], 30, fill=BG)
        label(base, "YAKUT", "", W / 2, 640, t - 0.95, INK)
    if t > 3.0:
        dr = ImageDraw.Draw(base, "RGBA")
        dr.text((W / 2, 980), "Bu ad, komşu Tunguzların", font=font(FI, 56), fill=CREAM + (a_(t, 3.0, 0.3),), anchor="mm")
        dr.text((W / 2, 1060), "verdiği “Yako” adından gelir", font=font(FI, 56), fill=CREAM + (a_(t, 3.2, 0.3),), anchor="mm")
    if t > 3.4: paste_pop(base, stamp_card(["DIŞARIDAN", "VERİLEN AD"], 560, 200, RED, seed=5, sizes=[66, 66], bg=BG), W / 2, 1215, t - 3.4, rot=-3)
    return base.convert("RGB")

def s5(t, dur):  # they call themselves Saha
    base = SKY.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    spaced_text(dr, (W / 2, 230), "KENDİLERİNE İSE:", font(FB, 70), INK + (a_(t, 0, 0.25),), sp=4)
    dr.rounded_rectangle([110, 470, W - 110, 860], 30, fill=(236, 226, 200, 255))
    label(base, "YAKUT", "", W / 2, 640, 1.0, (120, 104, 90), crossed=ease(clamp(t / 0.5)))
    if t > 1.45:
        base2 = base; dr = ImageDraw.Draw(base2, "RGBA")
        dr.rounded_rectangle([110, 470, W - 110, 860], 30, fill=(236, 226, 200, int(255 * clamp((t - 1.45) / 0.15))))
        label(base2, "SAHA", "", W / 2, 640, t - 1.45, SBLUE)
    f = flag(520); base.alpha_composite(f, (int(W / 2 - f.width / 2), 960))
    return base.convert("RGB")

def s6(t, dur):  # ending question
    base = Image.new("RGBA", (W, H), (13, 10, 7, 255))
    if t > 0:
        f = flag(700); f2 = f.copy(); a = np.asarray(f2).copy(); a[..., 3] = (a[..., 3] * 0.22 * clamp(t / 1.2)).astype(np.uint8)
        base.alpha_composite(Image.fromarray(a), (int(W / 2 - f.width / 2), 1030))
    dr = ImageDraw.Draw(base, "RGBA")
    spaced_text(dr, (W / 2, 520), "YAKUT mu,", font(FB, 80), (200, 190, 170, a_(t, 0.0, 0.3)), sp=4)
    spaced_text(dr, (W / 2, 630), "SAHA mı?", font(FB, 80), ICE + (a_(t, 0.2, 0.3),), sp=4)
    if t > 0.6:
        p = back((t - 0.6) / 0.45); s = int(84 * (0.6 + 0.4 * p))
        spaced_text(dr, (W / 2, 800), "BİR HALKI HANGİ", font(FB, max(10, s)), GOLD + (a_(t, 0.6, 0.25),), sp=5)
        spaced_text(dr, (W / 2, 910), "ADIYLA ÇAĞIRMALI?", font(FB, max(10, s)), (230, 80, 60, a_(t, 0.6, 0.25)), sp=4)
    return base.convert("RGB")

_B = [0.0, 3.4, 14.4, 21.5, 27.35, 29.95, 33.6]
_F = [s1, s2, s3, s4, s5, s6]
SCENES = [(f"s{i+1}", f, (_B[i + 1] - _B[i]) / SP) for i, f in enumerate(_F)]
XF = 0.3
STARTS = []; _a = 0.0
for _n, _f, _d in SCENES: STARTS.append(_a); _a += _d
TOTAL = _a
IMPACTS = {"s2": [4.3, 5.4, 7.9], "s3": [3.6, 5.9], "s4": [0.95, 3.4], "s5": [1.45], "s6": [0.6]}

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
