import os, sys, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import make as M
from make import (W, H, FPS, OUT, SCREEN_PAPER, DESK, stamp_card, paste_pop, shadow, spaced_text, font, FB, FI, INK, RED,
                  CREAM, ease, ease_out, back, clamp, finish, dust, title_band)

PAPER_DARK = Image.fromarray((np.asarray(DESK, np.float32) * 0.45).astype(np.uint8))
BG = (240, 228, 196, 240)
GOLD = (226, 170, 90)

def a_(t, t0, d=0.4): return int(255 * clamp((t - t0) / d))

def clock(dr, cx, cy, r, hh, mm, ss=0.0, col=INK, face=(244, 234, 208), alpha=255, sec=True):
    dr.ellipse([cx - r - 10, cy - r - 10, cx + r + 10, cy + r + 10], fill=col + (alpha,))
    dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=face + (alpha,))
    for i in range(60):
        ang = i * math.pi / 30 - math.pi / 2; big = i % 5 == 0
        r0 = r * (0.82 if big else 0.9)
        dr.line([(cx + math.cos(ang) * r0, cy + math.sin(ang) * r0), (cx + math.cos(ang) * r * 0.96, cy + math.sin(ang) * r * 0.96)],
                fill=col + (alpha,), width=int(r * (0.035 if big else 0.012)) + 1)
    fn = font(FB, int(r * 0.17))
    for n in range(1, 13):
        ang = n * math.pi / 6 - math.pi / 2
        dr.text((cx + math.cos(ang) * r * 0.66, cy + math.sin(ang) * r * 0.66), str(n), font=fn, fill=col + (alpha,), anchor="mm")
    def hand(frac, L, w, c):
        ang = frac * 2 * math.pi - math.pi / 2
        dr.line([(cx - math.cos(ang) * r * 0.1, cy - math.sin(ang) * r * 0.1), (cx + math.cos(ang) * L, cy + math.sin(ang) * L)],
                fill=c + (alpha,), width=w)
    hand(((hh % 12) + mm / 60) / 12, r * 0.5, int(r * 0.07), col)
    hand((mm + ss / 60) / 60, r * 0.78, int(r * 0.045), col)
    if sec: hand(ss / 60, r * 0.86, max(3, int(r * 0.018)), RED)
    dr.ellipse([cx - r * 0.05, cy - r * 0.05, cx + r * 0.05, cy + r * 0.05], fill=RED + (alpha,))

def note(dr, text="Temsilî çizim", col=INK):
    dr.text((W - 40, H - 250), text, font=font(FI, 30), fill=col + (150,), anchor="rb")

# ---------- scenes ----------
def s1(t, dur):  # hook: war ended at 11:00, this man died at 10:59
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    spaced_text(dr, (W / 2, 300), "SAVAŞ SAAT 11:00'DE", font(FB, 68), INK + (255,), sp=4)
    spaced_text(dr, (W / 2, 395), "BİTTİ", font(FB, 92), RED + (255,), sp=10)
    rw = ease((t - 2.7) / 0.6)
    s = 0.92 + 0.08 * ease_out(t / 0.5)
    clock(dr, W / 2, 830, int(300 * s), 10, 60 - rw, 0, sec=False)
    if t > 3.7:
        paste_pop(base, stamp_card(["BU ADAM", "10:59'DA ÖLDÜ"], 820, 250, RED, seed=1, sizes=[64, 92], bg=BG), W / 2, 1300, t - 3.7, rot=-3)
    return base.convert("RGB")

def carriage(dr, cx, cy, k):
    a = int(255 * k); c = (60, 44, 30)
    w, h = 820, 250; x0, y0 = cx - w / 2, cy - h / 2
    dr.rounded_rectangle([x0, y0, x0 + w, y0 + h], 22, fill=c + (a,), outline=INK + (a,), width=5)
    dr.rounded_rectangle([x0 - 20, y0 - 34, x0 + w + 20, y0 + 6], 20, fill=(45, 32, 22, a))
    for i in range(7):
        wx = x0 + 50 + i * 106
        dr.rounded_rectangle([wx, y0 + 40, wx + 74, y0 + 130], 8, fill=(236, 200, 120, int(a * 0.9)))
    dr.line([(x0 + 10, y0 + 170), (x0 + w - 10, y0 + 170)], fill=GOLD + (a,), width=4)
    for wx in (x0 + 130, x0 + 230, x0 + w - 230, x0 + w - 130):
        dr.ellipse([wx - 42, y0 + h - 30, wx + 42, y0 + h + 54], fill=(30, 22, 15, a), outline=(110, 90, 60, a), width=5)
    dr.line([(x0 - 120, y0 + h + 58), (x0 + w + 120, y0 + h + 58)], fill=INK + (a,), width=8)

def s2(t, dur):  # 11 Nov 1918, 05:00, armistice signed in a railway carriage
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    title_band(base, "11 KASIM 1918", t - 0.15, y=290, size=86, col=INK)
    dr = ImageDraw.Draw(base, "RGBA")
    if t > 1.2:
        k = a_(t, 1.2)
        clock(dr, W / 2, 610, 130, 5, 0, 0, alpha=k, sec=False)
        spaced_text(dr, (W / 2, 790), "SABAH 05:00", font(FB, 60), INK + (k,), sp=6)
    if t > 2.9:
        k = ease((t - 2.9) / 0.5)
        carriage(dr, W / 2, 1010 + (1 - k) * 40, k)
        spaced_text(dr, (W / 2, 1230), "Compiègne Ormanı, Fransa · bir tren vagonu", font(FI, 40), INK + (int(255 * k),))
    if t > 4.5:
        paste_pop(base, stamp_card(["ATEŞKES İMZALANDI"], 880, 160, RED, seed=2, sizes=[70], bg=BG), W / 2, 1360, t - 4.5, rot=-2)
    note(dr)
    return base.convert("RGB")

def s3(t, dur):  # guns only stop at 11 -> 6 more hours of war
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    k = a_(t, 0.1)
    spaced_text(dr, (W / 2, 300), "AMA SİLAHLAR", font(FB, 76), INK + (k,), sp=6)
    spaced_text(dr, (W / 2, 400), "11:00'DE SUSACAKTI", font(FB, 76), RED + (k,), sp=4)
    clock(dr, 290, 760, 170, 5, 0, sec=False, alpha=a_(t, 0.6))
    p = ease((t - 1.2) / 1.4)
    hh = 5 + 6 * p
    clock(dr, W - 290, 760, 170, int(hh) if p < 1 else 11, (hh % 1) * 60 if p < 1 else 0, sec=False, alpha=a_(t, 0.6))
    ka = a_(t, 0.6)
    spaced_text(dr, (290, 975), "05:00", font(FB, 52), INK + (ka,))
    spaced_text(dr, (W - 290, 975), "11:00", font(FB, 52), RED + (ka,))
    bx0, bx1, by = 140, W - 140, 1080
    dr.rounded_rectangle([bx0, by - 18, bx1, by + 18], 18, outline=INK + (ka,), width=4)
    f = ease((t - 2.9) / 2.0)
    if f > 0: dr.rounded_rectangle([bx0 + 6, by - 12, bx0 + 6 + (bx1 - bx0 - 12) * f, by + 12], 12, fill=RED + (255,))
    if t > 3.0:
        paste_pop(base, stamp_card(["6 SAAT DAHA", "SAVAŞ"], 760, 230, RED, seed=3, sizes=[80, 70], bg=BG), W / 2, 1300, t - 3.0, rot=-3)
    return base.convert("RGB")

CROSS = []
_r = np.random.default_rng(4)
for row in range(6):
    for col in range(9):
        CROSS.append((110 + col * 107 + (row % 2) * 50 + _r.uniform(-8, 8), 900 + row * 85, _r.uniform(0, 1)))

def s4(t, dur):  # at least 2,738 died that day
    base = PAPER_DARK.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    k = a_(t, 0.05, 0.3)
    spaced_text(dr, (W / 2, 300), "SADECE O GÜN", font(FB, 70), CREAM + (k,), sp=6)
    n = int(2738 * ease_out((t - 0.3) / 1.7))
    s = f"{n:,}".replace(",", ".")
    spaced_text(dr, (W / 2, 575), s, font(FB, 210), (230, 80, 60, a_(t, 0.3, 0.2)), sp=8)
    spaced_text(dr, (W / 2, 730), "ASKER ÖLDÜ", font(FB, 70), CREAM + (a_(t, 1.4),), sp=8)
    for (x, y, d) in CROSS:
        kk = clamp((t - 0.4 - d * 1.6) / 0.3)
        if kk <= 0: continue
        c = (215, 200, 170, int(200 * kk))
        dr.rectangle([x - 5, y - 34, x + 5, y + 30], fill=c); dr.rectangle([x - 20, y - 20, x + 20, y - 10], fill=c)
    spaced_text(dr, (W / 2, 400), "EN AZ", font(FB, 56), (230, 80, 60, a_(t, 0.2, 0.3)), sp=10)
    return base.convert("RGB")

LETTER = None
def make_letter():
    w, h = 620, 760
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, h], fill=(248, 240, 220, 255), outline=(150, 130, 100, 255), width=3)
    rng = np.random.default_rng(7)
    for i in range(14):
        y = 70 + i * 46; L = rng.uniform(380, 520)
        x = 50
        while x < 50 + L:
            ww = rng.uniform(30, 90)
            d.line([(x, y), (x + ww, y)], fill=(70, 60, 90, 255), width=4); x += ww + 16
    return im
LETTER = make_letter()
BARS = [(1, 0.0), (3, 0.25), (4, 0.4), (7, 0.6), (8, 0.75), (11, 0.95)]

def s5(t, dur):  # Henry Gunther: censored letter, demoted
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    paste_pop(base, stamp_card(["HENRY GUNTHER"], 900, 170, INK, seed=6, sizes=[84], bg=BG), W / 2, 290, t - 0.13, rot=-2)
    dr = ImageDraw.Draw(base, "RGBA")
    k = a_(t, 0.6)
    spaced_text(dr, (W / 2, 420), "23 yaşında · Baltimore, ABD", font(FI, 48), INK + (k,))
    if t > 1.1:
        rise = ease_out((t - 1.1) / 0.6)
        lt = LETTER.copy(); ld = ImageDraw.Draw(lt)
        for (row, d0) in BARS:
            p = ease((t - 2.4 - d0) / 0.35)
            if p > 0:
                y = 70 + row * 46
                ld.rectangle([40, y - 18, 40 + 540 * p, y + 18], fill=(15, 12, 10, 255))
        lt = lt.rotate(-3, expand=True, resample=Image.BICUBIC)
        if rise < 1:
            a = np.asarray(lt).copy(); a[..., 3] = (a[..., 3] * rise).astype(np.uint8); lt = Image.fromarray(a)
        cx, cy = W / 2, 950 + (1 - rise) * 200
        base.alpha_composite(shadow(lt), (int(cx - lt.width / 2 - 18), int(cy - lt.height / 2 - 14)))
        base.alpha_composite(lt, (int(cx - lt.width / 2), int(cy - lt.height / 2)))
        spaced_text(ImageDraw.Draw(base, "RGBA"), (W / 2, 485), "Cepheden yazdığı mektup", font(FI, 42), INK + (a_(t, 1.3),))
    if t > 3.2:
        paste_pop(base, stamp_card(["SANSÜR"], 520, 170, RED, seed=7, sizes=[96], bg=(240, 228, 196, 200)), W / 2 + 120, 780, t - 3.2, rot=-12)
    if t > 4.5:
        c = stamp_card(["ÇAVUŞ  →  ER"], 760, 160, INK, seed=8, sizes=[76], bg=BG)
        paste_pop(base, c, W / 2, 1340, t - 4.5, rot=2)
        if t > 4.9:
            dr = ImageDraw.Draw(base, "RGBA"); p = ease((t - 4.9) / 0.3)
            dr.line([(W / 2 - 300, 1345), (W / 2 - 300 + 240 * p, 1325)], fill=RED + (255,), width=10)
    return base.convert("RGB")

def soldier(dr, x, y, t, run=True, col=(60, 44, 30), a=255):
    ph = t * 9 if run else 0
    c = col + (a,)
    dr.ellipse([x - 22, y - 120, x + 22, y - 76], fill=c)                      # head
    dr.pieslice([x - 34, y - 138, x + 34, y - 90], 180, 360, fill=c)           # helmet
    dr.line([(x, y - 76), (x + 10, y - 10)], fill=c, width=22)                 # body (leaning)
    for s in (1, -1):
        sw = math.sin(ph) * 28 * s
        dr.line([(x + 10, y - 10), (x + 10 + sw, y + 60)], fill=c, width=16)   # legs
        dr.line([(x + 4, y - 60), (x + 28 - sw * 0.6, y - 26)], fill=c, width=12)  # arms

def s6(t, dur):  # 10:59 - charges the German machine gun; Germans wave him off; he does not stop; shot
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    ss = min(59.0, t * 1.0)
    clock(dr, 190, 330, 120, 10, 59, ss, sec=True)
    k = a_(t, 0.25)
    spaced_text(dr, (650, 300), "SAAT 11'E", font(FB, 66), INK + (k,), sp=4)
    spaced_text(dr, (650, 380), "1 DAKİKA VAR", font(FB, 66), RED + (k,), sp=4)
    # ground / no man's land
    gy = 1080
    dr.rectangle([0, gy, W, gy + 360], fill=(150, 118, 80, 255))
    rng = np.random.default_rng(9)
    for i in range(30):
        x = rng.uniform(0, W); y = gy + rng.uniform(20, 340); r = rng.uniform(16, 50)
        dr.ellipse([x - r, y - r * 0.4, x + r, y + r * 0.4], fill=(120, 92, 60, 255))
    for i in range(0, W, 46):  # barbed wire
        dr.line([(i, gy - 20), (i + 46, gy - 6)], fill=(70, 55, 40, 255), width=3)
        dr.line([(i + 23, gy - 30), (i + 23, gy + 4)], fill=(70, 55, 40, 255), width=4)
    # German position (right)
    gx = 900; ka = a_(t, 2.2)
    dr.rounded_rectangle([gx - 120, gy - 120, gx + 140, gy + 10], 30, fill=(90, 80, 60, ka), outline=INK + (ka,), width=5)
    dr.line([(gx - 110, gy - 70), (gx - 240, gy - 85)], fill=(30, 25, 20, ka), width=14)  # gun barrel
    if t > 2.2:
        spaced_text(dr, (gx - 60, gy - 200), "ALMAN", font(FB, 44), INK + (ka,), sp=3, stroke=5, sfill=(245, 235, 211, ka))
        spaced_text(dr, (gx - 90, gy - 150), "MAKİNELİ TÜFEĞİ", font(FB, 34), INK + (ka,), sp=2, stroke=5, sfill=(245, 235, 211, ka))
    # runner
    shot = 9.35
    run = ease((t - 0.95) / (shot - 0.95)) if t < shot else 1.0
    sx = 120 + 480 * run
    if t < shot:
        soldier(dr, sx, gy + 70, t, run=t > 0.95)
    else:
        kk = clamp((t - shot) / 0.4)
        c = (60, 44, 30, int(255 * (1 - 0.6 * kk)))
        dr.ellipse([sx - 60, gy + 70, sx + 70, gy + 100], fill=c)
    if t > 0.95:
        dr.line([(120, gy + 150), (sx, gy + 150)], fill=RED + (200,), width=6)
    if t > 4.9:
        kb = a_(t, 4.9)
        dr.rounded_rectangle([110, 520, W - 110, 640], 20, fill=(240, 228, 196, int(kb * 0.94)), outline=INK + (kb,), width=4)
        spaced_text(dr, (W / 2, 580), "ALMANLAR ATEŞKESİ BİLİYORDU", font(FB, 40), INK + (kb,))
    if t > 6.5:
        kb = a_(t, 6.5, 0.25)
        wv = math.sin(t * 10) * 18
        dr.line([(gx + 120, gy - 110), (gx + 160 + wv, gy - 200)], fill=INK + (kb,), width=10)   # waving arm
        dr.polygon([(gx + 20, 800), (gx + 70, 800), (gx + 130, 870)], fill=(255, 250, 235, kb), outline=INK + (kb,))
        dr.rounded_rectangle([gx - 390, 690, gx + 120, 810], 26, fill=(255, 250, 235, kb), outline=INK + (kb,), width=5)
        spaced_text(dr, (gx - 135, 750), "GERİ DÖN!", font(FB, 62), RED + (kb,))
    if t > 8.5 and t < shot + 0.1:
        paste_pop(base, stamp_card(["DURMADI"], 620, 170, RED, seed=10, sizes=[96], bg=BG), W / 2, 1300, t - 8.5, rot=-4)
    if t > shot:
        veil = Image.new("RGBA", (W, H), (20, 14, 9, int(150 * clamp((t - shot) / 0.3)))); base.alpha_composite(veil)
        paste_pop(base, stamp_card(["VURULDU"], 620, 170, CREAM, seed=11, sizes=[96], bg=(60, 20, 18, 235)), W / 2, 1300, t - shot, rot=-4)
    note(ImageDraw.Draw(base, "RGBA"))
    return base.convert("RGB")

def s7(t, dur):  # 60 seconds later the guns fell silent
    base = PAPER_DARK.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    k = a_(t, 0.1)
    spaced_text(dr, (W / 2, 300), "60 SANİYE SONRA", font(FB, 80), CREAM + (k,), sp=6)
    p = ease((t - 0.2) / 1.8)
    ss = 10 + 50 * p
    if p < 1: clock(dr, W / 2, 800, 330, 10, 59, ss, col=(40, 28, 18), face=(236, 222, 186))
    else: clock(dr, W / 2, 800, 330, 11, 0, 0, col=(40, 28, 18), face=(236, 222, 186))
    if t > 2.1:
        paste_pop(base, stamp_card(["11:00", "SİLAHLAR SUSTU"], 860, 250, (230, 80, 60), seed=12, sizes=[100, 60], bg=(40, 28, 18, 235)),
                  W / 2, 1320, t - 2.1, rot=-2)
    return base.convert("RGB")

def s8(t, dur):  # ending
    base = Image.new("RGBA", (W, H), (13, 10, 7, 255)); dr = ImageDraw.Draw(base, "RGBA")
    clock(dr, W / 2, 900, 380, 11, 0, 0, col=(40, 30, 22), face=(26, 20, 14), alpha=int(70 + 30 * clamp(t / 2)), sec=False)
    spaced_text(dr, (W / 2, 700), "Barış sabah 5'te imzalanmıştı...", font(FI, 56), CREAM + (a_(t, 0.2, 0.5),))
    if t > 2.1:
        p = back((t - 2.1) / 0.45); s = int(96 * (0.6 + 0.4 * p))
        spaced_text(dr, (W / 2, 900), "O SON 6 SAAT", font(FB, max(10, s)), GOLD + (a_(t, 2.1, 0.25),), sp=8)
        spaced_text(dr, (W / 2, 1030), "NEYE DEĞDİ?", font(FB, max(10, int(s * 1.15))), (230, 80, 60, a_(t, 2.1, 0.25)), sp=8)
    return base.convert("RGB")

SCENES = [("s1", s1, 5.45), ("s2", s2, 5.85), ("s3", s3, 5.45), ("s4", s4, 3.05), ("s5", s5, 6.9),
          ("s6", s6, 10.15), ("s7", s7, 4.65), ("s8", s8, 3.8)]
XF = 0.35
STARTS = []; _a = 0.0
for _n, _f, _d in SCENES: STARTS.append(_a); _a += _d
TOTAL = _a
IMPACTS = {"s1": [3.7], "s2": [0.15, 4.5], "s3": [3.0], "s4": [2.0], "s5": [0.13, 3.2, 4.5], "s6": [8.5, 9.35], "s7": [2.1], "s8": [2.1]}

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
    else:
        for k, sc in enumerate(SCENES):
            if sc[0] in sys.argv[2:]: render(k)
