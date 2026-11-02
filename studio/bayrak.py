import os, sys, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import make as M
from make import (W, H, FPS, OUT, SCREEN_PAPER, DESK, render_map, camera, P, CITY, to_screen, city_dot, pulse, stamp_card,
                  paste_pop, wave_flag, make_flag, shadow, spaced_text, font, FB, FI, INK, RED, BLUE, CREAM, ease, ease_out,
                  back, clamp, finish, dust, title_band)

RED_F = make_flag(860, 573, (200, 16, 46))
BLUE_F = make_flag(860, 573, (86, 165, 222))
BLUE_S = make_flag(240, 160, (86, 165, 222))
BLUE_M = make_flag(560, 373, (86, 165, 222))
PAPER_DARK = Image.fromarray((np.asarray(DESK, np.float32) * 0.45).astype(np.uint8))

def put_flag(base, flag, cx, cy, t, amp=18, op=1.0, sat=1.0):
    wf = wave_flag(flag, t, amp=amp)
    if sat < 1.0:
        g = wf.convert("LA").convert("RGBA"); a = wf.getchannel("A")
        wf = Image.blend(g, wf, sat); wf.putalpha(a)
    if op < 1.0:
        a = np.asarray(wf).copy(); a[..., 3] = (a[..., 3] * op).astype(np.uint8); wf = Image.fromarray(a)
    sh = shadow(wf, op=int(110 * op))
    base.alpha_composite(sh, (int(cx - wf.width / 2 - 30 + 12), int(cy - wf.height / 2 - 30 + 16)))
    base.alpha_composite(wf, (int(cx - wf.width / 2), int(cy - wf.height / 2)))
    return wf

# ---------- scenes ----------
def b1(t, dur):  # hook: red flag turns blue
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    a = int(255 * clamp((t - 0.1) / 0.35))
    spaced_text(dr, (W / 2, 290), "BU BAYRAĞI", font(FB, 78), INK + (a,), sp=8)
    spaced_text(dr, (W / 2, 385), "TANIYOR MUSUN?", font(FB, 78), INK + (a,), sp=6)
    # morph red -> blue as a dye sweep
    p = ease((t - 3.85) / 0.8)
    ra, ba = np.asarray(RED_F, np.float32), np.asarray(BLUE_F, np.float32)
    xs = np.arange(RED_F.width)[None, :, None]
    edge = p * (RED_F.width + 160) - 80
    m = np.clip((edge - xs) / 80 + 0.5, 0, 1)
    fl = Image.fromarray((ra * (1 - m) + ba * m).astype(np.uint8))
    s_in = ease_out(t / 0.5); z = 0.85 + 0.15 * s_in
    fl = fl.resize((int(fl.width * z), int(fl.height * z)), Image.BILINEAR)
    put_flag(base, fl, W / 2, 860, t)
    dr = ImageDraw.Draw(base, "RGBA")
    if t > 2.2:
        k = int(255 * clamp((t - 2.2) / 0.3) * (1 - clamp((t - 3.85) / 0.15)))
        pass
    if t > 4.0:
        paste_pop(base, stamp_card(["AMA MAVİ"], 560, 150, (40, 110, 175), seed=3, sizes=[82], bg=(240, 228, 196, 235)),
                  W / 2, 1270, t - 4.0, rot=-4)
    return base.convert("RGB")

KAS = P(*CITY["Kaşgar"])
def b2(t, dur):  # map: Kashgar, 12 Nov 1933
    p = ease((t - 0.2) / 3.0)
    cx0, cy0 = P(62, 0)[0], P(0, 38)[1]
    cx = cx0 + (KAS[0] - cx0) * p; cy = cy0 + (KAS[1] + 60 - cy0) * p
    vh = 3000 + (1250 - 3000) * p - 60 * clamp((t - 3) / 5)
    cam = camera(cx, cy, vh)
    base = render_map(cam).convert("RGBA")
    if t > 2.4: M.draw_region(base, cam, BLUE, 0.22 * ease((t - 2.4) / 0.8))
    dr = ImageDraw.Draw(base, "RGBA")
    kx, ky = to_screen(cam, *CITY["Kaşgar"])
    if t > 2.6: pulse(dr, kx, ky, t, color=BLUE)
    city_dot(dr, kx, ky, "Kaşgar", t - 2.6, color=BLUE, labelside="d", size=58)
    if t > 3.6:
        k = int(255 * clamp((t - 3.6) / 0.4))
        dr.text((kx, ky + 110), "İdgâh Camii'nde toplanan kalabalık", font=font(FI, 40), fill=INK + (k,), anchor="mt",
                stroke_width=6, stroke_fill=(245, 235, 211, k))
    title_band(base, "12 KASIM 1933", t - 0.3, y=290, size=86, col=INK)
    if t > 7.0:
        put_flag(base, BLUE_S, kx + 10, ky - 140, t, amp=7, op=clamp((t - 7.0) / 0.3))
        paste_pop(base, stamp_card(["DOĞU TÜRKİSTAN", "CUMHURİYETİ İLAN EDİLDİ"], 900, 220, RED, seed=8, sizes=[62, 40],
                                   bg=(240, 228, 196, 240)), W / 2, 1220, t - 7.0, rot=-2)
    return base.convert("RGB")

def b3(t, dur):  # anatomy of the flag
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    a = int(255 * clamp((t - 0.1) / 0.35) * (1 - clamp((t - 5.9) / 0.3)))
    spaced_text(dr, (W / 2, 285), "SEÇTİKLERİ BAYRAK", font(FB, 70), INK + (a,), sp=6)
    fcx, fcy = W / 2, 800
    put_flag(base, BLUE_F, fcx, fcy, t, amp=14)
    dr = ImageDraw.Draw(base, "RGBA")
    x0, y0 = fcx - 430, fcy - 286
    G = 573
    if t > 3.0:
        k = clamp((t - 3.0) / 0.35)
        cx, cy, r = x0 + 0.7 * G, y0 + 0.5 * G + 40 - 40, 210 * back(k)
        dr.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(200, 16, 46, 255), width=8)
        dr.line([(cx, cy - r), (cx, 460)], fill=(200, 16, 46, int(255 * k)), width=5)
        dr.rounded_rectangle([140, 380, W - 140, 460], 14, fill=(240, 228, 196, int(240 * k)), outline=(200, 16, 46, int(255 * k)), width=4)
        spaced_text(dr, (W / 2, 420), "AY-YILDIZ: TÜRK BAYRAĞIYLA AYNI", font(FB, 38), (200, 16, 46, int(255 * k)))
    if t > 3.9:
        k = clamp((t - 3.9) / 0.35)
        px, py = x0 + 0.86 * 860, y0 + 0.82 * G
        dr.ellipse([px - 18, py - 18, px + 18, py + 18], fill=(40, 110, 175, int(255 * k)), outline=(255, 255, 255, int(255 * k)), width=4)
        dr.line([(px, py), (px, 1180)], fill=(40, 110, 175, int(255 * k)), width=5)
        dr.rounded_rectangle([300, 1180, W - 60, 1260], 14, fill=(240, 228, 196, int(240 * k)), outline=(40, 110, 175, int(255 * k)), width=4)
        spaced_text(dr, ((300 + W - 60) / 2, 1220), "ZEMİN: GÖK MAVİSİ", font(FB, 40), (40, 110, 175, int(255 * k)))
    if t > 6.1:
        paste_pop(base, stamp_card(["GÖK BAYRAK"], 760, 160, (40, 110, 175), seed=12, sizes=[88], bg=(240, 228, 196, 245)),
                  W / 2, 285, t - 6.1, rot=-3)
    return base.convert("RGB")

def b4(t, dur):  # only 5 months
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    # pole
    px = 250
    dr.rectangle([px - 9, 380, px + 9, 1180], fill=(70, 48, 30, 255)); dr.ellipse([px - 16, 364, px + 16, 396], fill=(170, 130, 60, 255))
    low = ease((t - 3.0) / 1.6)
    fy = 400 + low * 560
    sat = 1 - 0.85 * low
    wf = wave_flag(BLUE_M, t, amp=14 * (1 - 0.7 * low))
    if sat < 1:
        g = wf.convert("LA").convert("RGBA"); al = wf.getchannel("A"); wf = Image.blend(g, wf, sat); wf.putalpha(al)
    base.alpha_composite(shadow(wf), (px + 9 - 30 + 10, int(fy - 40 - 30 + 14)))
    base.alpha_composite(wf, (px + 9, int(fy - 40)))
    dr = ImageDraw.Draw(base, "RGBA")
    # timeline bar
    bx0, bx1, by = 120, W - 120, 1260
    a = int(255 * clamp((t - 0.2) / 0.3))
    dr.rounded_rectangle([bx0, by - 16, bx1, by + 16], 16, outline=INK + (a,), width=4)
    f = ease((t - 0.4) / 1.6)
    if f > 0: dr.rounded_rectangle([bx0 + 6, by - 10, bx0 + 6 + (bx1 - bx0 - 12) * f, by + 10], 10, fill=(40, 110, 175, 255))
    dr.text((bx0, by + 36), "KASIM 1933", font=font(FB, 36), fill=INK + (a,), anchor="lt")
    dr.text((bx1, by + 36), "1934", font=font(FB, 36), fill=INK + (a,), anchor="rt")
    paste_pop(base, stamp_card(["SADECE 5 AY"], 800, 160, RED, seed=21, sizes=[86], bg=(240, 228, 196, 240)), W / 2, 270, t - 1.3, rot=-3)
    paste_pop(base, stamp_card(["1934", "YIKILDI"], 360, 200, INK, seed=22, sizes=[70, 44], bg=(240, 228, 196, 240)),
              W - 280, 760, t - 3.1, rot=8)
    return base.convert("RGB")

def b5(t, dur):  # banned
    base = PAPER_DARK.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    a = int(255 * clamp((t - 0.1) / 0.35))
    spaced_text(dr, (W / 2, 300), "BUGÜN ÇİN'DE", font(FB, 74), CREAM + (a,), sp=8)
    sat = 1 - 0.6 * clamp((t - 2.25) / 0.2)
    put_flag(base, BLUE_F, W / 2, 820, t, amp=14, sat=sat)
    if t > 2.25:
        red = Image.new("RGBA", (W, H), (150, 10, 10, int(70 * clamp((t - 2.25) / 0.2)))); base.alpha_composite(red)
    paste_pop(base, stamp_card(["YASAK"], 760, 230, (215, 25, 25), seed=31, sizes=[150]), W / 2, 830, t - 2.2, rot=-14, dur=0.25)
    return base.convert("RGB")

def b6(t, dur):  # still carried at protests
    base = SCREEN_PAPER.copy().convert("RGBA"); dr = ImageDraw.Draw(base, "RGBA")
    rise = ease_out(t / 0.8)
    put_flag(base, BLUE_F, W / 2, 620 + (1 - rise) * 200, t, amp=22)
    dr = ImageDraw.Draw(base, "RGBA")
    paste_pop(base, stamp_card(["İSTANBUL"], 520, 130, RED, seed=41, sizes=[66], bg=(240, 228, 196, 240)), W / 2 - 200, 1040, t - 0.6, rot=-5)
    paste_pop(base, stamp_card(["WASHINGTON"], 560, 130, RED, seed=42, sizes=[60], bg=(240, 228, 196, 240)), W / 2 + 180, 1200, t - 1.7, rot=4)
    if t > 2.8:
        k = int(255 * clamp((t - 2.8) / 0.5))
        spaced_text(dr, (W / 2, 1330), "New York · Hong Kong · Taipei", font(FI, 42), INK + (k,))
    a = int(255 * clamp((t - 0.1) / 0.4))
    spaced_text(dr, (W / 2, 230), "HÂLÂ TAŞINIYOR", font(FB, 70), INK + (a,), sp=6)
    return base.convert("RGB")

def b7(t, dur):  # ending
    base = Image.new("RGBA", (W, H), (13, 10, 7, 255))
    put_flag(base, BLUE_F, W / 2, 900, t, amp=12, op=0.16 + 0.1 * clamp((t - 2.4) / 1.5))
    dr = ImageDraw.Draw(base, "RGBA")
    def a(t0, d=0.5): return int(255 * clamp((t - t0) / d))
    spaced_text(dr, (W / 2, 720), "Bir bayrak yasaklanabilir...", font(FI, 56), CREAM + (a(0.35),))
    if t > 2.4:
        p = back((t - 2.4) / 0.45); s = int(78 * (0.6 + 0.4 * p))
        spaced_text(dr, (W / 2, 900), "YA BİR MİLLETİN", font(FB, max(10, s)), (110, 180, 235, a(2.4, 0.25)), sp=6)
        spaced_text(dr, (W / 2, 1020), "HAFIZASI?", font(FB, max(10, int(s * 1.35))), (110, 180, 235, a(2.4, 0.25)), sp=10)
    return base.convert("RGB")

SCENES = [("b1", b1, 5.3), ("b2", b2, 8.1), ("b3", b3, 7.3), ("b4", b4, 4.8), ("b5", b5, 3.0), ("b6", b6, 5.3), ("b7", b7, 6.0)]
XF = 0.4
STARTS = []; _a = 0.0
for _n, _f, _d in SCENES: STARTS.append(_a); _a += _d
TOTAL = _a
IMPACTS = {"b1": [4.0], "b2": [0.3, 7.0], "b3": [6.1], "b4": [1.3, 3.1], "b5": [2.2], "b6": [0.6, 1.7], "b7": [2.4]}

def shake(img, name, t):
    amp = 0.0
    for t0 in IMPACTS.get(name, []):
        dt = t - t0 - 0.06
        if 0 <= dt < 0.45: amp += (22 if name == "b5" else 14) * math.exp(-dt * 9)
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
    out = finish(im, SCENES[k][0] != "b7").astype(np.float32)
    if T < 0.15: out *= T / 0.15
    if T > TOTAL - 0.6: out *= max(0, (TOTAL - T) / 0.6)
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
        for ts in sys.argv[2:]: Image.fromarray(global_frame(float(ts))).save(os.path.join(OUT, f"bf_{ts}.png"))
    else:
        for k, sc in enumerate(SCENES):
            if sc[0] in sys.argv[2:]: render(k)
