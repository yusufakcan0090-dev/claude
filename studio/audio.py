"""Ferman Tarih ses motoru: kodla üretilen sinematik müzik + ses efektleri, seslendirmeyle karıştırma.

Telifsiz: her şey burada sentezlenir. Kullanım (örnek):
    from audio import score, mix
    music = score(total, starts=[...], impacts=[(t, guc), ...], drop_at=t_son, final_hit=t_hit, seed=1)
    mix("vo.mp3", music, "out.m4a")   # seslendirmeyi müzikle karıştırır (konuşurken müzik kısılır)
"""
import subprocess
import numpy as np
from scipy import signal

SR = 48000

def _t(n): return np.arange(n) / SR

def _env(n, a, r):
    e = np.ones(n); ai, ri = int(a * SR), int(r * SR)
    if ai: e[:ai] = np.linspace(0, 1, ai)
    if ri: e[-ri:] *= np.linspace(1, 0, ri)
    return e

def _lp(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), "low"); return signal.lfilter(b, a, x)

def _bp(x, lo, hi, order=2):
    b, a = signal.butter(order, [lo / (SR / 2), hi / (SR / 2)], "band"); return signal.lfilter(b, a, x)

def _saw(f, n, ph=0.0):
    return 2 * ((_t(n) * f + ph) % 1.0) - 1

# ---------- building blocks ----------
def drone(n, root=73.42, rng=None):
    """Low dark bed: root + fifth + octave, slow beating and filter breathing."""
    t = _t(n); x = np.zeros(n)
    for mult, amp in [(1, 0.5), (1.5, 0.22), (2, 0.25), (0.5, 0.3)]:
        for det in (-0.35, 0.35):
            x += amp * np.sin(2 * np.pi * (root * mult + det) * t + rng.uniform(0, 6.28))
    pad = sum(_saw(root * m * (1 + d), n, rng.uniform()) for m in (2, 3) for d in (-0.003, 0.003))
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * t)
    pad = _lp(pad, 380) * (0.10 + 0.08 * lfo)
    return (x * 0.18 + pad) * (0.85 + 0.15 * np.sin(2 * np.pi * 0.11 * t))

def chord_pad(n, freqs, rng):
    t = _t(n); x = np.zeros(n)
    for f in freqs:
        for det in (-0.004, 0.0, 0.004):
            x += np.sin(2 * np.pi * f * (1 + det) * t + rng.uniform(0, 6.28)) * (1 + 0.3 * np.sin(2 * np.pi * 3.0 * f / 440 * t))
    x = _lp(x, 1400) / (len(freqs) * 3)
    return x

def boom(strength=1.0, dur=2.2):
    """Cinematic low hit: pitch-dropping sine + body thump + noise crack."""
    n = int(dur * SR); t = _t(n)
    f = 38 + 90 * np.exp(-t * 9)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 2.4)
    noise = np.random.default_rng(int(strength * 100)).normal(size=n)
    crack = _bp(noise, 150, 2500) * np.exp(-t * 28) * 0.6
    tail = _lp(noise, 200) * np.exp(-t * 3.5) * 0.25
    return (body * 0.9 + crack + tail) * strength

def whoosh(dur=0.9, rng=None, up=True):
    n = int(dur * SR); t = _t(n)
    noise = rng.normal(size=n)
    shape = np.sin(np.pi * t / dur) ** 2
    sweep = np.linspace(300, 3000, n) if up else np.linspace(3000, 300, n)
    out = np.zeros(n); seg = 2400
    for i in range(0, n, seg):
        f = sweep[min(i + seg // 2, n - 1)]
        out[i:i + seg] = _bp(noise[i:i + seg], f * 0.6, min(f * 1.6, 20000))
    return out * shape * 0.35

def rustle(dur=1.2, rng=None):
    n = int(dur * SR); out = np.zeros(n)
    for _ in range(int(dur * 22)):
        p = rng.integers(0, n - 2000); ln = rng.integers(300, 1800)
        g = _bp(rng.normal(size=ln), 1500, 7000) * np.hanning(ln) * rng.uniform(0.1, 0.35)
        out[p:p + ln] += g
    return out

def pulse_track(n, start, stop, period, rng):
    """Soft low drum pulse (heartbeat-like) between start and stop."""
    out = np.zeros(n); k = boom(0.22, 0.9)
    tt = start
    while tt < stop:
        i = int(tt * SR); seg = k[: max(0, min(len(k), n - i))]
        out[i:i + len(seg)] += seg * (0.6 + 0.4 * min(1, (tt - start) / 6))
        tt += period
    return out

def score(total, starts=(), impacts=(), drop_at=None, final_hit=None, seed=1, root=73.42, pulse=True):
    """Return stereo float32 music+sfx bed of `total` seconds.
    starts: scene start times (whoosh), impacts: [(time, strength 0..1.5)], drop_at: music fades out
    here (dramatic silence before the last line), final_hit: one last boom."""
    rng = np.random.default_rng(seed)
    n = int(total * SR)
    bed = drone(n, root, rng) + chord_pad(n, [root * 4, root * 4 * 1.189, root * 6], rng) * 0.10
    # gentle intro fade, and the drop
    env = np.ones(n); fi = int(1.5 * SR); env[:fi] = np.linspace(0, 1, fi)
    if drop_at is not None:
        d0 = int(max(0, drop_at - 0.8) * SR); d1 = int(drop_at * SR)
        env[d0:d1] *= np.linspace(1, 0.12, d1 - d0); env[d1:] *= 0.12
    bed *= env
    fx = np.zeros(n)
    if pulse:
        fx += pulse_track(n, 3.0, (drop_at or total) - 1.0, 1.65, rng)
    fx[: int(1.2 * SR)] += rustle(1.2, rng)
    for s in starts:
        if s <= 0.3: continue
        w = whoosh(0.8, rng); i = int(max(0, s - 0.45) * SR); seg = w[: max(0, n - i)]
        fx[i:i + len(seg)] += seg
    for tt, st in impacts:
        b = boom(st); i = int(tt * SR); seg = b[: max(0, n - i)]
        fx[i:i + len(seg)] += seg * 0.55
    if final_hit is not None:
        b = boom(1.4, 3.5); i = int(final_hit * SR); seg = b[: max(0, n - i)]
        fx[i:i + len(seg)] += seg * 0.7
    mono = bed * 0.55 + fx
    # simple stereo width: delayed, filtered copy
    d = int(0.012 * SR)
    left = mono; right = np.concatenate([np.zeros(d), mono[:-d]]) * 0.92 + _lp(mono, 900) * 0.08
    st = np.stack([left, right], 1)
    st /= max(1e-6, np.abs(st).max()) / 0.9
    return st.astype(np.float32)

def _decode(path, ch=1):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "f32le", "-ac", str(ch), "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, ch)

def mix(voice_path, music, out_path, music_db=-13.0, duck_db=-9.0):
    """Mix voice over music; music is ducked while the voice speaks. Writes AAC (.m4a)."""
    v = _decode(voice_path, 1)[:, 0]
    n = max(len(v), len(music))
    v = np.pad(v, (0, n - len(v))); m = np.pad(music, ((0, n - len(music)), (0, 0)))
    # voice envelope -> ducking gain
    e = np.abs(v); e = _lp(e, 6, 1)
    on = (e > 0.02).astype(np.float64)
    on = _lp(on, 3, 1)  # smooth attack/release
    on = np.clip(on * 1.4, 0, 1)
    g = 10 ** ((music_db + duck_db * on) / 20)
    out = m * g[:, None] + v[:, None] * 0.95
    out /= max(1.0, np.abs(out).max() / 0.98)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", out_path],
                   input=out.astype(np.float32).tobytes(), check=True)
    return out_path
