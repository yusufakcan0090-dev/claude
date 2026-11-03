"""Ferman Tarih kaydırmalı gönderi tasarımı v3: SAVAŞ AFİŞİ (1080x1350).
Az yazı, büyük görsel: güneş ışını arka planlar, kalın siyah siluetler, halftone baskı noktaları,
kırmızı / siyah / krem palet, baskı dokusu. Tüm çizimler 2x çözünürlükte yapılıp küçültülür (pürüzsüz kenar).
"""
import os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FD = os.path.join(HERE, "fonts")
W, H = 1080, 1350
S = 2                                 # supersampling
SW, SH = W * S, H * S
F_BLACK = os.path.join(FD, "InterDisplay-Black.otf")
F_BOLD = os.path.join(FD, "InterDisplay-Bold.otf")
F_SEMI = os.path.join(FD, "Inter-SemiBold.otf")

RED = (200, 34, 34)
DRED = (122, 18, 18)
BLACK = (20, 17, 17)
CREAM = (241, 231, 206)
MUSTARD = (232, 178, 58)
STEEL = (70, 74, 80)
WHITE = (255, 255, 255)

_fc = {}
def F(path, size):
    k = (path, size)
    if k not in _fc: _fc[k] = ImageFont.truetype(path, size * S)
    return _fc[k]

def _noise(w, h, scale, amp, seed):
    r = np.random.default_rng(seed)
    sm = r.normal(0, 1, (h // scale + 2, w // scale + 2)).astype(np.float32)
    im = Image.fromarray(((sm - sm.min()) / np.ptp(sm) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return (np.asarray(im, np.float32) / 255 - 0.5) * amp

# ---------- canvas ----------
def canvas(color=CREAM):
    return Image.new("RGBA", (SW, SH), color + (255,))

def P(x, y): return (x * S, y * S)                      # 1080-space -> 2x canvas

def rays(img, cx, cy, n=24, c1=RED, c2=DRED, rot=0.0):
    d = ImageDraw.Draw(img); R = 4000 * S; cx, cy = cx * S, cy * S
    d.rectangle([0, 0, SW, SH], fill=c2 + (255,))
    for i in range(n):
        if i % 2: continue
        a0 = rot + 2 * math.pi * i / n; a1 = rot + 2 * math.pi * (i + 1) / n
        d.polygon([(cx, cy), (cx + R * math.cos(a0), cy + R * math.sin(a0)), (cx + R * math.cos(a1), cy + R * math.sin(a1))], fill=c1 + (255,))

def halftone(img, box, color=BLACK, step=22, rmax=9, direction="down", alpha=255):
    """Dot pattern inside box (1080-space), dots grow toward the bottom (or top/left/right)."""
    x0, y0, x1, y1 = box; d = ImageDraw.Draw(img, "RGBA")
    yy = y0
    row = 0
    while yy <= y1:
        xx = x0 + (step / 2 if row % 2 else 0)
        while xx <= x1:
            t = {"down": (yy - y0) / max(1, y1 - y0), "up": (y1 - yy) / max(1, y1 - y0),
                 "right": (xx - x0) / max(1, x1 - x0), "left": (x1 - xx) / max(1, x1 - x0)}[direction]
            r = rmax * t
            if r > 0.6:
                d.ellipse([(xx - r) * S, (yy - r) * S, (xx + r) * S, (yy + r) * S], fill=color + (alpha,))
            xx += step
        yy += step * 0.866; row += 1

def band(img, y0, y1, color=BLACK, alpha=255):
    ImageDraw.Draw(img, "RGBA").rectangle([0, y0 * S, SW, y1 * S], fill=color + (alpha,))

# ---------- type ----------
def title(img, text, x, y, size=120, color=CREAM, anchor="la", tracking=-2, shadow=None):
    d = ImageDraw.Draw(img, "RGBA"); fnt = F(F_BLACK, size)
    tw = sum(fnt.getlength(c) for c in text) + tracking * S * (len(text) - 1)
    if anchor[0] == "m": x = x - tw / S / 2
    elif anchor[0] == "r": x = x - tw / S
    cx = x * S
    for c in text:
        if shadow: d.text((cx + 6 * S, y * S + 6 * S), c, font=fnt, fill=shadow + (255,))
        d.text((cx, y * S), c, font=fnt, fill=color + (255,)); cx += fnt.getlength(c) + tracking * S
    return y + size

def line(img, text, x, y, size=40, color=CREAM, path=None, anchor="la"):
    d = ImageDraw.Draw(img, "RGBA"); fnt = F(path or F_BOLD, size)
    d.text((x * S, y * S), text, font=fnt, fill=color + (255,), anchor=anchor)

def tag(img, text, x, y, size=30, bg=MUSTARD, fg=BLACK, anchor="la"):
    d = ImageDraw.Draw(img, "RGBA"); fnt = F(F_BLACK, size); tw = fnt.getlength(text) / S
    if anchor == "ma": x -= (tw + 36) / 2
    d.rectangle([x * S, y * S, (x + tw + 36) * S, (y + size + 22) * S], fill=bg + (255,))
    d.text(((x + 18) * S, (y + 9) * S), text, font=fnt, fill=fg + (255,))

def stamp(img, text, cx, cy, size=80, color=RED, rot=-12, seed=3):
    fnt = F(F_BLACK, size); tw = fnt.getlength(text); pad = 30 * S
    w, h = int(tw + pad * 2), int(size * S * 1.3 + pad)
    st = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(st)
    d.rounded_rectangle([6 * S, 6 * S, w - 6 * S, h - 6 * S], 14 * S, outline=color + (255,), width=8 * S)
    d.text((w / 2, h / 2), text, font=fnt, fill=color + (255,), anchor="mm")
    a = np.asarray(st).copy(); n = _noise(w, h, 6, 1, seed)
    a[..., 3] = (a[..., 3] * np.where(n > 0.22, 0.2, 1.0)).astype(np.uint8)
    st = Image.fromarray(a).rotate(rot, resample=Image.BICUBIC, expand=True)
    img.alpha_composite(st, (int(cx * S - st.width / 2), int(cy * S - st.height / 2)))

# ---------- silhouettes (drawn in local units, placed with scale) ----------
def _layer(w, h): return Image.new("RGBA", (int(w * S), int(h * S)), (0, 0, 0, 0))

def tank(scale=1.0, color=BLACK, rim=None, valve=False, hose=False):
    """Sherman-like tank silhouette, ~1100x620 local units at scale 1."""
    k = scale * S; L = _layer(1120 * scale, 640 * scale); d = ImageDraw.Draw(L)
    def p(pts): return [(x * k, (y + 120) * k) for x, y in pts]
    c = color + (255,)
    d.rounded_rectangle([20 * k, 330 * k + 120 * k, 960 * k, 480 * k + 120 * k], int(75 * k), fill=c)            # track
    d.polygon(p([(0, 330), (70, 205), (830, 205), (980, 270), (990, 335), (930, 365), (40, 365)]), fill=c)     # hull
    d.polygon(p([(290, 210), (325, 105), (430, 62), (640, 62), (720, 110), (735, 210)]), fill=c)              # turret
    d.rectangle([700 * k, (118 + 120) * k, 770 * k, (180 + 120) * k], fill=c)                                   # mantlet
    d.rectangle([745 * k, (134 + 120) * k, 1080 * k, (160 + 120) * k], fill=c)                                  # barrel
    d.rectangle([1050 * k, (124 + 120) * k, 1100 * k, (170 + 120) * k], fill=c)
    d.ellipse([450 * k, (30 + 120) * k, 560 * k, (78 + 120) * k], fill=c)                                       # hatch
    d.line([(380 * k, (66 + 120) * k), (320 * k, -100 * k + 120 * k)], fill=c, width=int(7 * k))               # antenna
    hole = (0, 0, 0, 0)
    if rim:                                                                                                     # wheels & details in rim color
        r_ = rim + (255,)
        for i in range(8):
            x = 120 + i * 105
            d.ellipse([(x - 40) * k, (365 + 120) * k, (x + 40) * k, (445 + 120) * k], outline=r_, width=int(6 * k))
        d.line([(80 * k, (335 + 120) * k), (900 * k, (335 + 120) * k)], fill=r_, width=int(4 * k))
        d.line([(330 * k, (150 + 120) * k), (700 * k, (150 + 120) * k)], fill=r_, width=int(3 * k))
    if valve:
        d.rectangle([180 * k, (150 + 120) * k, 205 * k, (210 + 120) * k], fill=c)
        d.ellipse([160 * k, (120 + 120) * k, 225 * k, (160 + 120) * k], fill=c)
    return L

def soldier(scale=1.0, color=BLACK, prop=None):
    """Standing soldier silhouette with M1-style helmet. prop: 'brush' | 'pump' | None. ~260x620 local."""
    k = scale * S; L = _layer(300 * scale, 640 * scale); d = ImageDraw.Draw(L); c = color + (255,)
    d.chord([60 * k, 10 * k, 200 * k, 120 * k], 180, 360, fill=c)                       # helmet dome
    d.rectangle([48 * k, 62 * k, 212 * k, 74 * k], fill=c)                               # brim
    d.ellipse([88 * k, 60 * k, 172 * k, 150 * k], fill=c)                                # head
    d.rectangle([115 * k, 140 * k, 145 * k, 170 * k], fill=c)                            # neck
    d.polygon([(70 * k, 170 * k), (190 * k, 170 * k), (205 * k, 360 * k), (55 * k, 360 * k)], fill=c)   # torso
    d.polygon([(60 * k, 350 * k), (128 * k, 350 * k), (120 * k, 610 * k), (70 * k, 610 * k)], fill=c)   # left leg
    d.polygon([(132 * k, 350 * k), (200 * k, 350 * k), (195 * k, 610 * k), (145 * k, 610 * k)], fill=c) # right leg
    d.rectangle([60 * k, 600 * k, 128 * k, 625 * k], fill=c); d.rectangle([145 * k, 600 * k, 215 * k, 625 * k], fill=c)
    d.polygon([(70 * k, 180 * k), (40 * k, 330 * k), (62 * k, 336 * k), (92 * k, 200 * k)], fill=c)    # left arm
    if prop == "brush":
        d.polygon([(185 * k, 180 * k), (260 * k, 120 * k), (272 * k, 136 * k), (200 * k, 210 * k)], fill=c)
        d.line([(262 * k, 126 * k), (295 * k, 40 * k)], fill=c, width=int(9 * k))
        d.polygon([(288 * k, 52 * k), (300 * k, 0 * k), (306 * k, 56 * k)], fill=RED + (255,))
    else:
        d.polygon([(190 * k, 180 * k), (220 * k, 330 * k), (198 * k, 336 * k), (170 * k, 200 * k)], fill=c)
    return L

def pump(scale=1.0, color=BLACK):
    k = scale * S; L = _layer(200 * scale, 320 * scale); d = ImageDraw.Draw(L); c = color + (255,)
    d.rectangle([80 * k, 90 * k, 120 * k, 300 * k], fill=c)
    d.rectangle([40 * k, 290 * k, 160 * k, 315 * k], fill=c)
    d.rectangle([96 * k, 20 * k, 104 * k, 100 * k], fill=c)
    d.rectangle([40 * k, 10 * k, 160 * k, 30 * k], fill=c)
    return L

def halftrack_speaker(scale=1.0, color=BLACK):
    k = scale * S; L = _layer(900 * scale, 560 * scale); d = ImageDraw.Draw(L); c = color + (255,)
    d.polygon([(0, 330 * k), (40 * k, 250 * k), (230 * k, 230 * k), (260 * k, 160 * k), (380 * k, 160 * k), (400 * k, 260 * k), (860 * k, 260 * k), (860 * k, 380 * k), (0, 380 * k)], fill=c)
    d.ellipse([60 * k, 330 * k, 200 * k, 470 * k], fill=c)
    d.rounded_rectangle([440 * k, 360 * k, 860 * k, 470 * k], int(55 * k), fill=c)
    d.rectangle([560 * k, 150 * k, 590 * k, 262 * k], fill=c)                              # mast
    d.polygon([(500 * k, 120 * k), (580 * k, 120 * k), (760 * k, 0), (760 * k, 260 * k), (580 * k, 160 * k), (500 * k, 160 * k)], fill=c)  # horn
    return L

def radio_tower(scale=1.0, color=BLACK):
    k = scale * S; L = _layer(420 * scale, 900 * scale); d = ImageDraw.Draw(L); c = color + (255,); w = int(10 * k)
    top, base = (210, 40), 880
    d.line([(top[0] * k, top[1] * k), (40 * k, base * k)], fill=c, width=w)
    d.line([(top[0] * k, top[1] * k), (380 * k, base * k)], fill=c, width=w)
    for i in range(1, 9):
        t = i / 9; y = top[1] + (base - top[1]) * t
        xl = top[0] + (40 - top[0]) * t; xr = top[0] + (380 - top[0]) * t
        d.line([(xl * k, y * k), (xr * k, y * k)], fill=c, width=int(6 * k))
        if i < 8:
            t2 = (i + 1) / 9; y2 = top[1] + (base - top[1]) * t2
            xl2 = top[0] + (40 - top[0]) * t2; xr2 = top[0] + (380 - top[0]) * t2
            d.line([(xl * k, y * k), (xr2 * k, y2 * k)], fill=c, width=int(4 * k))
            d.line([(xr * k, y * k), (xl2 * k, y2 * k)], fill=c, width=int(4 * k))
    d.ellipse([(top[0] - 22) * k, (top[1] - 22) * k, (top[0] + 22) * k, (top[1] + 22) * k], fill=RED + (255,))
    return L

def waves(img, cx, cy, radii, color=CREAM, width=14, a0=-50, a1=50, alpha=255):
    d = ImageDraw.Draw(img, "RGBA")
    for i, r in enumerate(radii):
        al = int(alpha * (1 - i / (len(radii) + 1)))
        d.arc([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], a0, a1, fill=color + (al,), width=width * S)

def put(img, layer, x, y, flip=False, rot=0.0, shadow=None):
    if flip: layer = layer.transpose(Image.FLIP_LEFT_RIGHT)
    if rot: layer = layer.rotate(rot, resample=Image.BICUBIC, expand=True)
    if shadow:
        sh = Image.new("RGBA", layer.size, shadow + (0,)); sh.putalpha(layer.getchannel("A").point(lambda v: v * 120 // 255))
        img.alpha_composite(sh, (int(x * S + 14 * S), int(y * S + 14 * S)))
    img.alpha_composite(layer, (int(x * S), int(y * S)))
    return layer.width / S, layer.height / S

# ---------- chrome ----------
def footer(img, page, total, dark=True):
    d = ImageDraw.Draw(img, "RGBA"); col = CREAM if dark else BLACK
    d.text((60 * S, (H - 70) * S), "@fermantarih", font=F(F_BOLD, 30), fill=col + (230,), anchor="lm")
    if page < total:
        d.text(((W - 60) * S, (H - 70) * S), f"{page}/{total}  →", font=F(F_BLACK, 30), fill=col + (230,), anchor="rm")

def finish(img, seed=0):
    im = img.resize((W, H), Image.LANCZOS).convert("RGB")
    a = np.asarray(im, np.float32)
    a += _noise(W, H, 2, 14, seed + 1)[..., None]                           # grain
    a *= (1 + _noise(W, H, 120, 0.10, seed + 2))[..., None]                 # print unevenness
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = np.clip(1.08 - 0.32 * (((xx - W / 2) / (W * 0.7)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2), 0.6, 1)[..., None]
    return Image.fromarray(np.clip(a * v, 0, 255).astype(np.uint8))

def save_all(slides, outdir):
    os.makedirs(outdir, exist_ok=True); out = []
    for i, s in enumerate(slides, 1):
        p = os.path.join(outdir, f"{i}.jpg"); finish(s, i).save(p, quality=92); out.append(p)
    return out

def contact_sheet(paths, out, cols=4, tw=360):
    th = int(tw * H / W); rows = math.ceil(len(paths) / cols)
    s = Image.new("RGB", (cols * tw, rows * th), (0, 0, 0))
    for i, p in enumerate(paths):
        s.paste(Image.open(p).resize((tw, th)), ((i % cols) * tw, (i // cols) * th))
    s.save(out); return out
