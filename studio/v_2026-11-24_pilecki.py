"""Witold Pilecki: Auschwitz'e kendi isteğiyle giren Polonyalı subay (1940), kaçış (1943), komünist Polonya'da idam (25 Mayıs 1948).
Şablon: v_2026-11-21_balon.py. Zamanlar seslendirmenin orijinal hızına göre; ses SP ile hızlandırılır.
Nazi sembolü çizilmez; kamp tel örgü + gözetleme kulesiyle temsil edilir."""
import os, sys, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from figures import put
from make import (W, H, FPS, OUT, SCREEN_PAPER, DESK, stamp_card, paste_pop, shadow, spaced_text, font, FB, FI, INK, RED,
                  CREAM, ease, ease_out, back, clamp, finish, dust, wave_flag)

SP = 1.1
PAPER_DARK = Image.fromarray((np.asarray(DESK, np.float32) * 0.45).astype(np.uint8))
_g = np.linspace(0.35, 0.85, H)[:, None, None]
NIGHT = Image.fromarray(np.clip(np.asarray(DESK, np.float32) * np.array([0.42, 0.48, 0.62]) * _g * 1.6, 0, 255).astype(np.uint8))
GREY = Image.fromarray(np.clip(np.asarray(SCREEN_PAPER, np.float32) * np.array([0.62, 0.62, 0.62]), 0, 255).astype(np.uint8))
BG = (240, 228, 196, 240)
GOLD = (226, 170, 90)
PRED = (212, 33, 61)

def a_(t, t0, d=0.4): return int(255 * clamp((t - t0) / d))

def note(dr, text="Temsilî çizim", col=INK):
    dr.text((W - 40, H - 250), text, font=font(FI, 30), fill=col + (150,), anchor="rb")

def pl_flag(w=420, h=262):
    im = Image.new("RGBA", (w, h), (255, 255, 255, 255)); d = ImageDraw.Draw(im)
    d.rectangle([0, h // 2, w, h], fill=PRED + (255,)); d.rectangle([0, 0, w - 1, h - 1], outline=(150, 140, 130, 255), width=2)
    return im

def fence(dr, y0=1000, y1=1380, a=255, col=(16, 13, 12), tower=True, x_off=0):
    """Kamp tel örgüsü (beton direkler + dikenli tel) ve gözetleme kulesi."""
    for i in range(-1, 7):
        x = 60 + i * 190 + x_off
        dr.rectangle([x, y0 - 30, x + 16, y1], fill=col + (a,))
        dr.line([(x + 8, y0 - 30), (x + 40, y0 - 70)], fill=col + (a,), width=10)
    for k in range(6):
        y = y0 + k * (y1 - y0) / 6
        dr.line([(0, y), (W, y + 6)], fill=col + (a,), width=3)
        for x in range(10 + (k * 23) % 40, W, 46):
            dr.line([(x - 8, y - 8), (x + 8, y + 8)], fill=col + (a,), width=3)
            dr.line([(x - 8, y + 8), (x + 8, y - 8)], fill=col + (a,), width=3)
    if tower:
        tx = 840 + x_off
        dr.polygon([(tx - 70, y1), (tx - 40, y0 - 320), (tx + 40, y0 - 320), (tx + 70, y1)], fill=col + (int(a * 0.0),))
        for sx in (-1, 1): dr.line([(tx + sx * 70, y1), (tx + sx * 40, y0 - 320)], fill=col + (a,), width=14)
        for yy in range(int(y0 - 280), int(y1), 120): dr.line([(tx - 66, yy + 100), (tx + 60, yy)], fill=col + (a,), width=8)
        dr.rectangle([tx - 90, y0 - 450, tx + 90, y0 - 320], fill=col + (a,))
        dr.polygon([(tx - 115, y0 - 450), (tx + 115, y0 - 450), (tx, y0 - 530)], fill=col + (a,))
        dr.rectangle([tx - 60, y0 - 420, tx + 60, y0 - 370], fill=(230, 210, 150, int(a * 0.6)))

def searchlight(base, t, x0=840, y0=570, a=70):
    ang = -2.2 + 0.5 * math.sin(t * 0.9)
    L = 1500
    p1 = (x0 + L * math.cos(ang - 0.12), y0 - L * math.sin(-(ang - 0.12)))
    p2 = (x0 + L * math.cos(ang + 0.12), y0 - L * math.sin(-(ang + 0.12)))
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).polygon([(x0, y0), p1, p2], fill=(250, 240, 200, a))
    base.alpha_composite(g.filter(ImageFilter.GaussianBlur(18)))


# ---------- scenes (t = local seconds in ORIGINAL voice time) ----------
def s1(t, dur):  # hook: entered Auschwitz voluntarily
    base = NIGHT.copy().convert("RGBA")
    searchlight(base, t)
    dr = ImageDraw.Draw(base, "RGBA")
    fence(dr, 1010, 1400)
    put(base, "civilian", 330, 1330, 560, dark=0.95)
    p = back(t / 0.35); s = int(82 * (0.85 + 0.15 * p))
    spaced_text(dr, (W / 2, 240), "KENDİ İSTEĞİYLE", font(FB, max(10, s)), CREAM + (255,), sp=4)
    spaced_text(dr, (W / 2, 360), "AUSCHWITZ'E", font(FB, max(10, int(s * 1.05))), (232, 90, 70, 255), sp=4)
    if t > 1.5:
        paste_pop(base, stamp_card(["GİRDİ"], 380, 140, RED, seed=1, sizes=[88], bg=BG), W / 2, 520, t - 1.5, rot=-4)
    note(ImageDraw.Draw(base, "RGBA"), col=CREAM)
    return base.convert("RGB")

def rooftops(dr, a=255, y=1150, col=(70, 60, 56)):
    rng = np.random.default_rng(8); x = 0
    while x < W:
        w = int(rng.integers(90, 180)); h = int(rng.integers(140, 320))
        dr.rectangle([x, y - h, x + w, y + 400], fill=col + (a,))
        dr.polygon([(x - 6, y - h), (x + w + 6, y - h), (x + w / 2, y - h - 60)], fill=(50, 42, 40, a))
        for j in range(2):
            dr.rectangle([x + 20 + j * 50, y - h + 50, x + 44 + j * 50, y - h + 90], fill=(236, 210, 150, a))
        x += w + 6

def s2(t, dur):  # September 1940
    base = GREY.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    rooftops(dr, y=1180)
    p = back(t / 0.45); s = int(120 * (0.6 + 0.4 * p))
    spaced_text(dr, (W / 2, 330), "EYLÜL 1940", font(FB, max(10, s)), RED + (a_(t, 0, 0.2),), sp=8, stroke=3, sfill=(245, 235, 211))
    f = wave_flag(pl_flag(360, 225), t, amp=10)
    base.alpha_composite(f, (int(W / 2 - f.width / 2), 520))
    if t > 0.7: paste_pop(base, stamp_card(["VARŞOVA"], 460, 150, INK, seed=2, sizes=[84], bg=BG), W / 2, 1290, t - 0.7, rot=3)
    return base.convert("RGB")

def card_portrait():
    w, h = 620, 800
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, h], fill=(244, 232, 200, 255), outline=(120, 96, 60, 255), width=6)
    d.rectangle([90, 60, w - 90, 560], fill=(196, 190, 176, 255))
    put(im, "civilian", w / 2, 1180, 1100, shadow=False)
    d.rectangle([0, 562, w, h], fill=(244, 232, 200, 255)); d.rectangle([0, 0, w, h], outline=(120, 96, 60, 255), width=6)
    d.rectangle([90, 60, w - 90, 560], outline=INK + (255,), width=4)
    spaced_text(d, (w / 2, 630), "WITOLD PILECKI", font(FB, 50), RED + (255,), sp=2)
    spaced_text(d, (w / 2, 710), "Polonyalı subay", font(FI, 40), INK + (255,))
    return im
CARD = card_portrait()

def s3(t, dur):  # Polish officer, deliberately caught in street roundup
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    spaced_text(dr, (W / 2, 220), "SOKAK BASKINI", font(FB, 80), INK + (a_(t, 0, 0.3),), sp=4)
    rise = ease_out(clamp(t / 0.6))
    c = CARD.rotate(-2, expand=True, resample=Image.BICUBIC)
    k = clamp(t / 0.3)
    c.putalpha(Image.fromarray((np.asarray(c)[..., 3] * k).astype(np.uint8)))
    cx, cy = W / 2, 760 + (1 - rise) * 120
    base.alpha_composite(shadow(c), (int(cx - c.width / 2 - 18), int(cy - c.height / 2 - 14)))
    base.alpha_composite(c, (int(cx - c.width / 2), int(cy - c.height / 2)))
    if t > 3.9: paste_pop(base, stamp_card(["BİLEREK", "YAKALANDI"], 620, 230, RED, seed=3, sizes=[78, 78], bg=BG), W / 2, 1250, t - 3.9, rot=-5)
    note(ImageDraw.Draw(base, "RGBA"))
    return base.convert("RGB")

def s4(t, dur):  # prisoner number 4859
    base = PAPER_DARK.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    # striped camp-uniform fabric patch
    pw, ph = 760, 820; x0, y0 = (W - pw) // 2, 420
    patch = Image.new("RGBA", (pw, ph), (0, 0, 0, 0)); pd = ImageDraw.Draw(patch)
    for i in range(0, pw, 90):
        pd.rectangle([i, 0, i + 45, ph], fill=(150, 160, 178, 255)); pd.rectangle([i + 45, 0, i + 90, ph], fill=(214, 214, 206, 255))
    m = Image.new("L", (pw, ph), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, pw, ph], 20, fill=255)
    patch.putalpha(m)
    base.alpha_composite(shadow(patch), (x0 - 18, y0 - 14)); base.alpha_composite(patch, (x0, y0))
    dr = ImageDraw.Draw(base, "RGBA")
    spaced_text(dr, (W / 2, 240), "NUMARASI", font(FB, 88), CREAM + (a_(t, 0, 0.25),), sp=8)
    if t > 0.9:
        n = int(min(4859, 4859 * ease_out(clamp((t - 0.9) / 0.9))))
        paste_pop(base, stamp_card([f"{n}"], 640, 240, INK, seed=4, sizes=[150], bg=(244, 238, 222, 250)), W / 2, 830, t - 0.9, rot=-2)
    note(ImageDraw.Draw(base, "RGBA"), col=CREAM)
    return base.convert("RGB")

def paper(w=200, h=140, rot=0):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, h], fill=(244, 236, 214, 255), outline=(120, 96, 60, 255), width=3)
    for k in range(5): d.line([(18, 24 + k * 22), (w - 18 - (k % 2) * 40, 24 + k * 22)], fill=(90, 70, 50, 200), width=4)
    return im.rotate(rot, expand=True, resample=Image.BICUBIC)

def s5(t, dur):  # secret resistance; reports smuggled out
    base = NIGHT.copy().convert("RGBA")
    searchlight(base, t * 1.3, a=50)
    dr = ImageDraw.Draw(base, "RGBA")
    fence(dr, 1010, 1400)
    for i, x in enumerate((180, 320, 460)):
        put(base, "civilian", x, 1330, 440, dark=0.9, shadow=False)
    spaced_text(dr, (W / 2, 240), "GİZLİ DİRENİŞ", font(FB, 92), CREAM + (a_(t, 0, 0.25),), sp=6)
    if t > 2.0:
        for i in range(4):
            k = ease(clamp((t - 2.0 - i * 0.25) / 1.4))
            if k <= 0: continue
            x = 420 + k * (560 + i * 40); y = 1150 - k * (520 + i * 70) + 140 * k * k
            p = paper(150, 104, rot=int(20 * math.sin(t * 3 + i)))
            base.alpha_composite(p, (int(x - p.width / 2), int(y - p.height / 2)))
    if t > 2.3: paste_pop(base, stamp_card(["RAPORLAR SIZDI"], 700, 140, RED, seed=5, sizes=[64], bg=BG), W / 2, 430, t - 2.3, rot=-3)
    note(ImageDraw.Draw(base, "RGBA"), col=CREAM)
    return base.convert("RGB")

def s6(t, dur):  # April 1943: escape with two comrades
    base = NIGHT.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    for i in range(40):
        x = (i * 263) % W; y = 120 + (i * 151) % 480; dr.ellipse([x, y, x + 4, y + 4], fill=(240, 230, 200, 120))
    shift = -int(ease(clamp(t / 3.0)) * 380)
    fence(dr, 1010, 1400, x_off=shift)
    run = ease(clamp(t / 3.2))
    for i in range(3):
        x = 380 + i * 150 + run * 420; h = 420 - i * 20
        put(base, "civilian", x, 1360 + i * 20, h, dark=0.9, shadow=False)
    p = back(t / 0.4); s = int(104 * (0.6 + 0.4 * p))
    spaced_text(dr, (W / 2, 240), "NİSAN 1943", font(FB, max(10, s)), CREAM + (a_(t, 0, 0.2),), sp=8)
    if t > 1.6: paste_pop(base, stamp_card(["KAÇTI"], 400, 150, RED, seed=6, sizes=[92], bg=BG), W / 2, 450, t - 1.6, rot=-4)
    note(ImageDraw.Draw(base, "RGBA"), col=CREAM)
    return base.convert("RGB")

def s7(t, dur):  # war over... but his war not
    base = PAPER_DARK.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    spaced_text(dr, (W / 2, 560), "SAVAŞ BİTTİ.", font(FB, 100), CREAM + (a_(t, 0, 0.3),), sp=6)
    if t > 1.4:
        p = back((t - 1.4) / 0.45); s = int(84 * (0.6 + 0.4 * p))
        spaced_text(dr, (W / 2, 820), "AMA ONUN SAVAŞI", font(FB, max(10, s)), GOLD + (a_(t, 1.4, 0.25),), sp=4)
        spaced_text(dr, (W / 2, 940), "BİTMEDİ", font(FB, max(10, int(s * 1.3))), (232, 90, 70, a_(t, 1.4, 0.25)), sp=8)
    return base.convert("RGB")

def bars(dr, a=255, col=(28, 26, 26)):
    for i in range(8):
        x = 70 + i * 135; dr.rectangle([x, 380, x + 26, 1400], fill=col + (a,))
    for y in (380, 900, 1380): dr.rectangle([40, y, W - 40, y + 26], fill=col + (a,))

def s8(t, dur):  # 1947: communist Poland arrests & tortures him
    base = GREY.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    f = wave_flag(pl_flag(420, 262), t, amp=10)
    base.alpha_composite(f, (int(W / 2 - f.width / 2), 470))
    put(base, "civilian", W / 2, 1330, 520, dark=0.4)
    dr = ImageDraw.Draw(base, "RGBA")
    k = ease(clamp((t - 1.0) / 0.5))
    if k > 0: bars(dr, int(255 * k))
    p = back(t / 0.4); s = int(110 * (0.6 + 0.4 * p))
    spaced_text(dr, (W / 2, 240), "1947", font(FB, max(10, s)), RED + (a_(t, 0, 0.2),), sp=10, stroke=3, sfill=(245, 235, 211))
    if t > 1.4: paste_pop(base, stamp_card(["KOMÜNİST POLONYA"], 760, 120, INK, seed=8, sizes=[56], bg=BG), W / 2, 1000, t - 1.4, rot=2)
    if t > 3.2: paste_pop(base, stamp_card(["TUTUKLANDI"], 600, 150, RED, seed=9, sizes=[80], bg=BG), W / 2, 1260, t - 3.2, rot=-4)
    note(ImageDraw.Draw(base, "RGBA"))
    return base.convert("RGB")

def s9(t, dur):  # 25 May 1948 executed
    base = Image.new("RGBA", (W, H), (22, 18, 16, 255)); dr = ImageDraw.Draw(base, "RGBA")
    c = CARD.convert("L").convert("RGBA").rotate(3, expand=True, resample=Image.BICUBIC)
    k = clamp(t / 0.5); c.putalpha(Image.fromarray((np.asarray(c)[..., 3] * k * 0.9).astype(np.uint8)))
    base.alpha_composite(c, (int(W / 2 - c.width / 2), 430))
    p = back(t / 0.4); s = int(100 * (0.6 + 0.4 * p))
    spaced_text(dr, (W / 2, 250), "25 MAYIS 1948", font(FB, max(10, s)), CREAM + (a_(t, 0, 0.2),), sp=6)
    if t > 2.1: paste_pop(base, stamp_card(["İDAM EDİLDİ"], 640, 160, RED, seed=10, sizes=[80], bg=BG), W / 2, 1320, t - 2.1, rot=-6)
    return base.convert("RGB")

def s10(t, dur):  # escaped the Nazis, killed by his own country
    base = PAPER_DARK.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    spaced_text(dr, (W / 2, 420), "NAZİLERDEN KAÇTI", font(FB, 82), CREAM + (a_(t, 0, 0.3),), sp=4)
    if t > 1.4:
        paste_pop(base, stamp_card(["KENDİ ÜLKESİ", "ÖLDÜRDÜ"], 760, 260, RED, seed=11, sizes=[84, 84], bg=BG), W / 2, 760, t - 1.4, rot=-4)
    if t > 2.0:
        spaced_text(dr, (W / 2, 1080), "Adı ancak 1990'da temize çıkarıldı.", font(FI, 48), CREAM + (a_(t, 2.0, 0.4),))
    return base.convert("RGB")

def s11(t, dur):  # ending question
    base = Image.new("RGBA", (W, H), (13, 10, 7, 255)); dr = ImageDraw.Draw(base, "RGBA")
    spaced_text(dr, (W / 2, 560), "Mahkûm 4859.", font(FI, 62), CREAM + (a_(t, 0.0, 0.4),))
    p = back(t / 0.45); s = int(76 * (0.6 + 0.4 * p))
    spaced_text(dr, (W / 2, 760), "BİR ÜLKE KENDİ", font(FB, max(10, s)), GOLD + (a_(t, 0.2, 0.25),), sp=6)
    spaced_text(dr, (W / 2, 880), "KAHRAMANINA", font(FB, max(10, s)), GOLD + (a_(t, 0.2, 0.25),), sp=6)
    spaced_text(dr, (W / 2, 1020), "BUNU NASIL YAPAR?", font(FB, max(10, s)), (230, 80, 60, a_(t, 0.2, 0.25)), sp=6)
    return base.convert("RGB")

# durations in ORIGINAL voice seconds (sentence starts from the transcript)
_B = [0.0, 3.3, 5.1, 10.2, 12.98, 17.0, 20.6, 23.94, 29.08, 32.4, 35.6, 39.2]
_F = [s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11]
SCENES = [(f"s{i+1}", f, (_B[i + 1] - _B[i]) / SP) for i, f in enumerate(_F)]
XF = 0.3
STARTS = []; _a = 0.0
for _n, _f, _d in SCENES: STARTS.append(_a); _a += _d
TOTAL = _a
IMPACTS = {"s1": [1.5], "s2": [0.7], "s3": [3.9], "s4": [0.9], "s5": [2.3], "s6": [1.6], "s7": [1.4], "s8": [3.2],
           "s9": [2.1], "s10": [1.4], "s11": [0.2]}   # local ORIGINAL seconds

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
