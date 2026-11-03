"""Ferman Tarih kaydırmalı gönderi (carousel) yardımcıları. 1080x1350 (4:5), parşömen tarzı."""
import os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from make import parchment, noise_img, stamp_card, spaced_text, font, FB, FI, FR, INK, RED, CREAM

W, H = 1080, 1350
GOLD = (222, 180, 96)
DARK_BG = (24, 18, 13)

_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_d = np.sqrt(((_xx - W / 2) / (W * 0.62)) ** 2 + ((_yy - H / 2) / (H * 0.62)) ** 2)
VIG = np.clip(1.06 - 0.5 * _d ** 2.2, 0.4, 1.0)[..., None].astype(np.float32)
GRAIN = noise_img(W, H, 2, 12, 77)[..., None].astype(np.float32)

def slide(dark=False, seed=0):
    if dark:
        a = np.zeros((H, W, 3), np.float32) + np.array(DARK_BG, np.float32) + noise_img(W, H, 60, 14, seed)[..., None]
    else:
        a = parchment(W, H, (236, 222, 186), seed + 3)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")

def finish(img):
    a = np.asarray(img.convert("RGB"), np.float32) * VIG + GRAIN
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def wrap(text, fnt, maxw):
    out = []
    for para in text.split("\n"):
        cur = ""
        for w in para.split():
            cand = (cur + " " + w).strip()
            if fnt.getlength(cand) > maxw and cur:
                out.append(cur); cur = w
            else:
                cur = cand
        out.append(cur)
    return out

def text_block(img, text, y, size=52, color=INK, f=FR, maxw=900, gap=14, align="center"):
    d = ImageDraw.Draw(img, "RGBA"); fnt = font(f, size)
    for ln in wrap(text, fnt, maxw):
        if align == "center":
            d.text((W / 2, y), ln, font=fnt, fill=color + (255,) if len(color) == 3 else color, anchor="mt")
        else:
            d.text(((W - maxw) / 2, y), ln, font=fnt, fill=color + (255,) if len(color) == 3 else color, anchor="lt")
        y += size + gap
    return y

def heading(img, text, y, size=76, color=INK, sp=4):
    d = ImageDraw.Draw(img, "RGBA"); fnt = font(FB, size)
    for ln in wrap(text, fnt, 960):
        spaced_text(d, (W / 2, y + size / 2), ln, fnt, color + (255,), sp=sp); y += size + 16
    return y

def stamp(img, lines, cx, cy, w=760, h=170, col=RED, sizes=None, rot=-3, seed=1):
    c = stamp_card(lines, w, h, col, seed=seed, sizes=sizes, bg=(240, 228, 196, 240)).rotate(rot, resample=Image.BICUBIC, expand=True)
    img.alpha_composite(c, (int(cx - c.width / 2), int(cy - c.height / 2)))

def frame(img, dark=False):
    d = ImageDraw.Draw(img, "RGBA"); col = GOLD if dark else (150, 30, 30)
    d.rectangle([28, 28, W - 28, H - 28], outline=col + (200,), width=5)
    d.rectangle([42, 42, W - 42, H - 42], outline=col + (90,), width=2)

def footer(img, page, total, dark=False):
    d = ImageDraw.Draw(img, "RGBA"); col = (CREAM if dark else INK)
    d.text((W / 2, H - 78), "@fermantarih", font=font(FB, 30), fill=col + (170,), anchor="mm")
    d.text((W - 80, H - 78), f"{page}/{total}", font=font(FB, 28), fill=col + (140,), anchor="rm")
    if page < total:
        d.text((80, H - 78), "kaydır →", font=font(FI, 28), fill=col + (150,), anchor="lm")

def save_all(slides, outdir):
    os.makedirs(outdir, exist_ok=True); paths = []
    for i, s in enumerate(slides, 1):
        frame(s, getattr(s, "_dark", False))
        footer(s, i, len(slides), getattr(s, "_dark", False))
        p = os.path.join(outdir, f"{i}.jpg"); finish(s).save(p, quality=92); paths.append(p)
    return paths
