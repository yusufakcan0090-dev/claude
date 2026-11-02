"""Ferman Tarih ses motoru: kodla üretilen yumuşak müzik (Hicaz makamında telli çalgı + def), seslendirmeyle karıştırma.

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

# ---------- soft instruments (default score) ----------
HICAZ = [0, 1, 4, 5, 7, 8, 10, 12]   # semitones above the tonic: Hicaz makamı (D Eb F# G A Bb C D)

def pluck(freq, dur, bright=0.5, seed=0):
    """Karplus-Strong plucked string (ud/kanun-like), gentle attack, no harsh highs."""
    n = int(dur * SR); L = max(2, int(SR / freq))
    rng = np.random.default_rng(seed)
    exc = _lp(rng.uniform(-1, 1, L), 1500 + 2500 * bright, 1)
    x = np.zeros(n); x[:L] = exc
    a = np.zeros(L + 2); a[0] = 1; a[L] = -0.497; a[L + 1] = -0.497
    y = signal.lfilter([1.0], a, x)
    y = _lp(y, 3200, 2)
    att = int(0.004 * SR); y[:att] *= np.linspace(0, 1, att)
    return y * np.exp(-_t(n) * 1.2)

def soft_drum(strength=1.0):
    """Bendir/def-like low 'düm': soft attack, no noise crack."""
    n = int(1.2 * SR); t = _t(n)
    f = 62 + 40 * np.exp(-t * 14)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5.5)
    att = int(0.008 * SR); body[:att] *= np.linspace(0, 1, att)
    return _lp(body, 400, 2) * strength

def warm_pad(n, root, rng):
    """Very soft sine pad: tonic + fifth + octave, slow breathing."""
    t = _t(n); x = np.zeros(n)
    for mult, amp in [(1, 0.5), (1.5, 0.25), (2, 0.3)]:
        x += amp * np.sin(2 * np.pi * root * mult * t + rng.uniform(0, 6.28))
    return x * (0.75 + 0.25 * np.sin(2 * np.pi * 0.06 * t)) * 0.18

def reverb(x, secs=2.2, wet=0.28, seed=3):
    rng = np.random.default_rng(seed); n = int(secs * SR)
    ir = _lp(rng.normal(size=n), 2500, 2) * np.exp(-_t(n) * 3.0 / secs)
    ir /= np.sqrt((ir ** 2).sum())
    y = signal.fftconvolve(x, ir)[: len(x)]
    return x * (1 - wet) + y * wet

def melody(n, tonic, rng, start, stop, beat=0.95):
    """Slow plucked Hicaz phrase: random walk on the scale, phrases with rests."""
    out = np.zeros(n); tt = start; idx = 0; k = 0
    while tt < stop - 0.5:
        if k % 8 == 7:            # rest at phrase end
            tt += beat; k += 1; continue
        idx = int(np.clip(idx + rng.choice([-2, -1, -1, 0, 1, 1, 2]), 0, len(HICAZ) - 1))
        f = tonic * 2 ** (HICAZ[idx] / 12)
        note = pluck(f, 2.4, bright=rng.uniform(0.3, 0.6), seed=int(rng.integers(1e6)))
        if rng.random() < 0.3:    # occasional octave-below drone pluck
            note = note + 0.6 * pluck(tonic / 2, 2.4, 0.3, int(rng.integers(1e6)))
        i = int(tt * SR); seg = note[: max(0, n - i)]
        out[i:i + len(seg)] += seg * rng.uniform(0.55, 0.85)
        tt += beat * (2 if rng.random() < 0.25 else 1); k += 1
    return out

def score(total, starts=(), impacts=(), drop_at=None, final_hit=None, seed=1, root=73.42, pulse=True):
    """Soft, ear-friendly bed: plucked Hicaz melody + warm pad + gentle 'düm' on impacts.
    starts: unused (kept for compatibility), impacts: [(time, strength)], drop_at: music recedes here
    (silence before the last line), final_hit: one last soft düm."""
    rng = np.random.default_rng(seed)
    n = int(total * SR)
    tonic = root * 4          # e.g. 73.42 -> D4 (293.7 Hz)
    stop = drop_at if drop_at is not None else total
    mel = melody(n, tonic, rng, 0.6, stop, beat=rng.uniform(0.85, 1.05))
    pad = warm_pad(n, root * 2, rng)
    drums = np.zeros(n)
    for tt, st in impacts:
        d = soft_drum(min(1.0, 0.45 + 0.35 * st)); i = int(tt * SR); seg = d[: max(0, n - i)]
        drums[i:i + len(seg)] += seg
    if final_hit is not None:
        d = soft_drum(1.0); i = int(final_hit * SR); seg = d[: max(0, n - i)]
        drums[i:i + len(seg)] += seg
    music = reverb(mel * 0.5 + pad, wet=0.3)
    env = np.ones(n); fi = int(1.5 * SR); env[:fi] = np.linspace(0, 1, fi)
    if drop_at is not None:
        d0 = int(max(0, drop_at - 1.0) * SR); d1 = int(drop_at * SR)
        env[d0:d1] *= np.linspace(1, 0.08, d1 - d0); env[d1:] *= 0.08
    fo = int(1.2 * SR); env[-fo:] *= np.linspace(1, 0, fo)
    mono = music * env + reverb(drums, 1.2, 0.2) * 0.8
    mono = _lp(mono, 5000, 2)
    d = int(0.011 * SR)
    left = mono; right = np.concatenate([np.zeros(d), mono[:-d]])
    st = np.stack([left, right], 1)
    st /= max(1e-6, np.abs(st).max()) / 0.85
    return st.astype(np.float32)

def _decode(path, ch=1):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "f32le", "-ac", str(ch), "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, ch)

def mix(voice_path, music, out_path, music_db=-20.0, duck_db=-12.0):
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


# ---------- effects only (no music): what the channel uses ----------
def soft_whoosh(dur=0.7, seed=0):
    """Gentle air swell for scene changes: low-passed noise, slow envelope, no hiss."""
    rng = np.random.default_rng(seed); n = int(dur * SR)
    x = _lp(rng.normal(size=n), 900, 2)
    x = _bp(x, 120, 900, 1)
    return x * np.sin(np.pi * _t(n) / dur) ** 3 * 0.5

def soft_paper(dur=0.5, seed=0):
    """Short, muffled paper rustle."""
    rng = np.random.default_rng(seed); n = int(dur * SR); out = np.zeros(n)
    for _ in range(int(dur * 14)):
        p = rng.integers(0, n - 1500); ln = rng.integers(400, 1400)
        out[p:p + ln] += _bp(rng.normal(size=ln), 600, 2400) * np.hanning(ln) * rng.uniform(0.05, 0.15)
    return out

def effects(total, starts=(), impacts=(), final_hit=None, seed=1):
    """Soft sound effects only: düm on stamps/impacts, air swell at scene changes, paper at the start."""
    n = int(total * SR); x = np.zeros(n)
    def put(sig, tt, g=1.0):
        i = int(max(0, tt) * SR); seg = sig[: max(0, n - i)]; x[i:i + len(seg)] += seg * g
    put(soft_paper(0.5, seed), 0.05, 1.0)
    for k, s in enumerate(starts):
        if s > 0.3: put(soft_whoosh(0.7, seed + k), s - 0.35, 1.0)
    for tt, st in impacts:
        put(soft_drum(min(1.0, 0.5 + 0.3 * st)), tt, 1.0)
    if final_hit is not None:
        put(soft_drum(1.0), final_hit, 1.0)
    x = reverb(x, 1.0, 0.15)
    x = _lp(x, 4000, 2)
    x /= max(1e-6, np.abs(x).max()) / 0.85
    return np.stack([x, x], 1).astype(np.float32)

def mix_fx(voice_path, fx, out_path, fx_db=-14.0):
    """Voice + soft effects (no ducking needed; effects sit well below the voice)."""
    v = _decode(voice_path, 1)[:, 0]
    n = max(len(v), len(fx))
    v = np.pad(v, (0, n - len(v))); f = np.pad(fx, ((0, n - len(fx)), (0, 0)))
    out = f * 10 ** (fx_db / 20) + v[:, None] * 0.95
    out /= max(1.0, np.abs(out).max() / 0.98)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", out_path],
                   input=out.astype(np.float32).tobytes(), check=True)
    return out_path
