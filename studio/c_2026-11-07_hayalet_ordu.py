"""Kaydırmalı gönderi: Hayalet Ordu (ABD 23. Karargâh Özel Birlikleri, 1944-45)."""
import os, sys
from PIL import Image, ImageDraw
import carousel as C
from carousel import W, H, GOLD
from make import INK, RED, CREAM, font, FB, FI, spaced_text

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "posts", "2026-11-07_hayalet_ordu")
OLIVE = (92, 98, 62)

def tank(d, cx, cy, s=1.0, col=OLIVE, a=255):
    c = col + (a,); k = INK + (a,)
    d.rounded_rectangle([cx - 230 * s, cy - 10 * s, cx + 230 * s, cy + 80 * s], int(40 * s), fill=c, outline=k, width=5)
    d.rounded_rectangle([cx - 110 * s, cy - 90 * s, cx + 90 * s, cy], int(30 * s), fill=c, outline=k, width=5)
    d.rectangle([cx + 80 * s, cy - 60 * s, cx + 300 * s, cy - 38 * s], fill=c, outline=k, width=4)
    for i in range(6):
        x = cx - 175 * s + i * 70 * s
        d.ellipse([x - 28 * s, cy + 40 * s, x + 28 * s, cy + 96 * s], fill=(60, 60, 50, a), outline=k, width=4)

def valve(d, cx, cy, s=1.0):
    d.rectangle([cx - 10 * s, cy - 40 * s, cx + 10 * s, cy], fill=INK + (255,))
    d.ellipse([cx - 22 * s, cy - 60 * s, cx + 22 * s, cy - 30 * s], outline=INK + (255,), width=5)

def speaker(d, cx, cy):
    d.rectangle([cx - 120, cy - 60, cx - 40, cy + 60], fill=INK + (255,))
    d.polygon([(cx - 40, cy - 60), (cx + 60, cy - 140), (cx + 60, cy + 140), (cx - 40, cy + 60)], fill=INK + (255,))
    for i, r in enumerate((120, 200, 280)):
        d.arc([cx + 60 - r, cy - r, cx + 60 + r, cy + r], -40, 40, fill=RED + (255 - i * 60,), width=12)

def radio(d, cx, cy):
    d.rounded_rectangle([cx - 170, cy - 90, cx + 170, cy + 110], 20, fill=(70, 62, 50, 255), outline=INK + (255,), width=6)
    for i in range(5):
        d.ellipse([cx - 140 + i * 44, cy - 50, cx - 110 + i * 44, cy - 20], fill=GOLD + (255,))
    d.rectangle([cx - 140, cy + 10, cx + 140, cy + 70], fill=(30, 26, 20, 255))
    d.line([(cx + 120, cy - 90), (cx + 180, cy - 200)], fill=INK + (255,), width=8)
    for i, r in enumerate((40, 75, 110)):
        d.arc([cx + 180 - r, cy - 200 - r, cx + 180 + r, cy - 200 + r], 200, 340, fill=RED + (255 - i * 60,), width=8)
    d.text((cx, cy + 40), "•–•  ––•  •••", font=font(FB, 34), fill=GOLD + (255,), anchor="mm")

def s1():
    s = C.slide(dark=True, seed=1); s._dark = True; d = ImageDraw.Draw(s, "RGBA")
    tank(d, W / 2, 760, 1.3, col=(80, 86, 56), a=90)
    tank(d, W / 2 - 40, 700, 1.0, col=(92, 98, 62), a=255)
    valve(d, W / 2 - 40, 610, 1.0)
    C.heading(s, "1944'te Amerika'nın", 200, size=60, color=CREAM)
    C.heading(s, "tankları şişme olan", 280, size=60, color=CREAM)
    C.heading(s, "bir ordusu vardı.", 360, size=60, color=CREAM)
    C.stamp(s, ["HAYALET ORDU"], W / 2, 1030, w=820, h=190, sizes=[104], rot=-4, seed=3)
    C.text_block(s, "Ve Almanları defalarca kandırdı.", 1150, size=40, color=(230, 215, 185), f=FI)
    return s

def s2():
    s = C.slide(seed=2); d = ImageDraw.Draw(s, "RGBA")
    C.heading(s, "23. KARARGÂH ÖZEL BİRLİKLERİ", 130, size=50, color=RED, sp=2)
    C.stamp(s, ["~1.100 ASKER"], W / 2, 400, w=700, h=170, col=INK, sizes=[96], seed=4)
    y = C.text_block(s, "Ocak 1944'te kuruldu. Görevi savaşmak değil, düşmanı KANDIRMAKTI.", 560, size=50)
    C.text_block(s, "Saflarında ressamlar, tasarımcılar ve ses uzmanları vardı. Biri ileride ünlü moda tasarımcısı Bill Blass olacaktı.", y + 40, size=44, f=FI)
    return s

def s3():
    s = C.slide(seed=5); d = ImageDraw.Draw(s, "RGBA")
    C.heading(s, "1. SİLAH: LASTİK", 130, size=70, color=RED)
    tank(d, W / 2 - 40, 470, 1.15)
    valve(d, W / 2 - 40, 366, 1.1)
    d.line([(W / 2 - 20, 320), (W / 2 + 120, 260)], fill=INK + (255,), width=4)
    d.text((W / 2 + 130, 258), "hava valfi", font=font(FI, 36), fill=INK + (255,), anchor="lm")
    C.text_block(s, "Lastikten şişme tanklar ve toplar. Hava kompresörleriyle şişiriliyor, uzaktan gerçeğinden ayırt etmek çok zordu.", 700, size=48)
    C.text_block(s, "Düşman keşif uçakları yukarıdan koca bir zırhlı birlik görüyordu.", 1000, size=42, f=FI)
    return s

def s4():
    s = C.slide(seed=6); d = ImageDraw.Draw(s, "RGBA")
    C.heading(s, "2. SİLAH: SES", 130, size=70, color=RED)
    speaker(d, W / 2 - 60, 440)
    C.stamp(s, ["24 KM"], W / 2, 690, w=420, h=150, sizes=[92], rot=3, seed=7)
    C.text_block(s, "Zırhlı araçlara bağlı dev hoparlörler, önceden kaydedilmiş tank, kamyon ve inşaat seslerini çaldı.", 800, size=46)
    C.text_block(s, "Bu sesler 24 kilometre öteden duyulabiliyordu. Gece karanlığında bütün bir tümen yürüyormuş gibi.", 1030, size=42, f=FI)
    return s

def s5():
    s = C.slide(seed=8); d = ImageDraw.Draw(s, "RGBA")
    C.heading(s, "3. SİLAH: SAHTE TELSİZ", 130, size=62, color=RED)
    radio(d, W / 2 - 40, 560)
    C.text_block(s, "Telsizciler, Almanların dinlediğini bildikleri kanallara sahte emirler yolladı.", 760, size=46)
    C.text_block(s, "Bazıları başka birliklerin telsizcilerinin mors vuruş tarzını bile taklit edebiliyordu; birlik gitmiş olsa da hâlâ oradaymış gibi.", 960, size=42, f=FI)
    return s

def s6():
    s = C.slide(seed=9); d = ImageDraw.Draw(s, "RGBA")
    C.heading(s, "EN BÜYÜK BLÖF", 130, size=70, color=RED)
    C.heading(s, "Mart 1945 · Ren Nehri", 230, size=44, color=INK, sp=2)
    # river and arrows
    pts = [(120, 520), (300, 560), (480, 520), (640, 580), (820, 540), (960, 590)]
    d.line(pts, fill=(70, 120, 160, 255), width=40, joint="curve")
    for x in (260, 420):
        tank(d, x, 400, 0.35, col=OLIVE, a=140)
    d.text((340, 330), "SAHTE", font=font(FB, 40), fill=RED + (255,), anchor="mm")
    d.line([(760, 760), (760, 600)], fill=INK + (255,), width=10)
    d.polygon([(735, 610), (785, 610), (760, 560)], fill=INK + (255,))
    d.text((760, 800), "GERÇEK GEÇİŞ", font=font(FB, 36), fill=INK + (255,), anchor="mm")
    C.text_block(s, "600 şişme araçla iki tümen varmış gibi gösterdiler. Almanlar güçlerini yanlış noktaya kaydırdı; asıl ordu nehri başka yerden geçti.", 900, size=44)
    return s

def s7():
    s = C.slide(seed=10); d = ImageDraw.Draw(s, "RGBA")
    C.heading(s, "20'DEN FAZLA OPERASYON", 130, size=58, color=RED, sp=2)
    C.stamp(s, ["ÇOK GİZLİ"], W / 2, 420, w=640, h=170, sizes=[100], rot=-8, seed=11)
    C.text_block(s, "Savaştan sonra askerlere yemin ettirildi: kimseye anlatmayacaklardı.", 600, size=48)
    C.stamp(s, ["1996"], W / 2 - 180, 900, w=360, h=150, col=INK, sizes=[96], rot=4, seed=12)
    C.text_block(s, "yılına kadar dosyalar gizli kaldı.", 1000, size=46, f=FI)
    C.text_block(s, "2024'te birliğe ABD Kongre Altın Madalyası verildi.", 1110, size=40)
    return s

def s8():
    s = C.slide(dark=True, seed=13); s._dark = True
    C.heading(s, "SİZCE?", 330, size=110, color=GOLD, sp=10)
    C.text_block(s, "Savaşta en güçlü silah hangisi: tank mı, yoksa düşmanın inandığı yalan mı?", 520, size=56, color=CREAM, f=FB)
    C.text_block(s, "Yorumlara yaz", 820, size=48, color=(230, 215, 185), f=FI)
    C.text_block(s, "Daha fazla unutulmuş tarih için takip et", 1010, size=38, color=(200, 190, 170))
    C.heading(s, "@fermantarih", 1080, size=52, color=GOLD, sp=2)
    return s

if __name__ == "__main__":
    paths = C.save_all([s1(), s2(), s3(), s4(), s5(), s6(), s7(), s8()], OUT)
    print("\n".join(paths))
