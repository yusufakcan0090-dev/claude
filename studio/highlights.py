"""Öne çıkan hikâye kapakları: lacivert zemin, altın halka, ortada sade simge (küçük boyutta okunur)."""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from make import parchment

OUT = os.path.dirname(os.path.abspath(__file__))
S = 1080
GOLD = (222, 180, 96)

def base():
    a = parchment(S, S, (22, 34, 66), 61)
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    d = np.sqrt((xx - S / 2) ** 2 + (yy - S / 2) ** 2) / (S / 2)
    a = a * np.clip(1.1 - 0.4 * d ** 2, 0.4, 1)[..., None]
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(im, "RGBA"); c = S / 2
    d.ellipse([c - 470, c - 470, c + 470, c + 470], outline=GOLD + (255,), width=14)
    d.ellipse([c - 440, c - 440, c + 440, c + 440], outline=GOLD + (120,), width=3)
    return im

def shadowed(im, layer):
    a = layer.getchannel("A"); sh = Image.new("RGBA", (S, S), (0, 0, 0, 0)); sm = Image.new("L", (S, S), 0)
    sm.paste(a, (8, 14)); sh.putalpha(sm.filter(ImageFilter.GaussianBlur(10)).point(lambda v: v * 150 // 255))
    im.alpha_composite(sh); im.alpha_composite(layer); return im

def crescent_star(color):
    s = 3; L = Image.new("RGBA", (S * s, S * s), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    c = S * s / 2; R = 250 * s
    d.ellipse([c - 120 * s - R, c - R, c - 120 * s + R, c + R], fill=color + (255,))
    r2 = 205 * s; o = 60 * s
    d.ellipse([c - 120 * s + o - r2, c - r2, c - 120 * s + o + r2, c + r2], fill=(0, 0, 0, 0))
    cx, cy, rr = c + 230 * s, c, 105 * s
    pts = [(cx + math.cos(math.pi + i * math.pi / 5) * (rr if i % 2 == 0 else rr * 0.382),
            cy + math.sin(math.pi + i * math.pi / 5) * (rr if i % 2 == 0 else rr * 0.382)) for i in range(10)]
    d.polygon(pts, fill=color + (255,))
    return L.resize((S, S), Image.LANCZOS)

def dome():
    """Gold mosque silhouette: dome, two minarets (Ottoman)."""
    s = 3; L = Image.new("RGBA", (S * s, S * s), (0, 0, 0, 0)); d = ImageDraw.Draw(L); g = GOLD + (255,)
    c = S * s / 2; y0 = 720 * s
    d.rectangle([c - 260 * s, 560 * s, c + 260 * s, y0], fill=g)                  # body
    d.pieslice([c - 230 * s, 330 * s, c + 230 * s, 790 * s], 180, 360, fill=g)    # dome
    d.rectangle([c - 8 * s, 260 * s, c + 8 * s, 340 * s], fill=g)                 # finial
    d.ellipse([c - 22 * s, 230 * s, c + 22 * s, 274 * s], fill=g)
    for mx in (c - 340 * s, c + 340 * s):                                          # minarets
        d.rectangle([mx - 22 * s, 300 * s, mx + 22 * s, y0], fill=g)
        d.polygon([(mx - 26 * s, 300 * s), (mx + 26 * s, 300 * s), (mx, 190 * s)], fill=g)
        d.rectangle([mx - 34 * s, 420 * s, mx + 34 * s, 440 * s], fill=g)
    d.rectangle([c - 380 * s, y0, c + 380 * s, y0 + 24 * s], fill=g)                # ground line
    for k in (-1, 0, 1):                                                            # arches
        ax = c + k * 150 * s
        d.pieslice([ax - 50 * s, 590 * s, ax + 50 * s, 690 * s], 180, 360, fill=(22, 34, 66, 255))
        d.rectangle([ax - 50 * s, 640 * s, ax + 50 * s, y0], fill=(22, 34, 66, 255))
    return L.resize((S, S), Image.LANCZOS)

def compass():
    s = 3; L = Image.new("RGBA", (S * s, S * s), (0, 0, 0, 0)); d = ImageDraw.Draw(L); c = S * s / 2
    for ang, ln, w in [(0, 330, 70), (90, 330, 70), (180, 330, 70), (270, 330, 70), (45, 200, 50), (135, 200, 50), (225, 200, 50), (315, 200, 50)]:
        a = math.radians(ang - 90)
        tip = (c + math.cos(a) * ln * s, c + math.sin(a) * ln * s)
        l = (c + math.cos(a + 1.57) * w * s, c + math.sin(a + 1.57) * w * s)
        r = (c + math.cos(a - 1.57) * w * s, c + math.sin(a - 1.57) * w * s)
        d.polygon([tip, l, (c, c)], fill=GOLD + (255,))
        d.polygon([tip, r, (c, c)], fill=(170, 130, 60, 255))
    d.ellipse([c - 260 * s, c - 260 * s, c + 260 * s, c + 260 * s], outline=GOLD + (255,), width=12 * s)
    d.ellipse([c - 30 * s, c - 30 * s, c + 30 * s, c + 30 * s], fill=(22, 34, 66, 255), outline=GOLD + (255,), width=6 * s)
    return L.resize((S, S), Image.LANCZOS)

covers = {"kapak_dogu_turkistan.png": crescent_star((110, 180, 235)),
          "kapak_osmanli.png": dome(),
          "kapak_haritalar.png": compass()}
os.makedirs(os.path.join(OUT, "kapaklar"), exist_ok=True)
ims = []
for name, layer in covers.items():
    im = shadowed(base(), layer).convert("RGB"); im.save(os.path.join(OUT, "kapaklar", name)); ims.append(im)
sheet = Image.new("RGB", (3 * 300, 300), (0, 0, 0))
for i, im in enumerate(ims):
    t = im.resize((260, 260), Image.LANCZOS); m = Image.new("L", (260, 260), 0); ImageDraw.Draw(m).ellipse([0, 0, 259, 259], fill=255)
    sheet.paste(t, (i * 300 + 20, 20), m)
sheet.save(os.path.join(OUT, "kapaklar", "onizleme.png"))
print("ok")
