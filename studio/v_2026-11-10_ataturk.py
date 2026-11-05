"""10 Kasım özel Reels: Atatürk — güçlü, zeki, ömrünü millete veren lider.
Çanakkale 25 Nisan 1915 (emir beklemeden, 57. Alay: 'ölmeyi emrediyorum'), Conkbayırı cep saati (Ağustos 1915),
19 Mayıs 1919 Samsun, Sakarya (23 Ağustos-13 Eylül 1921, 22 gün), 'Ordular! İlk hedefiniz Akdeniz'dir' (1 Eylül 1922),
harf devrimi / Başöğretmen (1928), kadınlara seçme-seçilme hakkı (5 Aralık 1934), 10 Kasım 1938 09.05, 57 yaşında.
Kaynaklar: Wikipedia 'Mustafa Kemal Atatürk', 'Battle of Sakarya'; MEB Atatürk biyografisi; Küre Ansiklopedisi."""
import os, sys, math, json
import numpy as np
from PIL import Image, ImageDraw
import make as M
from make import (W, H, FPS, OUT, SCREEN_PAPER, render_map, camera, P, to_screen, city_dot, pulse, stamp_card,
                  paste_pop, make_flag, spaced_text, font, FB, FI, INK, RED, CREAM, ease, ease_out, back, clamp, title_band, shadow)
import bayrak as B

TR_FLAG = make_flag(860, 573, (200, 16, 46))
T = json.load(open(os.path.join(OUT, "ata_times.json"))) if os.path.exists(os.path.join(OUT, "ata_times.json")) else {}
def e(k, d): return T.get(k, d)

ARIBURNU = (26.28, 40.24); SAMSUN = (36.33, 41.29); SAKARYA = (32.15, 39.58); KOCATEPE = (30.55, 38.75); IZMIR = (27.14, 38.42)

def _nolabel_map():
    im = M.MAP.copy(); x, y = P(33.5, 39.4)
    box = (int(x - 290), int(y - 30), int(x + 290), int(y + 30))
    im.paste(im.crop((box[0], box[1] + 70, box[2], box[3] + 70)), box[:2]); return im
MAP2 = _nolabel_map()

def arrow(dr, x0, y0, x1, y1, k, col=RED, w=14):
    if k <= 0: return
    xe, ye = x0 + (x1 - x0) * k, y0 + (y1 - y0) * k
    dr.line([(x0, y0), (xe, ye)], fill=col + (255,), width=w)
    a = math.atan2(ye - y0, xe - x0); L = 44
    dr.polygon([(xe + math.cos(a) * 10, ye + math.sin(a) * 10),
                (xe - math.cos(a - 0.5) * L, ye - math.sin(a - 0.5) * L),
                (xe - math.cos(a + 0.5) * L, ye - math.sin(a + 0.5) * L)], fill=col + (255,))

def c1(t, dur):  # Çanakkale 1915: emir beklemedi
    p = ease(t / 3.0)
    ax, ay = P(*ARIBURNU)
    cam = camera(ax + 60, ay, 900 - 420 * p)
    base = render_map(cam).convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    x, y = to_screen(cam, *ARIBURNU)
    # düşman çıkarması (denizden oklar)
    for i, off in enumerate([-90, 0, 90]):
        k = ease(clamp((t - 0.6 - i * 0.15) / 1.0))
        arrow(dr, x - 330, y + off * 1.4, x - 40, y + off * 0.5, k, col=(60, 60, 70), w=10)
    if t > e("harekete", 2.6):
        k = ease(clamp((t - e("harekete", 2.6)) / 0.8))
        arrow(dr, x + 300, y + 60, x + 40, y + 10, k, col=RED, w=16)
        pulse(dr, x, y, t, color=RED)
    title_band(base, "25 NİSAN 1915", t - 0.0, y=300, size=86, col=RED, sub="ÇANAKKALE")
    a = int(255 * clamp(t / 0.15))
    dr = ImageDraw.Draw(base, "RGBA")
    spaced_text(dr, (W / 2, 560), "EMİR BEKLEMEDİ", font(FB, 74), INK + (a,), sp=6, stroke=8, sfill=(245, 235, 211, a))
    paste_pop(base, stamp_card(["DÜŞMANI", "ÖNCEDEN GÖRDÜ"], 700, 220, RED, seed=71, sizes=[58, 70], bg=(240, 228, 196, 245)),
              W / 2, 1290, t - e("gordu", 5.2), rot=-3)
    return base.convert("RGB")

def c2(t, dur):  # 'ölmeyi emrediyorum'
    base = B.PAPER_DARK.copy().convert("RGBA")
    B.put_flag(base, TR_FLAG, W / 2, 900, t, amp=10, op=0.12)
    dr = ImageDraw.Draw(base, "RGBA")
    a1 = int(255 * clamp((t - e("q1", 1.2)) / 0.4))
    spaced_text(dr, (W / 2, 640), "BEN SİZE", font(FB, 70), CREAM + (a1,), sp=6)
    spaced_text(dr, (W / 2, 740), "TAARRUZU", font(FB, 70), CREAM + (a1,), sp=6)
    spaced_text(dr, (W / 2, 840), "EMRETMİYORUM,", font(FB, 70), CREAM + (a1,), sp=6)
    tt = t - e("q2", 3.6)
    if tt > 0:
        p = back(tt / 0.5); s = int(86 * (0.6 + 0.4 * p)); a2 = int(255 * clamp(tt / 0.25))
        spaced_text(dr, (W / 2, 1000), "ÖLMEYİ", font(FB, s), (230, 70, 60, a2), sp=8)
        spaced_text(dr, (W / 2, 1120), "EMREDİYORUM", font(FB, s), (230, 70, 60, a2), sp=8)
    a3 = int(255 * clamp((t - 0.2) / 0.4))
    spaced_text(dr, (W / 2, 470), "— 57. Alay'a, 25 Nisan 1915 —", font(FI, 40), CREAM + (int(a3 * 0.8),))
    return base.convert("RGB")

def watch(base, cx, cy, R, t, crack):
    im = Image.new("RGBA", (int(R * 2.6), int(R * 2.9)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    ox, oy = im.width / 2, im.height / 2 + R * 0.18
    d.ellipse([ox - 26, oy - R - 70, ox + 26, oy - R - 18], outline=(150, 112, 50, 255), width=10)       # halka
    d.rectangle([ox - 22, oy - R - 26, ox + 22, oy - R + 6], fill=(170, 130, 60, 255))                # kurma
    d.ellipse([ox - R, oy - R, ox + R, oy + R], fill=(176, 136, 66, 255))
    d.ellipse([ox - R + 22, oy - R + 22, ox + R - 22, oy + R - 22], fill=(240, 230, 206, 255))
    for k in range(12):
        a = math.radians(k * 30 - 90); r0, r1 = R - 40, R - 70
        d.line([(ox + r0 * math.cos(a), oy + r0 * math.sin(a)), (ox + r1 * math.cos(a), oy + r1 * math.sin(a))], fill=INK + (255,), width=6)
    for ang, ln, wd in [(-60, R * 0.45, 10), (100, R * 0.65, 6)]:
        a = math.radians(ang - 90); d.line([(ox, oy), (ox + ln * math.cos(a), oy + ln * math.sin(a))], fill=INK + (255,), width=wd)
    d.ellipse([ox - 12, oy - 12, ox + 12, oy + 12], fill=INK + (255,))
    if crack > 0:   # şarapnel izi + çatlak cam
        hx, hy = ox + R * 0.32, oy + R * 0.28
        d.ellipse([hx - 30, hy - 26, hx + 30, hy + 26], fill=(70, 50, 30, int(255 * crack)))
        rng = np.random.default_rng(5)
        for k in range(9):
            a = rng.uniform(0, 2 * math.pi); L = rng.uniform(0.5, 1.0) * R * 0.9 * crack
            pts = [(hx, hy)]
            for s in range(1, 5):
                pts.append((hx + math.cos(a + rng.uniform(-0.2, 0.2)) * L * s / 4, hy + math.sin(a + rng.uniform(-0.2, 0.2)) * L * s / 4))
            d.line(pts, fill=(60, 50, 45, int(230 * crack)), width=4)
    base.alpha_composite(shadow(im), (int(cx - im.width / 2 - 20), int(cy - im.height / 2 - 16)))
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

def c3(t, dur):  # cep saati
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    title_band(base, "AĞUSTOS 1915", t - 0.0, y=280, size=84, col=INK, sub="CONKBAYIRI")
    tc = e("carpti", 1.0)
    crack = ease_out(clamp((t - tc) / 0.25))
    watch(base, W / 2, 790, 250, t, crack)
    paste_pop(base, stamp_card(["SAAT", "ONU KURTARDI"], 660, 220, RED, seed=72, sizes=[64, 70], bg=(240, 228, 196, 245)),
              W / 2, 1250, t - e("kurtardi", 2.4), rot=-3)
    return base.convert("RGB")

def c4(t, dur):  # 1919 Samsun
    p = ease(t / 3.0)
    sx, sy = P(*SAMSUN); cx0, cy0 = P(33.0, 39.2)
    cam = camera(cx0 + (sx - cx0) * p * 0.6, cy0 + (sy - cy0) * p * 0.6, 1400 - 500 * p)
    base = render_map(cam).convert("RGBA")
    dim = Image.new("RGBA", (W, H), (60, 20, 10, int(70 * clamp(t / 0.5)))); base.alpha_composite(dim)
    dr = ImageDraw.Draw(base, "RGBA")
    x, y = to_screen(cam, *SAMSUN)
    if t > e("samsun", 2.2): pulse(dr, x, y, t, color=RED)
    city_dot(dr, x, y, "Samsun", t - e("samsun", 2.2), color=RED, labelside="u", size=58)
    title_band(base, "19 MAYIS 1919", t - 0.0, y=300, size=90, col=RED, sub="ÜLKE İŞGAL ALTINDA")
    return base.convert("RGB")

def c5(t, dur):  # Sakarya 22 gün + Akdeniz emri
    p = ease(t / 4.0)
    mx, my = P(30.0, 39.0)
    cam = camera(mx, my, 1300 - 200 * p)
    base = render_map(cam, MAP2).convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    x, y = to_screen(cam, *SAKARYA)
    city_dot(dr, x, y, "Sakarya", t - 0.3, color=RED, labelside="r", size=48)
    paste_pop(base, stamp_card(["22 GÜN", "22 GECE"], 520, 230, RED, seed=73, sizes=[86, 86], bg=(240, 228, 196, 245)),
              W / 2, 1320, t - 0.6, rot=-4)
    te = e("ordular", 4.4)
    if t > te - 0.2:
        x0, y0 = to_screen(cam, *KOCATEPE); x1, y1 = to_screen(cam, *IZMIR)
        dr = ImageDraw.Draw(base, "RGBA")
        arrow(dr, x0, y0, x1, y1, ease(clamp((t - te) / 1.2)), col=RED, w=20)
        city_dot(dr, x1, y1, "İzmir", t - te - 1.0, color=RED, labelside="d", size=48)
        dim = Image.new("RGBA", (W, 520), (20, 13, 8, int(200 * clamp((t - te) / 0.3)))); base.alpha_composite(dim, (0, 120))
        dr = ImageDraw.Draw(base, "RGBA"); a = int(255 * clamp((t - te) / 0.3))
        spaced_text(dr, (W / 2, 250), "ORDULAR!", font(FB, 96), (230, 70, 60, a), sp=8)
        spaced_text(dr, (W / 2, 380), "İLK HEDEFİNİZ", font(FB, 70), CREAM + (a,), sp=6)
        spaced_text(dr, (W / 2, 480), "AKDENİZ'DİR!", font(FB, 86), CREAM + (a,), sp=6)
        spaced_text(dr, (W / 2, 580), "1 Eylül 1922", font(FI, 38), CREAM + (int(a * 0.8),))
    return base.convert("RGB")

ABC = "A B C Ç D E F G"
def c6(t, dur):  # Başöğretmen + kadın hakları
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    tk = e("kadin", 4.6)
    if t < tk:
        bx0, by0, bx1, by1 = 110, 480, 970, 1000
        dr.rectangle([bx0 - 24, by0 - 24, bx1 + 24, by1 + 24], fill=(110, 74, 40, 255))
        dr.rectangle([bx0, by0, bx1, by1], fill=(34, 62, 48, 255))
        n = int(clamp((t - 0.6) / 2.2) * len(ABC))
        spaced_text(dr, ((bx0 + bx1) / 2, 650), ABC[:n], font(FB, 92), (236, 236, 226, 235), sp=4)
        if t > 2.0:
            k = int(255 * clamp((t - 2.0) / 0.5))
            spaced_text(dr, ((bx0 + bx1) / 2, 840), "Türk alfabesi", font(FI, 64), (236, 236, 226, k))
        title_band(base, "1928", t - 0.0, y=280, size=96, col=INK, sub="HARF DEVRİMİ")
        paste_pop(base, stamp_card(["BAŞÖĞRETMEN"], 720, 170, RED, seed=74, sizes=[86], bg=(240, 228, 196, 245)),
                  W / 2, 1220, t - e("ogretti", 2.6), rot=-3)
    else:
        tt = t - tk
        k = ease_out(clamp(tt / 0.5))
        bx, by = W / 2, 820 + (1 - k) * 60
        dr.rectangle([bx - 230, by - 120, bx + 230, by + 240], fill=(150, 112, 70, 255), outline=INK + (255,), width=6)
        dr.rectangle([bx - 110, by - 132, bx + 110, by - 108], fill=INK + (255,))
        if tt > 0.5:
            yy = by - 120 - 120 * (1 - ease(clamp((tt - 0.5) / 0.6)))
            dr.rectangle([bx - 70, yy - 150, bx + 70, yy], fill=(246, 240, 226, 255), outline=INK + (255,), width=4)
        spaced_text(dr, (bx, by + 70), "SANDIK", font(FB, 60), CREAM + (255,), sp=6)
        title_band(base, "5 ARALIK 1934", tt, y=280, size=84, col=RED, sub="KADINLARA SEÇME VE SEÇİLME HAKKI")
        paste_pop(base, stamp_card(["FRANSA'DAN", "10 YIL ÖNCE"], 640, 220, RED, seed=75, sizes=[64, 74], bg=(240, 228, 196, 245)),
                  W / 2, 1300, tt - 1.0, rot=-4)
    return base.convert("RGB")

def c7(t, dur):  # kapanış
    base = Image.new("RGBA", (W, H), (13, 10, 7, 255))
    B.put_flag(base, TR_FLAG, W / 2, 900, t, amp=12, op=0.18)
    dr = ImageDraw.Draw(base, "RGBA")
    tn = e("isim", 6.4)
    if t < tn:
        a = int(255 * clamp(t / 0.4))
        spaced_text(dr, (W / 2, 760), "10 KASIM 1938", font(FB, 92), CREAM + (a,), sp=8)
        spaced_text(dr, (W / 2, 880), "09.05", font(FB, 120), (230, 70, 60, a), sp=8)
        if t > e("yas", 2.6):
            spaced_text(dr, (W / 2, 1020), "57 yaşındaydı", font(FI, 56), CREAM + (int(255 * clamp((t - e("yas", 2.6)) / 0.4)),))
    else:
        tt = t - tn; p = back(tt / 0.5); s = int(84 * (0.6 + 0.4 * p)); a = int(255 * clamp(tt / 0.3))
        spaced_text(dr, (W / 2, 780), "MUSTAFA KEMAL", font(FB, s), CREAM + (a,), sp=8)
        spaced_text(dr, (W / 2, 890), "ATATÜRK", font(FB, int(s * 1.35)), (230, 70, 60, a), sp=12)
        if tt > e("unutmadik", 1.6):
            spaced_text(dr, (W / 2, 1040), "Seni unutmadık.", font(FI, 60), CREAM + (int(255 * clamp((tt - e("unutmadik", 1.6)) / 0.5)),))
    return base.convert("RGB")

DUR = T.get("durs", [7.0, 7.0, 6.5, 4.5, 8.5, 9.5, 11.0])
SCENES = [("c1", c1, DUR[0]), ("c2", c2, DUR[1]), ("c3", c3, DUR[2]), ("c4", c4, DUR[3]), ("c5", c5, DUR[4]), ("c6", c6, DUR[5]), ("c7", c7, DUR[6])]
XF = 0.4
STARTS = []; _a = 0.0
for _n, _f, _d in SCENES: STARTS.append(_a); _a += _d
TOTAL = _a
IMPACTS = {"c1": [0.05, e("gordu", 5.2)], "c2": [e("q2", 3.6)], "c3": [e("carpti", 1.0), e("kurtardi", 2.4)], "c4": [e("samsun", 2.2)],
           "c5": [0.6, e("ordular", 4.4)], "c6": [e("ogretti", 2.6), e("kadin", 4.6) + 1.0], "c7": [e("isim", 6.4)]}
B.SCENES, B.XF, B.STARTS, B.TOTAL, B.IMPACTS = SCENES, XF, STARTS, TOTAL, IMPACTS

if __name__ == "__main__":
    if sys.argv[1] == "frames":
        for ts in sys.argv[2:]: Image.fromarray(B.global_frame(float(ts))).save(os.path.join(OUT, f"cf_{ts}.png"))
    else:
        for k, sc in enumerate(SCENES):
            if sc[0] in sys.argv[2:]: B.render(k)
