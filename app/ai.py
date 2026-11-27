"""Yapay zekâ (Google Gemini) bağlantısı.

Anahtar Ayarlar → Yapay Zekâ'dan girilir (Google AI Studio'dan ücretsiz alınır).
Model adları sık değiştiği için en uygun "flash" modeli listeden kendisi seçer.
"""
import json
import re
import time
import urllib.error
import urllib.request

from core import load_settings

BASE = "https://generativelanguage.googleapis.com/v1beta"
_MODELS = {"pick": None, "lite": None, "all": [], "t": 0}


class AIError(RuntimeError):
    pass


def key():
    return (load_settings().get("gemini_anahtar") or "").strip()


def enabled():
    return bool(key())


def _log(msg):
    import sys
    print(f"[ai] {time.strftime('%H:%M:%S')} {msg}", file=sys.stderr, flush=True)


def _err(code, err):
    msg, status = err.get("message", ""), err.get("status", "")
    _log(f"HTTP {code} {status}: {msg[:400]}")
    if code == 401 or "ACCESS_TOKEN_TYPE_UNSUPPORTED" in json.dumps(err):
        return AIError("Google bu anahtarı kabul etmedi (401). AI Studio'da yeni bir anahtar oluşturup tekrar dene; "
                       "anahtarın tamamını kopyaladığından emin ol.")
    if code == 400 and ("API key" in msg or "API_KEY" in msg):
        return AIError("Gemini anahtarı geçersiz. Ayarlar → Yapay Zekâ'dan kontrol et.")
    if code == 403:
        return AIError("Gemini anahtarının izni yok (anahtar kapatılmış ya da bölge desteklenmiyor).")
    if code == 429 or status == "RESOURCE_EXHAUSTED":
        return AIError("KOTA:Gemini ücretsiz kullanım sınırı doldu. Biraz bekleyip tekrar dene.")
    if code == 404:
        return AIError("MODEL:" + msg)
    if code >= 500:
        return AIError("MESGUL:Gemini şu an çok yoğun, biraz sonra tekrar dene.")
    return AIError(f"Gemini hatası ({code}): {msg[:300]}")


def _http(method, path, body=None, timeout=60, k=None):
    """Gemini'ye istek. Kesin süre sınırı var (takılıp kalmasın)."""
    k = k or key()
    if not k:
        raise AIError("Yapay zekâ için Ayarlar → Yapay Zekâ kısmına Gemini anahtarını gir.")
    url = f"{BASE}/{path}"
    t0 = time.time()
    try:
        from curl_cffi import requests as creq
    except Exception:
        creq = None
    if creq:
        try:
            r = creq.request(method, url, data=json.dumps(body).encode("utf-8") if body is not None else None,
                             timeout=timeout, headers={"Content-Type": "application/json", "x-goog-api-key": k})
        except Exception as e:
            _log(f"bağlantı hatası ({time.time() - t0:.0f} sn): {str(e)[:200]}")
            if "timed out" in str(e).lower() or "timeout" in str(e).lower():
                raise AIError("MESGUL:Gemini zamanında cevap vermedi.")
            raise AIError("İnternete bağlanılamadı. Bağlantını kontrol et.")
        if r.status_code >= 400:
            try:
                err = r.json().get("error", {})
            except Exception:
                err = {"message": r.text[:300]}
            raise _err(r.status_code, err)
        return r.json()
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json", "x-goog-api-key": k})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read().decode("utf-8")).get("error", {})
        except Exception:
            err = {}
        raise _err(e.code, err)
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        _log(f"bağlantı hatası: {e}")
        if "timed out" in str(e).lower():
            raise AIError("MESGUL:Gemini zamanında cevap vermedi.")
        raise AIError("İnternete bağlanılamadı. Bağlantını kontrol et.")


def _ver(name):
    m = re.search(r"gemini-(\d+(?:\.\d+)?)", name)
    return float(m.group(1)) if m else 0.0


def pick_model(force=False):
    """Kullanılabilir en yeni Flash modelini seç (ayarlardan elle de seçilebilir)."""
    manual = (load_settings().get("ai_model") or "").strip()
    if manual and manual != "auto":
        return manual
    if _MODELS["pick"] and not force and time.time() - _MODELS["t"] < 6 * 3600:
        return _MODELS["pick"]
    st = load_settings()
    remembered = st.get("ai_son_model") if not force and time.time() - float(st.get("ai_son_model_t") or 0) < 24 * 3600 else None
    names = []
    try:
        tok = ""
        for _ in range(5):
            r = _http("GET", "models?pageSize=200" + (f"&pageToken={tok}" if tok else ""), timeout=30)
            for m in r.get("models", []):
                if "generateContent" in (m.get("supportedGenerationMethods") or []):
                    names.append(m["name"].split("/", 1)[-1])
            tok = r.get("nextPageToken")
            if not tok:
                break
    except AIError as e:
        if "geçersiz" in str(e) or "izni yok" in str(e):
            raise
    bad = ("image", "live", "tts", "audio", "embed", "robotics", "computer", "translate", "transcribe", "omni", "learnlm", "gemma", "exp", "thinking")

    def ok(n):
        return n.startswith("gemini-") and "flash" in n and not any(b in n for b in bad)
    full = [n for n in names if ok(n) and "lite" not in n]
    lite = [n for n in names if ok(n) and "lite" in n]

    def best(lst):
        # en yeni sürüm, kararlı olan (preview değil) öne
        return sorted(lst, key=lambda n: (_ver(n), "preview" not in n, -len(n)), reverse=True)[0] if lst else None
    order = lambda lst: sorted(lst, key=lambda n: (_ver(n), "preview" not in n, -len(n)), reverse=True)  # noqa: E731
    _MODELS["pick"] = best(full) or "gemini-flash-latest"
    _MODELS["lite"] = best(lite) or "gemini-flash-lite-latest"
    # yoğunlukta sırayla denenecek yedekler: diğer flash'lar, sonra lite'lar
    _MODELS["all"] = order(full) + order(lite) + ["gemini-flash-latest", "gemini-flash-lite-latest"]
    if remembered and remembered in names:
        _MODELS["pick"] = remembered
    _MODELS["t"] = time.time()
    return _MODELS["pick"]


def generate(contents, system=None, tools=None, json_mode=False, temperature=0.7, timeout=60):
    """Ham generateContent çağrısı. contents: Gemini biçiminde mesaj listesi. Dönen: ilk adayın content'i."""
    body = {"contents": contents, "generationConfig": {"temperature": temperature}}
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}
    if tools:
        body["tools"] = [{"functionDeclarations": tools}]
    if json_mode:
        body["generationConfig"]["responseMimeType"] = "application/json"
    from concurrent.futures import ThreadPoolExecutor, FIRST_COMPLETED, wait as fwait
    first = pick_model()
    lite = _MODELS.get("lite")
    # hız önce: "lite" modeller genelde birkaç saniyede cevap verir; yarışa en başta katılsın
    order = ([first] if first and "lite" in first else []) + ([lite] if lite else []) + [first] + [m for m in (_MODELS.get("all") or []) if m != first]
    order = list(dict.fromkeys(order))

    def one(model):
        b = json.loads(json.dumps(body))
        cfg = b["generationConfig"]
        if _ver(model) >= 3:  # Gemini 3+: sıcaklık varsayılan, kısa düşünsün (hızlı cevap)
            cfg.pop("temperature", None)
            cfg["thinkingConfig"] = {"thinkingLevel": "minimal" if "lite" in model else "low"}
        else:
            cfg["temperature"] = temperature
        t0 = time.time()
        _log(f"istek → {model}")
        try:
            r = _http("POST", f"models/{model}:generateContent", b, timeout=timeout)
        except AIError as e:
            if "thinking" in str(e).lower() and "thinkingConfig" in cfg:
                cfg.pop("thinkingConfig", None)  # bu model düşünme ayarını desteklemiyor
                r = _http("POST", f"models/{model}:generateContent", b, timeout=timeout)
            else:
                raise
        _log(f"cevap ← {model} ({time.time() - t0:.1f} sn)")
        return model, r

    # son 10 dakikada çalışan model varsa önce tek başına onu dene; yoksa 3 modele aynı anda sor, ilk gelen cevabı al
    fresh = _MODELS.get("ok") == first and time.time() - _MODELS.get("ok_t", 0) < 600
    waves = ([order[:1], order[1:4], order[4:7]] if fresh else [order[:3], order[3:6]])
    r, last = None, None
    for wave in waves:
        if not wave:
            continue
        ex = ThreadPoolExecutor(max_workers=len(wave))
        futs = {ex.submit(one, m): m for m in wave}
        pending = set(futs)
        while pending and r is None:
            done, pending = fwait(pending, return_when=FIRST_COMPLETED)
            for f in done:
                try:
                    model, rr = f.result()
                    r = rr
                    _MODELS["ok"], _MODELS["ok_t"] = model, time.time()
                    if (load_settings().get("ai_model") or "auto") == "auto" and model != _MODELS.get("pick"):
                        _MODELS["pick"] = model
                        from core import save_settings
                        save_settings({"ai_son_model": model, "ai_son_model_t": time.time()})
                    break
                except AIError as e:
                    last = e
                    if not str(e).startswith(("MODEL:", "MESGUL:", "KOTA:")):
                        ex.shutdown(wait=False, cancel_futures=True)
                        raise
                except Exception as e:  # beklenmeyen
                    last = AIError(str(e)[:200])
        ex.shutdown(wait=False, cancel_futures=True)  # kalanları bekleme
        if r is not None:
            break
    if r is None:
        s = str(last or "Gemini yanıt vermedi.")
        raise AIError(s.split(":", 1)[1] if s.startswith(("MODEL:", "MESGUL:", "KOTA:")) else s)
    cands = r.get("candidates") or []
    if not cands:
        fb = (r.get("promptFeedback") or {}).get("blockReason")
        raise AIError("Gemini bu isteğe yanıt vermedi" + (f" ({fb})" if fb else "") + ".")
    c = cands[0].get("content") or {"role": "model", "parts": []}
    c.setdefault("role", "model")
    c.setdefault("parts", [])
    return c


def _merge_parts(parts):
    """Akışla parça parça gelen cevabı tek içeriğe toplar (imzalar korunur)."""
    out = []
    for p in parts:
        if set(p) <= {"text", "thoughtSignature"} and out and set(out[-1]) <= {"text", "thoughtSignature"} \
                and "thoughtSignature" not in out[-1] and not p.get("thought"):
            out[-1]["text"] = out[-1].get("text", "") + p.get("text", "")
            if p.get("thoughtSignature"):
                out[-1]["thoughtSignature"] = p["thoughtSignature"]
        else:
            out.append(dict(p))
    return out


def stream(contents, system=None, tools=None, timeout=45):
    """Cevabı akış olarak alır. ('text', parça) olayları üretir, en sonda ('done', content).
    Hızlı model önce denenir; ilk bayt gelmeden hata olursa sıradakine geçer."""
    body = {"contents": contents, "generationConfig": {}}
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}
    if tools:
        body["tools"] = [{"functionDeclarations": tools}]
    k = key()
    if not k:
        raise AIError("Yapay zekâ için Ayarlar → Yapay Zekâ kısmına Gemini anahtarını gir.")
    first = pick_model()
    lite = _MODELS.get("lite")
    ok = _MODELS.get("ok") if time.time() - _MODELS.get("ok_t", 0) < 1800 else None
    order = list(dict.fromkeys([m for m in [ok, lite, first] + (_MODELS.get("all") or []) if m]))[:5]
    last = None
    for model in order:
        b = json.loads(json.dumps(body))
        cfg = b["generationConfig"]
        if _ver(model) >= 3 and not _MODELS.get("nothink"):
            cfg["thinkingConfig"] = {"thinkingLevel": "minimal" if "lite" in model else "low"}
        t0 = time.time()
        _log(f"akış → {model}")
        req = urllib.request.Request(f"{BASE}/models/{model}:streamGenerateContent?alt=sse", data=json.dumps(b).encode("utf-8"),
                                     method="POST", headers={"Content-Type": "application/json", "x-goog-api-key": k})
        parts, got = [], False
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                for raw in r:
                    line = raw.decode("utf-8", "replace").strip()
                    if not line.startswith("data:"):
                        continue
                    d = json.loads(line[5:].strip() or "{}")
                    if d.get("error"):
                        raise _err(int(d["error"].get("code") or 500), d["error"])
                    for c in d.get("candidates") or []:
                        for p in (c.get("content") or {}).get("parts") or []:
                            if not got:
                                _log(f"ilk parça ← {model} ({time.time() - t0:.1f} sn)")
                            got = True
                            parts.append(p)
                            if p.get("text") and not p.get("thought"):
                                yield ("text", p["text"])
        except urllib.error.HTTPError as e:
            try:
                err = json.loads(e.read().decode("utf-8")).get("error", {})
            except Exception:
                err = {}
            ex = _err(e.code, err)
            if "thinking" in str(ex).lower():
                _MODELS["nothink"] = True
            last = ex
            if got or not str(ex).startswith(("MODEL:", "MESGUL:", "KOTA:")) and "thinking" not in str(ex).lower():
                raise ex
            continue
        except AIError as e:
            last = e
            if got or not str(e).startswith(("MODEL:", "MESGUL:", "KOTA:")):
                raise
            continue
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            _log(f"akış bağlantı hatası: {e}")
            last = AIError("MESGUL:Gemini zamanında cevap vermedi.")
            if got:
                raise AIError("Bağlantı yarıda kesildi, tekrar dene.")
            continue
        _log(f"akış bitti ← {model} ({time.time() - t0:.1f} sn)")
        _MODELS["ok"], _MODELS["ok_t"] = model, time.time()
        yield ("done", {"role": "model", "parts": _merge_parts(parts)})
        return
    s = str(last or "Gemini yanıt vermedi.")
    raise AIError(s.split(":", 1)[1] if s.startswith(("MODEL:", "MESGUL:", "KOTA:")) else s)


def text_of(content):
    return "".join(p.get("text", "") for p in content.get("parts", []) if not p.get("thought"))


def ask(prompt, system=None, json_mode=False, temperature=0.7):
    c = generate([{"role": "user", "parts": [{"text": prompt}]}], system=system, json_mode=json_mode, temperature=temperature)
    t = text_of(c).strip()
    if not json_mode:
        return t
    return parse_json(t)


def parse_json(t):
    t = t.strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t)
    try:
        return json.loads(t)
    except Exception:
        m = re.search(r"(\{.*\}|\[.*\])", t, re.S)
        if m:
            return json.loads(m.group(1))
        raise AIError("Yapay zekânın cevabı anlaşılamadı, tekrar dene.")


def test(k):
    """Ayarlar'daki 'Dene' düğmesi: anahtar çalışıyor mu?"""
    r = _http("GET", "models?pageSize=50", timeout=30, k=k)
    n = [m["name"] for m in r.get("models", [])]
    if not n:
        raise AIError("Anahtar çalıştı ama hiç model görünmüyor.")
    return True


# ---------------------------------------------------------------- paylaşım metni
META_SYS = ("Türkçe sosyal medya editörüsün. Kick/YouTube yayın kesitleri için dikkat çekici ama tık tuzağı olmayan, "
            "doğal, genç bir dille başlık ve açıklama yazarsın. Emojiyi abartmadan kullanırsın. Yalnızca JSON döndürürsün.")


def write_meta(title, transcript, channel="", extra=""):
    """YouTube Shorts / TikTok / Instagram Reels için başlık, açıklama, etiket."""
    tr = (transcript or "").strip()[:6000]
    prompt = f"""Video adı: {title}
Kanal / yayıncı: {channel or 'bilinmiyor'}
{('Not: ' + extra) if extra else ''}
Videoda konuşulanlar (otomatik altyazı, hatalı olabilir):
\"\"\"{tr or '(altyazı yok)'}\"\"\"

Bu kısa video için üç platforma ayrı ayrı paylaşım metni yaz. JSON biçimi:
{{"youtube": {{"baslik": "en fazla 90 karakter, merak uyandıran", "aciklama": "2-4 cümle + en sonda 3-5 hashtag", "etiketler": ["8-15 arama etiketi"]}},
 "tiktok": {{"aciklama": "kısa, akılda kalan 1-2 cümle + 4-6 hashtag (#keşfet dahil)"}},
 "instagram": {{"aciklama": "1-3 cümle, okuyanı yorum yapmaya çağıran + 5-8 hashtag"}}}}
Hashtagler Türkçe karakterli olabilir. Yayıncının adını doğru yaz. Uydurma bilgi ekleme."""
    d = ask(prompt, system=META_SYS, json_mode=True, temperature=0.8)
    if not isinstance(d, dict):
        raise AIError("Yapay zekânın cevabı anlaşılamadı, tekrar dene.")
    yt, tt, ig = d.get("youtube") or {}, d.get("tiktok") or {}, d.get("instagram") or {}
    tags = yt.get("etiketler") or []
    if isinstance(tags, str):
        tags = [x.strip() for x in tags.split(",") if x.strip()]
    return {"youtube": {"baslik": str(yt.get("baslik") or title)[:100], "aciklama": str(yt.get("aciklama") or ""), "etiketler": [str(t).lstrip("#") for t in tags][:20]},
            "tiktok": {"aciklama": str(tt.get("aciklama") or "")},
            "instagram": {"aciklama": str(ig.get("aciklama") or "")},
            "time": time.time()}


# ---------------------------------------------------------------- otomatik edit: en iyi anları seç
PICK_SYS = ("Kick ve YouTube yayınlarından viral kısa video (Reels/Shorts/TikTok) kesen deneyimli bir Türk editörsün. "
            "Komik, şaşırtıcı, duygusal ya da tartışmalı, tek başına anlaşılan anları seçersin. Yalnızca JSON döndürürsün.")


def pick_moments(cands, n, maxlen=60):
    """cands: [{i, start, end, score, text}] (text: '[12.3] söz ...' biçiminde zamanlı). En iyi n tanesini seçer."""
    lines = []
    for c in cands:
        lines.append(f"### Aday {c['i']} ({c['start']:.1f}-{c['end']:.1f} sn, ses heyecanı {c.get('score', 0)}/100)\n{c.get('text') or '(konuşma yok)'}")
    prompt = f"""Aşağıda bir yayından ses heyecanına göre bulunmuş aday anlar ve içlerinde konuşulanlar var (zaman damgalı).
En iyi {n} tanesini seç. Her biri için:
- kısa videonun başlangıç ve bitiş saniyesi: cümle ortasında başlamasın/bitmesin, olayın kurulumunu da içersin, {maxlen} saniyeyi geçmesin, adayın sınırlarının en fazla 5 sn dışına çıkabilir
- kısa bir Türkçe başlık (en fazla 60 karakter)
- neden seçtiğin (tek cümle)
JSON: {{"secimler": [{{"aday": 0, "bas": 12.3, "bit": 41.0, "baslik": "...", "neden": "..."}}]}}
En iyiden başlayarak sırala.

{chr(10).join(lines)}"""
    d = ask(prompt, system=PICK_SYS, json_mode=True, temperature=0.4)
    out = []
    for s in (d.get("secimler") if isinstance(d, dict) else d) or []:
        try:
            out.append({"aday": int(s.get("aday")), "bas": float(s.get("bas")), "bit": float(s.get("bit")),
                        "baslik": str(s.get("baslik") or "")[:80], "neden": str(s.get("neden") or "")[:200]})
        except Exception:
            continue
    return out[:n]
