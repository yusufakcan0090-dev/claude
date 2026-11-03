"""Kaydırmalı gönderi (10 Kasım özel): Atatürk'ün 15 yıl süren son yolculuğu (1938-1953).
Kaynak: MEB "Atatürk'ün son yılları ve ölümü"; Küre Ansiklopedisi "Atatürk'ün naaşının İstanbul'dan Ankara'ya nakli".
Tasarım: scene.py (gerçeğe yakın sinematik çizim, sayfa başına tek cümle)."""
import os, sys, math
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter
import scene as SC
from scene import Scene, C, S, W, H, WW, HH, F, F_BLACK, F_BOLD, F_SEMI, text_overlay, Shape, noise2

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "posts", "2026-11-10_son_yolculuk")
N = 6
RED = C(200, 16, 46); WHITE = C(245, 242, 236)

def fill(sc, m, col, a=1.0):
    sc.img = sc.img * (1 - a * m[..., None]) + col * (a * m[..., None])

def flag(sc, x, y, w, h, wave=0.06, seed=0):
    """Türk bayrağı (dalgalı). (x,y) direğe bağlı sol üst köşe."""
    fl = Shape(0, 0, 1.0); d = fl.d
    pts_t, pts_b = [], []
    for i in range(41):
        t = i / 40; dy = math.sin(t * 5.5 + seed) * h * wave * t
        pts_t.append(((x + w * t) * S, (y + dy) * S)); pts_b.append(((x + w * t) * S, (y + h + dy) * S))
    d.polygon(pts_t + pts_b[::-1], fill=255)
    m = gaussian_filter(np.asarray(fl.im, np.float32) / 255, 0.7 * S)
    shade = 0.85 + 0.25 * np.sin((sc.xx / S - x) / w * 5.5 * 1.0 + seed)
    fill(sc, m, RED * shade[..., None] if False else RED, 1.0)
    sc.img = sc.img * (1 - m[..., None] * (1 - shade[..., None]) * 0.6)
    # hilal ve yıldız
    cs = Shape(0, 0, 1.0); g = h / 1.0
    cx, cy = x + w * 0.36, y + h / 2 + math.sin(0.36 * 5.5 + seed) * h * wave * 0.36
    r1, r2 = g * 0.25, g * 0.2
    cs.d.ellipse([(cx - r1) * S, (cy - r1) * S, (cx + r1) * S, (cy + r1) * S], fill=255)
    cs.d.ellipse([(cx - r2 + g * 0.0625) * S, (cy - r2) * S, (cx + r2 + g * 0.0625) * S, (cy + r2) * S], fill=0)
    sx, sy, R = cx + g * 0.333 - g * 0.0625 + 0.0, cy, g * 0.125
    star = []
    for k in range(10):
        a = math.pi + k * math.pi / 5; rr = R if k % 2 == 0 else R * 0.382
        star.append(((sx + rr * math.cos(a)) * S, (sy + rr * math.sin(a)) * S))
    cs.d.polygon(star, fill=255)
    m2 = gaussian_filter(np.asarray(cs.im, np.float32) / 255, 0.6 * S)
    fill(sc, m2, WHITE)

def pole(sc, x, y0, y1, w=6, col=C(30, 28, 30)):
    p = Shape(0, 0, 1.0); p.d.rectangle([(x - w / 2) * S, y1 * S, (x + w / 2) * S, y0 * S], fill=255)
    p.d.ellipse([(x - w) * S, (y1 - w * 1.6) * S, (x + w) * S, (y1 + w * 0.4) * S], fill=255)
    fill(sc, gaussian_filter(np.asarray(p.im, np.float32) / 255, 0.6 * S), col)

def sea(sc, y, c1, c2, seed=2, glint=None):
    m = np.clip((sc.yy - y * S) / (2 * S), 0, 1)
    k = np.clip((sc.yy - y * S) / ((H - y) * S), 0, 1)[..., None]
    col = c1 * (1 - k) + c2 * k
    n = SC.up(noise2(HH // 2, WW // 16, 2, 3, seed))
    ripple = gaussian_filter(n, (0.5, 8))
    col = col * (0.88 + 0.24 * ripple[..., None])
    if glint is not None:
        gx, gc = glint
        g = np.exp(-((sc.xx / S - gx) / 90) ** 2) * np.clip((ripple - 0.5) * 4, 0, 1) * (1 - k[..., 0] * 0.6)
        col = col + gc * g[..., None] * 0.7
    sc.img = sc.img * (1 - m[..., None]) + col * m[..., None]

class _D:
    def __init__(self, d): self.d = d
    def rectangle(self, xy, **k):
        (x0, y0), (x1, y1) = xy
        self.d.rectangle([min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)], **k)
    def __getattr__(self, n): return getattr(self.d, n)

def mask_of(fn, blur=0.7):
    sh = Shape(0, 0, 1.0); fn(_D(sh.d), lambda x, y: (x * S, y * S))
    return gaussian_filter(np.asarray(sh.im, np.float32) / 255, blur * S)

# ------------------------------------------------------------------ sayfalar
def s1():
    sc = Scene()
    sc.sky([(0, C(58, 70, 96)), (520, C(150, 150, 166)), (820, C(232, 196, 170)), (880, C(244, 214, 186))])
    sc.glow(830, 860, 380, C(255, 200, 150), 0.45, core=24)
    sc.clouds(250, 560, C(120, 118, 136), 0.4, seed=7)
    sc.ridge(880, 50, C(120, 112, 124), seed=40, haze=C(200, 180, 176), haze_h=60, scale=500)   # Asya yakası
    sea(sc, 880, C(150, 136, 140), C(30, 34, 48), glint=(830, C(255, 210, 160)))
    def palace(d, P):
        base = 905
        d.rectangle([P(40, base - 70), P(1040, base + 6)], fill=255)                     # uzun cephe
        d.rectangle([P(400, base - 130), P(680, base - 60)], fill=255)                   # Muayede salonu
        d.polygon([P(400, base - 130), P(540, base - 175), P(680, base - 130)], fill=255)
        for x in (60, 220, 820, 980):
            d.rectangle([P(x - 30, base - 92), P(x + 30, base - 66)], fill=255)
        for x in (300, 780):
            d.rectangle([P(x - 22, base - 112), P(x + 22, base - 66)], fill=255)
        d.rectangle([P(1000, base - 150), P(1030, base - 70)], fill=255)               # saat kulesi
        d.polygon([P(996, base - 150), P(1015, base - 182), P(1034, base - 150)], fill=255)
    m = mask_of(palace)
    fill(sc, m, C(40, 38, 46))
    win = mask_of(lambda d, P: [d.rectangle([P(x, 862), P(x + 9, 884)], fill=255) for x in range(60, 1030, 26)], 0.5)
    fill(sc, win * m, C(70, 66, 76), 0.8)
    # yansıma
    refl = np.flipud(m)[: HH - 0]
    shift = (905 * 2 + 12) * S - HH
    r = np.zeros_like(m); r[: HH - shift] = refl[shift:] if shift > 0 else refl
    r = gaussian_filter(r, (2 * S, 6 * S)) * np.clip((sc.yy - 905 * S) / (3 * S), 0, 1) * 0.35
    fill(sc, r, C(30, 28, 36))
    pole(sc, 540, 735, 560, w=5)
    flag(sc, 543, 640, 120, 80, seed=1)          # yarıya indirilmiş bayrak
    sc.fog(820, 900, C(220, 196, 186), 0.25)
    im = sc.finish(vignette=0.5, grain=0.03)
    return text_overlay(im, "Bir yolculuk ki tam 15 yıl sürdü", title="SON YOLCULUK", sub="10 KASIM 1938", page=1, total=N)

def s2():
    sc = Scene()
    g = SC.up(noise2(HH // 16, WW // 2, 8, 4, 5))
    stripes = np.sin(sc.yy / (11 * S) + g * 12) * 0.5 + 0.5
    sc.img[:] = C(70, 40, 24)[None, None] * (0.7 + 0.35 * stripes[..., None])
    sc.glow(420, 380, 800, C(255, 214, 160), 0.22)
    cx, cy, R = 540, 560, 360
    d = np.hypot(sc.xx / S - cx, sc.yy / S - cy)
    shadow = gaussian_filter((d < R + 30).astype(np.float32), 22 * S)
    sc.img *= (1 - 0.6 * np.roll(np.roll(shadow, 26 * S, 0), 14 * S, 1)[..., None])
    bez = np.clip((R + 30 - d) / 1.5, 0, 1)
    ang = np.arctan2(sc.yy / S - cy, sc.xx / S - cx)
    brass = C(176, 132, 62) * (0.75 + 0.45 * (0.5 + 0.5 * np.cos(ang + 2.4)))[..., None]
    fill(sc, bez, brass)
    dial = np.clip((R - d) / 1.5, 0, 1)
    paper = C(236, 226, 204) * (0.94 + 0.08 * SC.up(noise2(HH // 4, WW // 4, 20, 4, 8))[..., None])
    paper = paper * (1 - 0.18 * np.clip((d - R * 0.7) / (R * 0.3), 0, 1))[..., None]
    fill(sc, dial, paper)
    im_ = Image.new("L", (WW, HH), 0); dd = ImageDraw.Draw(im_)
    for k in range(60):
        a = math.radians(k * 6 - 90); r0 = R - 22; r1 = R - (60 if k % 5 == 0 else 36)
        dd.line([((cx + r0 * math.cos(a)) * S, (cy + r0 * math.sin(a)) * S), ((cx + r1 * math.cos(a)) * S, (cy + r1 * math.sin(a)) * S)],
                fill=255, width=(7 if k % 5 == 0 else 3) * S)
    fnt = F(F_BOLD, 54)
    for hnum in range(1, 13):
        a = math.radians(hnum * 30 - 90); rr = R - 108
        dd.text(((cx + rr * math.cos(a)) * S, (cy + rr * math.sin(a)) * S), str(hnum), font=fnt, fill=255, anchor="mm")
    fill(sc, gaussian_filter(np.asarray(im_, np.float32) / 255, 0.5 * S), C(34, 30, 28))
    # akrepler: 09.05
    def hand(angle_deg, length, width, tail=40):
        a = math.radians(angle_deg - 90); ex, ey = cx + length * math.cos(a), cy + length * math.sin(a)
        tx, ty = cx - tail * math.cos(a), cy - tail * math.sin(a)
        px, py = -math.sin(a) * width, math.cos(a) * width
        return [(tx * S, ty * S), ((cx + px) * S, (cy + py) * S), (ex * S, ey * S), ((cx - px) * S, (cy - py) * S)]
    hm = Image.new("L", (WW, HH), 0); hd = ImageDraw.Draw(hm)
    hd.polygon(hand((9 + 5 / 60) * 30, R * 0.52, 14), fill=255)
    hd.polygon(hand(5 * 6, R * 0.78, 10), fill=255)
    hd.ellipse([(cx - 20) * S, (cy - 20) * S, (cx + 20) * S, (cy + 20) * S], fill=255)
    hmask = gaussian_filter(np.asarray(hm, np.float32) / 255, 0.6 * S)
    sh = gaussian_filter(hmask, 6 * S); fill(sc, np.roll(np.roll(sh, 10 * S, 0), 8 * S, 1) * dial, C(60, 50, 40), 0.35)
    fill(sc, hmask, C(20, 18, 18))
    # cam yansıması
    gl = np.clip(1 - np.hypot((sc.xx / S - (cx - 120)) / 260, (sc.yy / S - (cy - 170)) / 120), 0, 1) ** 2 * dial
    sc.img += C(255, 255, 255) * gl[..., None] * 0.18
    im = sc.finish(vignette=0.55, grain=0.03)
    return text_overlay(im, "10 Kasım 1938, saat 09.05. Dolmabahçe Sarayı", page=2, total=N)

def s3():
    sc = Scene()
    sc.sky([(0, C(70, 78, 90)), (600, C(150, 156, 160)), (840, C(190, 192, 190))])
    sc.clouds(100, 600, C(110, 116, 124), 0.45, seed=12)
    sea(sc, 840, C(120, 128, 134), C(30, 38, 46), seed=5)
    def ship(d, P, x, y, s):
        q = lambda a, b: P(x + a * s, y + b * s)
        d.polygon([q(-420, 0), q(400, 0), q(440, -30), q(-440, -30)], fill=255)          # gövde
        d.rectangle([q(-380, -30), q(380, -60)], fill=255)
        d.rectangle([q(-140, -60), q(120, -110)], fill=255)                               # üst yapı
        d.rectangle([q(-60, -110), q(40, -150)], fill=255)
        d.polygon([q(-20, -150), q(-10, -260), q(0, -150)], fill=255)                     # direk
        d.rectangle([q(-110, -110), q(-70, -190)], fill=255)                               # bacalar
        d.rectangle([q(60, -110), q(100, -180)], fill=255)
        for tx in (-300, -200, 220, 310):                                                  # taretler
            d.rectangle([q(tx - 34, -60), q(tx + 34, -88)], fill=255)
            d.line([q(tx + (40 if tx > 0 else -40), -76), q(tx + (120 if tx > 0 else -120), -80)], fill=255, width=int(8 * s * S))
    for (x, y, s, col, a) in [(200, 820, 0.25, C(120, 124, 130), 0.8), (900, 826, 0.22, C(118, 122, 128), 0.8),
                              (540, 900, 1.0, C(42, 46, 52), 1.0)]:
        m = mask_of(lambda d, P: ship(d, P, x, y, s))
        fill(sc, m, col, a)
    sc.smoke(440, 690, 120, 70, C(80, 82, 86), 0.5, seed=50)
    sc.fog(780, 880, C(180, 184, 186), 0.35)
    im = sc.finish(vignette=0.5, grain=0.035)
    return text_overlay(im, "Naaşı Yavuz zırhlısıyla İzmit'e götürüldü", page=3, total=N)

def s4():
    sc = Scene()
    sc.sky([(0, C(10, 14, 28)), (700, C(30, 36, 60)), (900, C(56, 54, 70))])
    sc.glow(820, 260, 160, C(200, 210, 240), 0.35, core=36)
    rng = np.random.default_rng(4)
    for _ in range(200):
        x, y = rng.integers(0, WW), rng.integers(0, 640 * S)
        sc.img[y:y + 2, x:x + 2] += 0.3 + 0.6 * rng.random()
    sc.ridge(880, 120, C(22, 24, 36), seed=61, haze=C(46, 48, 66), haze_h=100)
    sc.ground(930, C(26, 24, 28), C(8, 8, 10), seed=3)
    def train(d, P):
        y = 960
        d.rectangle([P(80, y - 20), P(1080, y)], fill=255)                                  # şasi
        d.rectangle([P(120, y - 150), P(360, y - 20)], fill=255)                            # kazan
        d.rectangle([P(330, y - 200), P(450, y - 20)], fill=255)                            # kabin
        d.rectangle([P(150, y - 210), P(190, y - 150)], fill=255)                           # baca
        d.polygon([P(80, y), P(120, y - 60), P(120, y)], fill=255)
        for i in range(3):
            x0 = 480 + i * 210
            d.rectangle([P(x0, y - 170), P(x0 + 195, y - 20)], fill=255)
        for wx in (150, 220, 290, 380, 520, 640, 730, 850, 940):
            d.ellipse([P(wx - 26, y - 26), P(wx + 26, y + 26)], fill=255)
    m = mask_of(train)
    fill(sc, m, C(12, 12, 14))
    win = mask_of(lambda d, P: [d.rectangle([P(500 + i * 210 + k * 46, 820), P(530 + i * 210 + k * 46, 860)], fill=255)
                                 for i in range(3) for k in range(4)], 0.5)
    fill(sc, win, C(255, 190, 110))
    sc.glow(700, 840, 260, C(255, 170, 80), 0.18)
    sc.smoke(240, 650, 260, 120, C(150, 154, 170), 0.55, seed=70)
    sc.smoke(420, 560, 320, 110, C(120, 124, 140), 0.45, seed=71)
    rail = mask_of(lambda d, P: d.rectangle([P(0, 986), P(1080, 992)], fill=255))
    fill(sc, rail, C(60, 60, 70))
    im = sc.finish(vignette=0.55, grain=0.035)
    return text_overlay(im, "Oradan özel bir trenle Ankara'ya getirildi", page=4, total=N)

def s5():
    sc = Scene()
    sc.sky([(0, C(96, 110, 130)), (600, C(176, 182, 190)), (900, C(206, 206, 204))])
    sc.clouds(80, 520, C(150, 156, 166), 0.4, seed=81)
    sc.ground(960, C(150, 150, 146), C(70, 70, 70), seed=9)
    def museum(d, P):
        b = 960
        d.rectangle([P(200, b - 300), P(880, b)], fill=255)                                  # ana kütle
        d.rectangle([P(380, b - 380), P(700, b - 300)], fill=255)
        d.ellipse([P(440, b - 500), P(640, b - 300)], fill=255)                              # kubbe
        d.rectangle([P(330, b - 40), P(750, b)], fill=255)                                    # merdiven
        d.rectangle([P(300, b - 20), P(780, b + 10)], fill=255)
    m = mask_of(museum)
    stone = C(226, 222, 212) * (0.92 + 0.1 * SC.up(noise2(HH // 4, WW // 4, 10, 3, 3))[..., None])
    stone = stone * (0.8 + 0.25 * np.clip((sc.xx / S - 200) / 680, 0, 1))[..., None]
    fill(sc, m, stone)
    det = mask_of(lambda d, P: (
        [d.rectangle([P(400 + i * 48, 960 - 280), P(416 + i * 48, 960 - 50)], fill=255) for i in range(6)],
        [d.rectangle([P(240 + i * 60, 960 - 230), P(270 + i * 60, 960 - 150)], fill=255) for i in range(3)],
        [d.rectangle([P(720 + i * 60, 960 - 230), P(750 + i * 60, 960 - 150)], fill=255) for i in range(3)],
        d.rectangle([P(380, 960 - 300), P(700, 960 - 290)], fill=255)), 0.5)
    fill(sc, det, C(130, 128, 124), 0.75)
    sh = mask_of(lambda d, P: d.rectangle([P(200, 960 - 300), P(260, 960)], fill=255))
    fill(sc, sh * m, C(150, 148, 144), 0.4)
    pole(sc, 540, 960 - 500, 960 - 680, w=5, col=C(60, 60, 64))
    flag(sc, 543, 960 - 670, 120, 80, seed=2)
    im = sc.finish(vignette=0.5, grain=0.03)
    return text_overlay(im, "21 Kasım 1938'de Etnografya Müzesi'ndeki geçici kabre kondu", page=5, total=N, line_size=46)

def s6():
    sc = Scene()
    sc.sky([(0, C(40, 56, 96)), (500, C(200, 130, 100)), (780, C(250, 196, 140)), (860, C(255, 222, 170))])
    sc.glow(300, 820, 420, C(255, 170, 90), 0.5, core=30)
    sc.clouds(200, 520, C(170, 96, 90), 0.4, seed=91)
    sc.ridge(880, 70, C(120, 80, 76), seed=92, haze=C(230, 160, 120), haze_h=80)
    sc.ground(880, C(80, 56, 46), C(20, 16, 14), seed=5)
    def anit(d, P):
        b = 900
        d.rectangle([P(120, b - 30), P(960, b)], fill=255)                                   # basamaklar
        d.rectangle([P(180, b - 60), P(900, b - 30)], fill=255)
        d.rectangle([P(240, b - 90), P(840, b - 60)], fill=255)
        d.rectangle([P(270, b - 300), P(810, b - 260)], fill=255)                            # saçak
        d.rectangle([P(300, b - 330), P(780, b - 300)], fill=255)
        for i in range(12):                                                                   # sütunlar
            x = 290 + i * 45.5
            d.rectangle([P(x, b - 260), P(x + 22, b - 90)], fill=255)
        d.rectangle([P(330, b - 260), P(750, b - 230)], fill=255)
    m = mask_of(anit)
    fill(sc, m, C(36, 28, 30))
    inner = mask_of(lambda d, P: d.rectangle([P(312, 900 - 230), P(768, 900 - 90)], fill=255))
    fill(sc, inner * (1 - m), C(60, 40, 40), 0.5)
    pole(sc, 900, 870, 560, w=5, col=C(30, 26, 28))
    flag(sc, 903, 568, 150, 100, seed=3)
    im = sc.finish(vignette=0.5, grain=0.03, warm=0.02)
    return text_overlay(im, "15 yıl sonra, 10 Kasım 1953'te Anıtkabir'e taşındı. Saygıyla anıyoruz.", page=6, total=N, line_size=46)

if __name__ == "__main__":
    fns = {"1": s1, "2": s2, "3": s3, "4": s4, "5": s5, "6": s6}
    os.makedirs(OUT, exist_ok=True)
    for k in (sys.argv[1:] or list(fns)):
        fns[k]().save(os.path.join(OUT, f"{k}.jpg"), quality=93)
    import glob
    SC.contact_sheet(sorted(glob.glob(os.path.join(OUT, "*.jpg"))), os.path.join(OUT, "..", "_onizleme_son_yolculuk.png"))
