"""Reels kapak görseli: videonun bir karesi + altyazı bölgesini kapatan kırmızı şerit üzerinde 2 satır büyük yazı.
Kullanım: python3 studio/cover.py VIDEO SANIYE CIKTI "SATIR 1" "SATIR 2" [y0]"""
import sys, os, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "InterDisplay-Black.otf")

def make(video, t, out, lines, y0=1345, size=64):
    tmp = tempfile.mktemp(suffix=".png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", video, "-frames:v", "1", tmp], check=True)
    im = Image.open(tmp).convert("RGBA").resize((1080, 1920)); os.remove(tmp); W = 1080
    f = ImageFont.truetype(FONT, size)
    while max(f.getlength(l) for l in lines) > 900: size -= 2; f = ImageFont.truetype(FONT, size)
    hs = [f.getbbox(l)[3] - f.getbbox(l)[1] for l in lines]
    H = max(sum(hs) + 30 * (len(lines) - 1) + 90, 1625 - y0)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([50, y0 + 14, W - 50, y0 + H + 14], 28, fill=(0, 0, 0, 150))
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(14)))
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.rounded_rectangle([50, y0, W - 50, y0 + H], 28, fill=(150, 20, 30, 250))
    d.rounded_rectangle([64, y0 + 14, W - 64, y0 + H - 14], 20, outline=(240, 226, 196, 200), width=3)
    y = y0 + (H - (sum(hs) + 30 * (len(lines) - 1))) / 2
    for l, h in zip(lines, hs):
        d.text((W / 2, y - f.getbbox(l)[1]), l, font=f, fill=(250, 240, 220), anchor="ma"); y += h + 30
    Image.alpha_composite(im, ov).convert("RGB").save(out, quality=92)
    return out

if __name__ == "__main__":
    a = sys.argv[1:]
    make(a[0], float(a[1]), a[2], [a[3], a[4]], *( [int(a[5])] if len(a) > 5 else []))
