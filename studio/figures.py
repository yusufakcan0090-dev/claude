"""Renkli, yumuşak kenarlı karakter çizimleri (1906 Prusya subayı, asker, ayakkabıcı, sivil).
Her figür bir kez yüksek çözünürlükte çizilir, sonra ölçeklenip önbelleğe alınır.
Kullanım: put(base, "officer", x, y_ayak, yukseklik_px, alpha=255, dark=0.0)
"""
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

U = 2                     # pixels per unit at master resolution
CW, CH = 440, 1040        # canvas in units (x: -220..220, y: 0..1040, feet at 1000)

SKIN = (228, 188, 150); SKIN_D = (196, 150, 112)
HAIR = (70, 48, 34)
BLUE = (34, 46, 80); BLUE_D = (24, 32, 58); BLUE_L = (52, 68, 112)
RED = (170, 34, 34)
GOLD = (222, 176, 86); GOLD_D = (170, 126, 52)
SILVER = (200, 204, 210)
BLACK = (22, 20, 20); BLACK_L = (58, 54, 52)
GREY = (92, 88, 84); GREY_D = (66, 62, 60)
BROWN = (110, 74, 44); BROWN_D = (80, 52, 30)
TAN = (176, 132, 84); TAN_D = (140, 100, 60)
SHIRT = (232, 226, 210)
WOOD = (120, 78, 40)

def _p(pts): return [((x + CW / 2) * U, y * U) for x, y in pts]
def _box(x0, y0, x1, y1): return [(x0 + CW / 2) * U, y0 * U, (x1 + CW / 2) * U, y1 * U]

class Pen:
    def __init__(self, d): self.d = d
    def poly(self, pts, fill, outline=None, w=0): self.d.polygon(_p(pts), fill=fill, outline=outline, width=w * U)
    def ell(self, x0, y0, x1, y1, fill, outline=None, w=0): self.d.ellipse(_box(x0, y0, x1, y1), fill=fill, outline=outline, width=w * U)
    def rect(self, x0, y0, x1, y1, fill, r=0):
        if r: self.d.rounded_rectangle(_box(x0, y0, x1, y1), r * U, fill=fill)
        else: self.d.rectangle(_box(x0, y0, x1, y1), fill=fill)
    def line(self, pts, fill, w): self.d.line(_p(pts), fill=fill, width=int(w * U), joint="curve")
    def arc(self, x0, y0, x1, y1, a0, a1, fill, w): self.d.arc(_box(x0, y0, x1, y1), a0, a1, fill=fill, width=int(w * U))
    def pie(self, x0, y0, x1, y1, a0, a1, fill): self.d.pieslice(_box(x0, y0, x1, y1), a0, a1, fill=fill)

def head(p, mustache=True, hair=True):
    p.rect(-22, 222, 22, 268, SKIN_D)                                   # neck
    p.ell(-60, 160, -40, 200, SKIN_D); p.ell(40, 160, 60, 200, SKIN_D)  # ears
    p.ell(-50, 112, 50, 240, SKIN)                                      # face
    if hair: p.pie(-52, 108, 52, 190, 180, 360, HAIR)
    p.rect(-30, 166, -12, 171, HAIR, 2); p.rect(12, 166, 30, 171, HAIR, 2)   # brows
    p.ell(-25, 176, -15, 186, BLACK); p.ell(15, 176, 25, 186, BLACK)        # eyes
    p.poly([(-4, 186), (4, 186), (8, 204), (-8, 204)], SKIN_D)            # nose
    if mustache:  # upturned "Kaiser" mustache
        p.poly([(0, 206), (-14, 204), (-30, 208), (-44, 196), (-48, 186), (-40, 200), (-28, 216), (-10, 216), (0, 212)], HAIR)
        p.poly([(0, 206), (14, 204), (30, 208), (44, 196), (48, 186), (40, 200), (28, 216), (10, 216), (0, 212)], HAIR)
    p.arc(-12, 214, 12, 230, 20, 160, SKIN_D, 3)                          # mouth

def tunic(p, col, col_d, trim=RED, officer=False):
    # torso with shoulders, waist and skirt
    p.poly([(-120, 290), (-96, 262), (96, 262), (120, 290), (110, 420), (86, 520), (104, 610), (-104, 610), (-86, 520), (-110, 420)], col)
    p.poly([(0, 262), (96, 262), (120, 290), (110, 420), (86, 520), (104, 610), (0, 610)], col_d)  # right-side shade
    p.rect(-44, 248, 44, 282, trim, 8)                                   # stand collar
    p.line([(0, 282), (0, 610)], col_d, 4)
    for i in range(7): p.ell(-8, 300 + i * 30, 8, 316 + i * 30, GOLD)    # buttons
    p.rect(-92, 500, 92, 528, BLACK if not officer else SILVER)          # belt
    p.rect(-20, 498, 20, 530, GOLD, 4)                                   # buckle
    if officer:
        p.ell(-128, 262, -76, 292, SILVER); p.ell(76, 262, 128, 292, SILVER)   # epaulettes
        p.line([(-110, 300), (90, 500)], SILVER, 10)                           # sash
    else:
        p.rect(-122, 270, -86, 286, trim, 4); p.rect(86, 270, 122, 286, trim, 4)  # shoulder straps

def arms(p, col, col_d, cuff, hands=True, right_hand_y=590):
    p.poly([(-120, 290), (-96, 290), (-112, 548), (-150, 548), (-140, 300)], col)
    p.poly([(120, 290), (96, 290), (112, 548), (150, 548), (140, 300)], col_d)
    p.rect(-152, 530, -110, 560, cuff, 6); p.rect(110, 530, 152, 560, cuff, 6)
    if hands:
        p.ell(-150, 552, -110, 600, SKIN); p.ell(110, 552, 150, 600, SKIN_D)

def legs(p, col, col_d, stripe=None, boots=BLACK, boot_top=850):
    p.poly([(-96, 600), (-6, 600), (-12, 900), (-78, 900)], col)
    p.poly([(96, 600), (6, 600), (12, 900), (78, 900)], col_d)
    if stripe:
        p.line([(-90, 610), (-76, 860)], stripe, 6); p.line([(90, 610), (76, 860)], stripe, 6)
    p.poly([(-82, boot_top), (-10, boot_top), (-12, 990), (-84, 990)], boots)
    p.poly([(82, boot_top), (10, boot_top), (12, 990), (84, 990)], boots)
    p.ell(-104, 968, -8, 1004, boots); p.ell(8, 968, 104, 1004, boots)
    p.rect(-82, boot_top, -10, boot_top + 8, BLACK_L); p.rect(10, boot_top, 82, boot_top + 8, BLACK_L)

def officer(p):
    p.line([(108, 530), (160, 900)], SILVER, 12); p.ell(150, 890, 170, 910, SILVER)   # saber (behind)
    legs(p, BLUE, BLUE_D, stripe=RED)
    arms(p, BLUE, BLUE_D, RED)
    tunic(p, BLUE, BLUE_D, officer=True)
    p.rect(-6, 510, 12, 560, GOLD)                                                   # sword knot
    head(p)
    # peaked cap
    p.ell(-70, 70, 70, 128, BLUE_L); p.rect(-58, 100, 58, 136, BLUE)
    p.rect(-58, 112, 58, 134, RED); p.ell(-8, 112, 8, 128, GOLD)
    p.pie(-60, 120, 60, 168, 0, 180, BLACK)

def soldier(p):
    legs(p, BLUE, BLUE_D)
    # rifle on right shoulder, held by right hand
    p.line([(140, 120), (140, 880)], BLACK_L, 9); p.poly([(126, 600), (156, 600), (162, 900), (122, 900)], WOOD)
    arms(p, BLUE, BLUE_D, RED)
    tunic(p, BLUE, BLUE_D)
    p.rect(-84, 506, -46, 540, BROWN); p.rect(46, 506, 84, 540, BROWN)              # ammo pouches
    head(p, mustache=False, hair=False)
    # pickelhaube
    p.pie(-60, 70, 60, 200, 180, 360, BLACK); p.rect(-60, 128, 60, 138, BLACK)
    p.pie(-62, 124, 62, 160, 0, 180, BLACK)
    p.poly([(0, 82), (-24, 98), (-20, 128), (0, 136), (20, 128), (24, 98)], GOLD)      # front plate
    p.poly([(-10, 72), (10, 72), (0, 22)], GOLD); p.ell(-14, 64, 14, 80, GOLD)

def shoemaker(p):
    legs(p, GREY, GREY_D, boots=BROWN_D, boot_top=880)
    # shirt sleeves rolled up, forearms bare
    p.poly([(-120, 290), (-96, 290), (-104, 430), (-140, 430), (-140, 300)], SHIRT)
    p.poly([(120, 290), (96, 290), (104, 430), (140, 430), (140, 300)], SHIRT)
    p.rect(-144, 420, -100, 440, SHIRT, 8); p.rect(100, 420, 144, 440, SHIRT, 8)
    p.poly([(-138, 440), (-106, 440), (-112, 560), (-146, 560)], SKIN); p.poly([(138, 440), (106, 440), (112, 560), (146, 560)], SKIN_D)
    p.ell(-150, 550, -110, 598, SKIN); p.ell(110, 550, 150, 598, SKIN_D)
    # hammer in right hand
    p.line([(130, 580), (130, 470)], WOOD, 10); p.rect(104, 448, 160, 474, BLACK_L, 4)
    # shirt + vest + apron
    p.poly([(-120, 290), (-96, 262), (96, 262), (120, 290), (110, 420), (90, 600), (-90, 600), (-110, 420)], SHIRT)
    p.poly([(-118, 292), (-30, 270), (-14, 440), (-86, 520), (-108, 420)], BROWN)
    p.poly([(118, 292), (30, 270), (14, 440), (86, 520), (108, 420)], BROWN_D)
    p.poly([(-70, 340), (70, 340), (96, 600), (104, 800), (-104, 800), (-96, 600)], TAN)
    p.poly([(0, 340), (70, 340), (96, 600), (104, 800), (0, 800)], TAN_D)
    p.line([(-70, 340), (-36, 262)], TAN_D, 6); p.line([(70, 340), (36, 262)], TAN_D, 6)
    p.rect(-40, 560, 40, 640, TAN_D, 6)                                              # pocket
    head(p)
    # flat cap
    p.ell(-58, 96, 58, 150, BROWN_D); p.pie(-66, 128, 74, 166, 0, 180, BROWN_D)

def civilian(p):
    legs(p, GREY_D, GREY, boots=BLACK, boot_top=880)
    arms(p, GREY, GREY_D, GREY_D)
    p.poly([(-120, 290), (-96, 262), (96, 262), (120, 290), (110, 420), (100, 640), (-100, 640), (-110, 420)], GREY)
    p.poly([(0, 262), (96, 262), (120, 290), (110, 420), (100, 640), (0, 640)], GREY_D)
    p.poly([(-30, 262), (30, 262), (0, 380)], SHIRT)                                  # shirt V
    p.poly([(-10, 272), (10, 272), (6, 350), (-6, 350)], BLACK)                       # tie
    p.line([(-30, 262), (0, 420)], GREY_D, 6); p.line([(30, 262), (0, 420)], BLACK_L, 6)  # lapels
    head(p)

KINDS = {"officer": officer, "soldier": soldier, "shoemaker": shoemaker, "civilian": civilian}

@lru_cache(maxsize=8)
def master(kind):
    im = Image.new("RGBA", (CW * U, CH * U), (0, 0, 0, 0))
    KINDS[kind](Pen(ImageDraw.Draw(im)))
    return im

@lru_cache(maxsize=256)
def sprite(kind, h, dark=0.0):
    m = master(kind)
    w = max(1, round(m.width * h / m.height))
    im = m.resize((w, h), Image.LANCZOS)
    if dark:
        a = np.asarray(im, np.float32).copy()
        a[..., :3] = a[..., :3] * (1 - dark) + np.array([18, 14, 10], np.float32) * dark
        im = Image.fromarray(a.astype(np.uint8))
    return im

def put(base, kind, x, yfeet, h, alpha=255, dark=0.0, shadow=True):
    """Figürü ayakları (x, yfeet) noktasında olacak şekilde, toplam yükseklik h px ile yapıştırır."""
    if alpha <= 0: return
    h = int(round(h)); im = sprite(kind, h, round(dark, 2))
    if alpha < 255:
        a = np.asarray(im).copy(); a[..., 3] = (a[..., 3].astype(np.float32) * alpha / 255).astype(np.uint8); im = Image.fromarray(a)
    left = int(round(x - im.width / 2))
    if shadow:
        sw = int(h * 0.26); sh_ = max(4, int(h * 0.03))
        s = Image.new("RGBA", (sw * 2, sh_ * 4), (0, 0, 0, 0))
        ImageDraw.Draw(s).ellipse([sw * 0.1, sh_, sw * 1.9, sh_ * 3], fill=(0, 0, 0, int(70 * alpha / 255)))
        s = s.filter(ImageFilter.GaussianBlur(sh_ * 0.6))
        _comp(base, s, int(x - sw), int(yfeet - sh_ * 2))
    _comp(base, im, left, int(round(yfeet - h * 1000 / CH)))

def _comp(base, im, x, y):
    cx0, cy0 = max(0, -x), max(0, -y)
    cx1, cy1 = min(im.width, base.width - x), min(im.height, base.height - y)
    if cx1 <= cx0 or cy1 <= cy0: return
    base.alpha_composite(im.crop((cx0, cy0, cx1, cy1)), (x + cx0, y + cy0))
