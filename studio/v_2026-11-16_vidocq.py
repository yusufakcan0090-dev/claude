import os, sys, math, subprocess
import numpy as np
from PIL import Image, ImageDraw
import make as M
from make import (W, H, FPS, OUT, SCREEN_PAPER, DESK, stamp_card, paste_pop, shadow, spaced_text, font, FB, FI, INK, RED,
                  CREAM, ease, ease_out, back, clamp, finish, dust, title_band)

PAPER_DARK = Image.fromarray((np.asarray(DESK, np.float32) * 0.45).astype(np.uint8))
BG = (240, 228, 196, 240)
GOLD = (226, 170, 90)
NAVY = (36, 52, 92)

def a_(t, t0, d=0.4): return int(255 * clamp((t - t0) / d))

def note(dr, text="Temsilî çizim", col=INK):
    dr.text((W - 40, H - 250), text, font=font(FI, 30), fill=col + (150,), anchor="rb")

def gent(dr, x, y, sc=1.0, col=INK, a=255, hat=True, coat=True, cap=False):
    """19. yy. erkek silüeti (önden), y = ayak hizası."""
    c = col + (a,)
    s = sc
    dr.ellipse([x - 42 * s, y - 470 * s, x + 42 * s, y - 370 * s], fill=c)              # head
    if hat:
        dr.rectangle([x - 40 * s, y - 560 * s, x + 40 * s, y - 455 * s], fill=c)        # top hat
        dr.rounded_rectangle([x - 72 * s, y - 468 * s, x + 72 * s, y - 452 * s], 6, fill=c)
    if cap:
        dr.pieslice([x - 50 * s, y - 500 * s, x + 50 * s, y - 420 * s], 180, 360, fill=c)
    dr.rectangle([x - 18 * s, y - 380 * s, x + 18 * s, y - 350 * s], fill=c)            # neck
    w = 110 if coat else 90
    dr.polygon([(x - w * s, y - 340 * s), (x + w * s, y - 340 * s), (x + (w + 20) * s, y - 120 * s),
                (x - (w + 20) * s, y - 120 * s)], fill=c)                                  # coat
    dr.rounded_rectangle([x - w * s, y - 360 * s, x + w * s, y - 320 * s], 30, fill=c)  # shoulders
    dr.rectangle([x - 60 * s, y - 130 * s, x - 12 * s, y], fill=c)                        # legs
    dr.rectangle([x + 12 * s, y - 130 * s, x + 60 * s, y], fill=c)
    dr.rectangle([x - (w + 28) * s, y - 340 * s, x - (w - 2) * s, y - 150 * s], fill=c)  # arms
    dr.rectangle([x + (w - 2) * s, y - 340 * s, x + (w + 28) * s, y - 150 * s], fill=c)

def bars(dr, x0, x1, y0, y1, a=255, n=7, col=(40, 32, 26)):
    c = col + (a,)
    for i in range(n):
        x = x0 + (x1 - x0) * (i + 0.5) / n
        dr.rounded_rectangle([x - 12, y0, x + 12, y1], 10, fill=c)
    dr.rectangle([x0, y0, x1, y0 + 26], fill=c); dr.rectangle([x0, y1 - 26, x1, y1], fill=c)

# ---------- scenes ----------
def s1(t, dur):  # hook
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    spaced_text(dr, (W / 2, 290), "FRANSIZ POLİSİNİN", font(FB, 66), INK + (255,), sp=4)
    spaced_text(dr, (W / 2, 390), "DEDEKTİF ŞEFİ", font(FB, 92), RED + (255,), sp=6)
    s = 0.95 + 0.05 * ease_out(t / 0.6)
    gent(dr, W / 2, 1230, 1.15 * s)
    # police badge on chest
    dr.ellipse([W / 2 - 40, 1230 - 330, W / 2 + 40, 1230 - 250], fill=GOLD + (255,))
    p = ease((t - 1.4) / 0.5)
    if p > 0:
        bars(dr, 160, W - 160, 560 - (1 - p) * 700, 1260, a=int(235 * p))
    if t > 1.9:
        paste_pop(base, stamp_card(["FİRARİ BİR", "MAHKÛMDU"], 820, 250, RED, seed=1, sizes=[70, 96], bg=BG), W / 2, 1360, t - 1.9, rot=-3)
    note(ImageDraw.Draw(base, "RGBA"))
    return base.convert("RGB")

def poster(t, k):
    w, h = 640, 800
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, h], fill=(244, 232, 200, 255), outline=(120, 96, 60, 255), width=6)
    spaced_text(d, (w / 2, 80), "ARANIYOR", font(FB, 78), INK + (255,), sp=8)
    d.rectangle([110, 150, w - 110, 560], fill=(214, 196, 156, 255), outline=INK + (255,), width=4)
    gent(d, w / 2, 640, 0.7, col=(70, 52, 34), hat=False)
    d.rectangle([110, 560, w - 110, 800], fill=(244, 232, 200, 255))
    d.rectangle([110, 150, w - 110, 560], outline=INK + (255,), width=4)
    spaced_text(d, (w / 2, 625), "E. F. VIDOCQ", font(FB, 62), RED + (255,), sp=4)
    spaced_text(d, (w / 2, 700), "Arras, 1775", font(FI, 40), INK + (255,))
    return im

def s2(t, dur):  # Vidocq: theft, forgery, prison to prison
    base = SCREEN_PAPER.copy().convert("RGBA")
    rise = ease_out(t / 0.6)
    pst = poster(t, rise).rotate(2, expand=True, resample=Image.BICUBIC)
    cx, cy = W / 2, 680 + (1 - rise) * 120
    base.alpha_composite(shadow(pst), (int(cx - pst.width / 2 - 18), int(cy - pst.height / 2 - 14)))
    base.alpha_composite(pst, (int(cx - pst.width / 2), int(cy - pst.height / 2)))
    items = [("HIRSIZLIK", 1.95, -8, 300, 1170), ("SAHTECİLİK", 2.75, 6, 780, 1170)]
    for txt, t0, rot, x, y in items:
        if t > t0: paste_pop(base, stamp_card([txt], 460, 140, RED, seed=len(txt), sizes=[58], bg=BG), x, y, t - t0, rot=rot)
    if t > 3.6:
        paste_pop(base, stamp_card(["HAPİSHANEDEN HAPİSHANEYE"], 900, 130, INK, seed=4, sizes=[50], bg=BG), W / 2, 1330, t - 3.6, rot=-1)
    return base.convert("RGB")

def s3(t, dur):  # escaped disguised as sailor; death sentence in absentia
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    k = a_(t, 0.05, 0.3)
    spaced_text(dr, (W / 2, 290), "DENİZCİ KILIĞINDA", font(FB, 70), INK + (k,), sp=4)
    spaced_text(dr, (W / 2, 385), "KAÇTI", font(FB, 96), RED + (k,), sp=10)
    bars(dr, 90, 470, 620, 1180, a=255, n=5)
    # broken bar gap
    dr.rectangle([300, 680, 360, 1120], fill=(236, 222, 186, 255))
    run = ease((t - 0.3) / 2.0)
    x = 330 + 420 * run
    gent(dr, x, 1180, 0.95, col=NAVY, hat=False, cap=True)
    # sailor stripes
    for i in range(4):
        yy = 1180 - (330 - i * 50) * 0.95
        dr.rectangle([x - 104, yy, x + 104, yy + 14], fill=(236, 226, 200, 255))
    if t > 2.5:
        veil = Image.new("RGBA", (W, H), (20, 14, 9, int(110 * clamp((t - 2.5) / 0.3)))); base.alpha_composite(veil)
        paste_pop(base, stamp_card(["GIYABİNDA", "İDAM KARARI"], 840, 250, RED, seed=5, sizes=[72, 84], bg=BG), W / 2, 1340, t - 2.5, rot=-4)
    note(ImageDraw.Draw(base, "RGBA"))
    return base.convert("RGB")

def s4(t, dur):  # 1809 caught again, makes an offer
    base = PAPER_DARK.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    p = back(t / 0.45); s = int(210 * (0.6 + 0.4 * p))
    spaced_text(dr, (W / 2, 330), "1809", font(FB, max(10, s)), GOLD + (a_(t, 0.0, 0.2),), sp=10)
    spaced_text(dr, (W / 2, 480), "yine yakalandı", font(FI, 56), CREAM + (a_(t, 0.5),))
    gent(dr, W / 2, 1150, 0.95, col=(18, 13, 9), hat=False)
    bars(dr, 150, W - 150, 600, 1170, a=255, n=6, col=(70, 58, 44))
    if t > 3.7:
        kb = a_(t, 3.7, 0.25)
        dr.rounded_rectangle([110, 1240, W - 110, 1390], 30, fill=(255, 250, 235, kb), outline=INK + (kb,), width=5)
        dr.polygon([(W / 2 - 40, 1242), (W / 2 + 30, 1242), (W / 2 - 10, 1190)], fill=(255, 250, 235, kb))
        spaced_text(dr, (W / 2, 1315), "“SUÇLULARI BEN YAKALARIM”", font(FB, 42), RED + (kb,))
    note(ImageDraw.Draw(base, "RGBA"), col=CREAM)
    return base.convert("RGB")

def s5(t, dur):  # Sûreté under Napoleon, agents ex-criminals
    base = SCREEN_PAPER.copy().convert("RGBA")
    title_band(base, "SÛRETÉ", t - 0.1, y=290, size=96, col=INK, sub="Napolyon dönemi · Paris")
    dr = ImageDraw.Draw(base, "RGBA")
    for i in range(8):
        r_, c_ = divmod(i, 4)
        x = 175 + c_ * 243; y = 860 + r_ * 430
        kk = int(255 * clamp((t - 0.6 - i * 0.12) / 0.3))
        if kk <= 0: continue
        gent(dr, x, y, 0.62, col=INK, a=kk, hat=(i % 2 == 0))
    if t > 2.05:
        for i in range(8):
            r_, c_ = divmod(i, 4)
            x = 175 + c_ * 243; y = 860 + r_ * 430
            kk = int(255 * clamp((t - 2.05 - i * 0.07) / 0.2))
            dr.rounded_rectangle([x - 95, y - 200, x + 95, y - 150], 10, fill=RED + (kk,))
            spaced_text(dr, (x, y - 175), "ESKİ SUÇLU", font(FB, 26), CREAM + (kk,))
    note(dr)
    return base.convert("RGB")

def mask_icon(d, cx, cy, a):
    c = INK + (a,)
    d.ellipse([cx - 150, cy - 60, cx - 10, cy + 60], fill=c); d.ellipse([cx + 10, cy - 60, cx + 150, cy + 60], fill=c)
    d.rectangle([cx - 40, cy - 40, cx + 40, cy + 10], fill=c)
    d.ellipse([cx - 110, cy - 22, cx - 50, cy + 22], fill=(236, 222, 186, a)); d.ellipse([cx + 50, cy - 22, cx + 110, cy + 22], fill=(236, 222, 186, a))

def cards_icon(d, cx, cy, a):
    for i in range(4):
        o = i * 18
        d.rounded_rectangle([cx - 140 + o, cy - 90 - o, cx + 120 + o, cy + 70 - o], 8, fill=(250, 244, 226, a), outline=INK + (a,), width=4)
    for j in range(4):
        d.line([(cx - 60 + 54, cy - 100 + 30 + j * 26 - 54), (cx + 120 + 30, cy - 100 + 30 + j * 26 - 54)], fill=INK + (a,), width=3)
    d.rectangle([cx - 100 + 54, cy - 90 - 54 + 25, cx - 50 + 54, cy - 90 - 54 + 85], fill=(150, 130, 100, a))

def foot_icon(d, cx, cy, a):
    d.rounded_rectangle([cx - 150, cy - 110, cx + 150, cy + 110], 20, fill=(232, 228, 216, a), outline=(150, 140, 120, a), width=4)
    c = (120, 108, 92, a)
    d.ellipse([cx - 55, cy - 80, cx + 45, cy + 30], fill=c); d.ellipse([cx - 40, cy + 35, cx + 30, cy + 95], fill=c)
    for i, (dx, r) in enumerate([(-50, 14), (-24, 12), (0, 11), (22, 10), (40, 9)]):
        d.ellipse([cx + dx - r, cy - 100 - r + abs(dx) * 0.2, cx + dx + r, cy - 100 + r + abs(dx) * 0.2], fill=c)

def s6(t, dur):  # disguise, card index, plaster casts
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    rows = [("KILIK DEĞİŞTİRME", mask_icon, 0.1, 560), ("SUÇLU KARTOTEKİ", cards_icon, 1.35, 900), ("AYAK İZİ ALÇI KALIBI", foot_icon, 2.6, 1240)]
    for txt, fn, t0, y in rows:
        k = a_(t, t0, 0.3)
        if k <= 0: continue
        dx = (1 - ease_out((t - t0) / 0.4)) * 120
        fn(dr, 250 - dx, y, k)
        spaced_text(dr, (680 + dx * 0.3, y), txt, font(FB, 44), INK + (k,), anchor="mm")
    if t > 3.9:
        paste_pop(base, stamp_card(["İLK KULLANANLARDAN"], 900, 150, RED, seed=6, sizes=[64], bg=BG), W / 2, 330, t - 3.9, rot=-2)
    else:
        spaced_text(dr, (W / 2, 330), "YÖNTEMLERİ", font(FB, 80), INK + (a_(t, 0, 0.2),), sp=8)
    return base.convert("RGB")

def s7(t, dur):  # 1833 first private detective agency
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    p = back(t / 0.45); s = int(190 * (0.6 + 0.4 * p))
    spaced_text(dr, (W / 2, 300), "1833", font(FB, max(10, s)), RED + (a_(t, 0, 0.2),), sp=10)
    k = a_(t, 0.4)
    # door
    dr.rounded_rectangle([290, 470, 790, 1150], 30, fill=(92, 60, 36, k), outline=INK + (k,), width=6)
    for (x0, y0, x1, y1) in [(330, 630, 520, 890), (560, 630, 750, 890), (330, 930, 520, 1110), (560, 930, 750, 1110)]:
        dr.rounded_rectangle([x0, y0, x1, y1], 10, outline=(60, 40, 24, k), width=5)
    dr.ellipse([710, 900, 740, 930], fill=GOLD + (k,))
    kb = a_(t, 0.9)
    dr.rounded_rectangle([320, 500, 760, 600], 10, fill=GOLD + (kb,), outline=INK + (kb,), width=4)
    spaced_text(dr, (540, 532), "BUREAU DE", font(FB, 32), INK + (kb,), sp=3)
    spaced_text(dr, (540, 572), "RENSEIGNEMENTS", font(FB, 32), INK + (kb,), sp=2)
    spaced_text(dr, (W / 2, 1185), "Paris", font(FI, 44), INK + (kb,))
    if t > 1.6:
        paste_pop(base, stamp_card(["DÜNYANIN İLK ÖZEL", "DEDEKTİFLİK BÜROSU"], 900, 230, RED, seed=7, sizes=[60, 60], bg=BG), W / 2, 1330, t - 1.6, rot=-2)
    note(dr)
    return base.convert("RGB")

def book(t):
    w, h = 420, 580
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w, h], 14, fill=(110, 28, 26, 255), outline=(60, 14, 12, 255), width=6)
    d.rectangle([24, 24, w - 24, h - 24], outline=GOLD + (255,), width=3)
    spaced_text(d, (w / 2, 200), "SEFİLLER", font(FB, 58), GOLD + (255,), sp=4)
    spaced_text(d, (w / 2, 290), "Victor Hugo", font(FI, 40), GOLD + (255,))
    spaced_text(d, (w / 2, 380), "1862", font(FB, 40), GOLD + (255,))
    return im

def s8(t, dur):  # Les Misérables: Valjean & Javert
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    rise = ease_out(t / 0.6)
    b = book(t)
    base.alpha_composite(shadow(b), (int(W / 2 - b.width / 2 - 18), int(190 + (1 - rise) * 80 - 14)))
    base.alpha_composite(b, (int(W / 2 - b.width / 2), int(190 + (1 - rise) * 80)))
    dr = ImageDraw.Draw(base, "RGBA")
    ka = a_(t, 1.5); kb = a_(t, 3.0)
    if ka: gent(dr, 270, 1150, 0.62, col=(70, 52, 34), a=ka, hat=False)
    if ka: spaced_text(dr, (270, 1195), "JEAN VALJEAN", font(FB, 40), INK + (ka,)); spaced_text(dr, (270, 1240), "kaçak", font(FI, 38), INK + (ka,))
    if kb: gent(dr, W - 270, 1150, 0.62, col=NAVY, a=kb)
    if kb: spaced_text(dr, (W - 270, 1195), "JAVERT", font(FB, 40), INK + (kb,)); spaced_text(dr, (W - 270, 1240), "polis", font(FI, 38), INK + (kb,))
    if t > 5.0:
        paste_pop(base, stamp_card(["İLHAM KAYNAĞI: VIDOCQ"], 860, 150, RED, seed=8, sizes=[70], bg=BG), W / 2, 1370, t - 5.0, rot=-3)
    return base.convert("RGB")

def s9(t, dur):  # ending
    base = Image.new("RGBA", (W, H), (13, 10, 7, 255)); dr = ImageDraw.Draw(base, "RGBA")
    gent(dr, W / 2, 1500, 1.3, col=(34, 26, 19), a=int(120 * clamp(t / 1.5)))
    spaced_text(dr, (W / 2, 720), "Bir suçluyu en iyi kim yakalar?", font(FI, 58), CREAM + (a_(t, 0.1, 0.5),))
    if t > 2.2:
        p = back((t - 2.2) / 0.45); s = int(104 * (0.6 + 0.4 * p))
        spaced_text(dr, (W / 2, 900), "BİR BAŞKA", font(FB, max(10, s)), GOLD + (a_(t, 2.2, 0.25),), sp=8)
        spaced_text(dr, (W / 2, 1040), "SUÇLU MU?", font(FB, max(10, int(s * 1.15))), (230, 80, 60, a_(t, 2.2, 0.25)), sp=8)
    return base.convert("RGB")

SCENES = [("s1", s1, 3.6), ("s2", s2, 4.95), ("s3", s3, 4.95), ("s4", s4, 5.4), ("s5", s5, 4.75),
          ("s6", s6, 5.85), ("s7", s7, 3.95), ("s8", s8, 6.4), ("s9", s9, 4.0)]
XF = 0.35
STARTS = []; _a = 0.0
for _n, _f, _d in SCENES: STARTS.append(_a); _a += _d
TOTAL = _a
IMPACTS = {"s1": [1.9], "s2": [1.95, 2.75, 3.6], "s3": [2.5], "s4": [0.0, 3.7], "s5": [2.05], "s6": [3.9], "s7": [0.0, 1.6],
           "s8": [5.0], "s9": [2.2]}

def shake(img, name, t):
    amp = 0.0
    for t0 in IMPACTS.get(name, []):
        dt = t - t0 - 0.06
        if 0 <= dt < 0.45: amp += 12 * math.exp(-dt * 9)
    if amp < 0.5: return img
    dx = amp * math.sin(t * 91); dy = amp * math.cos(t * 77)
    return img.transform((W, H), Image.AFFINE, (1, 0, -dx, 0, 1, -dy), Image.BILINEAR, fillcolor=(20, 14, 9))

def scene_frame(k, T):
    name, fn, dur = SCENES[k]; t = T - STARTS[k]
    return np.asarray(shake(fn(t, dur + XF), name, t), np.float32)

def global_frame(T):
    k = max(i for i, s0 in enumerate(STARTS) if s0 <= T + 1e-9)
    a = scene_frame(k, T)
    if k > 0 and T - STARTS[k] < XF:
        b = scene_frame(k - 1, T); w = ease((T - STARTS[k]) / XF); a = a * w + b * (1 - w)
    im = dust(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)), T)
    out = finish(im, SCENES[k][0] != "s9").astype(np.float32)
    if T > TOTAL - 0.5: out *= max(0, (TOTAL - T) / 0.5)
    return np.clip(out, 0, 255).astype(np.uint8)

def render(k):
    name = SCENES[k][0]
    t0 = STARTS[k]; t1 = STARTS[k + 1] if k + 1 < len(SCENES) else TOTAL
    n0, n1 = int(round(t0 * FPS)), int(round(t1 * FPS))
    tmp = os.path.join(OUT, f"{name}.tmp.mp4"); fin = os.path.join(OUT, f"{name}.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), tmp],
                         stdin=subprocess.PIPE)
    for i in range(n0, n1): p.stdin.write(global_frame(i / FPS).tobytes())
    p.stdin.close(); rc = p.wait()
    if rc == 0: os.replace(tmp, fin)
    print(name, "done", rc, flush=True)

if __name__ == "__main__":
    if sys.argv[1] == "frames":
        for ts in sys.argv[2:]: Image.fromarray(global_frame(float(ts))).save(os.path.join(OUT, f"sf_{ts}.png"))
    else:
        for k, sc in enumerate(SCENES):
            if sc[0] in sys.argv[2:]: render(k)
