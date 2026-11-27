"""Kanal Analizi: YouTube kanalının videolarını çeker, neyin tuttuğunu ölçer, ne yapılacağını söyler."""
import json
import re
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core import CACHE, load_settings, save_settings

TR = timezone(timedelta(hours=3))
GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
STOP = set("""ve ile bir bu şu o da de mi mı mu mü ne için gibi çok en daha ama ya ki her hiç kadar sonra önce
ben sen biz siz onlar beni seni bana sana benim senin onun bunu şunu olan oldu olur var yok değil diye
the a an of to in on for and or is are was with my your me i you at it this that vs ft feat shorts short""".split())
DIR = CACHE / "kanal"


# ---------------------------------------------------------------- kanal adresi
def channel_url(text):
    t = (text or "").strip()
    if not t:
        raise ValueError("Kanal adını ya da linkini yaz")
    m = re.search(r"youtube\.com/(@[\w.\-]+|channel/[\w\-]+|c/[\w.\-]+|user/[\w.\-]+)", t)
    if m:
        return "https://www.youtube.com/" + m.group(1)
    if re.fullmatch(r"UC[\w\-]{20,}", t):
        return "https://www.youtube.com/channel/" + t
    t = t.lstrip("@").strip()
    if not re.fullmatch(r"[\w.\-]+", t):
        raise ValueError("Kanal adı anlaşılmadı. Örnek: @kanaladi ya da youtube.com/@kanaladi")
    return "https://www.youtube.com/@" + t


def _key(url):
    return re.sub(r"[^\w\-]", "_", url.split("youtube.com/")[-1])[:80]


# ---------------------------------------------------------------- çekme (yt-dlp)
def _flat(url, n):
    import kick
    with kick._ydl({"extract_flat": "in_playlist", "playlistend": n, "ignoreerrors": True}) as y:
        info = y.extract_info(url, download=False) or {}
    return info, [e for e in (info.get("entries") or []) if e and e.get("id") and e.get("_type") != "playlist"]


def _full(vid):
    import kick
    try:
        with kick._ydl({"skip_download": True, "ignoreerrors": True}) as y:
            return y.extract_info("https://www.youtube.com/watch?v=" + vid, download=False, process=False)
    except Exception:
        return None


def fetch(job, text, n=50):
    url = channel_url(text)
    n = max(10, min(200, int(n or 50)))
    job.extra = {"t0": time.time()}
    job.set(0.02, "Kanal bulunuyor...")
    head = {}
    vids, shorts = [], []
    try:
        head, vids = _flat(url + "/videos", n)
    except Exception:
        pass
    job.set(0.08, "Shorts listesi alınıyor...")
    try:
        h2, shorts = _flat(url + "/shorts", n)
        head = head or h2
    except Exception:
        pass
    if not vids and not shorts:
        raise RuntimeError("Kanal bulunamadı ya da hiç video yok. Adı kontrol et (ör. @kanaladi). İnternet bağlantını da kontrol et.")
    items = [(e, False) for e in vids] + [(e, True) for e in shorts]  # ikisi de yeniden eskiye
    out, done = [], 0
    total = len(items)

    def one(item):
        e, is_short = item
        f = _full(e["id"]) or {}
        return _row(e, f, is_short)

    with ThreadPoolExecutor(4) as ex:
        for r in ex.map(one, items):
            job.wait_if_paused()
            if job.cancelled:
                raise RuntimeError("İptal edildi")
            done += 1
            if r:
                out.append(r)
            job.set(0.1 + 0.85 * done / max(1, total), f"Videolar inceleniyor ({done}/{total})...")
    ch = {
        "ad": head.get("channel") or head.get("uploader") or head.get("title", "").replace(" - Videos", "") or url.split("/")[-1],
        "abone": head.get("channel_follower_count"),
        "url": url,
        "avatar": next((t.get("url") for t in reversed(head.get("thumbnails") or []) if "avatar" in str(t.get("id"))), None),
    }
    data = {"kanal": ch, "videolar": out, "zaman": time.time(), "girdi": text}
    DIR.mkdir(parents=True, exist_ok=True)
    (DIR / f"{_key(url)}.json").write_text(json.dumps(data, ensure_ascii=False), "utf-8")
    _remember(text, ch["ad"])
    job.set(1, f"{len(out)} video incelendi")
    return {"key": _key(url), "analiz": analyze(data)}


def _remember(text, name):
    s = load_settings().get("kanal_son") or []
    s = [x for x in s if x.get("girdi") != text][:7]
    save_settings({"kanal_son": [{"girdi": text, "ad": name}] + s})


def _row(e, f, is_short):
    ts = f.get("timestamp") or e.get("timestamp")
    if not ts and (f.get("upload_date") or e.get("upload_date")):
        try:
            ts = datetime.strptime(f.get("upload_date") or e.get("upload_date"), "%Y%m%d").replace(hour=12, tzinfo=timezone.utc).timestamp()
        except Exception:
            ts = None
    views = f.get("view_count") if f.get("view_count") is not None else e.get("view_count")
    if views is None:
        return None
    dur = f.get("duration") or e.get("duration") or 0
    if f.get("live_status") in ("is_live", "is_upcoming"):
        return None
    return {"id": e["id"], "baslik": f.get("title") or e.get("title") or "", "izlenme": int(views or 0),
            "begeni": f.get("like_count"), "yorum": f.get("comment_count"), "sure": float(dur or 0),
            "ts": ts, "short": bool(is_short or (dur and dur <= 62 and "/shorts/" in (e.get("url") or ""))),
            "tarih_kesin": bool(f.get("timestamp")), "etiket": (f.get("tags") or [])[:15],
            "url": ("https://www.youtube.com/shorts/" if is_short else "https://www.youtube.com/watch?v=") + e["id"],
            "kapak": f"https://i.ytimg.com/vi/{e['id']}/mqdefault.jpg"}


def cached(key):
    f = DIR / f"{re.sub(r'[^\w\-]', '_', key or '')}.json"
    if not f.exists():
        return None
    data = json.loads(f.read_text("utf-8"))
    return {"key": f.stem, "analiz": analyze(data)}


# ---------------------------------------------------------------- analiz
def _med(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else 0


def _eng(v):
    if not v["izlenme"] or v["begeni"] is None:
        return None
    return (v["begeni"] + (v["yorum"] or 0)) / v["izlenme"] * 100


def _fmt(n):
    n = float(n or 0)
    if n >= 1e6:
        return f"{n / 1e6:.1f}".rstrip("0").rstrip(".").replace(".", ",") + " Mn"
    if n >= 1e3:
        return f"{n / 1e3:.1f}".rstrip("0").rstrip(".").replace(".", ",") + " B"
    return str(int(round(n)))


def _x(f):
    return f"{f:.1f}".replace(".", ",")


def _words(title):
    t = re.sub(r"https?://\S+|#\w+", " ", title.lower())
    return [w for w in re.findall(r"[a-zçğıöşü0-9]{3,}", t) if w not in STOP and not w.isdigit()]


def analyze(data):
    now = time.time()
    vs = [dict(v) for v in data["videolar"]]
    for v in vs:
        v["yas"] = max(0.5, (now - v["ts"]) / 86400) if v.get("ts") else None
        v["gunluk"] = v["izlenme"] / v["yas"] if v["yas"] else None
        v["etkilesim"] = _eng(v)
        if v.get("ts"):
            d = datetime.fromtimestamp(v["ts"], TR)
            v["gun"], v["saat"] = d.weekday(), (d.hour if v.get("tarih_kesin") else None)
            v["tarih"] = d.strftime("%d.%m.%Y")
        else:
            v["gun"] = v["saat"] = None
            v["tarih"] = ""
    longs, shorts = [v for v in vs if not v["short"]], [v for v in vs if v["short"]]
    # karşılaştırmalar kendi türü içinde: 1.0 = o türün ortancası kadar izlenme
    for lst in (longs, shorts):
        m = _med([v["izlenme"] for v in lst]) or 1
        for v in lst:
            v["rel"] = v["izlenme"] / m
    dated = sorted([v for v in vs if v.get("ts")], key=lambda v: v["ts"])
    span_days = (dated[-1]["ts"] - dated[0]["ts"]) / 86400 if len(dated) > 1 else 0
    last30 = [v for v in dated if now - v["ts"] <= 30 * 86400]
    engs = [v["etkilesim"] for v in vs if v["etkilesim"] is not None]

    def grp(vlist):
        return {"adet": len(vlist), "medyan": _med([v["izlenme"] for v in vlist]), "ort": (sum(v["izlenme"] for v in vlist) / len(vlist)) if vlist else 0,
                "etkilesim": _med([v["etkilesim"] for v in vlist]), "gunluk": _med([v["gunluk"] for v in vlist])}

    # gün / saat
    gun = [{"gun": GUNLER[i], "adet": len(g), "medyan": _med([v["izlenme"] for v in g]), "rel": _med([v["rel"] for v in g])} for i in range(7) for g in [[v for v in vs if v["gun"] == i]]]
    saat = [{"saat": h, "adet": len(g), "medyan": _med([v["izlenme"] for v in g]), "rel": _med([v["rel"] for v in g])} for h in range(24) for g in [[v for v in vs if v["saat"] == h]]]
    # süre dilimleri
    sdil = [("0-15 sn", 0, 15), ("15-30 sn", 15, 30), ("30-45 sn", 30, 45), ("45-60+ sn", 45, 1e9)]
    ldil = [("0-5 dk", 0, 300), ("5-10 dk", 300, 600), ("10-20 dk", 600, 1200), ("20+ dk", 1200, 1e9)]
    sure = {"shorts": [{"ad": a, "adet": len(g), "medyan": _med([v["izlenme"] for v in g])} for a, lo, hi in sdil for g in [[v for v in shorts if lo <= v["sure"] < hi]]],
            "uzun": [{"ad": a, "adet": len(g), "medyan": _med([v["izlenme"] for v in g])} for a, lo, hi in ldil for g in [[v for v in longs if lo <= v["sure"] < hi]]]}
    # başlıklar: her türün kendi içinde en iyi çeyreği
    top_titles, rest_titles = [], []
    for lst in (longs, shorts):
        s = sorted(lst, key=lambda v: -(v["gunluk"] or v["izlenme"]))
        q = max(1, len(s) // 4)
        top_titles += [v["baslik"] for v in s[:q]]
        rest_titles += [v["baslik"] for v in s[q:]]
    cnt_top, cnt_all = {}, {}
    for t in top_titles:
        for w in set(_words(t)):
            cnt_top[w] = cnt_top.get(w, 0) + 1
    for t in top_titles + rest_titles:
        for w in set(_words(t)):
            cnt_all[w] = cnt_all.get(w, 0) + 1
    kelime = sorted([(w, c) for w, c in cnt_top.items() if c >= 2], key=lambda x: (-x[1] / max(1, cnt_all[x[0]]) * x[1], x[0]))[:14]

    def feat(fn):
        a = [v for v in vs if fn(v["baslik"])]
        b = [v for v in vs if not fn(v["baslik"])]
        return a, b
    baslik = {"top_uzunluk": round(_med([len(t) for t in top_titles])), "diger_uzunluk": round(_med([len(t) for t in rest_titles])),
              "kelimeler": [{"k": w, "n": c} for w, c in kelime]}

    out = {
        "kanal": data["kanal"], "zaman": data["zaman"], "girdi": data.get("girdi"),
        "ozet": {"adet": len(vs), "uzun": len(longs), "shorts": len(shorts), "toplam": sum(v["izlenme"] for v in vs),
                 "medyan": _med([v["izlenme"] for v in vs]), "etkilesim": _med(engs),
                 "haftalik": round(len(dated) / (span_days / 7), 1) if span_days >= 7 else None,
                 "son30": len(last30), "ilk": dated[0]["tarih"] if dated else "", "son": dated[-1]["tarih"] if dated else ""},
        "uzun": grp(longs), "shorts_g": grp(shorts),
        "gun": gun, "saat": saat, "sure": sure, "baslik": baslik,
        "en_iyi": sorted(vs, key=lambda v: -v["izlenme"])[:6],
        "yukselen": sorted([v for v in vs if v["yas"] and v["yas"] <= 30], key=lambda v: -(v["gunluk"] or 0))[:4],
        "trend": [{"t": v["tarih"], "i": v["izlenme"], "s": v["short"], "b": v["baslik"][:80]} for v in dated],
        "videolar": sorted(vs, key=lambda v: -(v.get("ts") or 0)),
    }
    out["oneriler"] = insights(out, vs, feat)
    return out


def insights(a, vs, feat):
    """Kurallarla somut öneriler (az veride iddia yok: her grupta en az 3 video, fark en az %30)."""
    o, L, S = [], a["uzun"], a["shorts_g"]

    def big(x, y):
        return x and y and x >= y * 1.3
    if L["adet"] >= 3 and S["adet"] >= 3:
        if big(S["medyan"], L["medyan"]):
            o.append(("📱", f"Shorts videoların uzun videolardan {_x(S['medyan'] / max(1, L['medyan']))} kat fazla izleniyor (ortanca {_fmt(S['medyan'])} - {_fmt(L['medyan'])}). Daha sık Shorts at, uzun videolarına Shorts'tan yönlendir."))
        elif big(L["medyan"], S["medyan"]):
            o.append(("🎬", f"Uzun videoların Shorts'lardan {_x(L['medyan'] / max(1, S['medyan']))} kat fazla izleniyor. Asıl güç uzun videoda; Shorts'u sadece tanıtım için kullan."))
    elif S["adet"] == 0 and L["adet"] >= 3:
        o.append(("📱", "Hiç Shorts yok. Kesit kanalları için Shorts en hızlı büyüme yolu: en iyi anlarını 30-45 saniyelik dikey videolar olarak at."))
    # gün
    g = [x for x in a["gun"] if x["adet"] >= 3]
    if len(g) >= 3:
        b, w = max(g, key=lambda x: x["rel"]), min(g, key=lambda x: x["rel"])
        if b["rel"] >= 1.25 and big(b["rel"], w["rel"]):
            o.append(("📅", f"En iyi gün: {b['gun']}. O gün yüklediğin videolar normalden %{round((b['rel'] - 1) * 100)} fazla izleniyor; en zayıf gün {w['gun']}. Önemli videolarını {b['gun']} günü yükle."))
    # saat
    blocks = {}
    for v in vs:
        if v.get("saat") is not None:
            blocks.setdefault(v["saat"] // 3, []).append(v["rel"])
    bl = [(k, _med(v), len(v)) for k, v in blocks.items() if len(v) >= 3]
    if len(bl) >= 2:
        k, m, _ = max(bl, key=lambda x: x[1])
        if m >= 1.25 and big(m, _med([x[1] for x in bl])):
            o.append(("⏰", f"{k * 3:02d}:00 - {k * 3 + 3:02d}:00 arası yüklediğin videolar daha çok izleniyor (Türkiye saati). Yüklemeyi bu saatlere kaydır."))
    # süre
    for tur, ad in (("shorts", "Shorts"), ("uzun", "uzun video")):
        d = [x for x in a["sure"][tur] if x["adet"] >= 3]
        if len(d) >= 2:
            b = max(d, key=lambda x: x["medyan"])
            if big(b["medyan"], _med([x["medyan"] for x in d])):
                o.append(("⏱", f"{ad.capitalize()} için en iyi süre: {b['ad']} (ortanca {_fmt(b['medyan'])} izlenme)."))
    # başlık özellikleri
    for fn, iyi, kotu in ((lambda t: "?" in t, "Soru soran başlıklar (?) daha çok izleniyor. Merak uyandıran soru başlıkları dene.", None),
                          (lambda t: bool(re.search(r"\d", t)), "Başlığında sayı olan videolar daha çok izleniyor (ör. \"3 saniyede...\", \"100 kişi...\").", None),
                          (lambda t: sum(1 for w in t.split() if len(w) > 2 and w.isupper()) >= 1, "BÜYÜK HARFLİ vurgu kelimesi olan başlıklar daha çok izleniyor.", "Büyük harfli başlıklar daha az izleniyor; vurguyu tek bir kelimeye indir.")):
        x, y = feat(fn)
        if len(x) >= 3 and len(y) >= 3:
            mx, my = _med([v["rel"] for v in x]), _med([v["rel"] for v in y])
            if big(mx, my):
                o.append(("✍️", iyi + f" (yaklaşık %{round((mx / my - 1) * 100)} fazla)"))
            elif kotu and big(my, mx):
                o.append(("✍️", kotu))
    # yükleme sıklığı
    hz = a["ozet"]["haftalik"]
    if hz is not None and hz < 3:
        o.append(("📈", f"Haftada ortalama {str(hz).replace('.', ',')} video yüklüyorsun. Kesit kanallarında haftada en az 4-5 Shorts düzenli büyüme getirir; sık ve düzenli yükle."))
    if a["ozet"]["son30"] == 0 and a["ozet"]["adet"]:
        o.append(("⚠️", "Son 30 günde hiç video yok. YouTube düzenli yükleyen kanalı öne çıkarır; ara verme."))
    # etkileşim
    e = a["ozet"]["etkilesim"]
    if e:
        if e < 2:
            o.append(("💬", f"Etkileşim oranın %{_x(e)} (düşük). Videonun sonunda soru sor, yoruma sabitlenmiş bir soru yaz, beğeni iste."))
        elif e >= 5:
            o.append(("💬", f"Etkileşim oranın %{_x(e)}: çok iyi! İzleyicin sadık; bu yüzden daha sık yüklemek doğrudan büyüme getirir."))
    # en iyi videoyu tekrarla
    if a["en_iyi"]:
        t = a["en_iyi"][0]
        o.append(("🏆", f"En çok tutan videon: \"{t['baslik'][:70]}\" ({_fmt(t['izlenme'])}). Aynı konudan / aynı anlatımla devam videosu yap."))
    if not o:
        o.append(("ℹ️", "Belirgin bir fark çıkmadı. Daha çok video ile analiz et (50 ya da 100 seç)."))
    return [{"ikon": i, "metin": m} for i, m in o]


# ---------------------------------------------------------------- yapay zekâ yorumu
def ai_advice(key):
    import ai
    r = cached(key)
    if not r:
        raise RuntimeError("Önce kanalı analiz et")
    a = r["analiz"]
    best = "\n".join(f"- {v['baslik']} | {v['izlenme']} izlenme | {'Shorts' if v['short'] else 'uzun'}" for v in a["en_iyi"])
    worst = "\n".join(f"- {v['baslik']} | {v['izlenme']}" for v in sorted(a["videolar"], key=lambda v: v["izlenme"])[:5])
    summ = json.dumps({"ozet": a["ozet"], "uzun": a["uzun"], "shorts": a["shorts_g"], "kural_onerileri": [x["metin"] for x in a["oneriler"]]}, ensure_ascii=False)
    prompt = (f"Bir YouTube kanalını analiz ediyorsun. Kanal: {a['kanal']['ad']}.\nSayılar: {summ}\nEn çok izlenenler:\n{best}\nEn az izlenenler:\n{worst}\n\n"
              "Kanal sahibine Türkçe, samimi ve net konuş. Veriye dayan, uydurma sayı verme. JSON dön:\n"
              '{"ozet":"2 cümlelik genel durum","oneriler":["somut yapılacak iş (en fazla 6 madde, her biri 1-2 cümle)"],'
              '"basliklar":["en çok tutan konulara benzer 6 yeni video başlığı fikri"],"dikkat":"kaçınması gereken 1 şey"}')
    return ai.ask(prompt, json_mode=True, temperature=0.6)
