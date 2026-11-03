"""Kaydırmalı gönderi: Hayalet Ordu (ABD 23. Karargâh Özel Birlikleri, 1944-45). Tasarım: dosya.py ("GİZLİ DOSYA")."""
import os
from PIL import Image, ImageDraw
import dosya as D
from dosya import W, H, RED, INK, CREAM, MARKER, MUTED, F, F_BLACK, F_BOLD, F_MONO, F_MONOB

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "posts", "2026-11-07_hayalet_ordu_v2")
N = 8
OLIVE = (92, 98, 62)

# ---------- drawings ----------
def tank(d, cx, cy, s=1.0, col=OLIVE, a=255):
    c = col + (a,); k = INK + (a,)
    d.rounded_rectangle([cx - 230 * s, cy - 10 * s, cx + 230 * s, cy + 80 * s], int(40 * s), fill=c, outline=k, width=max(2, int(5 * s)))
    d.rounded_rectangle([cx - 110 * s, cy - 90 * s, cx + 90 * s, cy], int(30 * s), fill=c, outline=k, width=max(2, int(5 * s)))
    d.rectangle([cx + 80 * s, cy - 60 * s, cx + 300 * s, cy - 38 * s], fill=c, outline=k, width=max(2, int(4 * s)))
    for i in range(6):
        x = cx - 175 * s + i * 70 * s
        d.ellipse([x - 28 * s, cy + 40 * s, x + 28 * s, cy + 96 * s], fill=(60, 60, 50, a), outline=k, width=max(2, int(4 * s)))
    d.rectangle([cx - 20 * s, cy - 130 * s, cx - 4 * s, cy - 90 * s], fill=k)          # valve stem
    d.ellipse([cx - 32 * s, cy - 150 * s, cx + 8 * s, cy - 122 * s], outline=k, width=max(2, int(5 * s)))

def tank_art():
    a = D.art_canvas(620, 520, (196, 204, 188)); d = ImageDraw.Draw(a, "RGBA")
    d.rectangle([0, 380, 620, 520], fill=(150, 160, 120, 255))
    tank(d, 300, 330, 0.95)
    d.text((470, 190), "hava valfi", font=F(F_MONO, 26), fill=INK + (255,))
    d.line([(465, 205), (300, 185)], fill=INK + (255,), width=3)
    return a

def speaker_art():
    a = D.art_canvas(420, 340, (200, 196, 184)); d = ImageDraw.Draw(a, "RGBA"); cx, cy = 150, 170
    d.rectangle([cx - 90, cy - 50, cx - 20, cy + 50], fill=INK + (255,))
    d.polygon([(cx - 20, cy - 50), (cx + 70, cy - 120), (cx + 70, cy + 120), (cx - 20, cy + 50)], fill=INK + (255,))
    for i, r in enumerate((90, 150, 210)):
        d.arc([cx + 70 - r, cy - r, cx + 70 + r, cy + r], -40, 40, fill=RED + (255 - i * 60,), width=12)
    return a

def radio_art():
    a = D.art_canvas(620, 480, (204, 198, 184)); d = ImageDraw.Draw(a, "RGBA"); cx, cy = 280, 290
    d.rounded_rectangle([cx - 190, cy - 100, cx + 190, cy + 120], 22, fill=(70, 62, 50, 255), outline=INK + (255,), width=6)
    for i in range(5):
        d.ellipse([cx - 160 + i * 48, cy - 60, cx - 126 + i * 48, cy - 26], fill=(222, 180, 96, 255))
    d.rectangle([cx - 160, cy + 6, cx + 160, cy + 80], fill=(30, 26, 20, 255))
    d.text((cx, cy + 43), "•–•  ––•  •••", font=F(F_MONOB, 38), fill=(222, 180, 96, 255), anchor="mm")
    d.line([(cx + 140, cy - 100), (cx + 210, cy - 220)], fill=INK + (255,), width=8)
    for i, r in enumerate((40, 75, 110)):
        d.arc([cx + 210 - r, cy - 220 - r, cx + 210 + r, cy - 220 + r], 200, 340, fill=RED + (255 - i * 60,), width=8)
    return a

# ---------- slides ----------
def s1():
    b = D.dark_bg(1)
    D.kicker(b, "Gizli dosya · 1944", 70, 110)
    D.big_title(b, ["ŞİŞME", "TANKLARLA", "SAVAŞAN", "BİR ORDU"], 70, 190, size=124,
                colors=[CREAM, CREAM, RED, RED])
    f = D.folder(880, 400, "DOSYA No. 23")
    pol = D.polaroid(tank_art(), 440, 369, caption=None, seed=6)
    f.alpha_composite(pol.rotate(4, resample=Image.BICUBIC, expand=True), (390, 20))
    D.place(b, f, 60, 740, rot=-3)
    D.place(b, D.stamp("ÇOK GİZLİ", 76, rot=-14), 90, 880, sh=False)
    D.footer(b, 1, N)
    return b

def paper_slide(page, label, seed):
    b = D.dark_bg(seed, glow=(60, 40, 20)); D.header(b, page, N, label, dark=True)
    p = D.paper_tex(960, 1090, D.PAPER, seed + 7)
    return b, p

def put_paper(b, p, page, rot=-1.2):
    D.place(b, p, 50, 120, rot=rot)
    D.footer(b, page, N)
    return b

def s2():
    b, p = paper_slide(2, "Dosya 23 · Kim bunlar?", 2)
    d = ImageDraw.Draw(p, "RGBA")
    d.text((70, 70), "23. KARARGÂH", font=F(F_BLACK, 64), fill=INK + (255,))
    d.text((70, 140), "ÖZEL BİRLİKLERİ", font=F(F_BLACK, 64), fill=INK + (255,))
    d.rectangle([70, 222, 330, 232], fill=RED + (255,))
    d.text((70, 270), "1.100", font=F(F_BLACK, 230), fill=RED + (255,))
    d.text((640, 430), "asker", font=F(F_BOLD, 56), fill=INK + (255,))
    D.rich_text(p, "Ocak 1944'te kuruldu. Görevleri savaşmak değil, düşmanı **kandırmaktı.**", 70, 560, 820, size=42)
    D.rich_text(p, "Saflarında **ressamlar**, tasarımcılar ve ses uzmanları vardı. Biri ileride ünlü moda tasarımcısı **Bill Blass** olacaktı.", 70, 780, 820, size=40)
    D.paperclip(p, 820, -30)
    return put_paper(b, p, 2)

def s3():
    b, p = paper_slide(3, "Silah 01 · Lastik", 3)
    d = ImageDraw.Draw(p, "RGBA")
    d.text((70, 70), "SİLAH 01", font=F(F_MONOB, 34), fill=RED + (255,))
    d.text((70, 115), "LASTİK TANKLAR", font=F(F_BLACK, 76), fill=INK + (255,))
    pol = D.polaroid(tank_art(), 560, 470, caption="şişme tank, gerçek boyutta", seed=8)
    p.alpha_composite(pol.rotate(-3, resample=Image.BICUBIC, expand=True), (150, 230))
    D.rich_text(p, "Lastikten **şişme tanklar** ve toplar. Hava kompresörleriyle şişiriliyor, uzaktan gerçeğinden ayırt etmek çok zordu.", 70, 850, 820, size=38)
    return put_paper(b, p, 3, rot=1.0)

def s4():
    b = D.dark_bg(4); D.header(b, 4, N, "Silah 02 · Ses", dark=True)
    d = ImageDraw.Draw(b, "RGBA")
    d.text((70, 150), "SİLAH 02", font=F(F_MONOB, 34), fill=RED + (255,))
    d.text((70, 195), "SAHTE SESLER", font=F(F_BLACK, 84), fill=CREAM + (255,))
    fb = F(F_BLACK, 380); d.text((60, 330), "24", font=fb, fill=RED + (255,))
    x2 = 60 + fb.getlength("24") + 30
    d.text((x2, 720), "KM", font=F(F_BLACK, 150), fill=RED + (255,), anchor="ls")
    pol = D.polaroid(speaker_art(), 250, 202, seed=10)
    D.place(b, pol, 770, 110, rot=6)
    D.rich_text(b, "Araçlara bağlı dev hoparlörler, önceden kaydedilmiş tank, kamyon ve inşaat seslerini çaldı. Bu sesler **24 kilometre** öteden duyulabiliyordu.", 70, 800, 940, size=40, color=CREAM)
    D.rich_text(b, "Gece karanlığında bütün bir tümen yürüyormuş gibi.", 70, 1080, 940, size=36, color=MUTED, path=F_MONO)
    D.footer(b, 4, N)
    return b

def s5():
    b, p = paper_slide(5, "Silah 03 · Telsiz", 5)
    d = ImageDraw.Draw(p, "RGBA")
    d.text((70, 70), "SİLAH 03", font=F(F_MONOB, 34), fill=RED + (255,))
    d.text((70, 115), "SAHTE TELSİZ", font=F(F_BLACK, 80), fill=INK + (255,))
    pol = D.polaroid(radio_art(), 520, 400, seed=11)
    p.alpha_composite(pol.rotate(3, resample=Image.BICUBIC, expand=True), (170, 240))
    y = D.rich_text(p, "Telsizciler, Almanların dinlediğini bildikleri kanallara **sahte emirler** yolladı.", 70, 740, 820, size=38)
    D.rich_text(p, "Bazıları başka birliklerin telsizcilerinin **mors vuruş tarzını** bile taklit edebiliyordu.", 70, y + 30, 820, size=36)
    D.paperclip(p, 840, -30)
    return put_paper(b, p, 5, rot=-1.5)

def s6():
    b, p = paper_slide(6, "Mart 1945 · Ren Nehri", 6)
    d = ImageDraw.Draw(p, "RGBA")
    d.text((70, 70), "EN BÜYÜK BLÖF", font=F(F_BLACK, 84), fill=INK + (255,))
    # sketch map
    d.rectangle([70, 190, 890, 600], fill=(226, 220, 204, 255), outline=INK + (255,), width=3)
    pts = [(70, 420), (240, 460), (420, 410), (600, 480), (760, 440), (890, 490)]
    d.line(pts, fill=(70, 120, 160, 255), width=44, joint="curve")
    d.text((130, 470), "REN", font=F(F_MONOB, 30), fill=(255, 255, 255, 255))
    for x in (220, 340):
        tank(d, x, 300, 0.3, a=170)
    for x, y in ((220, 290), (340, 290)):
        d.line([(x - 50, y - 40), (x + 50, y + 40)], fill=RED + (255,), width=8)
        d.line([(x - 50, y + 40), (x + 50, y - 40)], fill=RED + (255,), width=8)
    d.text((280, 215), "SAHTE", font=F(F_BLACK, 40), fill=RED + (255,), anchor="mm")
    d.line([(720, 545), (720, 500)], fill=INK + (255,), width=10)
    d.polygon([(695, 510), (745, 510), (720, 455)], fill=INK + (255,))
    d.text((720, 575), "GERÇEK GEÇİŞ", font=F(F_BLACK, 30), fill=INK + (255,), anchor="mm")
    d.text((70, 640), "600", font=F(F_BLACK, 170), fill=RED + (255,))
    d.text((440, 690), "şişme\naraç", font=F(F_BOLD, 52), fill=INK + (255,))
    D.rich_text(p, "İki tümen varmış gibi gösterdiler. Almanlar güçlerini yanlış noktaya kaydırdı; **asıl ordu nehri başka yerden geçti.**", 70, 860, 820, size=38)
    return put_paper(b, p, 6, rot=1.2)

def s7():
    b = D.dark_bg(7); D.header(b, 7, N, "Gizlilik", dark=True)
    d = ImageDraw.Draw(b, "RGBA")
    D.rich_text(b, "Savaştan sonra askerlere yemin ettirildi: kimseye **anlatmayacaklardı.**", 70, 180, 940, size=44, color=CREAM)
    d.text((W / 2, 610), "1996", font=F(F_BLACK, 300), fill=CREAM + (255,), anchor="mm")
    D.place(b, D.stamp("GİZLİLİK KALKTI", 64, rot=-10), 170, 700, sh=False)
    D.rich_text(b, "yılına kadar dosyalar gizli kaldı. 20'den fazla operasyon yaptıkları ancak o zaman öğrenildi.", 70, 920, 940, size=40, color=CREAM)
    D.rich_text(b, "2024: ABD Kongre Altın Madalyası", 70, 1120, 940, size=36, color=MUTED)
    D.footer(b, 7, N)
    return b

def s8():
    b = D.dark_bg(8, glow=(140, 20, 20)); d = ImageDraw.Draw(b, "RGBA")
    d.text((W / 2, 300), "SİZCE?", font=F(F_BLACK, 190), fill=RED + (255,), anchor="mm")
    D.rich_text(b, "Savaşta en güçlü silah hangisi: tank mı, yoksa düşmanın **inandığı yalan** mı?", 90, 470, 900, size=54, path=F_BOLD, color=CREAM, align="center")
    d.text((W / 2, 820), "Yorumlara yaz", font=F(F_MONOB, 40), fill=MUTED + (255,), anchor="mm")
    fnt = F(F_BLACK, 52); t = "TAKİP ET  @fermantarih"; tw = fnt.getlength(t)
    d.rounded_rectangle([(W - tw) / 2 - 50, 960, (W + tw) / 2 + 50, 1070], 55, fill=RED + (255,))
    d.text((W / 2, 1015), t, font=fnt, fill=(255, 255, 255, 255), anchor="mm")
    d.text((W / 2, 1140), "Kimsenin bilmediği tarih", font=F(F_BOLD, 34), fill=MUTED + (255,), anchor="mm")
    return b

if __name__ == "__main__":
    paths = D.save_all([s1(), s2(), s3(), s4(), s5(), s6(), s7(), s8()], OUT)
    print(D.contact_sheet(paths, os.path.join(OUT, "..", "_onizleme_hayalet_ordu.png")))
