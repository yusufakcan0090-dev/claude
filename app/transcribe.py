"""Türkçe altyazı: faster-whisper (NVIDIA GPU) + yazım düzeltme."""
import os
import re
import site
import sys
import threading
from pathlib import Path

from core import load_settings, tr_lower

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "0")
os.environ.setdefault("HF_HUB_VERBOSITY", "error")

_model = None
_model_name = None
_device = None
_lock = threading.Lock()


def _add_cuda_dlls():
    """pip ile kurulan nvidia-cublas / cudnn DLL'lerini Windows'a tanıt."""
    if not sys.platform.startswith("win"):
        return
    roots = []
    try:
        roots += site.getsitepackages()
    except Exception:
        pass
    try:
        roots.append(site.getusersitepackages())
    except Exception:
        pass
    roots += [p for p in sys.path if p.endswith("site-packages")]
    seen = set()
    for r in roots:
        nv = Path(r) / "nvidia"
        if not nv.is_dir():
            continue
        for b in nv.glob("*/bin"):
            s = str(b)
            if s in seen:
                continue
            seen.add(s)
            try:
                os.add_dll_directory(s)
            except Exception:
                pass
            os.environ["PATH"] = s + os.pathsep + os.environ.get("PATH", "")


def device_info():
    try:
        _add_cuda_dlls()
        import ctranslate2
        n = ctranslate2.get_cuda_device_count()
        return {"gpu": n > 0, "count": n}
    except Exception as e:
        return {"gpu": False, "count": 0, "error": str(e)}


def get_model(job=None):
    global _model, _model_name, _device
    name = load_settings().get("whisper_model") or "large-v3"
    with _lock:
        if _model is not None and _model_name == name:
            return _model
        _add_cuda_dlls()
        from faster_whisper import WhisperModel
        if job:
            job.set(None, "Altyazı modeli yükleniyor (ilk sefer biraz sürebilir)...")
        errors = []
        for device, ctype in (("cuda", "float16"), ("cuda", "int8_float16"), ("cpu", "int8")):
            try:
                m = WhisperModel(name, device=device, compute_type=ctype)
                # GPU gerçekten çalışıyor mu dene
                if device == "cuda":
                    import numpy as np
                    list(m.transcribe(np.zeros(16000, dtype="float32"), language="tr")[0])
                _model, _model_name, _device = m, name, f"{device}/{ctype}"
                return _model
            except Exception as e:
                errors.append(f"{device}/{ctype}: {e}")
        raise RuntimeError("Altyazı modeli açılamadı: " + " | ".join(errors))


def current_device():
    return _device


# --------------------------------------------------------------- düzeltme
COMMON_FIXES = {
    "birşey": "bir şey", "herşey": "her şey", "hiçbirşey": "hiçbir şey", "şuan": "şu an",
    "yanlız": "yalnız", "yalnış": "yanlış", "herkez": "herkes", "birsürü": "bir sürü",
    "hiçkimse": "hiç kimse", "pekçok": "pek çok", "birkere": "bir kere", "herkeze": "herkese",
    "orjinal": "orijinal", "tabiki": "tabii ki", "malesef": "maalesef", "yada": "ya da",
    "hergün": "her gün", "herzaman": "her zaman", "birgün": "bir gün", "eşşek": "eşek",
    "deyil": "değil", "yinede": "yine de",
}


def _fix_word(w, user_fixes):
    m = re.match(r"^([\"'“‘(\[]*)(.*?)([.,!?;:…\"'”’)\]]*)$", w)
    pre, core, post = m.groups() if m else ("", w, "")
    if not core:
        return w
    low = tr_lower(core)
    rep = user_fixes.get(low) or COMMON_FIXES.get(low)
    if rep and rep != low:
        if core[:1].isupper():
            rep = rep[:1].upper() + rep[1:]
        core = rep
    return pre + core + post


def apply_fixes(words, user_fixes=None):
    uf = {tr_lower(k).strip(): v for k, v in (user_fixes or {}).items() if k.strip()}
    out = []
    for w in words:
        nw = dict(w)
        new = _fix_word(w["w"], uf)
        if new != w["w"]:
            nw["w"] = new
            nw["p"] = 1.0
        out.append(nw)
    # çok kelimeli kullanıcı düzeltmeleri (örn. "ray ni" -> "RRaenee")
    multi = {k: v for k, v in uf.items() if " " in k}
    if multi:
        i = 0
        res = []
        while i < len(out):
            hit = False
            for k, v in multi.items():
                parts = k.split()
                seg = out[i:i + len(parts)]
                if len(seg) == len(parts) and all(
                        tr_lower(re.sub(r"[^\wçğıöşüÇĞİÖŞÜ]", "", a["w"])) == b for a, b in zip(seg, parts)):
                    trail = re.sub(r"^.*?([.,!?…]*)$", r"\1", seg[-1]["w"])
                    res.append({"w": v + trail, "s": seg[0]["s"], "e": seg[-1]["e"], "p": 1.0})
                    i += len(parts)
                    hit = True
                    break
            if not hit:
                res.append(out[i])
                i += 1
        out = res
    return out


def transcribe(job, path, duration, lo=0.0, hi=1.0):
    s = load_settings()
    model = get_model(job)
    names = s.get("ipucu_isimler") or ""
    prompt = ("Merhaba arkadaşlar, bugün yayındayız. Evet, gerçekten çok güzel oldu! "
              + (f"İsimler: {names}." if names else ""))
    job.set(lo, f"Konuşma yazıya dökülüyor ({_device})...")
    segments, info = model.transcribe(
        str(path), language="tr", word_timestamps=True, vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 400}, beam_size=5, best_of=5,
        initial_prompt=prompt, condition_on_previous_text=True, temperature=[0.0, 0.2, 0.4])
    words = []
    for seg in segments:
        if job.cancelled:
            raise RuntimeError("İptal edildi")
        for w in seg.words or []:
            t = w.word.strip()
            if not t:
                continue
            words.append({"w": t, "s": round(w.start, 3), "e": round(w.end, 3),
                          "p": round(float(w.probability), 3)})
        if duration:
            f = min(1, seg.end / duration)
            job.set(lo + (hi - lo) * f, f"Konuşma yazıya dökülüyor %{int(f*100)}")
    words = apply_fixes(words, s.get("duzeltmeler"))
    return words


def chunk_words(words, max_words=3, max_chars=18):
    """Kelimeleri ekranda görünecek kısa altyazı parçalarına böler."""
    chunks = []
    cur = []

    def flush():
        if cur:
            chunks.append({"id": f"c{len(chunks)}_{int(cur[0]['s']*1000)}",
                           "s": cur[0]["s"], "e": cur[-1]["e"], "words": list(cur)})
            cur.clear()
    for w in words:
        if cur:
            text_len = sum(len(x["w"]) + 1 for x in cur) + len(w["w"])
            gap = w["s"] - cur[-1]["e"]
            if len(cur) >= max_words or text_len > max_chars or gap > 0.6:
                flush()
        cur.append(w)
        if re.search(r"[.!?…]$", w["w"]):
            flush()
    flush()
    return chunks
