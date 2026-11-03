"""Ferman Tarih kaydırmalı gönderi tasarımı v2: "GİZLİ DOSYA" (1080x1350).
Koyu zemin, kalın başlıklar, manila klasör, daktilo metni, fosforlu vurgu, polaroid çizimler, dev rakamlar.

Metinde **kelime** yazılırsa o kelime sarı fosforla vurgulanır.
"""
import os, math, re
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FD = os.path.join(HERE, "fonts")
W, H = 1080, 1350
F_BLACK = os.path.join(FD, "InterDisplay-Black.otf")
F_BOLD = os.path.join(FD, "InterDisplay-Bold.otf")
F_MED = os.path.join(FD, "Inter-Medium.otf")
F_SEMI = os.path.join(FD, "Inter-SemiBold.otf")
F_MONO = os.path.join(FD, "LiberationMono-Regular.ttf")
F_MONOB = os.path.join(FD, "LiberationMono-Bold.ttf")

BG = (17, 17, 19)
PAPER = (243, 238, 226)
MANILA = (214, 182, 122)
RED = (214, 38, 38)
INK = (24, 24, 26)
CREAM = (245, 240, 228)
MARKER = (255, 214, 10)
MUTED = (150, 146, 138)

_fc = {}
def F(path, size):
    k = (path, size)
    if k not in _fc: _fc[k] = ImageFont.truetype(path, size)
    return _fc[k]

def _noise(w, h, scale, amp, seed):
    r = np.random.default_rng(seed)
    sm = r.normal(0, 1, (h // scale + 2, w // scale + 2)).astype(np.float32)
    im = Image.fromarray(((sm - sm.min()) / np.ptp(sm) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return (np.asarray(im, np.float32) / 255 - 0.5) * amp

GRAIN = _noise(W, H, 2, 16, 5)[..., None]

def dark_bg(seed=0, glow=(120, 20, 20)):
    a = np.zeros((H, W, 3), np.float32) + np.array(BG, np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    g = np.exp(-(((xx - W * 0.85) / (W * 0.7)) ** 2 + ((yy - H * 0.1) / (H * 0.6)) ** 2))
    a += g[..., None] * np.array(glow, np.float32) * 0.55
    a += _noise(W, H, 80, 10, seed)[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")

def paper_tex(w, h, base=PAPER, seed=1):
    a = np.zeros((h, w, 3), np.float32) + np.array(base, np.float32)
    a += (_noise(w, h, 40, 14, seed) + _noise(w, h, 4, 8, seed + 1))[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")

def shadow(layer, off=(14, 20), blur=22, op=170):
    a = layer.getchannel("A"); sh = Image.new("RGBA", layer.size, (0, 0, 0, 0)); m = Image.new("L", layer.size, 0)
    m.paste(a, off); sh.putalpha(m.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: v * op // 255)); return sh

def place(base, layer, x, y, rot=0.0, sh=True):
    if rot: layer = layer.rotate(rot, resample=Image.BICUBIC, expand=True)
    if sh: base.alpha_composite(shadow(layer), (int(x), int(y)))
    base.alpha_composite(layer, (int(x), int(y)))

# ---------- text ----------
def _tokens(text):
    out = []
    for part in re.split(r"(\*\*.+?\*\*)", text):
        if part.startswith("**") and part.endswith("**"):
            out += [(w, True) for w in part[2:-2].split()]
        else:
            out += [(w, False) for w in part.split()]
    return out

def rich_text(img, text, x, y, maxw, size=40, path=F_MONO, color=INK, lh=1.38, align="left"):
    """Word-wrapped text with **marker** highlights. Returns bottom y."""
    d = ImageDraw.Draw(img, "RGBA"); fnt = F(path, size); sp = fnt.getlength(" ")
    lines, cur, cw = [], [], 0
    for w, hl in _tokens(text):
        ww = fnt.getlength(w)
        if cur and cw + sp + ww > maxw:
            lines.append((cur, cw)); cur, cw = [], 0
        cur.append((w, hl, ww)); cw += (sp if len(cur) > 1 else 0) + ww
    if cur: lines.append((cur, cw))
    step = int(size * lh)
    for ln, lw in lines:
        cx = x + (maxw - lw) / 2 if align == "center" else x
        # highlight boxes first
        px = cx
        for i, (w, hl, ww) in enumerate(ln):
            if hl:
                nxt = ln[i + 1][1] if i + 1 < len(ln) else False
                ext = sp if nxt else 0
                d.rectangle([px - 6, y + size * 0.12, px + ww + ext + 6, y + size * 1.08], fill=MARKER + (230,))
            px += ww + sp
        px = cx
        for w, hl, ww in ln:
            d.text((px, y), w, font=fnt, fill=(INK if hl else color) + (255,)); px += ww + sp
        y += step
    return y

def big_title(img, lines, x, y, size=104, colors=None, tracking=-2, align="left"):
    d = ImageDraw.Draw(img, "RGBA"); fnt = F(F_BLACK, size)
    colors = colors or [CREAM] * len(lines)
    for ln, col in zip(lines, colors):
        tw = sum(fnt.getlength(c) + tracking for c in ln) - tracking
        cx = x if align == "left" else (W - tw) / 2
        for c in ln:
            d.text((cx, y), c, font=fnt, fill=col + (255,)); cx += fnt.getlength(c) + tracking
        y += int(size * 1.02)
    return y

def kicker(img, text, x, y, color=RED, size=30, align="left"):
    d = ImageDraw.Draw(img, "RGBA"); fnt = F(F_MONOB, size); t = text.upper()
    tw = fnt.getlength(t)
    if align == "center": x = (W - tw) / 2 - 16
    d.rectangle([x, y, x + tw + 32, y + size + 18], fill=color + (255,))
    d.text((x + 16, y + 8), t, font=fnt, fill=(255, 255, 255, 255))
    return y + size + 18

# ---------- props ----------
def stamp(text, size=96, color=RED, rot=-12, pad=34, seed=3):
    fnt = F(F_BLACK, size); tw = fnt.getlength(text)
    w, h = int(tw + pad * 2), int(size * 1.25 + pad)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([5, 5, w - 6, h - 6], 16, outline=color + (255,), width=9)
    d.text((w / 2, h / 2), text, font=fnt, fill=color + (255,), anchor="mm")
    a = np.asarray(im).copy(); n = _noise(w, h, 5, 1, seed)
    a[..., 3] = (a[..., 3] * np.where(n > 0.2, 0.25, 1.0)).astype(np.uint8)
    im = Image.fromarray(a)
    return im.rotate(rot, resample=Image.BICUBIC, expand=True)

def folder(w=860, h=620, label="DOSYA", seed=2):
    tab_h = 70
    im = Image.new("RGBA", (w, h + tab_h), (0, 0, 0, 0))
    body = paper_tex(w, h, MANILA, seed)
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], 18, fill=255); body.putalpha(m)
    tab = paper_tex(300, tab_h + 20, MANILA, seed + 1)
    mt = Image.new("L", tab.size, 0); ImageDraw.Draw(mt).rounded_rectangle([0, 0, 299, tab_h + 30], 18, fill=255); tab.putalpha(mt)
    im.alpha_composite(tab, (40, 0)); im.alpha_composite(body, (0, tab_h))
    d = ImageDraw.Draw(im, "RGBA")
    d.text((60, 18), label, font=F(F_MONOB, 30), fill=(80, 58, 30, 255))
    d.line([(0, tab_h + 8), (w, tab_h + 8)], fill=(170, 140, 90, 255), width=3)
    return im

def polaroid(art, w=620, h=520, caption=None, seed=4):
    pw, ph = w + 50, h + (110 if caption else 50)
    im = paper_tex(pw, ph, (250, 248, 242), seed)
    im.alpha_composite(art.resize((w, h), Image.LANCZOS), (25, 25))
    if caption:
        ImageDraw.Draw(im).text((pw / 2, h + 70), caption, font=F(F_MONO, 32), fill=INK + (255,), anchor="mm")
    # tape
    t = Image.new("RGBA", (170, 54), (235, 225, 190, 170))
    im2 = Image.new("RGBA", (pw, ph + 30), (0, 0, 0, 0)); im2.alpha_composite(im, (0, 30))
    im2.alpha_composite(t.rotate(-6, expand=True), (int(pw / 2 - 90), 0))
    return im2

def art_canvas(w=620, h=520, bg=(212, 206, 190)):
    a = paper_tex(w, h, bg, 9); return a

def paperclip(base, x, y):
    d = ImageDraw.Draw(base, "RGBA"); c = (160, 165, 172, 255)
    d.rounded_rectangle([x, y, x + 46, y + 150], 23, outline=c, width=7)
    d.rounded_rectangle([x + 10, y + 20, x + 36, y + 120], 13, outline=c, width=6)

def redacted(base, x, y, widths, h=30):
    d = ImageDraw.Draw(base, "RGBA")
    for i, w in enumerate(widths):
        d.rectangle([x, y + i * (h + 16), x + w, y + i * (h + 16) + h], fill=INK + (255,))

def header(base, page, total, label, dark=False):
    d = ImageDraw.Draw(base, "RGBA"); col = (CREAM if dark else INK)
    d.text((70, 62), label.upper(), font=F(F_MONOB, 28), fill=col + (200,))
    d.text((W - 70, 62), f"{page:02d}/{total:02d}", font=F(F_MONOB, 28), fill=col + (200,), anchor="ra")

def footer(base, page, total, dark=True):
    d = ImageDraw.Draw(base, "RGBA"); col = (CREAM if dark else INK)
    d.text((70, H - 86), "@fermantarih", font=F(F_BOLD, 32), fill=col + (220,))
    if page < total:
        fnt = F(F_BOLD, 30); t = "kaydır"; tw = fnt.getlength(t)
        d.rounded_rectangle([W - 70 - tw - 90, H - 98, W - 70, H - 46], 26, fill=RED + (255,))
        d.text((W - 70 - tw - 66, H - 72), t, font=fnt, fill=(255, 255, 255, 255), anchor="lm")
        ax = W - 70 - 34
        d.polygon([(ax - 10, H - 84), (ax + 10, H - 72), (ax - 10, H - 60)], fill=(255, 255, 255, 255))

def sheet(seed=0, rot=-1.5):
    """Paper document on dark background; returns (base, paper_layer, paper_box)."""
    base = dark_bg(seed, glow=(60, 40, 20))
    pw, ph = 960, 1130
    p = paper_tex(pw, ph, PAPER, seed + 7)
    return base, p, pw, ph

def finish(img):
    a = np.asarray(img.convert("RGB"), np.float32) + GRAIN
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = np.clip(1.08 - 0.35 * (((xx - W / 2) / (W * 0.7)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2), 0.55, 1)[..., None]
    return Image.fromarray(np.clip(a * v, 0, 255).astype(np.uint8))

def save_all(slides, outdir):
    os.makedirs(outdir, exist_ok=True); out = []
    for i, s in enumerate(slides, 1):
        p = os.path.join(outdir, f"{i}.jpg"); finish(s).save(p, quality=92); out.append(p)
    return out

def contact_sheet(paths, out, cols=4, tw=360):
    th = int(tw * H / W); rows = math.ceil(len(paths) / cols)
    s = Image.new("RGB", (cols * tw, rows * th), (0, 0, 0))
    for i, p in enumerate(paths):
        s.paste(Image.open(p).resize((tw, th)), ((i % cols) * tw, (i // cols) * th))
    s.save(out); return out
