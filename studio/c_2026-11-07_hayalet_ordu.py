"""Kaydırmalı gönderi: Hayalet Ordu (ABD 23. Karargâh Özel Birlikleri, 1944-45). Tasarım: poster.py (savaş afişi)."""
import os
from PIL import ImageDraw
import poster as P_
from poster import (W, H, S, RED, DRED, BLACK, CREAM, MUSTARD, STEEL, WHITE, F, F_BLACK, F_BOLD,
                    canvas, rays, halftone, band, title, line, tag, stamp, tank, soldier, pump,
                    halftrack_speaker, radio_tower, waves, put, footer)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "posts", "2026-11-07_hayalet_ordu_v3")
N = 8

def hose(img, pts, width=12, color=BLACK):
    ImageDraw.Draw(img).line([(x * S, y * S) for x, y in pts], fill=color + (255,), width=width * S, joint="curve")

def s1():
    im = canvas(); rays(im, 540, 1250, n=28, c1=RED, c2=DRED)
    halftone(im, (0, 820, 1080, 1180), BLACK, step=20, rmax=9, direction="down", alpha=200)
    put(im, tank(0.82, rim=STEEL, valve=True), 150, 600, shadow=BLACK)
    put(im, soldier(0.62), 40, 860)
    put(im, pump(0.62), 150, 960)
    hose(im, [(212, 966), (260, 1060), (330, 1040), (300, 840)], width=10)
    title(im, "ŞİŞME", 60, 120, size=170, color=CREAM, shadow=BLACK)
    title(im, "TANKLAR", 60, 290, size=170, color=CREAM, shadow=BLACK)
    tag(im, "1944 · HAYALET ORDU", 64, 490, size=34)
    band(im, 1180, 1350)
    line(im, "Almanları böyle kandırdılar", 540, 1215, size=46, color=CREAM, anchor="ma")
    footer(im, 1, N)
    return im

def s2():
    im = canvas(CREAM)
    halftone(im, (0, 560, 1080, 1180), RED, step=22, rmax=10, direction="down", alpha=230)
    title(im, "1.100", 540, 90, size=290, color=RED, anchor="ma")
    title(im, "ASKER", 540, 390, size=110, color=BLACK, anchor="ma")
    for i, (x, sc, pr) in enumerate([(60, 0.78, None), (250, 0.86, "brush"), (450, 0.92, None), (650, 0.86, "brush"), (840, 0.78, None)]):
        put(im, soldier(sc, prop=pr), x, 1180 - 625 * sc)
    band(im, 1180, 1350)
    line(im, "Aralarında ressamlar ve tasarımcılar vardı", 540, 1215, size=40, color=CREAM, anchor="ma")
    footer(im, 2, N)
    return im

def s3():
    im = canvas(); rays(im, 820, 300, n=30, c1=MUSTARD, c2=(214, 150, 40))
    tag(im, "SİLAH 1", 64, 90, size=34, bg=BLACK, fg=MUSTARD)
    title(im, "TANK DEĞİL,", 60, 160, size=130, color=BLACK)
    title(im, "BALON.", 60, 300, size=150, color=RED, shadow=BLACK)
    put(im, tank(0.78, rim=STEEL, valve=True), 230, 560, shadow=DRED)
    put(im, soldier(0.66), 50, 830)
    put(im, pump(0.66), 165, 935)
    hose(im, [(232, 942), (300, 1060), (380, 1020), (380, 800)], width=10)
    band(im, 1180, 1350)
    line(im, "Lastikten yapılıp hava ile şişiriliyordu", 540, 1215, size=42, color=CREAM, anchor="ma")
    footer(im, 3, N)
    return im

def s4():
    im = canvas(BLACK)
    halftone(im, (0, 0, 1080, 700), RED, step=24, rmax=10, direction="up", alpha=150)
    waves(im, 470, 860, [200, 330, 460, 590, 720], color=MUSTARD, width=16, a0=-45, a1=45)
    put(im, halftrack_speaker(0.62, color=CREAM), 60, 760)
    title(im, "24 KM", 540, 120, size=250, color=MUSTARD, anchor="ma")
    line(im, "öteden duyulan sahte tank sesleri", 540, 410, size=46, color=CREAM, anchor="ma")
    tag(im, "SİLAH 2", 64, 1130, size=34, bg=RED, fg=WHITE)
    footer(im, 4, N)
    return im

def s5():
    im = canvas(); rays(im, 540, 760, n=32, c1=CREAM, c2=(222, 208, 176))
    halftone(im, (0, 900, 1080, 1180), RED, step=20, rmax=9, direction="down", alpha=220)
    for side in (-1, 1):
        waves(im, 540, 650, [110, 190, 270], color=RED, width=16,
              a0=(-50 if side > 0 else 130), a1=(50 if side > 0 else 230))
    put(im, radio_tower(0.72), 390, 610)
    tag(im, "SİLAH 3", 64, 70, size=34, bg=BLACK, fg=CREAM)
    title(im, "SAHTE", 540, 140, size=140, color=BLACK, anchor="ma")
    title(im, "EMİRLER", 540, 280, size=110, color=RED, anchor="ma")
    band(im, 1180, 1350)
    line(im, "Almanların dinlediği telsize yalan yolladılar", 540, 1215, size=38, color=CREAM, anchor="ma")
    footer(im, 5, N)
    return im

def s6():
    im = canvas((226, 214, 186))
    d = ImageDraw.Draw(im, "RGBA")
    d.polygon([(0, 700 * S), (1080 * S, 560 * S), (1080 * S, 720 * S), (0, 860 * S)], fill=(62, 104, 140, 255))   # river
    line(im, "REN NEHRİ", 260, 745, size=34, color=CREAM, anchor="mm")
    for r in range(3):
        for c in range(5):
            put(im, tank(0.13), 60 + c * 140 + r * 30, 330 + r * 72)
    stamp(im, "SAHTE", 920, 420, size=60, rot=-12)
    put(im, tank(0.22), 440, 960)
    d = ImageDraw.Draw(im, "RGBA")
    d.polygon([(780 * S, 900 * S), (820 * S, 790 * S), (860 * S, 900 * S)], fill=RED + (255,))
    d.rectangle([806 * S, 890 * S, 834 * S, 1010 * S], fill=RED + (255,))
    line(im, "GERÇEK GEÇİŞ", 820, 1030, size=36, color=BLACK, anchor="ma")
    title(im, "600", 60, 60, size=230, color=RED)
    line(im, "şişme araç", 560, 180, size=60, color=BLACK)
    band(im, 1180, 1350)
    line(im, "Almanlar yanlış yere baktı", 540, 1215, size=46, color=CREAM, anchor="ma")
    footer(im, 6, N)
    return im

def s7():
    im = canvas(BLACK)
    halftone(im, (0, 700, 1080, 1350), RED, step=22, rmax=11, direction="down", alpha=170)
    line(im, "Dosyalar", 540, 300, size=60, color=CREAM, anchor="ma")
    title(im, "1996", 540, 380, size=300, color=CREAM, anchor="ma")
    line(im, "yılına kadar gizli kaldı", 540, 720, size=60, color=CREAM, anchor="ma")
    stamp(im, "ÇOK GİZLİ", 540, 940, size=96, rot=-10)
    footer(im, 7, N)
    return im

def s8():
    im = canvas(); rays(im, 540, 675, n=28, c1=RED, c2=DRED)
    title(im, "SİZCE?", 540, 300, size=210, color=CREAM, anchor="ma", shadow=BLACK)
    line(im, "Tank mı güçlü, yalan mı?", 540, 600, size=66, color=CREAM, anchor="ma")
    d = ImageDraw.Draw(im, "RGBA"); fnt = F(F_BLACK, 52); t = "TAKİP ET  @fermantarih"; tw = fnt.getlength(t) / S
    d.rounded_rectangle([(540 - tw / 2 - 50) * S, 880 * S, (540 + tw / 2 + 50) * S, 990 * S], 55 * S, fill=BLACK + (255,))
    d.text((540 * S, 935 * S), t, font=fnt, fill=CREAM + (255,), anchor="mm")
    line(im, "Yorumlara yaz", 540, 1050, size=40, color=CREAM, anchor="ma")
    return im

if __name__ == "__main__":
    paths = P_.save_all([s1(), s2(), s3(), s4(), s5(), s6(), s7(), s8()], OUT)
    print(P_.contact_sheet(paths, os.path.join(OUT, "..", "_onizleme_hayalet_ordu.png")))
