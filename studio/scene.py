"""Gerçeğe yakın, sinematik illüstrasyon motoru (kaydırmalı gönderiler için).
Fikir: atmosferli gökyüzü + katmanlı dağlar + sis + ters ışıkta (rim light) organik silüetler + film grenleri.
Tüm çizim 2x çözünürlükte numpy ile yapılır, sonra 1080x1350'ye küçültülür."""
import os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy.ndimage import gaussian_filter, zoom

W, H, S = 1080, 1350, 2
WW, HH = W * S, H * S
FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
F_BLACK = os.path.join(FONTS, "InterDisplay-Black.otf")
F_BOLD = os.path.join(FONTS, "InterDisplay-Bold.otf")
F_SEMI = os.path.join(FONTS, "Inter-SemiBold.otf")
F_MONO = os.path.join(FONTS, "LiberationMono-Bold.ttf")

def C(*rgb): return np.array(rgb, np.float32) / 255.0
def F(path, size): return ImageFont.truetype(path, int(size * S))

# ---------------------------------------------------------------- gürültü
def noise2(h, w, scale, octaves=4, seed=0):
    rng = np.random.default_rng(seed); out = np.zeros((h, w), np.float32); amp = 1.0; tot = 0
    for o in range(octaves):
        gh, gw = max(2, int(h / scale) + 2), max(2, int(w / scale) + 2)
        g = rng.random((gh, gw)).astype(np.float32)
        z = zoom(g, (h / gh * 1.0001, w / gw * 1.0001), order=3)[:h, :w]
        if z.shape != (h, w): z = np.pad(z, ((0, h - z.shape[0]), (0, w - z.shape[1])), mode="edge")
        out += z * amp; tot += amp; amp *= 0.5; scale /= 2
    return out / tot

def up(a, h=None, w=None):
    h = h or HH; w = w or WW
    z = zoom(a, (h / a.shape[0], w / a.shape[1]), order=1)
    z = z[:h, :w]
    if z.shape != (h, w): z = np.pad(z, ((0, h - z.shape[0]), (0, w - z.shape[1])), mode="edge")
    return z

def noise1(n, scale, octaves=5, seed=0):
    rng = np.random.default_rng(seed); out = np.zeros(n, np.float32); amp = 1.0; tot = 0
    for o in range(octaves):
        k = max(2, int(n / scale) + 2); g = rng.random(k).astype(np.float32)
        out += np.interp(np.linspace(0, k - 1, n), np.arange(k), g) * amp
        tot += amp; amp *= 0.5; scale /= 2
    return out / tot

# ---------------------------------------------------------------- tuval
class Scene:
    def __init__(self):
        self.img = np.zeros((HH, WW, 3), np.float32)
        self.yy, self.xx = np.mgrid[0:HH, 0:WW].astype(np.float32)

    def sky(self, stops):
        """stops: [(y_px, color), ...] dikey gradyan (y 1x koordinat)."""
        ys = np.array([s[0] * S for s in stops], np.float32); cols = np.array([s[1] for s in stops])
        y = np.arange(HH, dtype=np.float32)
        col = np.stack([np.interp(y, ys, cols[:, i]) for i in range(3)], -1)
        self.img[:] = col[:, None, :]
        n = noise2(HH // 8, WW // 8, 40, 3, seed=11); n = up(n)
        self.img *= (0.97 + 0.06 * n[..., None])

    def glow(self, cx, cy, r, color, strength=1.0, core=0.0):
        d = np.hypot(self.xx - cx * S, self.yy - cy * S) / (r * S)
        g = np.exp(-d ** 2 * 2.2) * strength
        self.img += color * g[..., None]
        if core:
            k = np.clip(1.0 - (d * r / core - 1.0) * 3, 0, 1)
            self.img = self.img * (1 - k[..., None]) + C(255, 250, 235) * k[..., None]

    def clouds(self, y0, y1, color, alpha=0.5, seed=3, scale=260):
        n = noise2(HH // 4, WW // 4, scale / 4, 5, seed); n = up(n)
        band = np.clip(1 - np.abs((self.yy - (y0 + y1) / 2 * S) / ((y1 - y0) / 2 * S)), 0, 1) ** 0.7
        a = np.clip((n - 0.5) * 3.0, 0, 1) * band * alpha
        n2 = gaussian_filter(n, 6)
        lit = color * (0.75 + 0.5 * (n - n2)[..., None] * 6)
        self.img = self.img * (1 - a[..., None]) + lit * a[..., None]

    def ridge(self, base_y, amp, color, scale=420, seed=1, haze=None, haze_h=120, sharp=1.0, tex=0.04):
        """Dağ / tepe silüeti. base_y ve amp 1x piksel."""
        n = noise1(WW, scale * S, 6, seed)
        n = (n - n.min()) / (n.max() - n.min() + 1e-6)
        n = np.abs(n * 2 - 1) ** sharp if sharp != 1.0 else n
        top = (base_y - amp * n) * S
        m = (self.yy >= top[None, :]).astype(np.float32)
        m = gaussian_filter(m, 1.2)
        col = np.broadcast_to(color, self.img.shape).copy()
        t = noise2(HH // 4, WW // 4, 30, 4, seed + 7); t = up(t)
        col *= (1 - tex + 2 * tex * t[..., None])
        if haze is not None:   # tepeden aşağı sisle açılan renk (atmosfer)
            k = np.clip(1 - (self.yy - top[None, :]) / (haze_h * S), 0, 1) ** 1.5
            col = col * (1 - k[..., None] * 0.6) + haze * (k[..., None] * 0.6)
        self.img = self.img * (1 - m[..., None]) + col * m[..., None]
        return top / S

    def fog(self, y0, y1, color, alpha=0.6, seed=5):
        n = noise2(HH // 4, WW // 4, 70, 4, seed); n = up(n)
        k = np.clip(1 - np.abs((self.yy - (y0 + y1) / 2 * S) / ((y1 - y0) / 2 * S)), 0, 1)
        a = k * alpha * (0.6 + 0.8 * n)
        self.img = self.img * (1 - a[..., None]) + color * a[..., None]

    def ground(self, y, color, color2, seed=9):
        m = np.clip((self.yy - y * S) / (4 * S), 0, 1)
        t = noise2(HH // 2, WW // 2, 20, 5, seed); t = up(t)
        k = np.clip((self.yy - y * S) / ((H - y) * S), 0, 1)
        col = color * (1 - k[..., None]) + color2 * k[..., None]
        col = col * (0.85 + 0.3 * t[..., None])
        self.img = self.img * (1 - m[..., None]) + col * m[..., None]

    def smoke(self, cx, cy, w, h, color, alpha=0.7, seed=21):
        n = noise2(HH // 4, WW // 4, 40, 5, seed); n = up(n)
        dx = (self.xx - cx * S) / (w * S); dy = (self.yy - cy * S) / (h * S)
        shape = np.clip(1 - (dx ** 2 + dy ** 2), 0, 1)
        a = np.clip(shape * (0.4 + n) - 0.3, 0, 1) * alpha
        self.img = self.img * (1 - a[..., None]) + color * a[..., None]

    # ------------------------------------------------------------ figürler
    def figure(self, mask, base, rim, light=(1, -0.3), rim_w=7, fur=0.0, shade=0.35, seed=0, rim_strength=1.0):
        """mask: 2x float maske. Ters ışık kenarı + hafif hacim gölgesi + kürk dokusu."""
        m = mask
        b = gaussian_filter(m, 18)
        gy, gx = np.gradient(b)
        L = np.array(light, np.float32); L /= np.linalg.norm(L)
        # kenardan ışığa bakan yön (dış normal = -grad)
        facing = np.clip(-(gx * L[0] + gy * L[1]) * 60, 0, 1)
        edge = np.clip(m - gaussian_filter(m, rim_w * S / 2) * 0 - _erode(m, rim_w * S), 0, 1)
        rimk = np.clip(edge * facing * rim_strength, 0, 1)
        vol = np.clip(-(gx * L[0] + gy * L[1]) * 25, -1, 1)
        col = np.broadcast_to(base, self.img.shape).copy() * (1 + shade * vol[..., None])
        if fur:
            n = noise2(HH, WW // 6, 3, 2, seed); n = up(n)
            n = gaussian_filter(n, (6, 0.6))
            col *= (1 - fur + 2 * fur * n[..., None])
        col = col * (1 - rimk[..., None]) + rim * rimk[..., None]
        self.img = self.img * (1 - m[..., None]) + col * m[..., None]
        # kenarda ışık taşması
        bloom = gaussian_filter(rimk, 10 * S) * 0.6
        self.img += rim * bloom[..., None] * 0.5

    def paste_rgba(self, rgba, x=0, y=0):
        a = rgba[..., 3:4]; h, w = rgba.shape[:2]
        y0, x0 = int(y * S), int(x * S)
        sub = self.img[y0:y0 + h, x0:x0 + w]
        sub[:] = sub * (1 - a[:sub.shape[0], :sub.shape[1]]) + rgba[:sub.shape[0], :sub.shape[1], :3] * a[:sub.shape[0], :sub.shape[1]]

    # ------------------------------------------------------------ bitiş
    def finish(self, vignette=0.45, grain=0.035, warm=0.0, seed=99):
        img = self.img
        if warm: img = img * (1 + np.array([warm, warm * 0.3, -warm], np.float32))
        d = np.hypot((self.xx - WW / 2) / (WW / 2), (self.yy - HH / 2) / (HH / 2))
        img = img * (1 - vignette * np.clip(d - 0.45, 0, 1)[..., None] ** 1.4)
        img = img / (1 + 0.25 * np.clip(img - 0.8, 0, None))  # tepe sıkıştırma
        rng = np.random.default_rng(seed)
        img = img + (rng.standard_normal((HH, WW, 1)).astype(np.float32) * grain)
        im = Image.fromarray((np.clip(img, 0, 1) ** (1 / 1.0) * 255).astype(np.uint8))
        return im

def _erode(m, r):
    return np.clip(gaussian_filter(m, r / 2.2) * 2 - 1, 0, 1) if r > 0 else m

# ---------------------------------------------------------------- şekil (metaball silüet)
class Shape:
    """Basit parçalardan (elips, kapsül, çokgen) organik silüet. Koordinatlar 1x, ölçek ve konumla."""
    def __init__(self, x, y, scale=1.0, flip=False):
        self.im = Image.new("L", (WW, HH), 0); self.d = ImageDraw.Draw(self.im)
        self.x, self.y, self.s, self.flip = x, y, scale, flip
    def P(self, px, py):
        if self.flip: px = -px
        return ((self.x + px * self.s) * S, (self.y + py * self.s) * S)
    def e(self, cx, cy, rx, ry, ang=0, v=255):
        pts = []
        for i in range(48):
            t = 2 * math.pi * i / 48; a = math.radians(ang)
            px = cx + rx * math.cos(t) * math.cos(a) - ry * math.sin(t) * math.sin(a)
            py = cy + rx * math.cos(t) * math.sin(a) + ry * math.sin(t) * math.cos(a)
            pts.append(self.P(px, py))
        self.d.polygon(pts, fill=v); return self
    def cap(self, x1, y1, x2, y2, r1, r2=None, v=255):
        r2 = r1 if r2 is None else r2
        n = 10
        for i in range(n + 1):
            t = i / n; self.e(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t, r1 + (r2 - r1) * t, r1 + (r2 - r1) * t, v=v)
        return self
    def poly(self, pts, v=255):
        self.d.polygon([self.P(*p) for p in pts], fill=v); return self
    def mask(self, smooth=10, fuzz=0.0, seed=0, soft=1.2):
        m = np.asarray(self.im, np.float32) / 255.0
        if smooth: m = gaussian_filter(m, smooth * S * self.s / 1.0 if self.s < 1 else smooth * S)
        if fuzz:
            n = noise2(HH, WW, 6, 2, seed) - 0.5
            m = m + n * fuzz
        m = np.clip((m - 0.5) * 6 + 0.5, 0, 1) if smooth else m
        return gaussian_filter(m, soft * S)

# ---------------------------------------------------------------- figür kütüphanesi
def bear_upright(x, y, sc=1.0, flip=False, crate=False):
    """Arka ayakları üzerinde, sağa yürüyen boz ayı. (x,y)= ayak hizası, boy ~ 520*sc."""
    s = Shape(x, y, sc, flip)
    s.cap(-40, -10, -30, -150, 34, 52)          # arka bacak
    s.cap(30, -10, 20, -150, 32, 50)            # ön arka bacak
    s.e(-50, -6, 46, 16).e(40, -6, 46, 16)      # tabanlar
    s.e(-5, -230, 105, 135, -12)                # gövde/kalça
    s.e(15, -360, 82, 100, -18)                 # göğüs
    s.e(55, -440, 52, 44, -10)                  # boyun-omuz
    s.e(95, -478, 48, 42)                       # kafa
    s.e(140, -466, 30, 20, 12)                  # burun
    s.e(70, -514, 14, 14).e(98, -520, 13, 13)   # kulaklar
    if crate:
        s.cap(40, -390, 140, -330, 30, 26)      # kollar öne
        s.cap(10, -370, 120, -300, 28, 24)
    else:
        s.cap(40, -390, 95, -280, 30, 24)
        s.cap(0, -380, 25, -260, 28, 22)
    return s

def bear_sitting(x, y, sc=1.0, flip=False, bottle=False):
    """Oturan ayı, yandan (sağa bakar). (x,y)= zemin."""
    s = Shape(x, y, sc, flip)
    s.e(0, -120, 135, 125)                      # gövde/kalça
    s.e(35, -250, 90, 95, -15)                  # göğüs
    s.e(70, -335, 55, 48)                       # kafa
    s.e(118, -322, 32, 21, 15)                  # burun
    s.e(45, -375, 15, 15).e(75, -383, 14, 14)   # kulaklar
    s.e(95, -14, 60, 20)                        # arka ayak tabanı
    s.cap(60, -60, 110, -20, 42, 28)            # arka bacak
    if bottle:
        s.cap(50, -250, 120, -310, 30, 24)      # kol ağza
    else:
        s.cap(70, -220, 95, -40, 32, 26)        # ön bacak
    return s

def soldier(x, y, sc=1.0, flip=False, pose="stand"):
    """İkinci Dünya Savaşı İngiliz tipi miğferli asker (Polonya II. Kolordusu İngiliz teçhizatı kullandı)."""
    s = Shape(x, y, sc, flip)
    if pose == "stand":
        s.cap(-14, -10, -10, -230, 18, 24).cap(16, -10, 12, -230, 18, 24)   # bacaklar
        s.e(-16, -6, 28, 10).e(22, -6, 28, 10)
        s.e(0, -330, 50, 120)                                               # gövde (palto)
        s.poly([(-48, -330), (48, -330), (60, -190), (-58, -190)])          # palto eteği
        s.cap(-38, -410, -46, -240, 16, 14).cap(40, -410, 50, -250, 16, 14)  # kollar
        s.e(4, -470, 26, 30)                                                 # kafa
        s.e(4, -486, 58, 9)                                                  # miğfer kenarı
        s.e(4, -496, 34, 20)                                                 # miğfer kubbesi
        s.cap(30, -410, 70, -560, 5, 5)                                      # tüfek namlusu (omuzda)
    elif pose == "sit":
        s.cap(-10, -10, 60, -60, 18, 24).cap(60, -60, 80, -8, 16, 18)
        s.e(-20, -150, 46, 100, 8)
        s.cap(-10, -210, 50, -110, 15, 13)
        s.e(-10, -270, 24, 28)
        s.e(-10, -285, 54, 8).e(-10, -294, 32, 18)
    return s

# ---------------------------------------------------------------- yazı
def text_overlay(im, line_text=None, title=None, sub=None, page=None, total=None, title_y=None, line_size=50):
    im = im.resize((W, H), Image.LANCZOS).convert("RGBA")
    ov = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    if line_text:
        g = Image.linear_gradient("L").resize((W * S, 520 * S)).point(lambda v: int(v * 0.85))
        blk = Image.new("RGBA", (W * S, 520 * S), (8, 6, 4, 255)); blk.putalpha(g)
        ov.alpha_composite(blk, (0, (H - 520) * S))
        _wrap(d, line_text, F(F_BOLD, line_size), 540, 1150, 900, (250, 244, 232))
    if title:
        ty = title_y if title_y is not None else 110
        g = Image.linear_gradient("L").rotate(180).resize((W * S, 520 * S)).point(lambda v: int(v * 0.7))
        blk = Image.new("RGBA", (W * S, 520 * S), (8, 6, 4, 255)); blk.putalpha(g)
        ov.alpha_composite(blk, (0, 0))
        d.text((540 * S, ty * S), title, font=F(F_BLACK, 120), fill=(250, 244, 232), anchor="ma")
        if sub: d.text((540 * S, (ty + 140) * S), sub, font=F(F_SEMI, 40), fill=(236, 196, 120), anchor="ma")
    d.text((44 * S, 1300 * S), "@fermantarih", font=F(F_SEMI, 26), fill=(250, 244, 232, 170), anchor="ls")
    if page:
        for i in range(total):
            cx = W - 44 - (total - 1 - i) * 22
            d.ellipse([(cx - 5) * S, 1288 * S, (cx + 5) * S, 1298 * S], fill=(250, 244, 232, 255 if i + 1 == page else 90))
    ov = ov.resize((W, H), Image.LANCZOS)
    im.alpha_composite(ov)
    return im.convert("RGB")

def _wrap(d, text, font, cx, y_bottom, maxw, fill):
    words = text.split(); lines = []; cur = ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if font.getlength(t) / S <= maxw: cur = t
        else: lines.append(cur); cur = w_
    lines.append(cur)
    lh = font.size / S * 1.22
    y = y_bottom - lh * (len(lines) - 1)
    for i, l in enumerate(lines):
        d.text((cx * S, (y + i * lh) * S), l, font=font, fill=fill, anchor="ms")

def save_all(slides, outdir):
    os.makedirs(outdir, exist_ok=True); paths = []
    for i, im in enumerate(slides, 1):
        p = os.path.join(outdir, f"{i}.jpg"); im.save(p, quality=93); paths.append(p)
    return paths

def contact_sheet(paths, out, cols=3):
    ims = [Image.open(p).resize((360, 450)) for p in paths]
    rows = (len(ims) + cols - 1) // cols
    sh = Image.new("RGB", (cols * 360, rows * 450), (20, 20, 20))
    for i, im in enumerate(ims): sh.paste(im, ((i % cols) * 360, (i // cols) * 450))
    sh.save(out); return out

# ---------------------------------------------------------------- elle çizilmiş dış hatlar (gerçekçi oranlar)
def catmull(pts, n=10, closed=True):
    P = list(pts); out = []
    L = len(P)
    rng = range(L) if closed else range(L - 1)
    for i in rng:
        p0, p1, p2, p3 = P[(i - 1) % L], P[i], P[(i + 1) % L], P[(i + 2) % L]
        for k in range(n):
            t = k / n; t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    return out

OUTLINES = {
 # ayakta (arka ayakları üzerinde) boz ayı, sağa bakar. y=0 zemin, boy ~860 birim
 "bear_up": [(-160,0),(-40,0),(-48,-40),(-30,-140),(0,-200),(40,-140),(40,-40),(30,0),(150,0),(140,-30),(118,-80),
             (110,-220),(130,-330),(150,-450),(200,-480),(250,-430),(280,-410),(288,-440),(240,-520),(212,-600),
             (240,-660),(300,-680),(358,-698),(386,-718),(376,-746),(322,-766),(282,-800),(268,-834),(244,-858),
             (214,-842),(170,-836),(100,-832),(20,-790),(-60,-700),(-120,-560),(-160,-400),(-180,-250),(-175,-120),(-170,-30)],
 # ayakta ayı, kolları önde (sandık taşır)
 "bear_carry": [(-160,0),(-40,0),(-48,-40),(-30,-140),(0,-200),(40,-140),(40,-40),(30,0),(150,0),(140,-30),(118,-80),
             (110,-220),(130,-330),(160,-430),(250,-470),(330,-470),(340,-500),(330,-540),(250,-560),(215,-610),
             (240,-660),(300,-680),(358,-698),(386,-718),(376,-746),(322,-766),(282,-800),(268,-834),(244,-858),
             (214,-842),(170,-836),(100,-832),(20,-790),(-60,-700),(-120,-560),(-160,-400),(-180,-250),(-175,-120),(-170,-30)],
 # oturan ayı (yan), sağa bakar, boy ~620
 "bear_sit": [(-230,0),(150,0),(175,-20),(160,-45),(90,-55),(120,-90),(150,-200),(165,-300),(190,-330),(200,-300),
              (205,-200),(215,-40),(260,-40),(265,-70),(240,-90),(235,-200),(225,-330),(215,-380),(250,-410),
              (305,-422),(338,-440),(330,-465),(280,-482),(250,-515),(236,-545),(212,-562),(190,-546),(150,-545),
              (80,-530),(0,-470),(-90,-380),(-170,-270),(-225,-150),(-245,-60)],
 # oturan ayı, şişeyi ağzına kaldırmış
 "bear_drink": [(-230,0),(150,0),(175,-20),(160,-45),(90,-55),(120,-90),(150,-200),(175,-300),(230,-330),(290,-380),
              (330,-430),(345,-470),(325,-480),(290,-450),(265,-430),(300,-445),(338,-440),(330,-465),(280,-482),(250,-515),
              (236,-545),(212,-562),(190,-546),(150,-545),(80,-530),(0,-470),(-90,-380),(-170,-270),(-225,-150),(-245,-60)],
 # İngiliz tipi miğferli, paltolu asker, sağa bakar, boy ~915
 "soldier": [(-70,0),(95,0),(90,-32),(50,-55),(52,-200),(60,-300),(95,-340),(88,-500),(78,-525),(88,-610),(80,-690),
             (50,-722),(44,-752),(58,-780),(52,-800),(50,-822),(88,-830),(82,-846),(52,-876),(4,-890),(-44,-874),
             (-74,-846),(-80,-834),(-34,-818),(-38,-756),(-76,-700),(-86,-550),(-100,-345),(-56,-300),(-64,-150),(-70,-40)],
 # bağdaş kurmuş/oturan asker, sağa bakar
 "soldier_sit": [(-120,0),(160,0),(165,-25),(130,-40),(150,-120),(110,-150),(30,-140),(50,-230),(40,-330),(25,-360),
                 (30,-392),(40,-418),(34,-440),(96,-452),(90,-468),(50,-500),(-10,-514),(-62,-494),(-104,-462),(-112,-450),
                 (-40,-436),(-42,-380),(-80,-330),(-110,-200),(-125,-80)],
}

def outline_mask(name, x, y, scale=1.0, flip=False, fuzz=0.0, seed=0, blur=0.8, extra=None):
    """Elle çizilmiş dış hattı 2x maske olarak döndürür. (x,y) = zemin noktası (1x)."""
    pts = catmull(OUTLINES[name], 8)
    sx = -1 if flip else 1
    poly = [((x + px * scale * sx) * S, (y + py * scale) * S) for px, py in pts]
    im = Image.new("L", (WW, HH), 0); d = ImageDraw.Draw(im); d.polygon(poly, fill=255)
    if extra: extra(d, lambda px, py: ((x + px * scale * sx) * S, (y + py * scale) * S), scale)
    m = np.asarray(im, np.float32) / 255.0
    if fuzz:
        n = noise2(HH, WW, 2.5, 2, seed) - 0.5
        m = np.clip(gaussian_filter(m, 2.5 * S) + n * fuzz, 0, 1)
        m = np.clip((m - 0.5) * 5 + 0.5, 0, 1)
    return gaussian_filter(m, blur * S)

def rifle(d, T, sc):
    """Omuzdaki tüfek (askıda), askerin sırtında."""
    a, b = T(-40, -420), T(-92, -1000)
    d.line([a, b], fill=255, width=max(2, int(15 * sc * S)))
