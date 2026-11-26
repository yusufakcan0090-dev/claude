"""Zamanlı efektler ve geçişler (Sapphire / Continuum tarzı, kendi yazımımız).

Her efekt, zaman aralığı kırpılmış (t=0'dan başlayan) bir video dalına uygulanır,
sonra ana videonun üstüne aynı zamanda geri konur. Böylece efekt yalnızca seçilen
aralıkta çalışır ve geri kalan video hiç yavaşlamaz."""
import subprocess

import numpy as np

from core import CACHE, FFMPEG, NO_WINDOW

# key: (ad, kategori, varsayılan süre)
EFFECTS = {
    "glitch": ("Glitch", "Glitch", 0.8),
    "rgbsplit": ("RGB Ayrışma", "Glitch", 0.8),
    "pixel": ("Piksel / Mozaik", "Glitch", 1.5),
    "glow": ("Renkli Parlama", "Işık", 1.5),
    "rainbow": ("Gökkuşağı Parlama", "Işık", 1.5),
    "softlight": ("Yumuşak Işık", "Işık", 2.0),
    "leak": ("Işık Sızıntısı", "Işık", 1.6),
    "flare": ("Lens Flare", "Işık", 1.6),
    "flash": ("Flaş", "Işık", 0.35),
    "strobe": ("Strobe", "Işık", 0.8),
    "film": ("Eski Film", "Retro", 2.5),
    "vhs": ("VHS", "Retro", 2.5),
    "motionblur": ("Hareket Bulanıklığı", "Bulanıklık", 0.8),
    "dirblur": ("Yön Bulanıklığı", "Bulanıklık", 0.6),
    "defocus": ("Odak Dışı", "Bulanıklık", 1.0),
    "shake": ("Hafif Kamera", "Sarsıntı", 2.0),
    "quake": ("Deprem", "Sarsıntı", 1.0),
    "punch": ("Yumruk", "Sarsıntı", 0.6),
    "posterize": ("Posterize", "Stilize", 1.5),
    "duotone": ("Duotone", "Stilize", 1.5),
    "halftone": ("Halftone", "Stilize", 1.2),
    "edges": ("Kenar Çizgisi", "Stilize", 1.2),
    "bwpop": ("Siyah-Beyaz Vurgu", "Stilize", 1.5),
    "colorkeep": ("Kırmızıyı Tut", "Stilize", 1.5),
    "invert": ("Negatif", "Stilize", 0.5),
    "symmetry": ("Ayna Simetri", "Stilize", 1.5),
}

TRANSITIONS = {
    "none": "Yok", "flash": "Flaş", "zoom": "Zoom", "slide": "Kayma", "glitch": "Glitch",
    "dip": "Kararma", "white": "Beyaz", "swirl": "Girdap",
}


def _hex(c, default="#FF3D8B"):
    c = (c or default).lstrip("#")
    if len(c) == 3:
        c = "".join(x * 2 for x in c)
    try:
        return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return _hex(default)


class Ctx:
    """Filtre grafiği kurarken gereken bilgiler."""

    def __init__(self, W, H, fps, add_input):
        self.W, self.H, self.fps = W, H, fps
        self.add_input = add_input   # (path, loop) -> giriş numarası
        self.n = 0

    def lab(self, p):
        self.n += 1
        return f"{p}{self.n}"


def flare_png(W, H):
    """Lens flare görüntüsünü bir kere üretip önbelleğe koyar (RGBA)."""
    path = CACHE / f"flare_{W}x{H}.png"
    if path.exists():
        return path
    w, h = int(W * 1.6), int(W * 0.9)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w * 0.5, h * 0.5
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / W
    core = np.exp(-(d / 0.035) ** 2)
    halo = np.exp(-(d / 0.18) ** 2) * 0.45
    ring = np.exp(-((d - 0.28) / 0.012) ** 2) * 0.22
    streak = np.exp(-((yy - cy) / (h * 0.012)) ** 2) * np.exp(-np.abs(xx - cx) / (w * 0.32)) * 0.75
    img = np.zeros((h, w, 3), np.float32)
    warm = np.array([1.0, 0.82, 0.55])
    blue = np.array([0.45, 0.7, 1.0])
    img += (core + halo)[..., None] * warm
    img += ring[..., None] * np.array([0.6, 1.0, 0.8])
    img += streak[..., None] * blue
    # hayaletler (lens yansımaları)
    for k, (gx, r, col) in enumerate([(-0.25, 0.03, (0.4, 0.9, 1)), (-0.42, 0.05, (1, 0.5, 0.9)), (0.3, 0.02, (1, 1, 0.6))]):
        g = np.exp(-(np.sqrt((xx - (cx + gx * w)) ** 2 + (yy - cy) ** 2) / W / r) ** 4) * 0.35
        img += g[..., None] * np.array(col)
    a = np.clip(img.max(axis=2), 0, 1)
    rgb = np.clip(img / np.maximum(a[..., None], 1e-3), 0, 1)
    out = np.concatenate([rgb, a[..., None]], axis=2)
    raw = (out * 255).astype(np.uint8).tobytes()
    subprocess.run([FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{w}x{h}",
                    "-i", "-", str(path)], input=raw, creationflags=NO_WINDOW)
    return path


def build(kind, inp, out, D, I, p, c):
    """kind efektini [inp] -> [out] olarak kurar. t = efektin başından itibaren saniye."""
    W, H = c.W, c.H
    I = max(0.0, min(1.0, I))
    D = max(0.05, D)
    s = []

    def chain(f):
        s.append(f"[{inp}]{f}[{out}]")

    if kind == "glitch":
        sh = max(2, int(W * 0.012 * (0.5 + I)))
        a, b, g = c.lab("ga"), c.lab("gb"), c.lab("gc")
        st1, st2, base = c.lab("gs"), c.lab("gt"), c.lab("gd")
        sh_h = max(2, (H // 10) // 2 * 2)
        s.append(f"[{inp}]rgbashift=rh=-{sh}:bh={sh}:rv={max(1, sh // 3)}:edge=wrap,"
                 f"hue=h='{40 * I:.1f}*sin(t*83)':s='1+{0.5 * I:.2f}*sin(t*61)',"
                 f"eq=brightness='{0.1 * I:.3f}*sin(t*97)':contrast={1 + 0.25 * I:.2f}:eval=frame,"
                 f"noise=alls={int(8 + 25 * I)}:allf=t,split=3[{base}][{a}][{b}]")
        s.append(f"[{a}]crop={W}:{sh_h}:0:'mod(floor(t*15)*397,{H - sh_h})'[{st1}]")
        s.append(f"[{b}]crop={W}:{sh_h // 2 * 2}:0:'mod(floor(t*12)*911+200,{H - sh_h})'[{st2}]")
        s.append(f"[{base}][{st1}]overlay=x='{W * 0.05 * I:.1f}*sin(floor(t*15)*13)':y='mod(floor(t*15)*397,{H - sh_h})'[{g}]")
        s.append(f"[{g}][{st2}]overlay=x='-{W * 0.07 * I:.1f}*sin(floor(t*12)*7)':y='mod(floor(t*12)*911+200,{H - sh_h})',format=yuv420p[{out}]")
    elif kind == "rgbsplit":
        sh = max(2, int(W * 0.018 * (0.4 + I)))
        chain(f"rgbashift=rh=-{sh}:bh={sh}:rv={sh // 2}:bv=-{sh // 2}:edge=smear")
    elif kind == "pixel":
        blk = int(6 + 40 * I)
        chain(f"scale={max(4, W // blk)}:-2:flags=neighbor,scale={W}:{H}:flags=neighbor,setsar=1")
    elif kind in ("glow", "rainbow", "softlight"):
        a, b, g = c.lab("wa"), c.lab("wb"), c.lab("wg")
        s.append(f"[{inp}]format=gbrp,split[{a}][{b}]")
        if kind == "glow":
            r, gg, bb = (v / 255 for v in _hex(p.get("color"), "#FF3D8B"))
            s.append(f"[{b}]gblur=sigma={W / 45:.1f},colorchannelmixer=rr={r:.2f}:rg=0.25:rb=0.25:gr=0.25:gg={gg:.2f}:gb=0.25:br=0.25:bg=0.25:bb={bb:.2f},eq=brightness=0.05[{g}]")
            s.append(f"[{a}][{g}]blend=all_mode=screen:all_opacity={0.35 + 0.6 * I:.2f},format=yuv420p[{out}]")
        elif kind == "rainbow":
            s.append(f"[{b}]gblur=sigma={W / 45:.1f},format=yuv420p,hue=h='t*300':s=2.5,format=gbrp[{g}]")
            s.append(f"[{a}][{g}]blend=all_mode=screen:all_opacity={0.35 + 0.6 * I:.2f},format=yuv420p[{out}]")
        else:
            s.append(f"[{b}]gblur=sigma={W / 30:.1f},eq=brightness=0.06:saturation=1.2[{g}]")
            s.append(f"[{a}][{g}]blend=all_mode=softlight:all_opacity={0.3 + 0.6 * I:.2f},format=yuv420p[{out}]")
    elif kind == "leak":
        r, g_, b = _hex(p.get("color"), "#FF8A00")
        gsrc, a, gg = c.lab("lk"), c.lab("la"), c.lab("lg")
        s.append(f"gradients=s={W}x{H}:d={D + 0.5:.3f}:r={c.fps:g}:type=radial:speed=0.015:"
                 f"c0=0x{r:02x}{g_:02x}{b:02x}:c1=0xffd27a:c2=0x000000:c3=0x000000:nb_colors=4:"
                 f"x0={int(W * 0.1)}:y0={int(H * 0.15)}:x1={int(W * 0.9)}:y1={int(H * 0.7)},"
                 f"fade=t=in:st=0:d=0.2,fade=t=out:st={max(0, D - 0.25):.3f}:d=0.25,format=gbrp[{gsrc}]")
        s.append(f"[{inp}]format=gbrp[{a}]")
        s.append(f"[{a}][{gsrc}]blend=all_mode=screen:all_opacity={0.4 + 0.6 * I:.2f}:shortest=1,format=yuv420p[{out}]")
    elif kind == "flare":
        idx = c.add_input(str(flare_png(W, H)), True)
        fl, a = c.lab("fl"), c.lab("fa")
        fw = int(W * 1.6)
        s.append(f"[{idx}:v]format=rgba,colorchannelmixer=aa={0.55 + 0.45 * I:.2f},"
                 f"fade=t=in:st=0:d=0.25:alpha=1,fade=t=out:st={max(0, D - 0.3):.3f}:d=0.3:alpha=1,"
                 f"trim=duration={D:.3f},setpts=PTS-STARTPTS[{fl}]")
        s.append(f"[{inp}][{fl}]overlay=x='-{fw * 0.75:.0f}+t/{D:.3f}*{W * 0.9:.0f}':y='{H * 0.22:.0f}-h/2':eof_action=pass:shortest=0,format=yuv420p[{out}]")
    elif kind == "flash":
        L = min(D, 0.35)
        chain(f"eq=brightness='{0.55 + 0.4 * I:.2f}*max(0,1-t/{L:.3f})':eval=frame")
    elif kind == "strobe":
        chain(f"eq=brightness='{0.4 + 0.5 * I:.2f}*lt(mod(t*{8 + 8 * I:.1f},1),0.5)':eval=frame")
    elif kind == "film":
        chain(f"colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131,"
              f"eq=contrast=1.1:brightness='0.04*sin(t*31)':eval=frame,"
              f"noise=alls={int(10 + 20 * I)}:allf=t,vignette=PI/4,"
              f"drawbox=x='mod(floor(t*24)*173,iw)':y=0:w=2:h=ih:color=white@0.35:t=fill:enable='lt(mod(floor(t*24),7),2)',"
              f"drawbox=x='mod(floor(t*24)*389+60,iw)':y=0:w=1:h=ih:color=black@0.45:t=fill:enable='lt(mod(floor(t*24),5),1)'")
    elif kind == "vhs":
        chain(f"rgbashift=rh=-{max(2, W // 260)}:bh={max(2, W // 260)},eq=saturation={1.2 + 0.3 * I:.2f}:contrast=1.08,"
              f"noise=alls={int(8 + 14 * I)}:allf=t,gblur=sigma=0.7,"
              f"drawgrid=w=iw:h={max(3, H // 480)}:t=1:c=black@{0.15 + 0.2 * I:.2f},"
              f"drawbox=x=0:y='mod(t*{H * 0.3:.0f},ih)':w=iw:h={H // 22}:color=white@{0.08 + 0.1 * I:.2f}:t=fill")
    elif kind == "motionblur":
        chain(f"tmix=frames={int(3 + 6 * I)}")
    elif kind == "dirblur":
        chain(f"dblur=angle={float(p.get('angle', 0)):.0f}:radius={10 + 50 * I:.0f}")
    elif kind == "defocus":
        chain(f"gblur=sigma={3 + 14 * I:.1f}")
    elif kind in ("shake", "quake", "punch"):
        if kind == "shake":
            z, A = 1.06, W * 0.012 * (0.5 + I)
            fx_ = f"sin(t*7)*{A:.1f}+sin(t*13)*{A / 2:.1f}"
            fy_ = f"cos(t*9)*{A:.1f}+sin(t*5)*{A / 3:.1f}"
        elif kind == "quake":
            z, A = 1.12, W * 0.03 * (0.4 + I)
            fx_ = f"(sin(t*47)+0.6*sin(t*83)+0.3*sin(t*131))*{A:.1f}*0.55"
            fy_ = f"(cos(t*53)+0.5*sin(t*97))*{A:.1f}*0.55"
        else:
            z, A = 1.12, W * 0.045 * (0.4 + I)
            fx_ = f"exp(-t*7)*sin(t*55)*{A:.1f}"
            fy_ = f"exp(-t*7)*cos(t*48)*{A * 0.7:.1f}"
        zw, zh = int(W * z) // 2 * 2, int(H * z) // 2 * 2
        chain(f"scale={zw}:{zh},crop={W}:{H}:x='({zw}-{W})/2+{fx_}':y='({zh}-{H})/2+{fy_}'")
    elif kind == "posterize":
        lv = max(2, int(6 - 4 * I))
        q = 256 // lv
        e = f"floor(val/{q})*{q}+{q // 2}"
        chain(f"format=rgb24,lutrgb=r='{e}':g='{e}':b='{e}',format=yuv420p")
    elif kind == "duotone":
        c0, c1 = _hex(p.get("color"), "#2B1055"), _hex(p.get("color2"), "#FF3D8B")
        ex = [f"{c0[i]}+({c1[i] - c0[i]})*val/255" for i in range(3)]
        chain(f"hue=s=0,eq=contrast={1 + 0.3 * I:.2f},format=rgb24,lutrgb=r='{ex[0]}':g='{ex[1]}':b='{ex[2]}',format=yuv420p")
    elif kind == "halftone":
        k = 0.75 - 0.45 * I
        chain(f"format=gray,geq=lum='if(gt(lum(X,Y),128+115*sin(X*{k:.3f})*sin(Y*{k:.3f})),245,15)',format=yuv420p")
    elif kind == "edges":
        chain(f"edgedetect=mode=colormix:high={0.25 - 0.15 * I:.2f}:low=0.05,eq=contrast=1.2")
    elif kind == "bwpop":
        chain(f"hue=s=0,eq=contrast={1.2 + 0.3 * I:.2f}:brightness=-0.03,vignette=PI/4")
    elif kind == "colorkeep":
        chain(f"format=gbrp,colorhold=color=0xE02020:similarity={0.15 + 0.25 * I:.2f}:blend=0.1,format=yuv420p")
    elif kind == "invert":
        chain("negate")
    elif kind == "symmetry":
        a, b, r2 = c.lab("ya"), c.lab("yb"), c.lab("yr")
        half = W // 2 // 2 * 2
        s.append(f"[{inp}]crop={half}:{H}:0:0,split[{a}][{b}]")
        s.append(f"[{b}]hflip[{r2}]")
        s.append(f"[{a}][{r2}]hstack,scale={W}:{H},setsar=1[{out}]")
    # ---------------- geçişler (t: geçişin başından, D: süresi, ortası kesim anı)
    elif kind == "tr_flash":
        chain(f"eq=brightness='0.95*max(0,1-abs(t-{D / 2:.3f})/{D / 2:.3f})':eval=frame")
    elif kind == "tr_dip":
        chain(f"eq=brightness='-1*max(0,1-abs(t-{D / 2:.3f})/{D / 2:.3f})':eval=frame")
    elif kind == "tr_white":
        chain(f"eq=brightness='1*max(0,1-abs(t-{D / 2:.3f})/{D / 2:.3f})':eval=frame")
    elif kind in ("tr_zoom", "tr_slide", "tr_swirl"):
        # piksel piksel hesaplanır (zoompan kullanmaz: zoompan bellekte kare biriktiriyordu)
        env = f"sin(PI*min(1,T/{D:.3f}))"
        if kind == "tr_zoom":
            Z = f"(1+0.45*{env})"
            sx, sy = f"(W/2+(X-W/2)/{Z})", f"(H/2+(Y-H/2)/{Z})"
        elif kind == "tr_slide":
            off = f"((T-{D / 2:.3f})/{D:.3f}*W*0.35)"
            sx, sy = f"(W/2+(X-W/2)/1.3+{off})", f"(H/2+(Y-H/2)/1.3)"
        else:
            Z = f"(1+0.5*{env})"
            ang = f"(1.4*{env}*(1-hypot(X-W/2,Y-H/2)/hypot(W/2,H/2)))"
            dx, dy = f"((X-W/2)/{Z})", f"((Y-H/2)/{Z})"
            sx = f"(W/2+{dx}*cos({ang})-{dy}*sin({ang}))"
            sy = f"(H/2+{dx}*sin({ang})+{dy}*cos({ang}))"
        cx, cy = f"clip({sx},0,W-1)", f"clip({sy},0,H-1)"
        g = f"geq=lum='lum({cx},{cy})':cb='cb({cx},{cy})':cr='cr({cx},{cy})'"
        extra = f",dblur=angle=0:radius={W // 18}" if kind == "tr_slide" else (",gblur=sigma=1.5" if kind == "tr_swirl" else "")
        hw, hh = max(2, W // 4 * 2), max(2, H // 4 * 2)  # yarım çözünürlükte hesapla (4 kat hızlı)
        chain(f"scale={hw}:{hh},format=yuv444p,{g},scale={W}:{H}:flags=bicubic{extra},format=yuv420p")
    elif kind == "tr_glitch":
        return build("glitch", inp, out, D, 1.0, p, c)
    else:
        chain("null")
    return s


def timed(cur, k, a, b, kind, I, params, c):
    """[cur] videosunda yalnızca a..b saniyeleri arasında efekt uygula.
    Efekt dalı başına boş (saydam) kare eklenerek ana video ile aynı hızda ilerler,
    böylece bellekte kare birikmez."""
    m, f, fi, fo, fx, o = (f"{x}{k}" for x in ("tm", "tf", "ti", "to", "tx", "tv"))
    parts = [f"[{cur}]split[{m}][{f}]",
             f"[{f}]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS[{fi}]"]
    parts += build(kind, fi, fo, b - a, I, params or {}, c)
    pad = f",tpad=start_duration={a:.3f}:color=black" if a > 0.001 else ""
    parts.append(f"[{fo}]setsar=1,fps={c.fps:g},format=yuv420p{pad}[{fx}]")
    parts.append(f"[{m}][{fx}]overlay=eof_action=pass:repeatlast=0:enable='between(t,{a:.3f},{b - 0.001:.3f})'[{o}]")
    return parts, o
