"""Reels: Başkurdistan bayrağı (7 yapraklı kuray çiçeği), kuray çalgısı, ağaç kovuğu arıcılığı, 'Başkurt' adının anlamı.
Kaynaklar: Bashinform (2011-02-25) + Wikipedia 'Flag of Bashkortostan' (25 Şubat 1992, renk anlamları);
FOTW ru-02 (R. Zinurov 1992: 7 yaprak = 7 boy, çiçek = dostluk); Wikipedia 'Quray' (bitki sapından millî çalgı);
Wikipedia 'Bashkirs' + kitaplong.ru (ağaç kovuğu arıcılığı, Burzyan); Wikipedia 'Bashkirs' + znanierussia.ru (baş+kurt);
TDV İslâm Ansiklopedisi + Küre 'Başkırt' (Togan: Beş Ogur)."""
import os, sys, math, json
import numpy as np
from PIL import Image, ImageDraw
from make import (W, H, OUT, SCREEN_PAPER, stamp_card, paste_pop, spaced_text, font, FB, FI, INK, RED, CREAM,
                  ease, ease_out, back, clamp, title_band, shadow)
import bayrak as B

FLAG = Image.open(os.path.join(OUT, "flags_ru_png", "ba.png")).convert("RGBA")
BLUE_C, GREEN_C, GOLD = (0, 133, 199), (0, 150, 70), (226, 170, 60)
BG = (240, 228, 196, 245)
_fc = {}
def flag(w):
    if w not in _fc:
        h = int(FLAG.height * w / FLAG.width); im = FLAG.resize((w, h), Image.LANCZOS)
        bd = Image.new("RGBA", (w + 4, h + 4), (40, 30, 20, 255)); bd.alpha_composite(im, (2, 2)); _fc[w] = bd
    return _fc[w]

def a_(t, t0, d=0.35): return int(255 * clamp((t - t0) / d))

def flower(dr, cx, cy, R, t, t0=0.0, step=0.12, col=GOLD, number=False):
    """Stilize 7 yapraklı kuray çiçeği; yapraklar sırayla açılır."""
    for i in range(7):
        k = back(clamp((t - t0 - i * step) / 0.3))
        if k <= 0: continue
        ang = -math.pi / 2 + i * 2 * math.pi / 7
        L = R * k; px, py = cx + math.cos(ang) * L * 0.62, cy + math.sin(ang) * L * 0.62
        w = R * 0.26 * k
        pts = []
        for s in np.linspace(0, 2 * math.pi, 28):
            ex, ey = math.cos(s) * L * 0.42, math.sin(s) * w
            pts.append((px + ex * math.cos(ang) - ey * math.sin(ang), py + ex * math.sin(ang) + ey * math.cos(ang)))
        dr.polygon(pts, fill=col + (255,), outline=(120, 80, 20, 255))
        if number:
            nx, ny = cx + math.cos(ang) * R * 1.22, cy + math.sin(ang) * R * 1.22
            dr.text((nx, ny), str(i + 1), font=font(FB, int(R * 0.22)), fill=RED + (int(255 * clamp(k)),), anchor="mm")
    r = R * 0.16 * back(clamp((t - t0) / 0.3))
    if r > 0: dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(200, 120, 30, 255))

# ---- sahneler ----
def s1(t, dur):  # kanca: 7 yaprak = 7 boy
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    p = back(clamp(t / 0.35)); s = 0.8 + 0.2 * p
    spaced_text(dr, (W / 2, 330), "7 YAPRAK", font(FB, int(120 * s)), INK + (a_(t, 0, 0.12),), sp=8)
    spaced_text(dr, (W / 2, 470), "7 BOY", font(FB, int(140 * s)), RED + (a_(t, 0, 0.12),), sp=10)
    flower(dr, W / 2, 1000, 300, t, -0.25, 0.12, number=True)
    return base.convert("RGB")

def s2(t, dur):  # bayrak 1992
    base = SCREEN_PAPER.copy().convert("RGBA")
    B.put_flag(base, flag(860), W / 2, 820 + (1 - ease_out(clamp(t / 0.5))) * 50, t, amp=14)
    title_band(base, "BAŞKURDİSTAN", t - 0.05, y=330, size=96, col=INK, sub="25 ŞUBAT 1992")
    return base.convert("RGB")

COLS = [("MAVİ", "DÜŞÜNCENİN AÇIKLIĞI", BLUE_C), ("BEYAZ", "BARIŞ", (250, 248, 240)), ("YEŞİL", "ÖZGÜRLÜK · SONSUZ YAŞAM", GREEN_C)]
def make_s3(times):
    def s3(t, dur):  # renkler
        base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
        spaced_text(dr, (W / 2, 250), "RENKLER", font(FB, 84), RED + (a_(t, 0),), sp=10)
        for i, ((nm, mean, c), tt) in enumerate(zip(COLS, times)):
            if t < tt: continue
            k = ease_out(clamp((t - tt) / 0.35)); y = 470 + i * 300; x0 = 110 + (1 - k) * -300
            dr.rounded_rectangle([x0, y - 110, x0 + 220, y + 110], 18, fill=c + (int(255 * k),), outline=INK + (int(255 * k),), width=5)
            a = int(255 * k)
            dr.text((x0 + 270, y - 40), nm, font=font(FB, 78), fill=INK + (a,), anchor="lm")
            f = font(FB, 44)
            while f.getlength(mean) > 600: f = font(FB, f.size - 2)
            dr.text((x0 + 272, y + 45), mean, font=f, fill=RED + (a,), anchor="lm")
        return base.convert("RGB")
    return s3

def make_s4(t_friend):
    def s4(t, dur):  # altın çiçek: dostluk
        base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
        spaced_text(dr, (W / 2, 280), "KURAY ÇİÇEĞİ", font(FB, 92), INK + (a_(t, 0),), sp=8)
        flower(dr, W / 2, 800, 290, 1.5 + t, 0.0, 0.0)
        paste_pop(base, stamp_card(["DOSTLUK"], 640, 190, RED, seed=91, sizes=[110], bg=BG), W / 2, 1260, t - t_friend, rot=-4)
        return base.convert("RGB")
    return s4

def kuray_pipe(dr, t, cx=W / 2, y0=420, y1=1180):
    k = ease_out(clamp(t / 0.6)); yb = y0 + (y1 - y0) * k
    dr.rounded_rectangle([cx - 34, y0, cx + 34, yb], 30, fill=(196, 160, 96, 255), outline=(110, 80, 40, 255), width=5)
    for j in range(1, 6):  # boğum çizgileri
        yy = y0 + (y1 - y0) * j / 6
        if yy < yb: dr.line([cx - 34, yy, cx + 34, yy], fill=(140, 105, 55, 255), width=4)
    for j, fy in enumerate([0.55, 0.64, 0.73, 0.82]):  # 4 ön delik
        yy = y0 + (y1 - y0) * fy
        if yy < yb: dr.ellipse([cx - 13, yy - 13, cx + 13, yy + 13], fill=(60, 40, 20, 255))
    # ses dalgaları
    if t > 0.7:
        for i in range(3):
            ph = ((t * 0.9 + i / 3) % 1.0); r = 40 + ph * 160; a = int(200 * (1 - ph))
            dr.arc([cx - r, y0 - r, cx + r, y0 + r], 200, 340, fill=RED + (a,), width=6)

def make_s5(t_stamp):
    def s5(t, dur):  # kuray çalgısı
        base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
        spaced_text(dr, (W / 2, 230), "BİTKİNİN SAPINDAN", font(FB, 64), INK + (a_(t, 0),), sp=4)
        kuray_pipe(dr, t, cx=W / 2 - 200, y0=420, y1=1250)
        flower(dr, W / 2 + 230, 640, 140, 1.5 + t, 0, 0)
        paste_pop(base, stamp_card(["MİLLÎ", "ÇALGI"], 420, 260, RED, seed=92, sizes=[86, 86], bg=BG), W / 2 + 230, 1040, t - t_stamp, rot=4)
        return base.convert("RGB")
    return s5

def s6(t, dur):  # ağaç kovuğu arıcılığı
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    spaced_text(dr, (W / 2, 230), "AĞAÇ KOVUĞUNDAN BAL", font(FB, 58), INK + (a_(t, 0),), sp=4)
    tx = W / 2 - 60
    dr.rectangle([tx - 120, 360, tx + 120, 1180], fill=(110, 78, 48, 255), outline=(60, 40, 22, 255), width=6)
    for j in range(7):  # kabuk dokusu
        yy = 400 + j * 115; dr.arc([tx - 110, yy, tx - 20, yy + 90], 90, 270, fill=(70, 48, 28, 255), width=5)
        dr.arc([tx + 20, yy + 50, tx + 110, yy + 140], 270, 90, fill=(70, 48, 28, 255), width=5)
    dr.rounded_rectangle([tx - 55, 640, tx + 55, 880], 30, fill=(40, 26, 14, 255))
    dr.ellipse([tx + 70, 980, tx + 100, 1010], fill=(30, 20, 10, 255))
    rng = np.random.default_rng(5)
    for i in range(14):  # arılar
        ph = rng.uniform(0, 6.28); rr = rng.uniform(60, 240); sp_ = rng.uniform(0.6, 1.3)
        bx = tx + math.cos(t * sp_ + ph) * rr; by = 760 + math.sin(t * sp_ * 1.3 + ph) * rr * 0.7
        dr.ellipse([bx - 11, by - 8, bx + 11, by + 8], fill=(230, 170, 30, 255), outline=(30, 20, 10, 255), width=3)
        dr.ellipse([bx - 6, by - 16, bx + 6, by - 6], fill=(255, 255, 255, 170))
    paste_pop(base, stamp_card(["YÜZYILLARDIR"], 640, 160, RED, seed=93, sizes=[84], bg=BG), W / 2, 1290, t - 1.0, rot=-3)
    return base.convert("RGB")

def make_s7(t_a, t_b):
    def s7(t, dur):  # Başkurt ne demek?
        base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
        p = back(clamp(t / 0.4)); s = 0.8 + 0.2 * p
        spaced_text(dr, (W / 2, 300), "BAŞKURT", font(FB, int(130 * s)), INK + (a_(t, 0, 0.15),), sp=10)
        spaced_text(dr, (W / 2, 440), "NE DEMEK?", font(FB, int(100 * s)), RED + (a_(t, 0, 0.15),), sp=8)
        paste_pop(base, stamp_card(["BAŞ + KURT", "= LİDER KURT"], 820, 280, INK, seed=94, sizes=[92, 70], bg=BG), W / 2, 760, t - t_a, rot=-3)
        paste_pop(base, stamp_card(["BEŞ OGUR", "ZEKİ VELİDİ TOGAN"], 820, 280, RED, seed=95, sizes=[92, 50], bg=BG), W / 2, 1130, t - t_b, rot=3)
        return base.convert("RGB")
    return s7

def s8(t, dur):  # kapanış
    base = Image.new("RGBA", (W, H), (13, 10, 7, 255))
    B.put_flag(base, flag(860), W / 2, 880, t, amp=12, op=0.14)
    dr = ImageDraw.Draw(base, "RGBA")
    p = back(clamp(t / 0.45)); s = 0.6 + 0.4 * p
    spaced_text(dr, (W / 2, 820), "SENCE", font(FB, int(110 * s)), CREAM + (a_(t, 0, 0.2),), sp=10)
    spaced_text(dr, (W / 2, 980), "HANGİSİ?", font(FB, int(140 * s)), (255, 196, 60, a_(t, 0, 0.2)), sp=10)
    spaced_text(dr, (W / 2, 1180), "Yorumlara yaz", font(FI, 54), CREAM + (a_(t, 0.8, 0.4),))
    return base.convert("RGB")

# ---- zamanlama (kelime zamanlarından doldurulur) ----
TM = json.load(open(os.path.join(OUT, "bask_times.json"))) if os.path.exists(os.path.join(OUT, "bask_times.json")) else None
if TM:
    st = TM["starts"]; TOTAL_ = TM["total"]; L = TM["local"]
    durs = [st[i + 1] - st[i] for i in range(len(st) - 1)] + [TOTAL_ - st[-1]]
else:
    durs = [3.5, 3.0, 6.0, 4.0, 5.0, 3.5, 7.0, 2.5]; L = {"c": [0.6, 1.8, 3.2], "friend": 2.0, "inst": 1.5, "a": 1.6, "b": 3.8}
SCENES = [("k1", s1, durs[0]), ("k2", s2, durs[1]), ("k3", make_s3(L["c"]), durs[2]), ("k4", make_s4(L["friend"]), durs[3]),
          ("k5", make_s5(L["inst"]), durs[4]), ("k6", s6, durs[5]), ("k7", make_s7(L["a"], L["b"]), durs[6]), ("k8", s8, durs[7])]
XF = 0.3
STARTS = []; _a = 0.0
for _n, _f, _d in SCENES: STARTS.append(_a); _a += _d
TOTAL = _a
IMPACTS = {"k1": [0.05], "k2": [0.05], "k3": L["c"], "k4": [L["friend"]], "k5": [L["inst"]], "k6": [1.0],
           "k7": [0.05, L["a"], L["b"]], "k8": [0.05]}
B.SCENES, B.XF, B.STARTS, B.TOTAL, B.IMPACTS = SCENES, XF, STARTS, TOTAL, IMPACTS

if __name__ == "__main__":
    if sys.argv[1] == "frames":
        for ts in sys.argv[2:]: Image.fromarray(B.global_frame(float(ts))).save(os.path.join(OUT, f"bf_{ts}.png"))
    else:
        for k, sc in enumerate(SCENES):
            if sc[0] in sys.argv[2:]: B.render(k)
