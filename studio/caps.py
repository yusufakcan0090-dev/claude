import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1920
F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 50)
BOTTOM = 1600  # caption box bottom edge (above Instagram's bottom UI)

def ts(s):
    h, m, r = s.split(":"); sec, ms = r.split(",")
    return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000

blocks = open(sys.argv[3] if len(sys.argv) > 3 else os.path.join(OUT, "altyazi.srt"), encoding="utf-8").read().strip().split("\n\n")
caps = []
for b in blocks:
    L = b.split("\n"); a, e = L[1].split(" --> ")
    caps.append((ts(a), ts(e), L[2:]))

inputs, filt, last = [], [], "0:v"
for i, (a, e, lines) in enumerate(caps):
    pad_x, pad_y, gap = 40, 26, 14
    words = " ".join(lines).split(); lines = []; cur = ""
    for w_ in words:
        cand = (cur + " " + w_).strip()
        if F.getlength(cand) > 860 and cur: lines.append(cur); cur = w_
        else: cur = cand
    lines.append(cur)
    widths = [F.getlength(l) for l in lines]
    lh = 58
    bw = int(max(widths) + 2 * pad_x); bh = int(len(lines) * lh + (len(lines) - 1) * gap + 2 * pad_y)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x0 = (W - bw) // 2; y0 = BOTTOM - bh
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], 22, fill=(30, 20, 12, 205))
    y = y0 + pad_y + lh / 2
    for l in lines:
        d.text((W / 2, y), l, font=F, fill=(245, 235, 211, 255), anchor="mm"); y += lh + gap
    p = os.path.join(OUT, f"cap_{i:02d}.png"); im.save(p)
    dur = e - a
    inputs += ["-loop", "1", "-t", f"{dur:.3f}", "-i", p]
    k = i + 1
    filt.append(f"[{k}:v]format=rgba,fade=in:st=0:d=0.15:alpha=1,fade=out:st={dur - 0.15:.3f}:d=0.15:alpha=1,setpts=PTS-STARTPTS+{a:.3f}/TB[c{k}]")
    filt.append(f"[{last}][c{k}]overlay=0:0:eof_action=pass[v{k}]")
    last = f"v{k}"

src, dst = sys.argv[1], sys.argv[2]
cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", src] + inputs + ["-filter_complex", ";".join(filt), "-map", f"[{last}]",
       "-map", "0:a?", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "copy", dst + ".tmp.mp4"]
subprocess.run(cmd, check=True)
os.replace(dst + ".tmp.mp4", dst)
print("ok")
