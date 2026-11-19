"""Tolstoy'un kaçışı ve Astapovo istasyonu (20 Kasım 1910). Şablon: v_2026-11-18_kopenick.py.
Zamanlar seslendirmenin orijinal hızına göre yazıldı; ses 1.1x hızlandırıldığı için SP ile bölünür."""
import os, sys, math, subprocess
import numpy as np
from PIL import Image, ImageDraw
from figures import put
from make import (W, H, FPS, OUT, SCREEN_PAPER, DESK, stamp_card, paste_pop, shadow, spaced_text, font, FB, FI, INK, RED,
                  CREAM, ease, ease_out, back, clamp, finish, dust)

SP = 1.1
PAPER_DARK = Image.fromarray((np.asarray(DESK, np.float32) * 0.45).astype(np.uint8))
NIGHT = Image.fromarray(np.clip(np.asarray(DESK, np.float32) * np.array([0.22, 0.25, 0.36]), 0, 255).astype(np.uint8))
BG = (240, 228, 196, 240)
GOLD = (226, 170, 90)
WIN = (255, 214, 120)

def a_(t, t0, d=0.4): return int(255 * clamp((t - t0) / d))

def note(dr, text="Temsilî çizim", col=INK):
    dr.text((W - 40, H - 250), text, font=font(FI, 30), fill=col + (150,), anchor="rb")

def house(dr, x0, y0, w, h, a=255, lit=True, wall=(70, 58, 52), roof=(40, 32, 30)):
    dr.rectangle([x0, y0, x0 + w, y0 + h], fill=wall + (a,))
    dr.polygon([(x0 - 40, y0), (x0 + w + 40, y0), (x0 + w / 2, y0 - h * 0.55)], fill=roof + (a,))
    for i in range(3):
        x = x0 + w * (0.18 + i * 0.28)
        c = (WIN if (lit and i == 1) else (30, 26, 30)) + (a,)
        dr.rectangle([x, y0 + h * 0.25, x + w * 0.16, y0 + h * 0.55], fill=c)
        dr.line([(x + w * 0.08, y0 + h * 0.25), (x + w * 0.08, y0 + h * 0.55)], fill=(40, 30, 26, a), width=4)

def clock(dr, cx, cy, r, hh, mm, a=255):
    dr.ellipse([cx - r - 18, cy - r - 18, cx + r + 18, cy + r + 18], fill=(40, 32, 26, a))
    dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(246, 238, 216, a))
    for i in range(12):
        ang = math.radians(i * 30 - 90); r0 = r * (0.80 if i % 3 else 0.72)
        dr.line([(cx + r0 * math.cos(ang), cy + r0 * math.sin(ang)), (cx + r * 0.92 * math.cos(ang), cy + r * 0.92 * math.sin(ang))],
                fill=INK + (a,), width=10 if i % 3 == 0 else 5)
    am = math.radians(mm * 6 - 90); ah = math.radians((hh % 12 + mm / 60) * 30 - 90)
    dr.line([(cx, cy), (cx + r * 0.5 * math.cos(ah), cy + r * 0.5 * math.sin(ah))], fill=INK + (a,), width=18)
    dr.line([(cx, cy), (cx + r * 0.8 * math.cos(am), cy + r * 0.8 * math.sin(am))], fill=INK + (a,), width=10)
    dr.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], fill=RED + (a,))

# ---------- scenes (t = local seconds in ORIGINAL voice time) ----------
def s1(t, dur):  # hook
    base = NIGHT.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    for i in range(40):  # stars
        x = (i * 263) % W; y = 120 + (i * 151) % 520; dr.ellipse([x, y, x + 4, y + 4], fill=(240, 230, 200, 120))
    house(dr, 120, 820, 520, 300, lit=True)
    walk = ease(t / 6.0)
    put(base, "tolstoy", 840 - walk * 120, 1250, 720, dark=0.4)
    dr = ImageDraw.Draw(base, "RGBA")
    p = back(t / 0.35); s = int(112 * (0.6 + 0.4 * p))
    spaced_text(dr, (W / 2, 290), "82 YAŞINDA", font(FB, max(10, s)), CREAM + (255,), sp=6)
    spaced_text(dr, (W / 2, 420), "EVİNDEN KAÇTI", font(FB, max(10, int(s * 0.86))), (232, 90, 70, 255), sp=6)
    if t > 4.3:
        paste_pop(base, stamp_card(["BİR GECE"], 520, 150, RED, seed=1, sizes=[76], bg=BG), W / 2, 1330, t - 4.3, rot=-4)
    note(ImageDraw.Draw(base, "RGBA"), col=CREAM)
    return base.convert("RGB")

def card_portrait():
    w, h = 620, 800
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, h], fill=(244, 232, 200, 255), outline=(120, 96, 60, 255), width=6)
    d.rectangle([90, 60, w - 90, 560], fill=(214, 196, 156, 255), outline=INK + (255,), width=4)
    put(im, "tolstoy", w / 2, 1180, 1100, shadow=False)
    d.rectangle([0, 562, w, h], fill=(244, 232, 200, 255)); d.rectangle([0, 0, w, h], outline=(120, 96, 60, 255), width=6)
    d.rectangle([90, 60, w - 90, 560], outline=INK + (255,), width=4)
    spaced_text(d, (w / 2, 630), "LEV TOLSTOY", font(FB, 60), RED + (255,), sp=4)
    spaced_text(d, (w / 2, 710), "Savaş ve Barış'ın yazarı", font(FI, 38), INK + (255,))
    return im

def s2(t, dur):  # 1910, Tolstoy, before dawn, only his doctor
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    p = back(t / 0.45); s = int(120 * (0.6 + 0.4 * p))
    spaced_text(dr, (W / 2, 250), "1910", font(FB, max(10, s)), RED + (a_(t, 0, 0.2),), sp=10)
    if t > 1.6:
        rise = ease_out((t - 1.6) / 0.6)
        c = card_portrait().rotate(-2, expand=True, resample=Image.BICUBIC)
        cx, cy = W / 2, 760 + (1 - rise) * 120
        k = clamp((t - 1.6) / 0.3)
        c.putalpha(Image.fromarray((np.asarray(c)[..., 3] * k).astype(np.uint8)))
        base.alpha_composite(shadow(c), (int(cx - c.width / 2 - 18), int(cy - c.height / 2 - 14)))
        base.alpha_composite(c, (int(cx - c.width / 2), int(cy - c.height / 2)))
    if t > 2.8: paste_pop(base, stamp_card(["ŞAFAK SÖKMEDEN"], 640, 130, RED, seed=2, sizes=[56], bg=BG), 360, 1230, t - 2.8, rot=-6)
    if t > 4.3: paste_pop(base, stamp_card(["YANINDA SADECE DOKTORU"], 900, 130, INK, seed=3, sizes=[52], bg=BG), W / 2, 1360, t - 4.3, rot=2)
    return base.convert("RGB")

def carriage(dr, x, y, a=255):
    dr.rounded_rectangle([x, y, x + 760, y + 330], 26, fill=(78, 96, 70, a))
    dr.rectangle([x, y + 280, x + 760, y + 300], fill=(48, 60, 44, a))
    for i in range(5):
        wx = x + 40 + i * 145; dr.rectangle([wx, y + 60, wx + 100, y + 170], fill=(250, 220, 140, a))
    dr.rectangle([x + 20, y - 26, x + 740, y], fill=(40, 34, 30, a))
    for wx in (x + 120, x + 640):
        dr.ellipse([wx - 55, y + 300, wx + 55, y + 410], fill=(30, 26, 24, a)); dr.ellipse([wx - 18, y + 337, wx + 18, y + 373], fill=(120, 110, 100, a))

def s3(t, dur):  # third class carriage, pneumonia
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    k = a_(t, 0, 0.25)
    spaced_text(dr, (W / 2, 290), "3. SINIF VAGON", font(FB, 86), INK + (k,), sp=6)
    off = (t * 70) % 120
    for i in range(12):  # rails / sleepers
        x = -120 + i * 120 - off; dr.rectangle([x, 1090, x + 60, 1110], fill=(110, 84, 60, 255))
    dr.rectangle([0, 1080, W, 1090], fill=(80, 70, 60, 255))
    bob = 4 * math.sin(t * 18)
    carriage(dr, 160, 670 + bob, k)
    for i in range(4):  # smoke puffs
        st = (t * 0.8 + i * 0.25) % 1.0
        r = 30 + 60 * st; x = 140 - st * 160; y = 600 - st * 240
        dr.ellipse([x - r, y - r, x + r, y + r], fill=(120, 110, 100, int(120 * (1 - st))))
    if t > 1.3: paste_pop(base, stamp_card(["ZATÜRRE"], 560, 170, RED, seed=4, sizes=[92], bg=BG), W / 2, 1300, t - 1.3, rot=-4)
    note(ImageDraw.Draw(base, "RGBA"))
    return base.convert("RGB")

def s4(t, dur):  # Astapovo station, stationmaster's house
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    k = a_(t, 0, 0.3)
    dr.rectangle([150, 300, 930, 450], fill=(30, 52, 92, k)); dr.rectangle([162, 312, 918, 438], outline=(240, 228, 196, k), width=4)
    spaced_text(dr, (W / 2, 375), "ASTAPOVO", font(FB, 96), (240, 228, 196, k), sp=10)
    dr.rectangle([240, 450, 256, 560], fill=(40, 34, 30, k)); dr.rectangle([824, 450, 840, 560], fill=(40, 34, 30, k))
    house(dr, 260, 760, 560, 330, a=a_(t, 0.3), lit=True, wall=(196, 150, 104), roof=(110, 60, 44))
    dr.rectangle([0, 1090, W, 1110], fill=(110, 90, 70, 255))
    spaced_text(dr, (W / 2, 1170), "küçük bir taşra istasyonu", font(FI, 50), INK + (a_(t, 0.8),))
    if t > 2.3: paste_pop(base, stamp_card(["İSTASYON ŞEFİNİN EVİ"], 880, 140, RED, seed=5, sizes=[56], bg=BG), W / 2, 1330, t - 2.3, rot=-2)
    note(ImageDraw.Draw(base, "RGBA"))
    return base.convert("RGB")

def s5(t, dur):  # journalists swarm
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    p = back(t / 0.4); s = int(96 * (0.6 + 0.4 * p))
    spaced_text(dr, (W / 2, 280), "GAZETECİLER", font(FB, max(10, s)), RED + (a_(t, 0, 0.2),), sp=6)
    rng = np.random.default_rng(7)
    for i in range(16):
        c, r = i % 8, i // 8
        x = 90 + c * 128 + (r * 60); y = 1000 + r * 260
        k = int(255 * clamp((t - 0.05 - i * 0.05) / 0.2))
        if k: put(base, "civilian", x, y, 420 + r * 60, alpha=k, dark=0.25 + 0.2 * (1 - r))
    dr = ImageDraw.Draw(base, "RGBA")
    for i in range(6):  # telegrams flying
        st = ((t * 0.7) + i / 6) % 1.0
        x = 120 + i * 170 + 40 * math.sin(i + t * 3); y = 560 - st * 140
        dr.rectangle([x, y, x + 110, y + 70], fill=(250, 244, 226, int(230 * (1 - st))), outline=INK + (int(200 * (1 - st)),), width=3)
        dr.line([(x + 14, y + 24), (x + 94, y + 24)], fill=INK + (int(160 * (1 - st)),), width=4)
        dr.line([(x + 14, y + 44), (x + 74, y + 44)], fill=INK + (int(160 * (1 - st)),), width=4)
    if t > 1.0: paste_pop(base, stamp_card(["İSTASYONA AKIN ETTİ"], 860, 140, INK, seed=6, sizes=[56], bg=BG), W / 2, 1320, t - 1.0, rot=-2)
    note(ImageDraw.Draw(base, "RGBA"))
    return base.convert("RGB")

def s6(t, dur):  # wife came, not let in
    base = NIGHT.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    spaced_text(dr, (W / 2, 280), "KARISI GELDİ", font(FB, 90), CREAM + (a_(t, 0, 0.25),), sp=6)
    dr.rectangle([520, 520, 1000, 1180], fill=(150, 116, 84, 255))           # wall
    dr.rectangle([640, 650, 880, 930], fill=WIN + (255,))                     # window
    dr.line([(760, 650), (760, 930)], fill=(80, 60, 40, 255), width=8); dr.line([(640, 790), (880, 790)], fill=(80, 60, 40, 255), width=8)
    dr.rectangle([620, 630, 900, 950], outline=(80, 60, 40, 255), width=14)
    step = ease_out(t / 1.0)
    put(base, "woman", 120 + step * 230, 1260, 640, dark=0.3)
    if t > 1.55:
        paste_pop(base, stamp_card(["İÇERİ ALINMADI"], 700, 160, RED, seed=7, sizes=[70], bg=BG), W / 2, 1330, t - 1.55, rot=-4)
    note(ImageDraw.Draw(base, "RGBA"), col=CREAM)
    return base.convert("RGB")

def s7(t, dur):  # only when he fell into a coma
    base = PAPER_DARK.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    dr.rounded_rectangle([160, 760, 920, 1000], 24, fill=(232, 222, 200, 255))   # bed
    dr.rectangle([140, 700, 190, 1120], fill=(80, 56, 36, 255)); dr.rectangle([890, 760, 940, 1120], fill=(80, 56, 36, 255))
    dr.ellipse([200, 760, 380, 860], fill=(246, 240, 228, 255))                  # pillow
    dr.ellipse([240, 720, 340, 830], fill=(228, 188, 150, 255))                  # head
    dr.polygon([(250, 800), (330, 800), (310, 900), (270, 900)], fill=(236, 234, 226, 255))  # beard
    dr.rounded_rectangle([300, 830, 900, 960], 30, fill=(150, 130, 110, 255))    # blanket
    k = a_(t, 0.3, 0.5)
    put(base, "woman", 640, 1200, 520, alpha=k, dark=0.35)
    dr = ImageDraw.Draw(base, "RGBA")
    spaced_text(dr, (W / 2, 290), "ANCAK", font(FB, 90), CREAM + (a_(t, 0, 0.25),), sp=8)
    if t > 0.55:
        paste_pop(base, stamp_card(["O KOMAYA", "GİRİNCE"], 720, 230, RED, seed=8, sizes=[74, 74], bg=BG), W / 2, 500, t - 0.55, rot=-3)
    note(ImageDraw.Draw(base, "RGBA"), col=CREAM)
    return base.convert("RGB")

def s8(t, dur):  # 20 November 1910, 6:05
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    p = back(t / 0.45); s = int(104 * (0.6 + 0.4 * p))
    spaced_text(dr, (W / 2, 280), "20 KASIM 1910", font(FB, max(10, s)), RED + (a_(t, 0, 0.2),), sp=6)
    prog = ease(clamp((t - 0.3) / 2.0))
    mins = 5.0 * 60 + 30 + prog * 35   # 5:30 -> 6:05
    clock(dr, W / 2, 800, 330, int(mins // 60), mins % 60, a=a_(t, 0, 0.3))
    if t > 2.3:
        spaced_text(dr, (W / 2, 1185), "06:05", font(FB, 96), INK + (a_(t, 2.3, 0.2),), sp=8)
    if t > 3.25:
        paste_pop(base, stamp_card(["ÖLDÜ"], 420, 160, RED, seed=9, sizes=[96], bg=BG), W / 2, 1340, t - 3.25, rot=-4)
    return base.convert("RGB")

def s9(t, dur):  # station clock still shows 6:05
    base = PAPER_DARK.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    k = a_(t, 0, 0.3)
    dr.rectangle([526, 1000, 554, 1200], fill=(40, 34, 30, k))
    clock(dr, W / 2, 760, 280, 6, 5, a=k)
    spaced_text(dr, (W / 2, 300), "İSTASYONUN SAATİ", font(FB, 76), CREAM + (k,), sp=4)
    if t > 1.15:
        paste_pop(base, stamp_card(["BUGÜN HÂLÂ 06:05"], 820, 160, RED, seed=10, sizes=[70], bg=BG), W / 2, 1330, t - 1.15, rot=-3)
    return base.convert("RGB")

def s10(t, dur):  # ending
    base = Image.new("RGBA", (W, H), (13, 10, 7, 255)); dr = ImageDraw.Draw(base, "RGBA")
    put(base, "tolstoy", W / 2, 1760, 820, alpha=int(150 * clamp(t / 1.5)), dark=0.6)
    dr = ImageDraw.Draw(base, "RGBA")
    spaced_text(dr, (W / 2, 520), "82 yaşında,", font(FI, 64), CREAM + (a_(t, 0.1, 0.5),))
    spaced_text(dr, (W / 2, 610), "her şeyini bırakıp...", font(FI, 64), CREAM + (a_(t, 0.6, 0.5),))
    if t > 1.7:
        p = back((t - 1.7) / 0.45); s = int(124 * (0.6 + 0.4 * p))
        spaced_text(dr, (W / 2, 790), "NEDEN", font(FB, max(10, s)), GOLD + (a_(t, 1.7, 0.25),), sp=10)
        spaced_text(dr, (W / 2, 930), "KAÇTI?", font(FB, max(10, s)), (230, 80, 60, a_(t, 1.7, 0.25)), sp=10)
    return base.convert("RGB")

# durations in ORIGINAL voice seconds (sentence starts from the transcript)
_B = [0.0, 6.42, 12.58, 15.42, 19.70, 21.88, 24.66, 27.60, 31.54, 35.60, 40.45]
_F = [s1, s2, s3, s4, s5, s6, s7, s8, s9, s10]
SCENES = [(f"s{i+1}", f, (_B[i + 1] - _B[i]) / SP) for i, f in enumerate(_F)]
XF = 0.3
STARTS = []; _a = 0.0
for _n, _f, _d in SCENES: STARTS.append(_a); _a += _d
TOTAL = _a
IMPACTS = {"s1": [4.3], "s2": [0.0, 2.8, 4.3], "s3": [1.3], "s4": [2.3], "s5": [1.0], "s6": [1.55], "s7": [0.55],
           "s8": [3.25], "s9": [1.15], "s10": [1.7]}   # local ORIGINAL seconds

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
    elif sys.argv[1] == "info":
        print(TOTAL, [round(s, 3) for s in STARTS])
    else:
        for k, sc in enumerate(SCENES):
            if sc[0] in sys.argv[2:]: render(k)
