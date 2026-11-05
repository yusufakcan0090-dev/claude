"""10 Kasım özel Reels: 'Anıtkabir'deki lahit boş' — sembolik lahit, alttaki mezar odası, yurdun dört yanından toprak,
1941 yarışması (6 ülke, 49 proje, Emin Onat & Orhan Arda), 10 Kasım 1953 nakil.
Kaynaklar: Küre Ansiklopedisi 'Anıtkabir'; Wikipedia 'Anıtkabir'; Hürriyet 'Anıtkabir'in bilinmeyenleri'; MEB."""
import os, sys, math, json
import numpy as np
from PIL import Image, ImageDraw
import make as M
from make import (W, H, FPS, OUT, SCREEN_PAPER, render_map, camera, P, to_screen, city_dot, pulse, stamp_card,
                  paste_pop, make_flag, spaced_text, font, FB, FI, INK, RED, CREAM, ease, ease_out, back, clamp, title_band, shadow)
import bayrak as B

TR_FLAG = make_flag(860, 573, (200, 16, 46))
TR_S = make_flag(260, 173, (200, 16, 46))
STONE = (214, 200, 172)
T = json.load(open(os.path.join(OUT, "anit_times.json"))) if os.path.exists(os.path.join(OUT, "anit_times.json")) else {}
def e(k, d): return T.get(k, d)

def anit(dr, cx, by, s, col, a=255):
    """Anıtkabir Şeref Holü (önden): basamaklar, sütun dizisi, saçak."""
    c = col + (a,)
    def R(x0, y0, x1, y1): dr.rectangle([cx + x0 * s, by + y0 * s, cx + x1 * s, by + y1 * s], fill=c)
    R(-420, -30, 420, 0); R(-380, -60, 380, -30); R(-330, -90, 330, -60)
    R(-300, -330, 300, -290); R(-270, -360, 270, -330)
    for i in range(12):
        x = -285 + i * 50.5; R(x, -290, x + 22, -90)
    R(-270, -290, 270, -270)

def a1(t, dur):  # hook
    base = B.PAPER_DARK.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    anit(dr, W / 2, 1180, 1.1, (90, 70, 50), 120)
    p = back(t / 0.45); s = int(120 * (0.7 + 0.3 * p)); a = int(255 * clamp(t / 0.25))
    spaced_text(dr, (W / 2, 560), "O LAHİT", font(FB, s), CREAM + (a,), sp=10)
    if t > e("bos", 2.4) - 0.1:
        paste_pop(base, stamp_card(["BOŞ"], 520, 210, (230, 70, 60), seed=61, sizes=[130], bg=(30, 20, 14, 230)), W / 2, 760, t - e("bos", 2.4) + 0.1, rot=-4)
    return base.convert("RGB")

def lahit(base, cx, cy, w, h, t0, t):
    if t < t0: return
    k = ease_out((t - t0) / 0.5)
    im = Image.new("RGBA", (w, h + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([0, 40, w, h + 40], fill=STONE + (255,))
    d.polygon([(20, 40), (w - 20, 40), (w - 60, 0), (60, 0)], fill=(232, 222, 198, 255))
    for i in range(6):  # mermer damarı
        y = 70 + i * (h - 40) / 6
        d.line([(10, y), (w * 0.4, y + 18), (w - 10, y - 8)], fill=(190, 176, 150, 120), width=3)
    d.rectangle([0, 40, w, h + 40], outline=INK + (255,), width=5)
    im.putalpha(Image.fromarray((np.asarray(im)[..., 3] * k).astype(np.uint8)))
    base.alpha_composite(shadow(im), (int(cx - w / 2 - 20), int(cy - h / 2 - 16 + (1 - k) * 40)))
    base.alpha_composite(im, (int(cx - w / 2), int(cy - h / 2 + (1 - k) * 40)))

def a2(t, dur):  # 40 ton, tek parça mermer, simge
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    a = int(255 * clamp(t / 0.3))
    spaced_text(dr, (W / 2, 280), "ŞEREF HOLÜ", font(FB, 72), INK + (a,), sp=6)
    lahit(base, W / 2, 720, 640, 300, 0.2, t)
    paste_pop(base, stamp_card(["40 TON"], 460, 170, RED, seed=62, sizes=[100], bg=(240, 228, 196, 240)), W / 2 + 250, 540, t - e("ton", 0.6), rot=6)
    paste_pop(base, stamp_card(["TEK PARÇA", "MERMER"], 560, 200, INK, seed=63, sizes=[56, 64], bg=(240, 228, 196, 240)), W / 2, 1010, t - e("mermer", 1.6), rot=-2)
    paste_pop(base, stamp_card(["SEMBOLİK"], 560, 160, RED, seed=64, sizes=[84], bg=(240, 228, 196, 245)), W / 2, 1230, t - e("simge", 3.0), rot=-5)
    return base.convert("RGB")

def a3(t, dur):  # kesit: asıl mezar altta
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    a = int(255 * clamp(t / 0.3))
    floor_y = 760
    dr.rectangle([0, floor_y, W, H], fill=(150, 126, 96, a))                           # toprak kesiti
    rng = np.random.default_rng(3)
    for _ in range(260):
        x, y = rng.integers(0, W), rng.integers(floor_y + 10, H)
        dr.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(120, 98, 72, int(a * 0.6)))
    dr.line([(0, floor_y), (W, floor_y)], fill=INK + (a,), width=8)
    dr.rectangle([W / 2 - 240, floor_y - 170, W / 2 + 240, floor_y], fill=STONE + (a,), outline=INK + (a,), width=5)
    spaced_text(dr, (W / 2, floor_y - 210), "LAHİT", font(FB, 46), INK + (a,), sp=6)
    # aşağı ok
    k = ease(clamp((t - 0.6) / 1.0))
    if k > 0:
        y0, y1 = floor_y + 30, floor_y + 30 + 340 * k
        dr.line([(W / 2, y0), (W / 2, y1)], fill=RED + (255,), width=14)
        dr.polygon([(W / 2 - 34, y1 - 6), (W / 2 + 34, y1 - 6), (W / 2, y1 + 40)], fill=RED + (255,))
    # mezar odası
    k2 = clamp((t - 1.4) / 0.5)
    if k2 > 0:
        ry = 1200
        dr.rectangle([W / 2 - 300, ry, W / 2 + 300, ry + 300], fill=(60, 44, 30, int(255 * k2)), outline=INK + (int(255 * k2),), width=6)
        dr.rectangle([W / 2 - 120, ry + 200, W / 2 + 120, ry + 260], fill=STONE + (int(255 * k2),))
    paste_pop(base, stamp_card(["ASIL MEZAR", "ALTTAKİ ODADA"], 700, 210, RED, seed=65, sizes=[78, 46], bg=(240, 228, 196, 245)), W / 2, 380, t - e("oda", 1.6), rot=-2)
    return base.convert("RGB")

TR_CITIES = [(29.0, 41.0), (27.1, 38.4), (30.7, 36.9), (35.3, 37.0), (39.7, 41.0), (41.3, 39.9), (43.4, 38.5), (40.2, 37.9),
             (37.4, 37.1), (34.0, 41.4), (36.3, 41.3), (26.6, 41.7), (32.5, 37.9), (38.3, 38.4), (42.0, 41.1), (30.5, 39.8)]
ANKARA = (32.86, 39.93)
def _tr_map():
    """Taban haritadaki 'OSMANLI DEVLETİ' yazısını sil, 'TÜRKİYE' yaz (1953)."""
    im = M.MAP.copy(); x, y = P(33.5, 39.4)
    box = (int(x - 290), int(y - 30), int(x + 290), int(y + 30))
    im.paste(im.crop((box[0], box[1] + 70, box[2], box[3] + 70)), box[:2])
    dr = ImageDraw.Draw(im); fnt = font(FI, 40); tx, ty = P(35.6, 38.5); text = "TÜRKİYE"; sp = 8
    tw = sum(fnt.getlength(c) + sp for c in text) - sp; cx = tx - tw / 2
    for c in text: dr.text((cx, ty), c, font=fnt, fill=(90, 62, 38), anchor="lm"); cx += fnt.getlength(c) + sp
    return im
TRMAP = _tr_map()
def a4(t, dur):  # dört bir yandan toprak
    cx, cy = P(35.3, 39.0)
    cam = camera(cx, cy, 980 - 60 * ease(t / 4))
    base = render_map(cam, TRMAP).convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    ax, ay = to_screen(cam, *ANKARA)
    for i, c in enumerate(TR_CITIES):
        t0 = 0.4 + i * 0.12; k = ease(clamp((t - t0) / 0.9))
        if k <= 0: continue
        x, y = to_screen(cam, *c)
        dr.line([(x, y), (x + (ax - x) * k, y + (ay - y) * k)], fill=RED + (200,), width=6)
        dr.ellipse([x - 10, y - 10, x + 10, y + 10], fill=(150, 110, 60, 255), outline=INK + (255,), width=3)
    if t > 1.0: pulse(dr, ax, ay, t, color=RED)
    city_dot(dr, ax, ay, "Anıtkabir", t - 0.8, color=RED, labelside="d", size=50)
    title_band(base, "DÖRT BİR YANDAN", t - 0.2, y=300, size=72, col=INK, sub="GETİRİLEN TOPRAKLAR")
    paste_pop(base, stamp_card(["YURT DIŞINDAN", "BİLE"], 640, 220, RED, seed=66, sizes=[64, 84], bg=(240, 228, 196, 245)), W / 2, 1280, t - e("yurtdisi", 3.6), rot=-4)
    return base.convert("RGB")

def a5(t, dur):  # 1941 yarışma, 49 proje
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    title_band(base, "1941 · YARIŞMA", t - 0.1, y=270, size=80, col=RED, sub="ALTI ÜLKE · 49 PROJE")
    dr = ImageDraw.Draw(base, "RGBA")
    cols, rows, cw, ch, gx, gy = 7, 7, 112, 82, 20, 20
    x0 = (W - (cols * cw + (cols - 1) * gx)) / 2; y0 = 450
    win = 24
    for i in range(49):
        t0 = 0.6 + i * 0.04
        if t < t0: continue
        k = clamp((t - t0) / 0.2); r, c = divmod(i, cols)
        x, y = x0 + c * (cw + gx), y0 + r * (ch + gy)
        lose = t > e("kazanan", 3.4) and i != win
        fill = (238, 226, 196, int(255 * k * (0.35 if lose else 1)))
        dr.rectangle([x, y, x + cw, y + ch], fill=fill, outline=INK + (int(200 * k * (0.35 if lose else 1)),), width=3)
        dr.line([(x + 14, y + ch - 18), (x + cw - 14, y + ch - 18)], fill=INK + (int(150 * k),), width=2)
        dr.rectangle([x + 30, y + 22, x + cw - 30, y + ch - 24], outline=INK + (int(120 * k),), width=2)
    if t > e("kazanan", 3.4):
        r, c = divmod(win, cols); x, y = x0 + c * (cw + gx), y0 + r * (ch + gy)
        dr.rectangle([x - 8, y - 8, x + cw + 8, y + ch + 8], outline=RED + (255,), width=8)
    paste_pop(base, stamp_card(["EMİN ONAT", "ORHAN ARDA"], 700, 220, RED, seed=67, sizes=[76, 76], bg=(240, 228, 196, 245)), W / 2, 1270, t - e("kazanan", 3.4), rot=-3)
    return base.convert("RGB")

def a6(t, dur):  # 10 Kasım 1953
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    k = ease_out(clamp(t / 0.8))
    anit(dr, W / 2, 1060 + (1 - k) * 60, 1.12, INK, int(255 * k))
    dr.line([(W / 2, 1060 - 360 * 1.12), (W / 2, 470)], fill=INK + (255,), width=8)
    B.put_flag(base, TR_S, W / 2 + 132, 540, t, amp=8)
    title_band(base, "10 KASIM 1953", t - 0.3, y=250, size=90, col=RED, sub="ÖLÜMÜNÜN 15. YILINDA")
    return base.convert("RGB")

def a7(t, dur):  # kapanış
    base = Image.new("RGBA", (W, H), (13, 10, 7, 255))
    B.put_flag(base, TR_FLAG, W / 2, 900, t, amp=12, op=0.16)
    dr = ImageDraw.Draw(base, "RGBA")
    a = int(255 * clamp(t / 0.4))
    if t < e("saygi", 4.2):
        spaced_text(dr, (W / 2, 820), "VATANIN HER KÖŞESİNDEN", font(FB, 56), CREAM + (a,), sp=4)
        spaced_text(dr, (W / 2, 910), "GELEN TOPRAKLA", font(FB, 56), CREAM + (a,), sp=4)
    else:
        tt = t - e("saygi", 4.2); p = back(tt / 0.5); s = int(96 * (0.6 + 0.4 * p)); a2_ = int(255 * clamp(tt / 0.3))
        spaced_text(dr, (W / 2, 820), "SAYGIYLA", font(FB, s), CREAM + (a2_,), sp=10)
        spaced_text(dr, (W / 2, 940), "ANIYORUZ", font(FB, s), (230, 70, 60, a2_), sp=10)
        if tt > 0.8:
            spaced_text(dr, (W / 2, 1060), "10 Kasım 1938 · 09.05", font(FI, 44), CREAM + (int(255 * clamp((tt - 0.8) / 0.5)),))
    return base.convert("RGB")

DUR = T.get("durs", [3.4, 5.0, 3.6, 6.4, 7.2, 5.6, 7.0])
SCENES = [("a1", a1, DUR[0]), ("a2", a2, DUR[1]), ("a3", a3, DUR[2]), ("a4", a4, DUR[3]), ("a5", a5, DUR[4]), ("a6", a6, DUR[5]), ("a7", a7, DUR[6])]
XF = 0.4
STARTS = []; _a = 0.0
for _n, _f, _d in SCENES: STARTS.append(_a); _a += _d
TOTAL = _a
IMPACTS = {"a1": [0.05, e("bos", 2.4)], "a2": [e("ton", 0.6), e("simge", 3.0)], "a3": [e("oda", 1.6)], "a4": [e("yurtdisi", 3.6)],
           "a5": [0.1, e("kazanan", 3.4)], "a6": [0.3], "a7": [e("saygi", 4.2)]}
B.SCENES, B.XF, B.STARTS, B.TOTAL, B.IMPACTS = SCENES, XF, STARTS, TOTAL, IMPACTS

if __name__ == "__main__":
    if sys.argv[1] == "frames":
        for ts in sys.argv[2:]: Image.fromarray(B.global_frame(float(ts))).save(os.path.join(OUT, f"af_{ts}.png"))
    else:
        for k, sc in enumerate(SCENES):
            if sc[0] in sys.argv[2:]: B.render(k)
