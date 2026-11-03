"""Kaydırmalı gönderi: Asker ayı Wojtek (Polonya II. Kolordusu, 22. Topçu İkmal Bölüğü, 1942-1963).
Tasarım: scene.py (gerçeğe yakın sinematik çizim, sayfa başına tek cümle)."""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter
import scene as SC
from scene import Scene, C, S, W, H, WW, HH, F, F_BLACK, F_BOLD, F_SEMI, F_MONO, text_overlay, bear_upright, bear_sitting, soldier, Shape, noise2

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "posts", "2026-11-07_wojtek")
N = 6
BEAR = C(58, 38, 24); BEAR_DARK = C(30, 20, 13); SIL = C(22, 16, 12)

def s1():
    sc = Scene()
    sc.sky([(0, C(40, 52, 82)), (520, C(196, 112, 70)), (820, C(250, 190, 110)), (900, C(255, 214, 150))])
    sc.glow(700, 830, 520, C(255, 160, 80), 0.55, core=46)
    sc.clouds(280, 560, C(150, 80, 70), 0.45, seed=4)
    sc.ridge(880, 160, C(150, 92, 78), seed=2, haze=C(240, 170, 120), haze_h=200, sharp=0.9)
    sc.ridge(950, 110, C(92, 56, 44), seed=5, haze=C(200, 120, 90), haze_h=120)
    sc.fog(900, 1010, C(240, 170, 120), 0.35)
    sc.ground(990, C(64, 40, 28), C(24, 16, 12))
    m = SC.outline_mask("soldier", 330, 1030, 0.62, extra=SC.rifle)
    sc.figure(m, SIL, C(255, 190, 120), light=(1, -0.2), rim_w=3)
    b = SC.outline_mask("bear_up", 560, 1032, 0.66, fuzz=0.5, seed=3)
    sc.figure(b, BEAR_DARK, C(255, 180, 110), light=(1, -0.2), rim_w=4, fur=0.25, seed=3)
    im = sc.finish(warm=0.03)
    return text_overlay(im, "Polonya ordusunun en tuhaf askeri", title="ASKER AYI", sub="WOJTEK · 1942–1963", page=1, total=N)

def s2():
    sc = Scene()
    sc.sky([(0, C(70, 92, 128)), (500, C(170, 160, 160)), (820, C(236, 200, 160)), (900, C(248, 222, 180))])
    sc.glow(240, 860, 420, C(255, 200, 140), 0.5, core=30)
    sc.clouds(200, 480, C(210, 180, 170), 0.35, seed=8)
    sc.ridge(860, 230, C(150, 140, 150), seed=12, haze=C(230, 205, 185), haze_h=260, sharp=0.8)
    sc.ridge(930, 120, C(120, 100, 96), seed=14, haze=C(210, 180, 160), haze_h=140)
    sc.fog(880, 980, C(240, 215, 190), 0.4)
    sc.ground(970, C(150, 118, 88), C(60, 44, 32), seed=4)
    m = SC.outline_mask("soldier", 700, 1060, 0.66, flip=True, extra=SC.rifle)
    sc.figure(m, SIL, C(255, 214, 160), light=(-1, -0.2), rim_w=3)
    b = SC.outline_mask("bear_sit", 440, 1064, 0.4, fuzz=0.6, seed=5)
    sc.figure(b, C(84, 58, 36), C(255, 214, 160), light=(-1, -0.2), rim_w=3, fur=0.3, seed=5)
    im = sc.finish(warm=0.02)
    return text_overlay(im, "1942, İran. Polonyalı askerler yavru bir ayı satın aldı", page=2, total=N)

def s3():
    rng = np.random.default_rng(7)
    sc = Scene()
    # ahşap masa
    g = noise2(HH // 16, WW // 2, 8, 4, 31); g = SC.up(g)
    stripes = np.sin(sc.yy / (9 * S) + g * 14) * 0.5 + 0.5
    wood = C(92, 58, 34)[None, None] * (0.72 + 0.35 * stripes[..., None]) * (0.9 + 0.2 * SC.up(noise2(HH // 4, WW // 4, 20, 3, 2))[..., None])
    sc.img[:] = wood
    sc.glow(420, 420, 900, C(255, 210, 150), 0.25)
    # defter (ayrı tuvalde çizip döndür)
    pw, ph = 720 * S, 900 * S
    paper = Image.new("RGBA", (pw, ph), (0, 0, 0, 0)); d = ImageDraw.Draw(paper)
    d.rounded_rectangle([0, 0, pw - 1, ph - 1], 14 * S, fill=(226, 212, 178, 255))
    pa = np.asarray(paper, np.float32) / 255.0
    n = noise2(ph // 2, pw // 2, 25, 5, 3); n = SC.up(n, ph, pw)
    stain = SC.up(noise2(ph // 8, pw // 8, 12, 3, 9), ph, pw)
    pa[..., :3] *= (0.93 + 0.1 * n[..., None]) * (1 - 0.08 * np.clip((stain - 0.55) * 4, 0, 1))[..., None]
    yy, xx = np.mgrid[0:ph, 0:pw]
    edge = np.minimum.reduce([xx, yy, pw - xx, ph - yy]) / (40 * S)
    pa[..., :3] *= (0.75 + 0.25 * np.clip(edge, 0, 1))[..., None]
    paper = Image.fromarray((pa * 255).astype(np.uint8), "RGBA"); d = ImageDraw.Draw(paper)
    ink = (40, 34, 30, 235)
    fm = F(F_MONO, 30); fs = F(F_MONO, 22)
    d.text((pw / 2, 70 * S), "KSIĄŻECZKA ŻOŁDOWA", font=F(F_MONO, 38), fill=ink, anchor="ma")
    d.line([(60 * S, 130 * S), (pw - 60 * S, 130 * S)], fill=ink, width=2 * S)
    rows = [("Nazwisko", "WOJTEK"), ("Stopień", "szeregowiec"), ("Jednostka", "22 Komp. Zaop. Art."), ("Rok", "1942")]
    for i, (k, v) in enumerate(rows):
        y = (200 + i * 92) * S
        d.text((70 * S, y), k + ":", font=fs, fill=(70, 60, 52, 230))
        d.text((300 * S, y - 4 * S), v, font=fm, fill=(28, 34, 70, 240))
        d.line([(290 * S, y + 40 * S), (pw - 70 * S, y + 40 * S)], fill=(90, 80, 70, 120), width=S)
    # pati izi (mürekkep)
    paw = Image.new("L", (pw, ph), 0); dp = ImageDraw.Draw(paw)
    cx, cy = pw / 2 + 90 * S, 690 * S
    dp.ellipse([cx - 95 * S, cy - 55 * S, cx + 95 * S, cy + 85 * S], fill=255)
    for k, (ox, oy) in enumerate([(-110, -90), (-58, -140), (0, -158), (58, -140), (110, -90)]):
        dp.ellipse([cx + (ox - 30) * S, cy + (oy - 34) * S, cx + (ox + 30) * S, cy + (oy + 34) * S], fill=255)
    pm = np.asarray(paw, np.float32) / 255.0
    pn = SC.up(noise2(ph // 2, pw // 2, 4, 3, 77), ph, pw)
    pm = np.clip(gaussian_filter(pm, 2 * S) * (0.55 + 0.6 * pn), 0, 0.85)
    pa = np.asarray(paper, np.float32) / 255.0
    pa[..., :3] = pa[..., :3] * (1 - pm[..., None]) + np.array([0.42, 0.10, 0.10]) * pm[..., None]
    paper = Image.fromarray((np.clip(pa, 0, 1) * 255).astype(np.uint8), "RGBA").rotate(-4, resample=Image.BICUBIC, expand=True)
    ra = np.asarray(paper, np.float32) / 255.0
    sh = gaussian_filter(ra[..., 3], 18 * S) * 0.65
    shadow = np.zeros_like(ra); shadow[..., 3] = sh
    sc.paste_rgba(shadow, 190, 150)
    sc.paste_rgba(ra, 170, 120)
    im = sc.finish(vignette=0.6, grain=0.03)
    return text_overlay(im, "Orduya er olarak yazıldı. Maaş defteri bile vardı", page=3, total=N)

def fire(sc, cx, cy, size):
    sc.glow(cx, cy - size * 0.4, size * 7, C(255, 120, 40), 0.55)
    sc.glow(cx, cy - size * 0.3, size * 2, C(255, 170, 70), 0.6)
    for k, (c, sc_) in enumerate([(C(255, 110, 30), 1.0), (C(255, 180, 60), 0.7), (C(255, 240, 180), 0.4)]):
        fl = Shape(cx, cy, size / 100 * sc_)
        fl.poly([(-60, 0), (-40, -60), (-20, -40), (-10, -130), (10, -70), (30, -110), (60, 0)])
        m = fl.mask(0, 0.0, soft=4 / sc_)
        sc.img = sc.img * (1 - m[..., None]) + c * m[..., None]

def s4():
    sc = Scene()
    sc.sky([(0, C(8, 12, 26)), (700, C(20, 26, 46)), (900, C(36, 34, 46))])
    rng = np.random.default_rng(3)
    for _ in range(260):
        x, y = rng.integers(0, WW), rng.integers(0, 680 * S); r = rng.random()
        sc.img[y:y + 2, x:x + 2] += 0.4 + 0.6 * r
    sc.ridge(900, 140, C(18, 20, 30), seed=21, haze=C(40, 40, 56), haze_h=120)
    sc.ground(960, C(30, 22, 18), C(10, 8, 6), seed=6)
    fire(sc, 560, 1040, 120)
    lg = Shape(560, 1048, 1.0); lg.cap(-80, 0, 70, -18, 12); lg.cap(80, 0, -60, -20, 12)
    m = lg.mask(0, 0, soft=1); sc.img = sc.img * (1 - m[..., None]) + C(30, 18, 10) * m[..., None]
    b = SC.outline_mask("bear_drink", 330, 1060, 0.62, fuzz=0.5, seed=8)
    sc.figure(b, C(26, 18, 12), C(255, 150, 70), light=(1, 0.1), rim_w=4, fur=0.3, seed=8, rim_strength=1.2)
    bt = Shape(330, 1060, 0.62)
    bt.cap(318, -462, 396, -520, 13, 11)
    m = bt.mask(0, 0, soft=0.8)
    sc.img = sc.img * (1 - m[..., None]) + C(90, 48, 18) * m[..., None]
    s = SC.outline_mask("soldier_sit", 810, 1060, 0.55, flip=True)
    sc.figure(s, C(14, 12, 10), C(255, 150, 70), light=(-1, 0.1), rim_w=3, rim_strength=1.2)
    im = sc.finish(vignette=0.55)
    return text_overlay(im, "Biraya bayılırdı, sigara da yerdi", page=4, total=N)

def s5():
    sc = Scene()
    sc.sky([(0, C(90, 96, 104)), (500, C(170, 160, 146)), (850, C(214, 190, 160))])
    sc.glow(820, 300, 500, C(255, 220, 170), 0.35)
    sc.clouds(100, 500, C(130, 128, 126), 0.5, seed=31)
    sc.ridge(820, 200, C(140, 134, 126), seed=33, haze=C(196, 184, 166), haze_h=240, scale=700)
    hx, hy = 730, 470
    xs = np.arange(WW) / S
    d2 = np.maximum(np.abs(xs - hx) - 120, 0)
    top = hy + 380 * (1 - np.exp(-(d2 / 230) ** 2)) + 10 * SC.noise1(WW, 60 * S, 4, 3)
    hm = gaussian_filter((sc.yy >= (top * S)[None, :]).astype(np.float32), 1.5)
    hc = C(104, 100, 94) * (0.92 + 0.16 * SC.up(noise2(HH // 4, WW // 4, 25, 4, 34))[..., None])
    k = np.clip(1 - (sc.yy / S - top[None, :]) / 300, 0, 1)[..., None] * 0.35
    hc = hc * (1 - k) + C(190, 178, 160) * k
    sc.img = sc.img * (1 - hm[..., None]) + hc * hm[..., None]
    ab = Shape(hx, hy + 14, 1.0)
    ab.poly([(-130, 0), (-130, -44), (-70, -44), (-70, -66), (50, -66), (50, -50), (130, -50), (130, 0)])
    ab.poly([(-14, -66), (-14, -104), (4, -120), (22, -104), (22, -66)])
    m = ab.mask(0, 0, soft=1.0)
    sc.img = sc.img * (1 - m[..., None] * 0.9) + C(84, 80, 78) * m[..., None] * 0.9
    sc.smoke(hx - 40, hy - 150, 220, 160, C(80, 76, 74), 0.6, seed=41)
    sc.smoke(300, 650, 260, 200, C(150, 144, 136), 0.55, seed=42)
    sc.smoke(900, 700, 220, 180, C(120, 112, 104), 0.5, seed=43)
    sc.ridge(990, 90, C(70, 64, 56), seed=36, haze=C(150, 140, 126), haze_h=120)
    sc.fog(900, 1020, C(190, 178, 160), 0.35)
    sc.ground(1000, C(66, 56, 44), C(28, 24, 20), seed=8)
    b = SC.outline_mask("bear_carry", 250, 1090, 0.58, fuzz=0.5, seed=9)
    sc.figure(b, C(46, 32, 22), C(240, 220, 190), light=(1, -0.8), rim_w=3, fur=0.3, seed=9, rim_strength=0.8)
    cr = Shape(250, 1090, 0.58)
    cr.poly([(225, -415), (395, -415), (395, -575), (225, -575)])
    m = cr.mask(0, 0, soft=0.8)
    wood = C(120, 92, 60) * (0.85 + 0.3 * SC.up(noise2(HH // 2, WW // 8, 3, 2, 5))[..., None])
    sc.img = sc.img * (1 - m[..., None]) + wood * m[..., None]
    for yy in (-470, -525):
        ln = Shape(250, 1090, 0.58); ln.poly([(225, yy), (395, yy), (395, yy - 6), (225, yy - 6)])
        mm = ln.mask(0, 0, soft=0.5); sc.img = sc.img * (1 - 0.6 * mm[..., None]) + C(60, 44, 30) * 0.6 * mm[..., None]
    im = sc.finish(vignette=0.5, warm=0.01)
    return text_overlay(im, "Monte Cassino, 1944. Mermi sandıkları taşıdığı anlatılır", page=5, total=N)

def s6():
    sc = Scene()
    n = SC.up(noise2(HH // 2, WW // 2, 2, 3, 61))
    weave = (np.sin(sc.xx / 3) * np.sin(sc.yy / 3)) * 0.04
    sc.img[:] = C(62, 66, 44)[None, None] * (0.85 + 0.25 * n[..., None] + weave[..., None])
    sc.glow(540, 560, 700, C(255, 230, 180), 0.18)
    # yuvarlak arma
    cx, cy, R = 540, 560, 330
    d = np.hypot(sc.xx - cx * S, sc.yy - cy * S) / S
    ring = np.clip((R - d) / 2, 0, 1)
    sh = gaussian_filter(ring, 14 * S) * 0.6
    sc.img *= (1 - np.roll(np.roll(sh, 16 * S, 0), 8 * S, 1)[..., None] * 0.7)
    stitch = SC.up(noise2(HH // 4, WW // 4, 2, 2, 9))
    sc.img = sc.img * (1 - ring[..., None]) + C(30, 34, 38)[None, None] * (0.9 + 0.2 * stitch[..., None]) * ring[..., None]
    border = np.clip((R - d) / 2, 0, 1) * np.clip((d - (R - 18)) / 2, 0, 1)
    sc.img = sc.img * (1 - border[..., None]) + C(200, 180, 130) * border[..., None]
    b = SC.outline_mask("bear_carry", 430, 790, 0.5)
    emb = C(214, 160, 90)[None, None] * (0.9 + 0.2 * stitch[..., None])
    sc.img = sc.img * (1 - b[..., None]) + emb * b[..., None]
    sh2 = Shape(430, 790, 0.5)
    sh2.cap(300, -330, 430, -560, 52, 52)
    sh2.poly([(385, -585), (475, -535), (500, -680)])
    shm = sh2.mask(0, 0, soft=0.8)
    out = np.clip(gaussian_filter(shm, 6 * S) * 3, 0, 1)
    sc.img = sc.img * (1 - out[..., None]) + C(30, 34, 38) * out[..., None]
    sc.img = sc.img * (1 - shm[..., None]) + C(236, 214, 160) * shm[..., None]
    im = sc.finish(vignette=0.55, grain=0.03)
    im = text_overlay(im, "Birliğinin amblemi oldu. Sizce hayvanlar askere alınmalı mı?", page=6, total=N, line_size=46)
    return im

if __name__ == "__main__":
    which = sys.argv[1:] or ["1", "2", "3", "4", "5", "6"]
    fns = {"1": s1, "2": s2, "3": s3, "4": s4, "5": s5, "6": s6}
    os.makedirs(OUT, exist_ok=True)
    for k in which:
        if k in fns: fns[k]().save(os.path.join(OUT, f"{k}.jpg"), quality=93)
