"""Kaydırmalı gönderi: Tohum bekçileri — Leningrad kuşatmasında (1941-1944) Vavilov enstitüsünün bilim insanları
açlıktan öldü ama tohum koleksiyonunu yemedi.
Kaynaklar: Science History Institute, "The Tragedy of the World's First Seed Bank"; LRB (2025) J. Childs,
"Resident Bean Expert"; Wikipedia, "Institute of Plant Industry"; Britannica, "Nikolai Vavilov".
Tasarım: scene.py (gerçeğe yakın sinematik çizim, sayfa başına tek cümle)."""
import os, sys, math
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter
import scene as SC
from scene import Scene, C, S, W, H, WW, HH, F, F_BLACK, F_BOLD, F_SEMI, F_MONO, text_overlay, Shape, noise2

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "posts", "2026-11-14_tohum_bekcileri")
N = 6

def fill(sc, m, col, a=1.0):
    sc.img = sc.img * (1 - a * m[..., None]) + col * (a * m[..., None])

def mask_of(fn, blur=0.7):
    sh = Shape(0, 0, 1.0); fn(sh.d, lambda x, y: (x * S, y * S))
    return gaussian_filter(np.asarray(sh.im, np.float32) / 255, blur * S)

def R(x0, y0, x1, y1): return [x0 * S, y0 * S, x1 * S, y1 * S]

def snowfall(sc, n, seed, y0=0, y1=H, size=(1.2, 3.2), color=C(240, 244, 250), alpha=0.85):
    rng = np.random.default_rng(seed)
    im = Image.new("L", (WW, HH), 0); d = ImageDraw.Draw(im)
    for _ in range(n):
        x, y = rng.uniform(0, W), rng.uniform(y0, y1); r = rng.uniform(*size)
        d.ellipse(R(x - r, y - r, x + r, y + r), fill=int(140 + 115 * rng.random()))
    m = gaussian_filter(np.asarray(im, np.float32) / 255, 0.9 * S)
    fill(sc, m, color, alpha)

def windows_tex(sc, m, col, seed, lit=0.0, lit_col=C(255, 190, 110)):
    """Bina maskesine pencere ızgarası (koyu) + nadiren yanan pencere."""
    rng = np.random.default_rng(seed)
    gx = (np.mod(sc.xx / S, 38) > 14) & (np.mod(sc.xx / S, 38) < 26)
    gy = (np.mod(sc.yy / S, 54) > 16) & (np.mod(sc.yy / S, 54) < 38)
    win = (gx & gy).astype(np.float32) * m
    fill(sc, gaussian_filter(win, 0.6 * S), col * 0.55, 0.6)
    if lit:
        cells = (np.floor(sc.xx / S / 38) * 131 + np.floor(sc.yy / S / 54) * 17 + seed) % 97
        lw = win * (cells < lit * 97)
        fill(sc, gaussian_filter(lw, 0.6 * S), lit_col, 0.9)
        sc.img += lit_col * gaussian_filter(lw, 8 * S)[..., None] * 0.6

def city_row(sc, base_y, hmin, hmax, col, seed, x0=0, x1=W, roof_snow=None, lit=0.0):
    rng = np.random.default_rng(seed)
    def draw(d, T):
        x = x0 - 20
        while x < x1 + 20:
            w = rng.uniform(110, 230); h = rng.uniform(hmin, hmax)
            d.rectangle(R(x, base_y - h, x + w, base_y + 400), fill=255)
            if rng.random() < 0.35:   # çatı katı / baca
                d.rectangle(R(x + w * 0.2, base_y - h - 22, x + w * 0.32, base_y - h), fill=255)
            x += w + rng.uniform(-6, 4)
    m = mask_of(draw, 0.6)
    fill(sc, m, col)
    windows_tex(sc, m * (sc.yy / S < base_y), col, seed, lit=lit)
    if roof_snow is not None:
        top = m - np.roll(m, 5 * S, 0)
        fill(sc, np.clip(top, 0, 1), roof_snow, 0.7)
    return m

def isaac(sc, cx, base, s, col, rim=None):
    """İsakiyevski Katedrali silüeti (kubbe + kasnak + sütunlu kasnak + fener + köşe kubbecikleri)."""
    def draw(d, T):
        P = lambda x, y: ((cx + x * s) * S, (base + y * s) * S)
        def rect(a, b, c, e): d.rectangle([*P(a, b), *P(c, e)], fill=255)
        def ell(a, b, c, e): d.ellipse([*P(a, b), *P(c, e)], fill=255)
        rect(-300, -260, 300, 0)              # ana gövde
        d.polygon([P(-170, -260), P(170, -260), P(0, -330)], fill=255)   # alınlık
        rect(-130, -440, 130, -260)           # sütunlu kasnak
        rect(-150, -455, 150, -430)
        rect(-110, -520, 110, -440)           # üst kasnak
        ell(-118, -660, 118, -380)            # kubbe (alt yarısı kasnakta kalır)
        rect(-16, -740, 16, -630)             # fener
        ell(-24, -760, 24, -716)
        rect(-3, -800, 3, -750)               # tepe çubuğu
        for sx in (-240, 240):                # köşe kubbecikleri
            rect(sx - 26, -330, sx + 26, -260); ell(sx - 30, -370, sx + 30, -300)
            rect(sx - 2, -392, sx + 2, -360)
    m = mask_of(draw, 0.6)
    fill(sc, m, col)
    # sütun aralıkları (hafif açık dikey çizgiler)
    cols = (np.mod((sc.xx / S - cx) / s, 26) < 9) & (sc.yy / S > base - 440 * s) & (sc.yy / S < base - 270 * s) \
        & (np.abs(sc.xx / S - cx) < 125 * s)
    fill(sc, gaussian_filter(cols.astype(np.float32), 0.6 * S) * m, col * 1.6 + 0.02, 0.5)
    if rim is not None:   # kubbe üstüne ışık
        d = np.hypot((sc.xx / S - cx) / (118 * s), (sc.yy / S - (base - 520 * s)) / (140 * s))
        k = np.clip((d - 0.75) * 4, 0, 1) * (sc.yy / S < base - 520 * s) * (sc.xx / S > cx - 20 * s) * m
        fill(sc, gaussian_filter(k, 1.5 * S), rim, 0.7)
    return m

def title_overlay(im, title, sub, line):
    """Kapak: text_overlay'in aynısı ama başlık genişliğe sığacak boyutta."""
    from scene import _wrap
    im = im.resize((W, H), Image.LANCZOS).convert("RGBA")
    ov = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    g = Image.linear_gradient("L").resize((W * S, 520 * S)).point(lambda v: int(v * 0.85))
    blk = Image.new("RGBA", (W * S, 520 * S), (8, 6, 4, 255)); blk.putalpha(g)
    ov.alpha_composite(blk, (0, (H - 520) * S))
    _wrap(d, line, F(F_BOLD, 50), 540, 1150, 900, (250, 244, 232))
    g = Image.linear_gradient("L").rotate(180).resize((W * S, 520 * S)).point(lambda v: int(v * 0.7))
    blk = Image.new("RGBA", (W * S, 520 * S), (8, 6, 4, 255)); blk.putalpha(g)
    ov.alpha_composite(blk, (0, 0))
    size = 120
    while F(F_BLACK, size).getlength(title) / S > 960: size -= 2
    d.text((540 * S, 110 * S), title, font=F(F_BLACK, size), fill=(250, 244, 232), anchor="ma")
    d.text((540 * S, (110 + size + 20) * S), sub, font=F(F_SEMI, 40), fill=(236, 196, 120), anchor="ma")
    d.text((44 * S, 1300 * S), "@fermantarih", font=F(F_SEMI, 26), fill=(250, 244, 232, 170), anchor="ls")
    for i in range(N):
        cx = W - 44 - (N - 1 - i) * 22
        d.ellipse([(cx - 5) * S, 1288 * S, (cx + 5) * S, 1298 * S], fill=(250, 244, 232, 255 if i == 0 else 90))
    ov = ov.resize((W, H), Image.LANCZOS); im.alpha_composite(ov)
    return im.convert("RGB")

# ------------------------------------------------------------------ sayfalar
def s1():
    """Kapak: karlı alacakaranlıkta İsakiyevski kubbesi, önde yalnız bir bekçi."""
    sc = Scene()
    sc.sky([(0, C(26, 34, 56)), (420, C(70, 80, 108)), (760, C(176, 132, 118)), (860, C(226, 166, 120))])
    sc.glow(760, 850, 420, C(255, 160, 100), 0.4, core=0)
    sc.clouds(220, 560, C(96, 96, 120), 0.45, seed=12)
    city_row(sc, 900, 120, 220, C(70, 66, 82), 3)
    isaac(sc, 540, 905, 0.78, C(40, 40, 56), rim=C(230, 160, 120))
    sc.fog(840, 940, C(150, 130, 140), 0.35, seed=4)
    city_row(sc, 960, 90, 170, C(30, 30, 42), 8, roof_snow=C(200, 205, 220), lit=0.03)
    sc.ground(985, C(196, 200, 214), C(120, 124, 140), seed=3)
    snowfall(sc, 900, 1, size=(0.8, 2.0), alpha=0.6)
    m = SC.outline_mask("civilian", 300, 1095, 0.42)
    sc.figure(m, C(18, 18, 24), C(255, 180, 130), light=(1, -0.4), rim_w=3)
    snowfall(sc, 260, 2, size=(2.0, 4.2), alpha=0.85)
    im = sc.finish(vignette=0.55)
    return title_overlay(im, "TOHUM BEKÇİLERİ", "LENİNGRAD · 1941–1944",
                         "Açlıktan öldüler ama tohumları yemediler")

def s2():
    """Vavilov tohum seferinde: dağ yamacında çanta taşıyan bir bilim insanı."""
    sc = Scene()
    sc.sky([(0, C(66, 104, 150)), (500, C(150, 178, 196)), (820, C(236, 220, 180)), (900, C(246, 230, 196))])
    sc.glow(800, 520, 380, C(255, 236, 190), 0.5, core=36)
    sc.clouds(160, 420, C(230, 230, 236), 0.4, seed=21)
    sc.ridge(820, 260, C(150, 160, 180), seed=24, haze=C(220, 214, 206), haze_h=300, scale=700)
    sc.ridge(900, 160, C(110, 116, 110), seed=27, haze=C(190, 186, 170), haze_h=160)
    sc.fog(860, 960, C(236, 226, 206), 0.35)
    # yamaç (çimen)
    xs = np.arange(WW) / S
    top = 1010 - 120 * np.clip((xs - 200) / 900, 0, 1) + 10 * SC.noise1(WW, 80 * S, 4, 6)
    hm = gaussian_filter((sc.yy >= (top * S)[None, :]).astype(np.float32), 1.2)
    k = np.clip((sc.yy / S - top[None, :]) / 300, 0, 1)[..., None]
    gcol = (C(110, 120, 64) * (1 - k) + C(48, 54, 30) * k) * (0.85 + 0.3 * SC.up(noise2(HH // 2, WW // 2, 6, 4, 9))[..., None])
    fill(sc, hm, gcol)
    # yürüyen bilim insanı + omuz çantası
    def bag(d, T, scl):
        d.ellipse([*T(-120, -560), *T(-40, -430)], fill=255)
        d.line([T(-80, -560), T(40, -700)], fill=255, width=max(2, int(10 * scl * S)))
    m = SC.outline_mask("civilian", 640, 1010 - 120 * (440 / 900) + 20, 0.5, extra=bag)
    sc.figure(m, C(40, 40, 36), C(255, 236, 190), light=(1, -0.6), rim_w=3)
    im = sc.finish(vignette=0.4, warm=0.02)
    return text_overlay(im, "Botanikçi Nikolay Vavilov dünyanın dört bir yanından tohum topladı", page=2, total=N)

def s3():
    """Kuşatma: karanlık, karlı Leningrad gecesi, dumanlar."""
    sc = Scene()
    sc.sky([(0, C(8, 10, 20)), (600, C(26, 30, 46)), (900, C(60, 50, 56))])
    sc.glow(860, 900, 420, C(255, 110, 50), 0.35)
    sc.smoke(820, 640, 260, 300, C(50, 44, 48), 0.7, seed=31)
    sc.smoke(260, 700, 220, 220, C(40, 38, 46), 0.6, seed=32)
    city_row(sc, 880, 160, 300, C(22, 24, 34), 41, roof_snow=C(110, 116, 136))
    sc.fog(820, 920, C(70, 64, 76), 0.4, seed=8)
    city_row(sc, 900, 200, 340, C(12, 13, 20), 44, roof_snow=C(150, 156, 176))
    sc.ground(905, C(150, 154, 170), C(60, 64, 78), seed=12)
    sc.glow(560, 920, 300, C(255, 130, 60), 0.18)
    # karda yürüyen iki kişi, biri kızak çeker
    m = SC.outline_mask("civilian", 400, 985, 0.36)
    m = np.maximum(m, SC.outline_mask("civilian", 520, 975, 0.33))
    def sled(d, T):
        d.rectangle(R(570, 958, 690, 972), fill=255)
        d.line([(536 * S, 900 * S), (574 * S, 962 * S)], fill=255, width=3 * S)
    m = np.maximum(m, mask_of(sled, 0.6))
    sc.figure(m, C(8, 8, 12), C(255, 150, 90), light=(1, -0.1), rim_w=3, rim_strength=1.0)
    snowfall(sc, 1400, 5, size=(0.8, 2.4), alpha=0.7)
    snowfall(sc, 260, 6, size=(2.2, 4.0), alpha=0.8)
    im = sc.finish(vignette=0.6)
    return text_overlay(im, "1941. Leningrad kuşatıldı ve şehirde açlık başladı", page=3, total=N)

def jars_shelf(sc, seed):
    """Ahşap raflar üzerinde etiketli tohum kavanozları ve kese kâğıtları."""
    rng = np.random.default_rng(seed)
    # duvar
    n = SC.up(noise2(HH // 4, WW // 4, 30, 4, seed))
    sc.img[:] = C(46, 42, 40)[None, None] * (0.85 + 0.3 * n[..., None])
    sc.glow(160, 300, 700, C(150, 180, 230), 0.25)    # pencereden soğuk ışık
    seeds = [C(220, 200, 150), C(150, 100, 60), C(200, 170, 90), C(120, 90, 60), C(230, 220, 200), C(90, 70, 40),
             C(190, 120, 70), C(170, 160, 100)]
    for row, y in enumerate([300, 560, 820]):
        # raf tahtası
        plank = mask_of(lambda d, T: d.rectangle(R(0, y, W, y + 26), fill=255), 0.6)
        fill(sc, plank, C(96, 64, 38) * (0.9 + 0.2 * n[..., None]))
        fill(sc, gaussian_filter(mask_of(lambda d, T: d.rectangle(R(0, y + 26, W, y + 40), fill=255)), 4 * S), C(10, 8, 6), 0.6)
        x = 30 + rng.uniform(0, 20)
        while x < W - 60:
            if rng.random() < 0.7:     # cam kavanoz
                w = rng.uniform(78, 100); h = rng.uniform(130, 170)
                body = mask_of(lambda d, T: d.rounded_rectangle(R(x, y - h, x + w, y), 14 * S, fill=255), 0.6)
                lev = y - h * rng.uniform(0.55, 0.85)
                seedm = body * (sc.yy / S > lev)
                c = seeds[rng.integers(len(seeds))]
                fill(sc, seedm, c * (0.75 + 0.5 * SC.up(noise2(HH // 2, WW // 2, 1.5, 2, int(x)))[..., None]))
                fill(sc, body * (sc.yy / S <= lev), C(110, 120, 130), 0.25)
                hl = body * (np.abs(sc.xx / S - (x + w * 0.22)) < 5)
                fill(sc, gaussian_filter(hl, 2 * S), C(230, 240, 255), 0.5)
                lid = mask_of(lambda d, T: d.rectangle(R(x + 4, y - h - 16, x + w - 4, y - h + 2), fill=255))
                fill(sc, lid, C(70, 70, 74))
                lab = mask_of(lambda d, T: d.rectangle(R(x + 12, y - h * 0.45, x + w - 12, y - h * 0.2), fill=255))
                fill(sc, lab, C(226, 214, 184))
                x += w + rng.uniform(10, 22)
            else:                        # kese kâğıdı
                w = rng.uniform(70, 90); h = rng.uniform(100, 130)
                bag = mask_of(lambda d, T: d.polygon([(x * S, y * S), ((x + w) * S, y * S), ((x + w - 6) * S, (y - h) * S),
                                                        ((x + w * 0.5) * S, (y - h - 10) * S), ((x + 6) * S, (y - h) * S)], fill=255))
                fill(sc, bag, C(176, 150, 110) * (0.85 + 0.3 * n[..., None]))
                x += w + rng.uniform(10, 22)
        # raf altı gölge
    sc.glow(860, 560, 360, C(255, 190, 110), 0.12)

def s4():
    sc = Scene()
    jars_shelf(sc, 7)
    # ön planda raflara bakan bekçi (sırtı dönük)
    m = SC.outline_mask("civilian", 760, 1200, 0.78, flip=True)
    sc.figure(m, C(16, 16, 20), C(170, 196, 236), light=(-1, -0.3), rim_w=3, rim_strength=0.8)
    im = sc.finish(vignette=0.6, grain=0.03)
    return text_overlay(im, "Bilim insanları açtı ama tohumları yemediler, korudular", page=4, total=N)

def s5():
    """Pirinç bölümünün boş masası: mum, pirinç keseleri, boş sandalye, buzlu pencere."""
    sc = Scene()
    n = SC.up(noise2(HH // 4, WW // 4, 30, 4, 50))
    sc.img[:] = C(30, 28, 30)[None, None] * (0.85 + 0.3 * n[..., None])
    # buzlu pencere
    win = mask_of(lambda d, T: d.rectangle(R(600, 140, 960, 640), fill=255), 0.8)
    frost = SC.up(noise2(HH // 2, WW // 2, 6, 5, 51))
    fill(sc, win, C(70, 96, 140) * (0.8 + 0.5 * frost[..., None]))
    edge = win * np.clip(1 - np.minimum.reduce([sc.xx / S - 600, 960 - sc.xx / S, sc.yy / S - 140, 640 - sc.yy / S]) / 90, 0, 1)
    fill(sc, edge * np.clip(frost * 1.6 - 0.3, 0, 1), C(220, 230, 245), 0.8)
    fr = mask_of(lambda d, T: (d.rectangle(R(774, 140, 786, 640), fill=255), d.rectangle(R(600, 384, 960, 396), fill=255)))
    fill(sc, fr, C(26, 22, 20))
    # boş sandalye (masanın arkasında)
    ch = mask_of(lambda d, T: (d.rectangle(R(250, 420, 274, 820), fill=255), d.rectangle(R(470, 420, 494, 820), fill=255),
                               d.rectangle(R(250, 420, 494, 446), fill=255), d.rectangle(R(250, 520, 494, 540), fill=255)))
    fill(sc, ch, C(58, 38, 24))
    # masa
    top = mask_of(lambda d, T: d.polygon([(40 * S, 800 * S), (1040 * S, 800 * S), (1080 * S, 1350 * S), (0, 1350 * S)], fill=255))
    g = SC.up(noise2(HH // 16, WW // 2, 8, 4, 31))
    grain = np.sin(sc.xx / (7 * S) + g * 12) * 0.5 + 0.5
    fill(sc, top, C(96, 60, 34) * (0.75 + 0.3 * grain[..., None]))
    # pirinç keseleri ve döküntü
    rng = np.random.default_rng(4)
    for (bx, by, bw, bh) in [(90, 1000, 200, 150), (270, 960, 170, 130), (520, 990, 210, 160), (690, 930, 150, 120)]:
        b = mask_of(lambda d, T: d.rounded_rectangle(R(bx, by - bh, bx + bw, by), 40 * S, fill=255), 1.0)
        cloth = SC.up(noise2(HH // 2, WW // 2, 2, 3, bx))
        fill(sc, b, C(196, 178, 140) * (0.8 + 0.35 * cloth[..., None]))
        tie = mask_of(lambda d, T: d.ellipse(R(bx + bw * 0.38, by - bh - 22, bx + bw * 0.62, by - bh + 14), fill=255))
        fill(sc, tie, C(170, 150, 112))
        lab = mask_of(lambda d, T: d.rectangle(R(bx + bw * 0.22, by - bh * 0.62, bx + bw * 0.78, by - bh * 0.32), fill=255))
        fill(sc, lab, C(236, 228, 206))
    im_ = Image.new("L", (WW, HH), 0); d = ImageDraw.Draw(im_)
    for _ in range(500):
        x, y = rng.normal(430, 120), rng.normal(1080, 30)
        a = rng.uniform(0, math.pi)
        d.line([(x * S, y * S), ((x + 6 * math.cos(a)) * S, (y + 3 * math.sin(a)) * S)], fill=255, width=3 * S)
    fill(sc, gaussian_filter(np.asarray(im_, np.float32) / 255, 0.5 * S), C(240, 234, 216), 0.9)
    # mum
    cm = mask_of(lambda d, T: d.rectangle(R(900, 880, 940, 1010), fill=255))
    fill(sc, cm, C(226, 214, 186))
    sc.glow(920, 860, 520, C(255, 170, 80), 0.45)
    sc.glow(920, 860, 60, C(255, 220, 150), 0.9)
    fl = mask_of(lambda d, T: d.ellipse(R(910, 838, 930, 882), fill=255), 1.5)
    fill(sc, fl, C(255, 236, 190))
    # mumdan gelen sıcak ışık sahneye
    warm = np.exp(-((sc.xx / S - 920) ** 2 + (sc.yy / S - 900) ** 2) / (2 * 380 ** 2))
    sc.img *= (0.6 + 0.6 * warm[..., None] * np.array([1.1, 0.95, 0.75], np.float32))
    im = sc.finish(vignette=0.6, grain=0.03)
    return text_overlay(im, "Pirinç bölümünün şefi, pirinç örneklerinin arasında öldü", page=5, total=N)

def s6():
    """Karda filizlenen tek fide, şafak ışığı."""
    sc = Scene()
    sc.sky([(0, C(40, 52, 84)), (500, C(150, 150, 170)), (800, C(250, 196, 150)), (880, C(255, 220, 170))])
    sc.glow(540, 860, 520, C(255, 190, 120), 0.6, core=40)
    sc.clouds(200, 520, C(170, 150, 170), 0.35, seed=61)
    sc.ridge(880, 50, C(120, 120, 150), seed=62, haze=C(220, 190, 180), haze_h=60, scale=600)
    sc.ground(900, C(226, 226, 236), C(150, 156, 176), seed=63)
    # karın üstünde ışık
    sc.img += C(255, 200, 150) * (np.exp(-((sc.xx / S - 540) / 300) ** 2) * np.clip(1 - (sc.yy / S - 900) / 300, 0, 1)
                                   * (sc.yy / S > 900))[..., None] * 0.25
    # filiz
    def sprout(d, T):
        pts = [(540 + 6 * math.sin(t / 30), 1040 - t) for t in range(0, 200, 4)]
        d.line([(x * S, y * S) for x, y in pts], fill=255, width=7 * S)
        d.polygon([(538 * S, 850 * S), (470 * S, 800 * S), (430 * S, 820 * S), (470 * S, 856 * S)], fill=255)
        d.polygon([(544 * S, 870 * S), (610 * S, 810 * S), (656 * S, 826 * S), (620 * S, 870 * S)], fill=255)
    m = mask_of(sprout, 1.2)
    sc.figure(m, C(60, 110, 50), C(255, 220, 150), light=(0, -1), rim_w=2, rim_strength=0.7)
    # karda gölge çukuru
    hole = np.exp(-(((sc.xx / S - 540) / 60) ** 2 + ((sc.yy / S - 1042) / 12) ** 2))
    sc.img *= (1 - 0.35 * hole[..., None])
    snowfall(sc, 140, 9, y0=0, y1=800, size=(1.0, 2.4), alpha=0.5)
    im = sc.finish(vignette=0.5)
    return text_overlay(im, "Vavilov ise 1943'te hapishanede açlıktan öldü. Sen yer miydin?", page=6, total=N)

if __name__ == "__main__":
    which = sys.argv[1:] or ["1", "2", "3", "4", "5", "6"]
    fns = {"1": s1, "2": s2, "3": s3, "4": s4, "5": s5, "6": s6}
    os.makedirs(OUT, exist_ok=True)
    for k in which:
        if k in fns: fns[k]().save(os.path.join(OUT, f"{k}.jpg"), quality=93)
