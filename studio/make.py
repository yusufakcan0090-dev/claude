import math, os, sys, subprocess, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

OUT = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 60
rng = np.random.default_rng(7)

FB = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
FC = "/usr/share/fonts/truetype/dejavu/DejaVuSerifCondensed-Bold.ttf"
FI = "/usr/share/fonts/truetype/dejavu/DejaVuSerifCondensed-Italic.ttf"
_fc = {}
def font(p, s):
    k = (p, s)
    if k not in _fc: _fc[k] = ImageFont.truetype(p, s)
    return _fc[k]

INK = (52, 36, 22)
PAPER = (236, 222, 186)
RED = (158, 30, 28)
BLUE = (58, 140, 205)
CREAM = (245, 235, 211)

# ---------------- easing ----------------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x):
    x = clamp(x); return x * x * (3 - 2 * x)
def ease_out(x):
    x = clamp(x); return 1 - (1 - x) ** 3
def back(x):
    x = clamp(x); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2

# ---------------- paper texture / vignette (screen space) ----------------
def noise_img(w, h, scale, amp, seed):
    r = np.random.default_rng(seed)
    small = r.normal(0, 1, (h // scale + 2, w // scale + 2)).astype(np.float32)
    im = Image.fromarray(((small - small.min()) / (np.ptp(small)) * 255).astype(np.uint8))
    im = im.resize((w, h), Image.BICUBIC)
    return (np.asarray(im, np.float32) / 255 - 0.5) * amp

def parchment(w, h, base=PAPER, seed=1):
    a = np.zeros((h, w, 3), np.float32) + np.array(base, np.float32)
    n = noise_img(w, h, 90, 34, seed) + noise_img(w, h, 18, 14, seed + 1) + noise_img(w, h, 3, 10, seed + 2)
    a += n[..., None] * np.array([1.0, 0.95, 0.8])
    # stains
    r = np.random.default_rng(seed + 9)
    yy, xx = np.mgrid[0:h, 0:w]
    for _ in range(6):
        cx, cy, rad = r.uniform(0, w), r.uniform(0, h), r.uniform(80, 260)
        d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
        ring = np.exp(-((d - rad) / 9) ** 2) * 16 + np.exp(-(d / rad) ** 2) * 6
        a -= ring[..., None] * np.array([0.6, 0.8, 1.2])
    return np.clip(a, 0, 255)

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
d = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.6)) ** 2)
VIG = np.clip(1.06 - 0.55 * d ** 2.2, 0.35, 1.0)[..., None].astype(np.float32)
GRAIN = (noise_img(W, H, 2, 14, 99))[..., None].astype(np.float32)
del yy, xx, d

def finish(img, vig=True):
    a = np.asarray(img, np.float32)
    if vig: a = a * VIG
    a = a + GRAIN
    return np.clip(a, 0, 255).astype(np.uint8)

SCREEN_PAPER = Image.fromarray(parchment(W, H, PAPER, 3).astype(np.uint8))
DESK = Image.fromarray(parchment(W, H, (120, 82, 50), 11).astype(np.uint8))

# ---------------- map ----------------
LON0, LON1, LAT0, LAT1 = 10, 110, -20, 70
SX, SY = 32, 40
MW, MH = int((LON1 - LON0) * SX), int((LAT1 - LAT0) * SY)
def P(lon, lat): return ((lon - LON0) * SX, (LAT1 - lat) * SY)

OCEAN = [(10,-20),(39.5,-20),(39.5,-5),(40.5,-2),(42,0),(46,2),(49,6),(51.2,10.5),(51.3,11.9),(48,11.2),(45,10.5),(43.3,11.9),(43.4,12.6),
 (45,12.8),(48.5,14),(52,15.8),(55,17),(56.8,18.5),(58.5,20.5),(59.8,22.5),(58.6,23.6),(56.4,24.9),(56.3,26.2),(54,24.2),(52,24),(51.6,25.3),
 (50.8,24.8),(50.1,26.2),(48.6,28),(48,29.9),(49.5,30),(50.5,29.2),(51.4,27.9),(54,26.6),(56.3,27.1),(57.3,25.8),(59,25.4),(61.6,25.2),(64,25.3),
 (66.6,25.4),(67.4,24),(68.5,23.4),(70,22.6),(69,22.2),(70,20.9),(72.6,21.4),(72.8,19),(73.4,16),(74.4,14),(75.3,11.5),(76.3,9.5),(77.5,8.1),
 (78.2,8.9),(79.3,10.3),(80.2,13),(80.3,15.5),(82.3,17),(84.8,19.3),(87,21.5),(88.5,22),(90,21.8),(91.8,22.4),(92.4,20.7),(94,18.5),(94.3,16),
 (97.6,16.5),(98.5,13),(98.3,9),(100,6),(103,1.5),(110,1),(110,-20)]
SRILANKA = [(79.8,6),(79.9,8.5),(80.1,9.8),(81.3,8.6),(81.9,7.3),(81.2,6.2),(80.3,5.9)]
REDSEA = [(43.4,12.6),(42.6,15.5),(40.8,19.5),(39,21.8),(37.5,24.5),(35.6,27.4),(34.9,29.4),(34.3,27.9),(32.6,29.9),(32.7,29.0),(33.8,27.2),
 (35.3,24),(37.2,21),(38.5,18),(39.7,15.6),(41.6,13.5),(43.2,12.4)]
MED = [(10,37.2),(10,30),(12,32.8),(15,32.3),(17,31),(19,30.3),(20.1,32.3),(21.5,32.9),(23,32.6),(25,31.6),(28,30.9),(29.9,31.2),(31,31.5),
 (32.3,31.2),(34.2,31.3),(34.6,31.8),(35.1,33),(35.6,34.5),(35.9,35.5),(35.9,36.6),(34.5,36.8),(32.5,36.1),(30.6,36.8),(29.5,36.2),(28.3,36.7),
 (27.3,37),(26.5,37.8),(27,38.5),(26.6,39.3),(26.2,40.3),(26,40.8),(24.5,40.9),(22.9,40.5),(23.8,38),(23.2,36.5),(22.3,36.4),(21,38.4),
 (20,39.6),(19.4,41.8),(16,41.4),(18.5,40.2),(17,39),(16.1,38),(15.6,40),(12,41.8),(10,43.5),(10,37.2)]
SICILY = [(12.4,38),(13.4,38.2),(15.6,38.3),(15.1,36.7),(12.5,37.6)]
MARMARA = [(26.2,40.3),(27.5,40.95),(28.9,41.05),(29.2,40.7),(27.8,40.35)]
BLACK = [(29.1,41.2),(28.1,41.6),(27.9,42.7),(28.6,43.8),(29.7,45.2),(30.8,46.5),(32,46.4),(33.4,45),(36.4,45.2),(37,44.8),(38.5,44.4),
 (40,43.4),(41.6,41.6),(40,41),(37.5,41.1),(35.2,42),(33.3,42),(31.3,41.1)]
CASPIAN = [(49.2,46.5),(51.2,47),(53.1,46.6),(53.2,45.3),(51.4,44.6),(52.7,42.3),(53.9,40.9),(53.1,39.4),(53.9,37.3),(51.6,36.7),(49.3,37.5),
 (48.9,38.6),(49.5,40.3),(48.4,41.9),(47.5,43),(46.9,44.6),(47.6,45.6)]
CYPRUS = [(32.3,35.1),(33.7,35.4),(34.6,35.7),(34,34.6),(32.6,34.7)]
CRETE = [(23.5,35.3),(24.5,35.5),(26.3,35.3),(25,35)]
SEAS = [OCEAN, REDSEA, MED, MARMARA, BLACK, CASPIAN]
ISLANDS = [SRILANKA, SICILY, CYPRUS, CRETE]

XINJIANG = [(73.5,39.4),(73.8,38.5),(74.9,37.4),(75.4,36.9),(76.0,36.6),(77.8,35.5),(79.0,35.9),(80.3,35.3),(81.0,35.6),(82.5,35.7),
 (84.5,36.4),(86.5,36.0),(89.0,36.0),(90.8,36.4),(91.5,37.0),(93.0,37.8),(95.3,38.4),(96.2,39.6),(95.6,41.0),(96.4,42.7),(95.3,44.2),
 (93.5,44.9),(91.0,45.2),(90.5,46.5),(91.0,47.0),(90.0,48.0),(88.0,48.6),(87.3,49.1),(86.5,48.5),(85.6,47.3),(85.0,47.0),(83.0,47.2),
 (82.4,46.0),(82.6,45.3),(80.0,45.0),(79.9,44.5),(80.8,43.2),(80.2,42.1),(78.5,41.5),(77.4,41.0),(76.5,40.4),(75.5,40.6),(74.8,40.4),(73.8,39.7)]

CITY = {"İstanbul": (28.98, 41.01), "Süveyş": (32.55, 29.97), "Bombay": (72.88, 19.08), "Kaşgar": (75.99, 39.47),
        "Hoten": (79.92, 37.11), "Turfan": (89.19, 42.95), "Urumçi": (87.62, 43.83), "Yarkent": (77.24, 38.41), "Kuça": (82.96, 41.72)}

ROUTE_LL = [(28.98,41.01),(27.9,40.6),(26.4,40.1),(25.6,39),(25.3,37),(26.8,35.6),(29.5,33.6),(31.6,31.8),(32.35,31.25),(32.55,29.97),
 (33.3,28.3),(34.6,26.6),(36.6,23.6),(38.4,20.5),(40.2,17),(42.3,14.4),(43.5,12.7),(46,12.4),(50,13.1),(54,14.6),(58,16.6),(63,18.4),
 (68,19.2),(72.88,19.08),(74.2,22.8),(74.6,26.8),(74.4,30.6),(74.6,33.6),(75.2,36.2),(75.99,39.47)]

def poly_px(pl, s=1): return [(P(*q)[0] * s, P(*q)[1] * s) for q in pl]

def build_map():
    s = 2  # supersample
    G = os.path.join(OUT, "geo")
    real = os.path.exists(os.path.join(G, "land.geojson"))
    def rings(path):
        import json
        js = json.load(open(path))
        for f in js["features"]:
            g = f["geometry"]
            if g is None: continue
            polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]] if g["type"] == "Polygon" else []
            for poly in polys:
                for k, ring in enumerate(poly):
                    lo = [p[0] for p in ring]; la = [p[1] for p in ring]
                    if max(lo) < LON0 - 5 or min(lo) > LON1 + 5 or max(la) < LAT0 - 5 or min(la) > LAT1 + 5: continue
                    yield k, [(P(p[0], p[1])[0] * s, P(p[0], p[1])[1] * s) for p in ring], f.get("properties", {})
    if real:
        mask = Image.new("L", (MW * s, MH * s), 0)
        dr = ImageDraw.Draw(mask)
        for k, pts, _ in rings(os.path.join(G, "land.geojson")):
            if len(pts) > 2: dr.polygon(pts, fill=255 if k == 0 else 0)
        if os.path.exists(os.path.join(G, "lakes.geojson")):
            for k, pts, _ in rings(os.path.join(G, "lakes.geojson")):
                if len(pts) > 2: dr.polygon(pts, fill=0 if k == 0 else 255)
    else:
        mask = Image.new("L", (MW * s, MH * s), 255)  # 255 land
        dr = ImageDraw.Draw(mask)
        for pl in SEAS: dr.polygon(poly_px(pl, s), fill=0)
        for pl in ISLANDS: dr.polygon(poly_px(pl, s), fill=255)
    mask = mask.resize((MW, MH), Image.LANCZOS)
    m = np.asarray(mask, np.float32) / 255
    m_blur = np.asarray(mask.filter(ImageFilter.GaussianBlur(14)), np.float32) / 255
    land = parchment(MW, MH, (238, 224, 188), 21)
    sea = parchment(MW, MH, (172, 190, 186), 22)
    # coastal water tint
    sea = sea - (m_blur[..., None] * np.array([18, 10, 0]))
    a = land * m[..., None] + sea * (1 - m[..., None])
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    dr = ImageDraw.Draw(img, "RGBA")
    # graticule
    for lon in range(LON0, LON1 + 1, 10):
        x = P(lon, 0)[0]; dr.line([(x, 0), (x, MH)], fill=(110, 80, 50, 40), width=2)
    for lat in range(LAT0, LAT1 + 1, 10):
        y = P(0, lat)[1]; dr.line([(0, y), (MW, y)], fill=(110, 80, 50, 40), width=2)
    # water lines (ripple contours) via dilated masks
    seam = (1 - m)
    for i, rad in enumerate([10, 22, 38]):
        er = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(2 * (rad // 2) + 1))
        edge = np.asarray(er.filter(ImageFilter.FIND_EDGES), np.float32) / 255
        col = np.array([95, 85, 70], np.float32)
        arr = np.asarray(img, np.float32)
        k = np.clip(edge * 1.6, 0, 1)[..., None] * (0.35 - i * 0.09) * seam[..., None]
        arr = arr * (1 - k) + col * k
        img = Image.fromarray(arr.astype(np.uint8))
    # coastline ink
    edge = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.FIND_EDGES), np.float32) / 255
    edge = np.asarray(Image.fromarray((np.clip(edge * 3, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)), np.float32) / 255
    arr = np.asarray(img, np.float32)
    k = edge[..., None] * 0.85
    arr = arr * (1 - k) + np.array(INK, np.float32) * k
    img = Image.fromarray(arr.astype(np.uint8))
    dr = ImageDraw.Draw(img, "RGBA")
    rv = os.path.join(G, "rivers.geojson")
    if os.path.exists(rv):
        import json
        for f in json.load(open(rv))["features"]:
            g = f["geometry"]
            if g is None: continue
            lines = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
            sr = (f.get("properties") or {}).get("scalerank", 5) or 5
            wdt = 4 if sr <= 3 else 3 if sr <= 6 else 2
            for ln in lines:
                pts = [P(p[0], p[1]) for p in ln]
                if len(pts) > 1 and any(0 <= x < MW and 0 <= y < MH for x, y in pts):
                    dr.line(pts, fill=(70, 95, 105, 170), width=wdt, joint="curve")
    # mountains
    ranges = [[(67,41),(73,41.3),(79,42),(84,43),(88,43.5),(95,43.2)],
              [(76,36.6),(80,36.3),(85,36),(90,36.4),(94,37)],
              [(72,35.2),(75,34),(78,31.5),(81,30),(84,28.6),(88,27.8),(92,27.6),(96,28.5)],
              [(66.5,34.5),(69,35.2),(71.5,36),(73.5,37)],
              [(41,40),(44,39.3),(48,38.5),(52,36.5),(56,37.5),(60,37)],
              [(32,37.2),(35,37.6),(38,38.2)],
              [(41.5,43),(44,42.7),(47,41.8)]]
    r = random.Random(4)
    for rg in ranges:
        pts = [P(*q) for q in rg]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            L = math.hypot(x1 - x0, y1 - y0); n = int(L / 30)
            for i in range(n):
                t = i / max(n, 1); x = x0 + (x1 - x0) * t + r.uniform(-10, 10); y = y0 + (y1 - y0) * t + r.uniform(-14, 14)
                hgt = r.uniform(16, 28); wd = hgt * 0.9
                dr.line([(x - wd, y + hgt * 0.5), (x, y - hgt * 0.5), (x + wd, y + hgt * 0.5)], fill=(80, 55, 32, 200), width=3)
                dr.line([(x, y - hgt * 0.5), (x + wd * 0.45, y + hgt * 0.5)], fill=(80, 55, 32, 90), width=2)
    # desert stipple (Taklamakan, Arabia)
    for (lo0, lo1, la0, la1, n) in [(78, 88, 37.4, 40.6, 900), (40, 55, 18, 28, 1300), (25, 32, 22, 29, 600)]:
        for _ in range(n):
            lon, lat = r.uniform(lo0, lo1), r.uniform(la0, la1)
            x, y = P(lon, lat)
            if m[int(y), int(x)] > 0.5:
                dr.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(150, 115, 70, 150))
    # region labels
    def lab(text, lon, lat, size, col=(90, 62, 38, 200), sp=6, f=FI):
        fnt = font(f, size); x, y = P(lon, lat)
        tw = sum(fnt.getlength(c) + sp for c in text) - sp
        cx = x - tw / 2
        for c in text:
            dr.text((cx, y), c, font=fnt, fill=col, anchor="lm"); cx += fnt.getlength(c) + sp
    lab("OSMANLI DEVLETİ", 33.5, 39.4, 40)
    lab("İRAN", 54, 32.5, 44)
    lab("HİNDİSTAN", 78.5, 22.5, 44)
    lab("ARABİSTAN", 45, 23.5, 38)
    lab("RUSYA", 62, 52, 48)
    lab("ÇİN", 102, 33, 56)
    lab("Hint Okyanusu", 66, 8, 40, (80, 75, 60, 170))
    lab("Akdeniz", 19, 34.5, 34, (80, 75, 60, 170))
    lab("Kızıldeniz", 37.4, 21.4, 22, (80, 75, 60, 170), sp=3)
    lab("Hazar", 50.5, 42.2, 26, (80, 75, 60, 170), sp=3)
    lab("Taklamakan", 83, 39.0, 28, (110, 80, 45, 190), sp=4)
    # compass rose
    cx, cy = P(57, 0)
    for ang, ln in [(0, 90), (90, 60), (180, 60), (270, 60), (45, 36), (135, 36), (225, 36), (315, 36)]:
        a = math.radians(ang - 90); x2, y2 = cx + math.cos(a) * ln, cy + math.sin(a) * ln
        pa = math.radians(ang); w_ = 10
        dr.polygon([(x2, y2), (cx + math.cos(a + 1.57) * w_, cy + math.sin(a + 1.57) * w_), (cx, cy),
                    (cx + math.cos(a - 1.57) * w_, cy + math.sin(a - 1.57) * w_)], fill=(80, 55, 32, 170))
    dr.ellipse([cx - 70, cy - 70, cx + 70, cy + 70], outline=(80, 55, 32, 140), width=3)
    dr.text((cx, cy - 112), "K", font=font(FB, 34), fill=(80, 55, 32, 200), anchor="mm")
    return img

MAPF = os.path.join(OUT, "map.png")
if os.path.exists(MAPF): MAP = Image.open(MAPF).convert("RGB")
else:
    MAP = build_map(); MAP.save(MAPF)

def camera(cx, cy, vh):
    vw = vh * W / H
    vh = min(vh, MH); vw = min(vw, MW)
    x0 = clamp(cx - vw / 2, 0, MW - vw); y0 = clamp(cy - vh / 2, 0, MH - vh)
    return x0, y0, vw, vh

def render_map(cam, extra=None):
    x0, y0, vw, vh = cam
    if extra is not None: src = extra
    else: src = MAP
    im = src.transform((W, H), Image.EXTENT, (x0, y0, x0 + vw, y0 + vh), Image.BILINEAR)
    return im

def to_screen(cam, lon, lat):
    x0, y0, vw, vh = cam; mx, my = P(lon, lat)
    return ((mx - x0) * W / vw, (my - y0) * H / vh)

# ---------------- drawing helpers ----------------
def spaced_text(dr, xy, text, fnt, fill, sp=0, anchor="mm", stroke=0, sfill=None):
    if len(fill) == 4 and fill[3] <= 0: return
    if sp == 0:
        dr.text(xy, text, font=fnt, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=sfill); return
    tw = sum(fnt.getlength(c) + sp for c in text) - sp
    x = xy[0] - tw / 2
    for c in text:
        dr.text((x, xy[1]), c, font=fnt, fill=fill, anchor="lm", stroke_width=stroke, stroke_fill=sfill)
        x += fnt.getlength(c) + sp

def grunge(img, amount=0.28, seed=0):
    a = np.asarray(img).copy()
    n = noise_img(img.width, img.height, 6, 1, seed) + noise_img(img.width, img.height, 2, 0.6, seed + 1)
    holes = n > (0.5 - amount)
    a[..., 3] = (a[..., 3] * np.where(holes, 0.25, 1.0)).astype(np.uint8)
    return Image.fromarray(a)

def stamp_card(lines, w, h, col=RED, seed=0, sizes=None, bg=None):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    if bg: dr.rounded_rectangle([6, 6, w - 6, h - 6], 14, fill=bg)
    dr.rounded_rectangle([6, 6, w - 6, h - 6], 14, outline=col + (255,), width=8)
    dr.rounded_rectangle([20, 20, w - 20, h - 20], 8, outline=col + (255,), width=3)
    sizes = sizes or [int(h * 0.36)] * len(lines)
    tot = sum(sizes) + 10 * (len(lines) - 1); y = h / 2 - tot / 2
    for ln, sz in zip(lines, sizes):
        fnt = font(FB, sz)
        while fnt.getlength(ln) + 4 * len(ln) > w - 70: sz -= 2; fnt = font(FB, sz)
        spaced_text(dr, (w / 2, y + sz / 2), ln, fnt, col + (255,), sp=4); y += sz + 10
    return grunge(im, 0.22, seed)

def paste_pop(base, card, cx, cy, t, rot=-3, dur=0.35):
    if t < 0: return
    p = clamp(t / dur)
    s = 1.0 + 0.9 * (1 - ease_out(p)) if p < 1 else 1.0
    alpha = clamp(t / 0.12)
    c = card.rotate(rot, resample=Image.BICUBIC, expand=True)
    c = c.resize((max(1, int(c.width * s)), max(1, int(c.height * s))), Image.BILINEAR)
    if alpha < 1:
        a = np.asarray(c).copy(); a[..., 3] = (a[..., 3] * alpha).astype(np.uint8); c = Image.fromarray(a)
    base.alpha_composite(c, (int(cx - c.width / 2), int(cy - c.height / 2)))

def make_flag(w, h, color):
    s = 3; im = Image.new("RGBA", (w * s, h * s), color + (255,)); dr = ImageDraw.Draw(im)
    G = h * s
    def circ(cx, cy, r, f): dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=f)
    circ(0.5 * G, 0.5 * G, 0.25 * G, (255, 255, 255, 255))
    circ(0.5625 * G, 0.5 * G, 0.2 * G, color + (255,))
    cx, cy, R = 0.93 * G, 0.5 * G, 0.125 * G
    pts = []
    for i in range(10):
        a = math.pi + i * math.pi / 5; r = R if i % 2 == 0 else R * 0.382
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    dr.polygon(pts, fill=(255, 255, 255, 255))
    im = im.resize((w, h), Image.LANCZOS)
    return im

def wave_flag(flag, t, amp=16, pad=40):
    a = np.asarray(flag).astype(np.float32); h, w = a.shape[:2]
    out = np.zeros((h + 2 * pad, w, 4), np.float32)
    xs = np.arange(w)
    ph = 2 * math.pi * (xs / (w * 0.55)) - t * 5.0
    off = amp * np.sin(ph) * (0.25 + 0.75 * xs / w)
    shade = 1 + 0.18 * np.cos(ph)
    for x in range(w):
        o = int(round(off[x])) + pad
        out[o:o + h, x, :3] = a[:, x, :3] * shade[x]
        out[o:o + h, x, 3] = a[:, x, 3]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))

def shadow(img, r=14, off=(10, 14), op=110):
    a = np.asarray(img)[..., 3]
    sh = Image.new("RGBA", (img.width + 60, img.height + 60), (0, 0, 0, 0))
    m = Image.fromarray(a); sm = Image.new("L", sh.size, 0); sm.paste(m, (30, 30))
    sm = sm.filter(ImageFilter.GaussianBlur(r))
    sh.putalpha(sm.point(lambda v: v * op // 255))
    return sh

def city_dot(dr, x, y, name, t, color=RED, labelside="r", size=46):
    if t < 0: return
    p = clamp(t / 0.3); r = 14 * back(p)
    dr.ellipse([x - r - 6, y - r - 6, x + r + 6, y + r + 6], fill=(245, 235, 211, int(220 * p)))
    dr.ellipse([x - r, y - r, x + r, y + r], fill=color + (int(255 * p),), outline=INK + (int(255 * p),), width=3)
    fnt = font(FB, size); a = int(255 * clamp(t / 0.35))
    if labelside == "r": xy, an = (x + 30, y), "lm"
    elif labelside == "l": xy, an = (x - 30, y), "rm"
    elif labelside == "u": xy, an = (x, y - 34), "mb"
    else: xy, an = (x, y + 34), "mt"
    dr.text(xy, name, font=fnt, fill=INK + (a,), anchor=an, stroke_width=6, stroke_fill=(245, 235, 211, a))

def pulse(dr, x, y, t, color=RED):
    for k in range(2):
        ph = ((t * 0.8 + k * 0.5) % 1.0)
        r = 18 + ph * 80; a = int(200 * (1 - ph))
        dr.ellipse([x - r, y - r, x + r, y + r], outline=color + (a,), width=5)

def title_band(base, text, t, y=270, size=66, col=RED, sub=None):
    if t < 0: return
    card = stamp_card([text] + ([sub] if sub else []), 900, 170 if not sub else 230, col, seed=len(text),
                      sizes=[size] + ([40] if sub else []), bg=(240, 228, 196, 235))
    paste_pop(base, card, W / 2, y, t, rot=-2)

def fade_black(img, t, dur, fin=0.18, fout=0.18):
    k = 1.0
    if t < fin: k = t / fin
    if t > dur - fout: k = min(k, (dur - t) / fout)
    k = clamp(k)
    if k >= 1: return img
    a = np.asarray(img, np.float32) * k + np.array([14, 10, 7], np.float32) * (1 - k)
    return Image.fromarray(a.astype(np.uint8))

# ---------------- scenes ----------------
OTT = make_flag(560, 373, (200, 16, 46))
ETF = make_flag(560, 373, (86, 165, 222))

def scene1(t, dur):
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    # title
    a = int(255 * clamp((t - 0.15) / 0.4))
    spaced_text(dr, (W / 2, 250), "OSMANLI'NIN", font(FB, 70), INK + (a,), sp=8)
    spaced_text(dr, (W / 2, 340), "UNUTULAN MÜTTEFİKİ", font(FB, 66), RED + (a,), sp=5)
    for i, (flag, name, y, t0) in enumerate([(OTT, "OSMANLI", 640, 0.35), (ETF, "KAŞGAR", 1080, 0.9)]):
        tt = t - t0
        if tt < 0: continue
        p = ease_out(tt / 0.45)
        wf = wave_flag(flag, t + i * 0.7)
        sh = shadow(wf)
        dx = (1 - p) * (-700 if i == 0 else 700)
        x = W / 2 - wf.width / 2 + dx
        base.alpha_composite(sh, (int(x - 30 + 12), int(y - wf.height / 2 - 30 + 16)))
        base.alpha_composite(wf, (int(x), int(y - wf.height / 2)))
        dr = ImageDraw.Draw(base, "RGBA")
        spaced_text(dr, (W / 2 + dx, y + wf.height / 2 + 6), name, font(FB, 44), INK + (int(255 * p),), sp=10)
    dr = ImageDraw.Draw(base, "RGBA")
    # link
    if t > 1.4:
        p = ease_out((t - 1.4) / 0.4)
        dr.line([(W / 2, 880), (W / 2, 880 + 0 * p)], fill=INK)
    stamp = stamp_card(["1873"], 300, 130, RED, seed=5, sizes=[78], bg=(240, 228, 196, 230))
    paste_pop(base, stamp, W / 2 + 255, 470, t - 1.9, rot=-12)
    return base.convert("RGB")

KAS = P(*CITY["Kaşgar"]); IST = P(*CITY["İstanbul"])

def region_layer(color, alpha, cam, xcut=None, base=None):
    pass

def draw_region(base, cam, color, alpha, lon_cut=None, from_east=True):
    pts = [to_screen(cam, *q) for q in XINJIANG]
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d2 = ImageDraw.Draw(lay)
    d2.polygon(pts, fill=color + (int(alpha * 255),))
    hatch = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dh = ImageDraw.Draw(hatch)
    for k in range(-H, W + H, 22): dh.line([(k, 0), (k + H, H)], fill=color + (int(alpha * 170),), width=3)
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).polygon(pts, fill=255)
    if lon_cut is not None:
        xc = to_screen(cam, lon_cut, 40)[0]
        cut = Image.new("L", (W, H), 0); ImageDraw.Draw(cut).rectangle([xc, 0, W, H] if from_east else [0, 0, xc, H], fill=255)
        m = ImageChops.multiply(m, cut)
    lay2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lay2.alpha_composite(lay); lay2.alpha_composite(hatch)
    lay2.putalpha(ImageChops.multiply(lay2.getchannel("A"), m))
    base.alpha_composite(lay2)
    d = ImageDraw.Draw(base, "RGBA")
    if lon_cut is None:
        d.line(pts + [pts[0]], fill=color + (int(min(1, alpha * 2.5) * 230),), width=5, joint="curve")

def scene2(t, dur):
    # pan Istanbul -> Kashgar
    p = ease((t - 0.2) / 2.8)
    cx = IST[0] + (KAS[0] + 230 - IST[0]) * p
    cy = IST[1] + (KAS[1] + 40 - IST[1]) * p
    vh = 1500 + 2100 * math.sin(math.pi * p) - 0 * p
    vh = vh * (1 - 0.06 * clamp((t - 3) / 3))
    cam = camera(cx, cy, vh)
    base = render_map(cam).convert("RGBA")
    if t > 3.0:
        draw_region(base, cam, BLUE, 0.28 * ease((t - 3.0) / 0.8))
    dr = ImageDraw.Draw(base, "RGBA")
    ix, iy = to_screen(cam, *CITY["İstanbul"])
    city_dot(dr, ix, iy, "İstanbul", 1.0, labelside="u")
    kx, ky = to_screen(cam, *CITY["Kaşgar"])
    if t > 2.6: pulse(dr, kx, ky, t)
    city_dot(dr, kx, ky, "Kaşgar", t - 2.6, color=BLUE, labelside="d", size=56)
    for i, (nm, side) in enumerate([("Hoten", "d"), ("Turfan", "d"), ("Urumçi", "u"), ("Kuça", "u")]):
        x, y = to_screen(cam, *CITY[nm]); city_dot(dr, x, y, nm, t - (5.6 + i * 0.5), color=BLUE, labelside=side, size=40)
    title_band(base, "KAŞGAR DEVLETİ", t - 2.9, y=300, size=72, col=RED, sub="YAKUP BEY · 1865")
    return base.convert("RGB")

def scene3(t, dur):
    base = DESK.copy().convert("RGBA")
    z = 1 + 0.05 * t / dur
    cw, ch = 880, 1060
    card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    pa = parchment(cw, ch, (240, 226, 190), 31).astype(np.uint8)
    pim = Image.fromarray(pa).convert("RGBA")
    m = Image.new("L", (cw, ch), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, cw - 1, ch - 1], 10, fill=255)
    pim.putalpha(m); card.alpha_composite(pim)
    dr = ImageDraw.Draw(card, "RGBA")
    dr.rectangle([30, 30, cw - 30, ch - 30], outline=RED + (230,), width=6)
    dr.rectangle([46, 46, cw - 46, ch - 46], outline=INK + (200,), width=2)
    for (x, y) in [(30, 30), (cw - 30, 30), (30, ch - 30), (cw - 30, ch - 30)]:
        dr.ellipse([x - 16, y - 16, x + 16, y + 16], fill=RED + (230,))
    def ap(t0): return int(255 * clamp((t - t0) / 0.5))
    spaced_text(dr, (cw / 2, 130), "BÂB-I ÂLÎ · İSTANBUL", font(FB, 40), INK + (ap(0.2),), sp=4)
    dr.line([(150, 185), (cw - 150, 185)], fill=INK + (ap(0.2),), width=2)
    spaced_text(dr, (cw / 2, 300), "16 HAZİRAN", font(FB, 92), RED + (ap(0.5),), sp=3)
    spaced_text(dr, (cw / 2, 410), "1873", font(FB, 118), RED + (ap(0.5),), sp=12)
    lines = [("Kaşgar elçisi", FI, 50, 1.0), ("Seyyid Yakub Han", FB, 56, 1.0),
             ("Sultan Abdülaziz'in", FI, 50, 3.9), ("huzurunda", FI, 50, 3.9)]
    y = 560
    for txt, f, sz, t0 in lines:
        spaced_text(dr, (cw / 2, y), txt, font(f, sz), INK + (ap(t0),)); y += sz + 22
    spaced_text(dr, (cw / 2, 880), "— ASKERÎ YARDIM TALEBİ —", font(FB, 40), RED + (ap(6.2),), sp=3)
    card = card.resize((int(cw * z), int(ch * z)), Image.BICUBIC).rotate(1.2, resample=Image.BICUBIC, expand=True)
    sh = shadow(card, r=24, op=150)
    cx, cy = W / 2, 760
    base.alpha_composite(sh, (int(cx - card.width / 2 - 30 + 14), int(cy - card.height / 2 - 30 + 20)))
    base.alpha_composite(card, (int(cx - card.width / 2), int(cy - card.height / 2)))
    # wax seal
    seal = Image.new("RGBA", (260, 260), (0, 0, 0, 0)); ds = ImageDraw.Draw(seal)
    ds.ellipse([10, 14, 250, 246], fill=(130, 20, 20, 255)); ds.ellipse([42, 44, 218, 216], outline=(200, 60, 50, 255), width=6)
    spaced_text(ds, (130, 130), "1873", font(FB, 52), (225, 120, 100, 255), sp=2)
    seal = grunge(seal, 0.08, 4)
    paste_pop(base, seal, W / 2 + 310, 1270, t - 6.8, rot=-15, dur=0.3)
    return base.convert("RGB")

# route precompute (map px)
def densify(pl, step=6):
    out = []
    for a, b in zip(pl, pl[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1]); n = max(1, int(L / step))
        for i in range(n): out.append((a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n))
    out.append(pl[-1]); return out
ROUTE_PX = densify([P(*q) for q in ROUTE_LL])
cum = [0.0]
for a, b in zip(ROUTE_PX, ROUTE_PX[1:]): cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
RT = cum[-1]
def route_idx_for_city(name):
    q = P(*CITY[name]); best = min(range(len(ROUTE_PX)), key=lambda i: (ROUTE_PX[i][0] - q[0]) ** 2 + (ROUTE_PX[i][1] - q[1]) ** 2)
    return cum[best] / RT
CFR = {n: route_idx_for_city(n) for n in ["Süveyş", "Bombay", "Kaşgar"]}

CARDS = [stamp_card([s], 860, 170, col, seed=i + 10, sizes=[74], bg=(240, 228, 196, 240)) for i, (s, col) in
         enumerate([("6 KRUPP TOPU", RED), ("1200 TÜFEK", RED), ("BARUT USTALARI", RED), ("OSMANLI SUBAYLARI", RED)])]

def draw_ship(dr, x, y, ang, sc=1.0):
    d = 1 if math.cos(ang) >= 0 else -1
    y = y - 10
    def X(u): return x + u * d * sc
    hull = [(X(-46), y), (X(46), y), (X(32), y + 20 * sc), (X(-34), y + 20 * sc)]
    dr.ellipse([x - 54 * sc, y + 4, x + 54 * sc, y + 30 * sc], fill=(245, 235, 211, 150))
    dr.polygon(hull, fill=(70, 45, 25, 255), outline=INK + (255,))
    dr.line([(X(-2), y), (X(-2), y - 62 * sc)], fill=INK + (255,), width=5)
    dr.polygon([(X(2), y - 58 * sc), (X(2), y - 6 * sc), (X(38), y - 8 * sc)], fill=(245, 235, 211, 255), outline=INK + (255,))
    dr.polygon([(X(-6), y - 52 * sc), (X(-6), y - 8 * sc), (X(-34), y - 8 * sc)], fill=(232, 220, 190, 255), outline=INK + (255,))
    dr.polygon([(X(-2), y - 62 * sc), (X(-26), y - 70 * sc), (X(-2), y - 78 * sc)], fill=(200, 16, 46, 255))

def scene4(t, dur):
    prog = ease((t - 1.8) / 4.8)
    L = prog * RT
    hi0 = next((i for i, c in enumerate(cum) if c >= L), len(cum) - 1)
    hxm, hym = ROUTE_PX[hi0]
    mx, my = P(52, 0)[0], P(0, 28.5)[1]
    fz = math.sin(math.pi * clamp((t - 1.4) / 5.4)) * 0.55
    cx = mx + (hxm - mx) * fz; cy = my + (hym - my) * fz
    vh = 3350 - 1100 * fz - 140 * clamp((t - 6.8) / 8)
    cam = camera(cx, cy, vh)
    base = render_map(cam).convert("RGBA")
    dr = ImageDraw.Draw(base, "RGBA")
    pts = [to_screen(cam, *ROUTE_PX[i]) if False else None for i in []]
    sp = [((x - cam[0]) * W / cam[2], (y - cam[1]) * H / cam[3]) for x, y in ROUTE_PX]
    # dashed line up to L
    dash, gap, acc = 26, 14, 0.0
    upto = [sp[i] for i in range(len(sp)) if cum[i] <= L]
    if len(upto) > 1:
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dg = ImageDraw.Draw(glow)
        dg.line(upto, fill=(255, 200, 120, 150), width=26, joint="curve")
        g4 = glow.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3)).resize((W, H), Image.BILINEAR)
        base.alpha_composite(g4)
        dr = ImageDraw.Draw(base, "RGBA")
    for i in range(len(sp) - 1):
        if cum[i] > L: break
        seg_on = (cum[i] % (dash + gap)) < dash
        if seg_on:
            dr.line([sp[i], sp[i + 1]], fill=RED + (255,), width=9)
    # head
    hi = max(0, min(len(sp) - 1, next((i for i, c in enumerate(cum) if c >= L), len(sp) - 1)))
    hx, hy = sp[hi]
    city_dot(dr, *to_screen(cam, *CITY["İstanbul"]), "İstanbul", 1.0, labelside="u", size=44)
    for nm, side in [("Süveyş", "l"), ("Bombay", "l"), ("Kaşgar", "u")]:
        tc = 0.4 + 5.4 * 0  # placeholder
        reached = prog >= CFR[nm] - 0.003
        if reached:
            # time since reached
            city_dot(dr, *to_screen(cam, *CITY[nm]), nm, 1.0, color=BLUE if nm == "Kaşgar" else RED, labelside=side, size=44)
    if 1.8 < t and prog < 0.999:
        j = max(0, hi - 6); jx, jy = sp[j]
        ang = math.atan2(hy - jy, hx - jx) if (hx, hy) != (jx, jy) else 0
        if prog < CFR["Bombay"]:
            draw_ship(dr, hx, hy, ang)
        else:
            dr.ellipse([hx - 20, hy - 20, hx + 20, hy + 20], fill=(245, 235, 211, 255), outline=RED + (255,), width=6)
            dr.ellipse([hx - 7, hy - 7, hx + 7, hy + 7], fill=RED + (255,))
    if prog >= 0.999: pulse(dr, *to_screen(cam, *CITY["Kaşgar"]), t, color=BLUE)
    if t < 6.9: title_band(base, "YARDIM YOLA ÇIKTI", t - 0.3, y=270, size=66, col=RED, sub="SÜVEYŞ → HİNDİSTAN → KAŞGAR")
    if t > 6.7:
        k = ease((t - 6.7) / 0.5)
        dark = Image.new("RGBA", (W, H), (20, 13, 8, int(170 * k))); base.alpha_composite(dark)
        dr = ImageDraw.Draw(base, "RGBA")
        spaced_text(dr, (W / 2, 290), "YARDIMDA NE VARDI?", font(FB, 64), CREAM + (int(255 * k),), sp=4)
        for i, c in enumerate(CARDS):
            paste_pop(base, c, W / 2, 500 + i * 225, t - (7.1, 8.6, 9.9, 12.6)[i], rot=(-3, 2, -2, 3)[i])
    return base.convert("RGB")

def scene5(t, dur):
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    a = int(255 * clamp(t / 0.4))
    spaced_text(dr, (W / 2, 240), "KAŞGAR'DA", font(FB, 64), INK + (a,), sp=8)
    spaced_text(dr, (W / 2, 325), "OSMANLI BAYRAĞI", font(FB, 72), RED + (a,), sp=4)
    # pole + flag
    dr.rectangle([196, 400, 212, 900], fill=(70, 48, 30, 255)); dr.ellipse([190, 386, 218, 414], fill=(170, 130, 60, 255))
    rise = ease_out(t / 1.0)
    wf = wave_flag(OTT, t, amp=18)
    fy = 420 + (1 - rise) * 300
    base.alpha_composite(shadow(wf), (212 - 30 + 10, int(fy - 40 - 30 + 14)))
    base.alpha_composite(wf, (212, int(fy - 40)))
    dr = ImageDraw.Draw(base, "RGBA")
    items = [("“EMİR” unvanı verildi", 0.8), ("Hutbe padişah adına okundu", 3.0), ("Paralara padişahın adı basıldı", 6.4)]
    for i, (txt, t0) in enumerate(items):
        tt = t - t0
        if tt < 0: continue
        p = ease_out(tt / 0.35); y = 930 + i * 135; x = 120 + (1 - p) * -60; al = int(255 * p)
        dr.rounded_rectangle([x, y - 34, x + 68, y + 34], 8, outline=RED + (al,), width=6)
        if tt > 0.2:
            q = clamp((tt - 0.2) / 0.25)
            pts = [(x + 14, y), (x + 30, y + 18), (x + 60, y - 26)]
            if q < 0.5: dr.line([pts[0], (pts[0][0] + (pts[1][0] - pts[0][0]) * q * 2, pts[0][1] + (pts[1][1] - pts[0][1]) * q * 2)], fill=RED + (255,), width=10)
            else:
                dr.line([pts[0], pts[1]], fill=RED + (255,), width=10)
                r_ = (q - 0.5) * 2
                dr.line([pts[1], (pts[1][0] + (pts[2][0] - pts[1][0]) * r_, pts[1][1] + (pts[2][1] - pts[1][1]) * r_)], fill=RED + (255,), width=10)
        dr.text((x + 100, y), txt, font=font(FB, 46), fill=INK + (al,), anchor="lm")
    # coin
    if t > 6.7:
        p = back((t - 6.7) / 0.4)
        R = 120 * p; cx, cy = 870, 640
        if R > 2:
            dr.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(198, 160, 80, 255), outline=(120, 90, 40, 255), width=6)
            dr.ellipse([cx - R * 0.8, cy - R * 0.8, cx + R * 0.8, cy + R * 0.8], outline=(140, 105, 50, 255), width=3)
            if p > 0.9:
                dr.text((cx, cy - 22), "SULTAN", font=font(FB, 30), fill=(110, 80, 35, 255), anchor="mm")
                dr.text((cx, cy + 18), "ABDÜLAZİZ", font=font(FB, 30), fill=(110, 80, 35, 255), anchor="mm")
    return base.convert("RGB")

def scene6(t, dur):
    cam = camera(P(84.5, 0)[0], P(0, 40.2)[1], 1700 - 90 * t / dur)
    base = render_map(cam).convert("RGBA")
    # desaturate gradually
    k = ease((t - 0.5) / 3.5)
    if k > 0:
        g = base.convert("L").convert("RGBA")
        base = Image.blend(base, g, 0.45 * k)
    draw_region(base, cam, BLUE, 0.28)
    wipe = 97 - 25 * ease((t - 4.0) / 2.8)
    if t > 4.0:
        draw_region(base, cam, (170, 20, 20), 0.45, lon_cut=wipe, from_east=True)
    dr = ImageDraw.Draw(base, "RGBA")
    kx, ky = to_screen(cam, *CITY["Kaşgar"])
    fallen = t > 6.6
    city_dot(dr, kx, ky, "Kaşgar", 1.0, color=(170, 20, 20) if fallen else BLUE, labelside="r", size=54)
    for nm, side in [("Hoten", "d"), ("Urumçi", "u"), ("Turfan", "d"), ("Kuça", "u")]:
        x, y = to_screen(cam, *CITY[nm]); lonc = CITY[nm][0]
        city_dot(dr, x, y, nm, 1.0, color=(170, 20, 20) if (t > 4.0 and lonc > wipe) else BLUE, labelside=side, size=38)
    title_band(base, "16 ARALIK 1877", t - 0.8, y=290, size=78, col=INK, sub="ÇİN ORDULARI KAŞGAR'DA")
    return base.convert("RGB")

def scene7(t, dur):
    base = Image.new("RGBA", (W, H), (13, 10, 7, 255)); dr = ImageDraw.Draw(base, "RGBA")
    def a(t0, d=0.6): return int(255 * clamp((t - t0) / d))
    spaced_text(dr, (W / 2, 640), "Bugün bu toprakların adı:", font(FI, 50), CREAM + (a(0.2),))
    spaced_text(dr, (W / 2, 770), "SİNCAN", font(FB, 128), (150, 150, 145, a(1.15, 0.4)), sp=14)
    spaced_text(dr, (W / 2, 1000), "Osmanlı o gün sahip çıktı...", font(FI, 50), CREAM + (a(2.9),))
    if t > 5.9:
        p = back((t - 5.9) / 0.45); s = int(138 * (0.6 + 0.4 * p))
        spaced_text(dr, (W / 2, 1170), "YA BUGÜN?", font(FB, max(10, s)), (205, 50, 40, a(5.9, 0.25)), sp=8)
    return base.convert("RGB")

SCENES = [("s1", scene1, 6.0), ("s2", scene2, 9.6), ("s3", scene3, 8.1), ("s4", scene4, 15.3),
          ("s5", scene5, 8.8), ("s6", scene6, 8.8), ("s7", scene7, 8.7)]
XF = 0.45
STARTS = []
_acc = 0.0
for _n, _f, _d in SCENES: STARTS.append(_acc); _acc += _d
TOTAL = _acc
# impacts (scene local seconds) for camera shake
IMPACTS = {"s1": [1.9], "s2": [2.9], "s4": [0.3, 7.1, 8.6, 9.9, 12.6], "s3": [6.8], "s6": [0.8], "s7": [5.9]}
DUST = [(random.Random(i).uniform(0, W), random.Random(i + 500).uniform(0, H), random.Random(i + 900).uniform(-12, 12),
         random.Random(i + 1300).uniform(-30, -8), random.Random(i + 1700).uniform(2, 5.5), random.Random(i + 2100).uniform(0, 6.28)) for i in range(60)]

def shake(img, name, t):
    amp = 0.0
    for t0 in IMPACTS.get(name, []):
        dt = t - t0 - 0.06
        if 0 <= dt < 0.45: amp += 14 * math.exp(-dt * 9)
    if amp < 0.5: return img
    dx = amp * math.sin(t * 91); dy = amp * math.cos(t * 77)
    return img.transform((W, H), Image.AFFINE, (1, 0, -dx, 0, 1, -dy), Image.BILINEAR, fillcolor=(20, 14, 9))

def dust(img, T):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for x0, y0, vx, vy, r, ph in DUST:
        x = (x0 + vx * T) % W; y = (y0 + vy * T) % H
        a = int(55 + 45 * math.sin(T * 1.7 + ph))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 240, 205, a))
    im = img.convert("RGBA"); im.alpha_composite(lay); return im.convert("RGB")

def scene_frame(k, T):
    name, fn, dur = SCENES[k]
    t = T - STARTS[k]
    im = fn(t, dur + XF)
    im = shake(im, name, t)
    return np.asarray(im, np.float32), name

def global_frame(T):
    k = max(i for i, s0 in enumerate(STARTS) if s0 <= T + 1e-9)
    a, nm = scene_frame(k, T)
    if k > 0 and T - STARTS[k] < XF:   # crossfade from previous scene's tail
        b, _ = scene_frame(k - 1, T)
        w = ease((T - STARTS[k]) / XF)
        a = a * w + b * (1 - w)
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    im = dust(im, T)
    vig = SCENES[k][0] != "s7"
    out = finish(im, vig).astype(np.float32)
    if T < 0.25: out = out * (T / 0.25)
    if T > TOTAL - 0.6: out = out * max(0, (TOTAL - T) / 0.6)
    return np.clip(out, 0, 255).astype(np.uint8)

def render(k):
    name = SCENES[k][0]
    t0 = STARTS[k]; t1 = STARTS[k + 1] if k + 1 < len(SCENES) else TOTAL
    wp = None
    if os.environ.get("WARP"):
        import json
        wj = json.load(open(os.path.join(OUT, "warp.json"))); wp = (wj["o"], wj["n"])
        t0, t1 = float(np.interp(t0, wp[0], wp[1])), float(np.interp(t1, wp[0], wp[1]))
    n0, n1 = int(round(t0 * FPS)), int(round(t1 * FPS))
    tmp = os.path.join(OUT, f"{name}.tmp.mp4"); fin = os.path.join(OUT, f"{name}.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), tmp],
                         stdin=subprocess.PIPE)
    for i in range(n0, n1):
        T = i / FPS
        if wp: T = float(np.interp(T, wp[1], wp[0]))
        p.stdin.write(global_frame(T).tobytes())
    p.stdin.close(); rc = p.wait()
    if rc == 0: os.replace(tmp, fin)
    print(name, "done", rc, flush=True)

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "frames":
        for ts in sys.argv[2:]:
            Image.fromarray(global_frame(float(ts))).save(os.path.join(OUT, f"g_{ts}.png"))
    else:
        for k, sc in enumerate(SCENES):
            if sc[0] in sys.argv[2:]: render(k)
