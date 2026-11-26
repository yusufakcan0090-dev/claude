"""Videodaki heyecanlı anları ses enerjisinden bulur."""
import subprocess

import numpy as np

from core import FFMPEG, popen

SR = 8000
WIN = 0.5  # saniye


def energy_curve(job, path, duration, lo=0.0, hi=0.6):
    """Her 0.5 sn için ses seviyesi (dB) dizisi."""
    p = popen([FFMPEG, "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", str(SR),
               "-f", "s16le", "pipe:1"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    n = int(SR * WIN)
    chunk_bytes = n * 2 * 240  # 2 dakikalık parça
    out = []
    rest = b""
    done = 0
    while True:
        if job and job.cancelled:
            p.kill()
            raise RuntimeError("İptal edildi")
        buf = p.stdout.read(chunk_bytes)
        if not buf:
            break
        buf = rest + buf
        usable = len(buf) - (len(buf) % (n * 2))
        rest = buf[usable:]
        a = np.frombuffer(buf[:usable], dtype=np.int16).astype(np.float32) / 32768.0
        a = a.reshape(-1, n)
        rms = np.sqrt(np.mean(a * a, axis=1) + 1e-10)
        out.append(20 * np.log10(rms))
        done += usable / 2 / SR
        if job and duration:
            job.set(lo + (hi - lo) * min(1, done / duration),
                    f"Ses analiz ediliyor %{int(min(1, done / duration) * 100)}")
    p.wait()
    if not out:
        raise RuntimeError("Videoda ses bulunamadı")
    return np.concatenate(out)


def _smooth(x, k):
    if k <= 1:
        return x
    ker = np.ones(k) / k
    return np.convolve(x, ker, mode="same")


def _rolling_median(x, k):
    if len(x) <= k:
        return np.full_like(x, np.median(x))
    from numpy.lib.stride_tricks import sliding_window_view
    pad = k // 2
    xp = np.pad(x, (pad, k - pad - 1), mode="edge")
    # hız için 4'lü adımlarla hesapla, sonra genişlet
    win = sliding_window_view(xp, k)[::4]
    med = np.median(win, axis=1)
    return np.repeat(med, 4)[: len(x)]


MODES = {
    "kisa": {"before": 7, "after": 4, "max_len": 20, "ext": 6},
    "orta": {"before": 18, "after": 8, "max_len": 40, "ext": 12},
    "uzun": {"before": 40, "after": 15, "max_len": 90, "ext": 25},
}


def find_moments(db, duration, before=20, after=10, max_count=20, max_len=40, ext=20):
    """max_count=0 -> sınırsız (belirgin olan bütün anlar)."""
    db = np.maximum(db, -70)
    sm = _smooth(db, 3)
    base = _rolling_median(db, 120)            # 60 sn'lik ortam sesi
    excite = sm - base                         # ortama göre ne kadar yükseldi
    loud = sm - np.median(db)
    raw = excite + 0.35 * loud
    raw_s = _smooth(raw, 5)

    win_sec = WIN
    gap = int((before + after) / win_sec)      # anlar üst üste binmesin
    scores = raw_s.copy()
    picks = []
    unlimited = not max_count
    thr = np.percentile(raw_s, 85 if unlimited else 75)
    limit = 400 if unlimited else max_count
    while len(picks) < limit:
        i = int(np.argmax(scores))
        if scores[i] <= thr or scores[i] == -np.inf:
            break
        picks.append(i)
        scores[max(0, i - gap): i + gap] = -np.inf

    if not picks:
        return [], _curve(raw_s)
    vals = np.array([raw_s[i] for i in picks])
    top, floor = vals.max(), thr
    moments = []
    for i in picks:
        t = i * win_sec
        # yükselişin başladığı yeri bul (en fazla 'before' sn geri)
        start = max(0.0, t - before)
        end = min(duration or t + after, t + after)
        # yüksek ses devam ediyorsa sonu uzat (en fazla +20 sn)
        j = i
        lim = min(len(excite) - 1, i + int(ext / win_sec))
        while j < lim and excite[j] > 4:
            j += 1
        end = min(duration or end, max(end, j * win_sec + 2))
        if end - start > max_len:  # çok uzun olmasın: zirveyi ortada tut
            start = max(0.0, min(start, t - max_len * 0.6))
            end = start + max_len
        peak = float(excite[max(0, i - 2): i + 3].max())
        sustained = float((excite[max(0, i - 20): i + 20] > 5).sum() * win_sec)
        if peak > 13:
            label = "Patlama"
        elif sustained > 8:
            label = "Uzun heyecan"
        elif peak > 7:
            label = "Ses yükselmesi"
        else:
            label = "Hareketli an"
        score = 45 + 55 * (raw_s[i] - floor) / max(1e-6, top - floor)
        moments.append({
            "id": f"m{i}",
            "peak": round(t, 2),
            "start": round(start, 2),
            "end": round(end, 2),
            "score": int(round(max(1, min(100, score)))),
            "label": label,
        })
    moments.sort(key=lambda m: -m["score"])
    return moments, _curve(raw_s)


def _curve(x, n=700):
    if len(x) == 0:
        return []
    idx = np.linspace(0, len(x), n + 1).astype(int)
    c = np.array([x[a:b].max() if b > a else x[min(a, len(x) - 1)] for a, b in zip(idx[:-1], idx[1:])])
    lo, hi = np.percentile(c, 5), c.max()
    c = (c - lo) / max(1e-6, hi - lo)
    return [round(float(v), 3) for v in np.clip(c, 0, 1)]


def waveform(path, n=1600):
    n = int(n)
    """Editör timeline'ı için dalga formu (0-1)."""
    p = popen([FFMPEG, "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", "4000",
               "-f", "s16le", "pipe:1"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    data, _ = p.communicate()
    a = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
    if len(a) == 0:
        return []
    idx = np.linspace(0, len(a), n + 1).astype(int)
    peaks = np.array([np.abs(a[x:y]).max() if y > x else 0 for x, y in zip(idx[:-1], idx[1:])])
    m = peaks.max() or 1
    return [round(float(v / m), 3) for v in peaks]
