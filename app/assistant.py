"""Sohbet asistanı: kullanıcı yazar, Gemini programın araçlarını çağırarak işi yapar."""
import json
import threading
import time
from pathlib import Path

import ai
from core import JOBS, VERI, read_json, write_json

HIST_FILE = VERI / "asistan.json"
_lock = threading.Lock()
MAX_STEPS = 8

SYS = """Sen B.E.K'in (Bul, Editle, Kaliteyi artır; eski adı Kesit Stüdyosu) içindeki asistansın. B.E.K; Kick/YouTube yayınlarından klip bulan, en iyi anları kesen,
Türkçe altyazı ekleyen, After Effects benzeri editörü olan, video/fotoğraf kalitesini artıran bir Windows programı.
NASIL CEVAP VERİRSİN:
- Türkçe, samimi ve ÇOK KISA yaz: en fazla 1-2 cümle. Liste, seçenek sıralama, uzun açıklama yok.
- Kullanıcı bir şey istediyse SORMADAN araçla yap. "İster misin?", "nasıl ilerleyelim?" gibi sorular sorma; en mantıklı yolu seç ve yap.
- Editörle ilgili her isteği araçlarla yap; gerçekten imkânsızsa (ör. sıfırdan resim çizmek) tek cümleyle söyle.
- Teknik terim (FFmpeg, API, model, proje_id) kullanma.
- Uzun işler arka planda çalışır; ilerleme sohbette kendiliğinden görünür ve bitince program haber verir. "Sık sık kontrol edeceğim" gibi yapamayacağın sözler verme.
- Kullanıcı "sorun var" derse "her şey yolunda" deme; neyin yanlış olduğunu kısaca sor ya da düzeltmeyi yap.
- Bir iş hata verirse sebebini sade dille söyle ve aynı işi bir kez daha dene (tekrar dene dendiğinde de).
EDİT:
- "Yüz", "yüz kısmı", "kamera", "adamın yüzü" denince Yüz + Oyun düzenindeki üstteki YÜZ kutusu kastedilir; yuzu_bul ile yüzü bulup oraya yerleştir.
- Editörde yapılabilen HER ŞEYİ sen de yapabilirsin: altyazı rengi/boyutu/yazı tipi/konumu (altyazi_stili), yazı ekleme/değiştirme/silme, renk filtresi ve efektler, zamanlı efektler, zoom, geçiş, biçim, ad, düzen, kesme, hız, ses.
  Özel bir araç yoksa önce proje_bilgisi ile yapıya bak, sonra ayar_degistir ile yap. "Yapamam" deme; mutlaka bir yolunu bul.
- Renk adlarını #RRGGBB'ye çevir (kırmızı #FF2D2D, sarı #FFE14D, beyaz #FFFFFF, siyah #000000, mavi #2D8CFF, yeşil #2DFF6A, mor #B84DFF, pembe #FF4FD8, turuncu #FF8A00).
- Düzen, kesme, hız, ses gibi değişiklikleri araçlarla açık projeye uygula (proje belirtilmediyse açık proje).
- Hangi projeden bahsedildiği belli değilse açık projeyi kullan; o da yoksa en son projeyi kullan.
- Sıfırdan resim üretemezsin. Paylaşımda son "Paylaş" tuşuna kullanıcı basar (platformlar otomatik paylaşıma izin vermiyor)."""

S = "string"
TOOLS = [
    {"name": "projeleri_listele", "description": "Kullanıcının projelerini (video düzenleme projeleri) en yeniden eskiye listeler.", },
    {"name": "proje_ac", "description": "Bir projeyi editörde açar.", "parameters": {"type": "object", "properties": {"proje_id": {"type": S}}, "required": ["proje_id"]}},
    {"name": "sayfa_ac", "description": "Programda bir sayfaya geçer.", "parameters": {"type": "object", "properties": {"sayfa": {"type": S, "enum": ["bul", "editor", "kalite", "ayarlar", "donustur"], "description": "bul=Klip Bulucu"}}, "required": ["sayfa"]}},
    {"name": "klip_ara", "description": "Kick/YouTube'da kanal, klip ya da konu arar (örn. 'rraenee', 'komik anlar'). Sonuçları Klip Bulucu'da da gösterir.", "parameters": {"type": "object", "properties": {"sorgu": {"type": S}}, "required": ["sorgu"]}},
    {"name": "otomatik_edit", "description": "Bir yayından/videodan en iyi anları seçip her biri için hazır kısa video projesi (altyazılı) oluşturur. Kaynak: video bağlantısı (Kick/YouTube), bilgisayardaki dosya yolu ya da 'acik_proje'.",
     "parameters": {"type": "object", "properties": {"kaynak": {"type": S}, "adet": {"type": "integer", "description": "kaç video (1-10), varsayılan 3"},
                                                     "bicim": {"type": S, "enum": ["dikey", "kaynak", "yatay", "kare"], "description": "dikey=Reels/Shorts 9:16, kaynak=videonun kendi boyutu"},
                                                     "altyazi": {"type": "boolean"}}, "required": ["kaynak"]}},
    {"name": "altyazi_olustur", "description": "Projedeki videoların Türkçe altyazısını çıkarır.", "parameters": {"type": "object", "properties": {"proje_id": {"type": S}}, "required": ["proje_id"]}},
    {"name": "disa_aktar", "description": "Projeyi MP4 olarak dışa aktarır.", "parameters": {"type": "object", "properties": {"proje_id": {"type": S}, "cozunurluk": {"type": "integer", "description": "720, 1080 ya da 1440"}, "fps": {"type": S, "description": "'kaynak' ya da 30/60"}}, "required": ["proje_id"]}},
    {"name": "kalite_artir", "description": "Bir video ya da fotoğrafın kalitesini yapay zekâ ile artırır.", "parameters": {"type": "object", "properties": {"dosya": {"type": S, "description": "dosya yolu"}, "mod": {"type": S, "enum": ["hizli", "en_iyi", "ust_duzey", "anime", "anime_ust_duzey", "klasik"], "description": "ust_duzey = en yüksek kalite (yavaş)"}, "cozunurluk": {"type": S, "enum": ["kaynak", "720", "1080", "1440", "2160", "x2", "x4"]}, "yuz": {"type": "boolean"}, "fps": {"type": S, "enum": ["kaynak", "30", "60"]}}, "required": ["dosya"]}},
    {"name": "paylasim_metni", "description": "Proje için YouTube Shorts, TikTok ve Instagram Reels başlık/açıklama/etiket yazar.", "parameters": {"type": "object", "properties": {"proje_id": {"type": S}, "not": {"type": S, "description": "isteğe bağlı ek istek (ton, vurgu)"}}, "required": ["proje_id"]}},
    {"name": "paylas", "description": "Paylaşım penceresini açar: dışa aktarılmış videoyu ve metni hazırlar, platformun yükleme sayfasını açar.", "parameters": {"type": "object", "properties": {"proje_id": {"type": S}, "platform": {"type": S, "enum": ["youtube", "tiktok", "instagram"]}}, "required": ["proje_id"]}},
    {"name": "arka_plan_sil", "description": "Fotoğrafın arka planını siler (şeffaf PNG).", "parameters": {"type": "object", "properties": {"dosya": {"type": S}}, "required": ["dosya"]}},
    {"name": "kapak_yap", "description": "Proje için kapak resmi (thumbnail) penceresini açar.", "parameters": {"type": "object", "properties": {"proje_id": {"type": S}}, "required": ["proje_id"]}},
    {"name": "yuzu_bul", "description": "Videodaki kişinin/kişilerin yüzünü otomatik bulur ve Yüz + Oyun düzenindeki üstteki YÜZ kutusunu yüzün olduğu yere yerleştirir.", "parameters": {"type": "object", "properties": {"proje_id": {"type": S}}, "required": ["proje_id"]}},
    {"name": "duzen", "description": "Videonun dikey ekrana yerleşimini değiştirir. yuz_oyun=üstte yüz altta oyun, tam_kirp=ekranı dolduracak şekilde kırp, bulanik=video ortada arka bulanık, sigdir=videonun tamamı.", "parameters": {"type": "object", "properties": {"proje_id": {"type": S}, "mod": {"type": S, "enum": ["yuz_oyun", "tam_kirp", "bulanik", "sigdir"]}, "yuz_orani": {"type": "integer", "description": "yuz_oyun'da üstteki yüz alanının yüksekliği (yüzde, 25-60)"}}, "required": ["proje_id", "mod"]}},
    {"name": "kes", "description": "Videoyu kısaltır: sadece bas_sn ile bit_sn arasını bırakır (projenin şu anki zamanına göre, saniye).", "parameters": {"type": "object", "properties": {"proje_id": {"type": S}, "bas_sn": {"type": "number"}, "bit_sn": {"type": "number"}}, "required": ["proje_id", "bas_sn", "bit_sn"]}},
    {"name": "hiz_ses", "description": "Videonun hızını ve/veya ses düzeyini değiştirir.", "parameters": {"type": "object", "properties": {"proje_id": {"type": S}, "hiz_yuzde": {"type": "integer", "description": "100 normal, 150 = 1.5x"}, "ses_yuzde": {"type": "integer", "description": "100 normal, 0 sessiz, 200 iki kat"}}, "required": ["proje_id"]}},
    {"name": "proje_bilgisi", "description": "Açık projenin şu anki halini verir: altyazı stili, yazılar, renk/efekt ayarları, zoomlar, efekt katmanları, geçiş, biçim, süre. Bir şeyi değiştirmeden önce ne olduğunu görmek için kullan.", "parameters": {"type": "object", "properties": {"proje_id": {"type": S}}}},
    {"name": "altyazi_stili", "description": "Altyazının görünüşünü değiştirir. Renkleri #RRGGBB olarak ver (kırmızı=#FF2D2D, sarı=#FFE14D, beyaz=#FFFFFF, siyah=#000000, yeşil=#2DFF6A, mavi=#2D8CFF, mor=#B84DFF, pembe=#FF4FD8, turuncu=#FF8A00). Sadece verilen alanlar değişir.",
     "parameters": {"type": "object", "properties": {"proje_id": {"type": S}, "renk": {"type": S, "description": "yazı rengi"}, "vurgu_rengi": {"type": S, "description": "o an söylenen kelimenin rengi (karaoke)"},
        "kontur_rengi": {"type": S}, "kontur_kalinligi": {"type": "integer", "description": "0-20"}, "boyut": {"type": "integer", "description": "40-160, normal 88"},
        "yazi_tipi": {"type": S, "enum": ["poppins-black", "poppins", "anton", "bangers"]}, "konum": {"type": "integer", "description": "dikey konum yüzde: 10 üst, 50 orta, 68 normal, 85 alt"},
        "buyuk_harf": {"type": "boolean"}, "karaoke": {"type": "boolean", "description": "söylenen kelime renklensin"}, "animasyon": {"type": "boolean"}, "golge": {"type": "boolean"},
        "kelime_sayisi": {"type": "integer", "description": "ekranda aynı anda kaç kelime (1-6)"}, "gizle": {"type": "boolean", "description": "true: altyazıyı gizle, false: göster"}}}},
    {"name": "yazi_ekle", "description": "Videoya yazı (başlık, etiket) ekler. Süre verilmezse videonun tamamında durur.",
     "parameters": {"type": "object", "properties": {"proje_id": {"type": S}, "metin": {"type": S}, "bas_sn": {"type": "number"}, "bit_sn": {"type": "number"},
        "konum": {"type": "integer", "description": "dikey konum yüzde: 10 üst, 50 orta, 85 alt"}, "renk": {"type": S}, "kutu": {"type": "boolean", "description": "arkasında renkli kutu"},
        "kutu_rengi": {"type": S}, "boyut": {"type": "integer", "description": "30-200, normal 80"}, "yazi_tipi": {"type": S, "enum": ["poppins-black", "poppins", "anton", "bangers"]},
        "animasyon": {"type": S, "enum": ["pop", "slide", "fade", "type", "none"]}, "buyuk_harf": {"type": "boolean"}}, "required": ["metin"]}},
    {"name": "yazi_duzenle", "description": "Projedeki yazıları değiştirir ya da siler. hedef: yazının metni (bir kısmı da olur), sırası (1, 2...) ya da 'hepsi'.",
     "parameters": {"type": "object", "properties": {"proje_id": {"type": S}, "hedef": {"type": S}, "sil": {"type": "boolean"}, "metin": {"type": S, "description": "yeni metin"},
        "bas_sn": {"type": "number"}, "bit_sn": {"type": "number"}, "konum": {"type": "integer"}, "renk": {"type": S}, "kutu": {"type": "boolean"}, "kutu_rengi": {"type": S},
        "boyut": {"type": "integer"}, "yazi_tipi": {"type": S, "enum": ["poppins-black", "poppins", "anton", "bangers"]}, "animasyon": {"type": S, "enum": ["pop", "slide", "fade", "type", "none"]}, "buyuk_harf": {"type": "boolean"}}, "required": ["hedef"]}},
    {"name": "renk_ayari", "description": "Videonun rengini ve genel efektlerini ayarlar. Sayılar -100..100 (0 normal). Sadece verilen alanlar değişir.",
     "parameters": {"type": "object", "properties": {"proje_id": {"type": S}, "hazir": {"type": S, "enum": ["none", "sinematik", "canli", "sb", "vintage", "soguk", "sicak", "neon"], "description": "renk filtresi; sb=siyah beyaz, none=filtre yok"},
        "parlaklik": {"type": "integer"}, "kontrast": {"type": "integer"}, "doygunluk": {"type": "integer"}, "sicaklik": {"type": "integer"},
        "vinyet": {"type": "boolean"}, "gren": {"type": "boolean"}, "parlama": {"type": "boolean"}, "rgb_kayma": {"type": "boolean"}, "keskinlestir": {"type": "boolean"}, "ayna": {"type": "boolean", "description": "görüntüyü sağa-sola çevir"},
        "acilis_karartma": {"type": "boolean", "description": "başta siyahtan açılsın"}, "kapanis_karartma": {"type": "boolean", "description": "sonda siyaha kapansın"}}}},
    {"name": "efekt_ekle", "description": "Belirli bir zaman aralığına efekt ekler (glitch, flaş, sarsıntı, VHS...). Süre verilmezse 1 saniye.",
     "parameters": {"type": "object", "properties": {"proje_id": {"type": S}, "tur": {"type": S, "enum": ["glitch", "rgbsplit", "pixel", "glow", "rainbow", "softlight", "leak", "flare", "flash", "strobe", "film", "vhs", "motionblur", "dirblur", "defocus", "shake", "quake", "punch", "posterize", "duotone", "halftone", "edges", "bwpop", "colorkeep", "invert", "symmetry"],
        "description": "shake=hafif kamera, quake=deprem, punch=yumruk, leak=ışık sızıntısı, bwpop=siyah-beyaz vurgu, colorkeep=kırmızıyı tut, pixel=mozaik"},
        "bas_sn": {"type": "number"}, "bit_sn": {"type": "number"}, "siddet": {"type": "integer", "description": "0-100, normal 70"}}, "required": ["tur"]}},
    {"name": "efektleri_sil", "description": "Zamanlı efektleri, zoomları ya da yazıları toplu siler.", "parameters": {"type": "object", "properties": {"proje_id": {"type": S}, "ne": {"type": S, "enum": ["efektler", "zoomlar", "yazilar", "hepsi"]}}, "required": ["ne"]}},
    {"name": "zoom_ekle", "description": "Belirli anda yakınlaştırma (zoom) ekler, istenirse sarsıntılı.", "parameters": {"type": "object", "properties": {"proje_id": {"type": S}, "an_sn": {"type": "number"}, "sure_sn": {"type": "number", "description": "normal 0.8"}, "oran_yuzde": {"type": "integer", "description": "125 = %25 yakın"}, "sarsinti": {"type": "boolean"}}, "required": ["an_sn"]}},
    {"name": "gecis", "description": "Klipler arası geçiş efekti.", "parameters": {"type": "object", "properties": {"proje_id": {"type": S}, "tur": {"type": S, "enum": ["none", "dip", "flash", "glitch", "slide", "swirl", "white", "zoom"]}, "sure_sn": {"type": "number"}}, "required": ["tur"]}},
    {"name": "bicim_degistir", "description": "Videonun biçimini değiştirir.", "parameters": {"type": "object", "properties": {"proje_id": {"type": S}, "bicim": {"type": S, "enum": ["dikey", "yatay", "kare", "kaynak"], "description": "dikey=Reels/Shorts, kaynak=videonun kendi boyutu"}}, "required": ["bicim"]}},
    {"name": "baslik_degistir", "description": "Projenin adını değiştirir.", "parameters": {"type": "object", "properties": {"proje_id": {"type": S}, "baslik": {"type": S}}, "required": ["baslik"]}},
    {"name": "ayar_degistir", "description": "Diğer araçların yapamadığı HER ŞEY için: projedeki herhangi bir ayarı yolundan değiştirir. Önce proje_bilgisi ile yapıya bak. Yol örnekleri: style.hl, style.outlineW, effects.bright, effects.texts.0.color, effects.zooms.1.z, media.music.vol, effects.hide.cap, clips.0.volume, clips.0.layout.split. deger JSON olarak (\"#FF0000\", 12, true, null...).",
     "parameters": {"type": "object", "properties": {"proje_id": {"type": S}, "yol": {"type": S}, "deger": {"type": S, "description": "JSON değer"}}, "required": ["yol", "deger"]}},
    {"name": "isler", "description": "Çalışan ve son biten işleri (indirme, altyazı, dışa aktarma...) gösterir.", },
    {"name": "son_dosyalar", "description": "Son dışa aktarılan videoların ve kalite artırılmış dosyaların yollarını listeler.", },
]


def _srv():
    import server
    return server


def _pid(srv, a, ctx):
    pid = (a.get("proje_id") or "").strip()
    if pid in ("", "acik_proje", "acik", "current", "son") or not srv.load_project(pid):
        pid = ctx.get("project") or ((srv.all_projects() or [{}])[0].get("id") if pid in ("", "son", "acik_proje", "acik", "current") else pid)
    p = srv.load_project(pid) if pid else None
    if not p:
        raise ValueError("Proje bulunamadı. Önce projeleri_listele ile doğru projeyi seç.")
    return p


RENKLER = {"kırmızı": "#FF2D2D", "kirmizi": "#FF2D2D", "sarı": "#FFE14D", "sari": "#FFE14D", "beyaz": "#FFFFFF", "siyah": "#000000", "yeşil": "#2DFF6A", "yesil": "#2DFF6A",
           "mavi": "#2D8CFF", "lacivert": "#1E3A8A", "mor": "#B84DFF", "pembe": "#FF4FD8", "turuncu": "#FF8A00", "gri": "#9CA3AF", "altın": "#FFC83D", "turkuaz": "#00D0FF", "kahverengi": "#8B5A2B"}


def _renk(v):
    if v is None or v == "":
        return None
    v = str(v).strip()
    if v.lower() in RENKLER:
        return RENKLER[v.lower()]
    import re as _re
    if _re.fullmatch(r"#?[0-9a-fA-F]{6}", v):
        return "#" + v.lstrip("#").upper()
    if _re.fullmatch(r"#?[0-9a-fA-F]{3}", v):
        h = v.lstrip("#")
        return "#" + "".join(c * 2 for c in h).upper()
    raise ValueError(f"Renk anlaşılmadı: {v}")


def _edit(srv, a, ctx, actions, fn):
    """Projeyi kilitle, değiştir, kaydet, editörü yenile."""
    p = _pid(srv, a, ctx)
    with srv._plock:
        p = srv.load_project(p["id"])
        msg = fn(p)
        srv.save_project(p)
    actions.append({"type": "reload", "id": p["id"]})
    return msg


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _tx_apply(t, a, total):
    if a.get("metin") is not None:
        t["text"] = str(a["metin"])
    if a.get("bas_sn") is not None:
        t["s"] = round(_clamp(float(a["bas_sn"]), 0, max(0.1, total)), 2)
    if a.get("bit_sn") is not None:
        t["e"] = round(_clamp(float(a["bit_sn"]), 0.1, max(0.1, total)), 2)
    if t.get("e", 0) <= t.get("s", 0):
        t["e"] = round(min(total, t["s"] + 2), 2)
    if a.get("konum") is not None:
        t["y"] = _clamp(int(a["konum"]), 3, 97)
        if isinstance(t.get("tf"), dict):
            t["tf"]["y"] = t["y"] / 100
    for k, key in (("renk", "color"), ("kutu_rengi", "boxColor")):
        if a.get(k):
            t[key] = _renk(a[k])
    if a.get("kutu") is not None:
        t["box"] = bool(a["kutu"])
    if a.get("boyut") is not None:
        t["size"] = _clamp(int(a["boyut"]), 20, 260)
    if a.get("yazi_tipi"):
        t["font"] = a["yazi_tipi"]
    if a.get("animasyon"):
        t["anim"] = a["animasyon"]
    if a.get("buyuk_harf") is not None:
        t["upper"] = bool(a["buyuk_harf"])


def _summary(p):
    import model
    fx = p.get("effects") or {}
    return {"baslik": p.get("title"), "bicim": p.get("format"), "sure_sn": round(model.total_duration(p), 2), "klip_sayisi": len(p.get("clips") or []),
            "altyazi_stili": p.get("style"), "altyazi_var": any(c.get("captions") for c in p.get("clips") or []),
            "renk": {k: fx.get(k) for k in ("preset", "bright", "contrast", "sat", "temp", "vignette", "grain", "glow", "rgb", "sharpen", "mirror", "fadeIn", "fadeOut")},
            "yazilar": [{"sira": i + 1, "metin": t.get("text"), "bas": t.get("s"), "bit": t.get("e"), "renk": t.get("color"), "boyut": t.get("size"), "konum": t.get("y"), "kutu": t.get("box", True)} for i, t in enumerate(fx.get("texts") or [])],
            "zoomlar": fx.get("zooms") or [], "efektler": [{"tur": L.get("kind"), "bas": L.get("s"), "bit": L.get("e"), "siddet": L.get("i")} for L in fx.get("fxLayers") or []],
            "gecis": fx.get("transition"), "gizli": fx.get("hide") or {}, "muzik": (p.get("media") or {}).get("music"),
            "klipler": [{"sira": i + 1, "hiz": c.get("speed"), "ses": c.get("volume", 1), "duzen": (c.get("layout") or {}).get("mode")} for i, c in enumerate(p.get("clips") or [])]}


def run_edit_tool(name, a, ctx, actions, srv):
    import model
    if name == "proje_bilgisi":
        return _summary(_pid(srv, a, ctx))

    def stil(p):
        st = p.setdefault("style", {})
        for k, key in (("renk", "color"), ("vurgu_rengi", "hl"), ("kontur_rengi", "outline")):
            if a.get(k):
                st[key] = _renk(a[k])
        if a.get("kontur_kalinligi") is not None:
            st["outlineW"] = _clamp(int(a["kontur_kalinligi"]), 0, 30)
        if a.get("boyut") is not None:
            st["size"] = _clamp(int(a["boyut"]), 30, 200)
        if a.get("yazi_tipi"):
            st["font"] = a["yazi_tipi"]
        if a.get("konum") is not None:
            st["y"] = _clamp(int(a["konum"]), 5, 95)
        for k, key in (("buyuk_harf", "upper"), ("karaoke", "karaoke"), ("animasyon", "anim"), ("golge", "shadow")):
            if a.get(k) is not None:
                st[key] = bool(a[k])
        if a.get("kelime_sayisi") is not None:
            st["maxWords"] = _clamp(int(a["kelime_sayisi"]), 1, 8)
            for c in p.get("clips") or []:  # altyazıyı yeni kelime sayısına göre böl
                if c.get("words"):
                    try:
                        import transcribe
                        c["captions"] = transcribe.chunk_words(c["words"], max_words=st["maxWords"])
                    except Exception:
                        pass
        if a.get("gizle") is not None:
            p.setdefault("effects", {}).setdefault("hide", {})["cap"] = bool(a["gizle"])
        if not any(c.get("captions") for c in p.get("clips") or []):
            return "Stil ayarlandı. Bu videoda henüz altyazı yok; altyazı oluşturunca bu stille çıkacak."
        return "Altyazı stili değişti."

    def yazi(p):
        fx = p.setdefault("effects", {})
        total = model.total_duration(p)
        t = {"id": __import__("core").new_id("t"), "text": "", "s": 0.0, "e": round(total, 2), "y": 18, "size": 80, "color": "#FFFFFF",
             "box": True, "boxColor": "#FF3D8B", "font": "poppins-black", "anim": "pop", "upper": True}
        _tx_apply(t, a, total)
        fx.setdefault("texts", []).append(t)
        return f"Yazı eklendi: {t['text']}"

    def yazi_duz(p):
        fx = p.setdefault("effects", {})
        texts = fx.get("texts") or []
        h = str(a.get("hedef") or "").strip()
        if h.lower() in ("hepsi", "tümü", "tumu", "all"):
            sel = list(texts)
        elif h.isdigit():
            sel = [texts[int(h) - 1]] if 0 < int(h) <= len(texts) else []
        else:
            sel = [t for t in texts if h.lower() in (t.get("text") or "").lower()]
        if not sel:
            raise ValueError("Bu yazıyı bulamadım. Projedeki yazılar: " + ", ".join((t.get("text") or "")[:30] for t in texts) if texts else "Projede yazı yok.")
        if a.get("sil"):
            fx["texts"] = [t for t in texts if t not in sel]
            return f"{len(sel)} yazı silindi."
        total = model.total_duration(p)
        for t in sel:
            _tx_apply(t, a, total)
        return f"{len(sel)} yazı güncellendi."

    def renk(p):
        fx = p.setdefault("effects", {})
        if a.get("hazir"):
            fx["preset"] = a["hazir"]
        for k, key in (("parlaklik", "bright"), ("kontrast", "contrast"), ("doygunluk", "sat"), ("sicaklik", "temp")):
            if a.get(k) is not None:
                fx[key] = _clamp(int(a[k]), -100, 100)
        for k, key in (("vinyet", "vignette"), ("gren", "grain"), ("parlama", "glow"), ("rgb_kayma", "rgb"), ("keskinlestir", "sharpen"),
                       ("ayna", "mirror"), ("acilis_karartma", "fadeIn"), ("kapanis_karartma", "fadeOut")):
            if a.get(k) is not None:
                fx[key] = bool(a[k])
        return "Renk ve efektler ayarlandı."

    def efekt(p):
        fx = p.setdefault("effects", {})
        total = model.total_duration(p)
        s0 = _clamp(float(a.get("bas_sn") or 0), 0, max(0, total - .1))
        e0 = _clamp(float(a.get("bit_sn") or (s0 + 1)), s0 + .1, total)
        fx.setdefault("fxLayers", []).append({"id": __import__("core").new_id("f"), "kind": a["tur"], "s": round(s0, 2), "e": round(e0, 2), "i": _clamp(int(a.get("siddet") or 70), 0, 100), "params": {}})
        return f"Efekt eklendi ({s0:.1f}-{e0:.1f} sn)."

    def sil(p):
        fx = p.setdefault("effects", {})
        ne = a.get("ne")
        keys = {"efektler": ["fxLayers"], "zoomlar": ["zooms"], "yazilar": ["texts"], "hepsi": ["fxLayers", "zooms", "texts"]}.get(ne, [])
        for k in keys:
            fx[k] = []
        return "Silindi."

    def zoom(p):
        fx = p.setdefault("effects", {})
        fx.setdefault("zooms", []).append({"t": round(float(a["an_sn"]), 2), "d": _clamp(float(a.get("sure_sn") or .8), .2, 5), "z": _clamp(int(a.get("oran_yuzde") or 125), 105, 250) / 100, "shake": bool(a.get("sarsinti"))})
        fx["zooms"].sort(key=lambda z: z["t"])
        return "Zoom eklendi."

    def gecis(p):
        fx = p.setdefault("effects", {})
        fx["transition"] = {"type": a["tur"], "d": _clamp(float(a.get("sure_sn") or .4), .15, 1.5)}
        if a["tur"] != "none" and len(p.get("clips") or []) < 2:
            return "Geçiş ayarlandı ama tek klip var; geçiş klipler arasında görünür."
        return "Geçiş ayarlandı."

    def bicim(p):
        fmt = a["bicim"]
        c0 = (p.get("clips") or [None])[0]
        if fmt == "kaynak":
            fmt = f"kaynak:{c0['width']}x{c0['height']}" if c0 else "kaynak"
        p["format"] = fmt
        for c in p.get("clips") or []:
            cw, ch = model.content_size(c)
            c["layout"] = model.fix_layout(model.default_layout(fmt, cw, ch), fmt, cw, ch)
        return "Biçim değişti."

    def baslik(p):
        p["title"] = str(a["baslik"])[:120]
        return "Ad değişti."

    def ayar(p):
        import json as _j
        yol = [x for x in str(a["yol"]).strip().split(".") if x]
        if not yol or yol[0] not in ("style", "effects", "media", "clips", "overlays", "title"):
            raise ValueError("Bu ayara dokunamam. Yol style., effects., media., clips., overlays. ile başlamalı.")
        if yol[0] == "clips" and len(yol) > 2 and yol[2] in ("source", "id", "words", "src_dur", "width", "height"):
            raise ValueError("Bu bilgi değiştirilemez.")
        raw = a.get("deger")
        try:
            val = _j.loads(raw) if isinstance(raw, str) else raw
        except Exception:
            val = raw
        if isinstance(val, str) and val.lower() in RENKLER:
            val = RENKLER[val.lower()]
        cur = p
        for i, k in enumerate(yol[:-1]):
            nxt = yol[i + 1]
            if isinstance(cur, list):
                cur = cur[int(k)]
            else:
                if k not in cur or cur[k] is None:
                    cur[k] = [] if nxt.isdigit() else {}
                cur = cur[k]
        last = yol[-1]
        if isinstance(cur, list):
            cur[int(last)] = val
        else:
            cur[last] = val
        return f"{'.'.join(yol)} = {val}"

    fn = {"altyazi_stili": stil, "yazi_ekle": yazi, "yazi_duzenle": yazi_duz, "renk_ayari": renk, "efekt_ekle": efekt, "efektleri_sil": sil,
          "zoom_ekle": zoom, "gecis": gecis, "bicim_degistir": bicim, "baslik_degistir": baslik, "ayar_degistir": ayar}[name]
    return _edit(srv, a, ctx, actions, fn)


EDIT_TOOLS = {"proje_bilgisi", "altyazi_stili", "yazi_ekle", "yazi_duzenle", "renk_ayari", "efekt_ekle", "efektleri_sil", "zoom_ekle", "gecis",
              "bicim_degistir", "baslik_degistir", "ayar_degistir"}


def run_tool(name, a, ctx, actions):
    srv = _srv()
    if name in EDIT_TOOLS:
        return run_edit_tool(name, a, ctx, actions, srv)
    if name == "projeleri_listele":
        return [{"proje_id": p["id"], "baslik": p.get("title"), "sure_sn": round(p.get("duration") or 0, 1), "klip": p.get("clips"),
                 "altyazi": p.get("subs_status"), "disa_aktarildi": bool(p.get("exports")), "bicim": p.get("format")}
                for p in srv.all_projects()[:20]]
    if name == "proje_ac":
        p = _pid(srv, a, ctx)
        actions.append({"type": "open_project", "id": p["id"]})
        return f"'{p.get('title')}' editörde açıldı."
    if name == "sayfa_ac":
        pg = {"bul": "finder", "editor": "editor", "kalite": "kalite", "ayarlar": "settings", "donustur": "donustur"}.get(a.get("sayfa"), "finder")
        actions.append({"type": "go", "page": pg})
        return "Açıldı."
    if name == "klip_ara":
        q = (a.get("sorgu") or "").strip()
        actions.append({"type": "search", "q": q})
        try:
            import kick
            r = kick.list_source(q)
        except Exception as e:
            return f"Arama Klip Bulucu'da başlatıldı ama sonuç alınamadı: {str(e)[:150]}"
        items = []
        for key in ("videos", "clips", "shorts"):
            for it in (r.get(key) or [])[:6]:
                items.append({"tur": key, "baslik": it.get("title"), "url": it.get("url"), "sure_sn": it.get("duration"), "kanal": it.get("channel")})
        return {"kanal": r.get("title") or r.get("slug"), "sonuclar": items[:15]} if items else "Sonuç bulunamadı."
    if name == "otomatik_edit":
        src = (a.get("kaynak") or "").strip()
        title = None
        if src in ("acik_proje", "acik", "") or src == ctx.get("project"):
            p = _pid(srv, {"proje_id": ctx.get("project") if src in ("acik_proje", "acik", "") else src}, ctx)
            if not p.get("clips"):
                raise ValueError("Açık projede video yok.")
            src, title = p["clips"][0]["source"], p.get("title")
        local = not src.lower().startswith("http")
        if local and not Path(src).exists():
            raise ValueError("Dosya bulunamadı: " + src)
        title = title or (Path(src).stem if local else "Yayın")
        n = int(a.get("adet") or 3)
        fmt = a.get("bicim") or "dikey"
        j = JOBS.start("otoedit", "Otomatik edit: " + title[:36], srv.job_autoedit, src, local, title, n, fmt, a.get("altyazi", True), heavy=True)
        actions.append({"type": "job", "id": j.id})
        return {"is": j.id, "durum": f"Otomatik edit başladı ({n} video). Bitince projeler açılır."}
    if name == "altyazi_olustur":
        p = _pid(srv, a, ctx)
        j = srv.start_transcribe(p["id"], p.get("title") or "")
        actions.append({"type": "job", "id": j.id})
        return {"is": j.id, "durum": "Altyazı çıkarılıyor."}
    if name == "disa_aktar":
        p = _pid(srv, a, ctx)
        opts = {"cozunurluk": int(a.get("cozunurluk") or 1080), "fps": str(a.get("fps") or "kaynak")}
        j = JOBS.start("aktar", "Dışa aktar: " + p["title"][:40], srv.job_export, p["id"], opts, heavy=True)
        actions.append({"type": "job", "id": j.id})
        return {"is": j.id, "durum": "Dışa aktarma başladı."}
    if name == "kalite_artir":
        import enhance
        f = (a.get("dosya") or "").strip()
        if not Path(f).exists():
            raise ValueError("Dosya bulunamadı: " + f)
        img = enhance.is_image(f)
        mod = a.get("mod") or ("en_iyi" if img else "hizli")
        o = {"model": {"hizli": "hizli", "en_iyi": "ultra", "ust_duzey": "ultra", "anime": "anime_pro", "anime_ust_duzey": "anime_pro", "klasik": "klasik"}.get(mod, "hizli"),
             "hedef": a.get("cozunurluk") or ("x2" if img else "1080"), "yuz": bool(a.get("yuz")), "fps": a.get("fps") or "kaynak"}
        if mod == "ust_duzey":
            o.update(keskin=55, detay=20, gurultu=20, blok=True, bant=True, yuz=True, yuz_model="codeformer", titreme=40, kayipsiz=True, kalite="ust", codec="h265")
        if mod == "anime_ust_duzey":
            o.update(keskin=70, gurultu=35, yumusat=25, blok=True, bant=True, titreme=30, kayipsiz=True, kalite="ust", codec="h265")
        fn = enhance.process_image if img else enhance.process
        j = JOBS.start("kalite", ("Fotoğraf: " if img else "Kalite: ") + Path(f).stem[:40], fn, f, o, heavy=True)
        actions.append({"type": "job", "id": j.id})
        return {"is": j.id, "durum": "Kalite artırma başladı."}
    if name == "paylasim_metni":
        p = _pid(srv, a, ctx)
        meta = ai.write_meta(p.get("title") or "", srv.project_text(p), (p.get("meta") or {}).get("oto_edit", {}).get("kaynak", ""), a.get("not") or "")
        with srv._plock:
            q = srv.load_project(p["id"])
            q["paylasim"] = meta
            srv.save_project(q)
        actions.append({"type": "meta", "id": p["id"]})
        return meta
    if name == "paylas":
        p = _pid(srv, a, ctx)
        actions.append({"type": "share", "id": p["id"], "platform": a.get("platform") or "youtube"})
        return "Paylaşım penceresi açıldı."
    if name == "kapak_yap":
        p = _pid(srv, a, ctx)
        actions.append({"type": "thumb", "id": p["id"]})
        return "Kapak penceresi açıldı."
    if name == "arka_plan_sil":
        import imgtools
        f = (a.get("dosya") or "").strip()
        if not Path(f).exists():
            raise ValueError("Dosya bulunamadı: " + f)
        j = JOBS.start("gorsel", "Arka plan siliniyor: " + Path(f).stem[:30], imgtools.job_remove_bg, f, heavy=True)
        actions.append({"type": "job", "id": j.id})
        return {"is": j.id, "durum": "Arka plan siliniyor."}
    if name == "yuzu_bul":
        p = _pid(srv, a, ctx)
        if not p.get("clips"):
            raise ValueError("Projede video yok.")
        j = JOBS.start("yuz", "Yüz bulunuyor: " + (p.get("title") or "")[:30], srv.job_face, p["id"], None)
        actions.append({"type": "job", "id": j.id})
        return {"durum": "Yüz aranıyor, bulununca YÜZ kutusu oraya yerleşecek."}
    if name in ("duzen", "kes", "hiz_ses"):
        p = _pid(srv, a, ctx)
        if not p.get("clips"):
            raise ValueError("Projede video yok.")
        import model
        with srv._plock:
            p = srv.load_project(p["id"])
            fmt = p.get("format") or "dikey"
            if name == "duzen":
                m = {"yuz_oyun": "split", "tam_kirp": "crop", "bulanik": "blur", "sigdir": "fit"}.get(a.get("mod"), "fit")
                if m == "split" and fmt != "dikey":
                    raise ValueError("Yüz + Oyun düzeni sadece dikey videoda olur.")
                for c in p["clips"]:
                    lay = c.setdefault("layout", {})
                    lay["mode"] = m
                    if a.get("yuz_orani"):
                        lay["split"] = max(.2, min(.65, int(a["yuz_orani"]) / 100))
                    cw, ch = model.content_size(c)
                    model.fix_layout(lay, fmt, cw, ch)
                msg = "Düzen değişti."
            elif name == "kes":
                bas, bit = float(a.get("bas_sn") or 0), float(a.get("bit_sn") or 0)
                if bit <= bas:
                    raise ValueError("Bitiş, başlangıçtan sonra olmalı.")
                tl, _ = model.timeline(p)
                keep = []
                for c, t0, L in tl:
                    a0, a1 = max(bas, t0), min(bit, t0 + L)
                    if a1 - a0 < .05:
                        continue
                    sp = float(c.get("speed") or 1)
                    nin = c["in"] + (a0 - t0) * sp
                    c["out"], c["in"] = round(c["in"] + (a1 - t0) * sp, 3), round(nin, 3)
                    keep.append(c)
                if not keep:
                    raise ValueError("Bu aralıkta video yok.")
                p["clips"] = keep
                msg = f"Video {bit - bas:.1f} saniyeye kısaltıldı."
            else:
                for c in p["clips"]:
                    if a.get("hiz_yuzde"):
                        c["speed"] = max(.25, min(4, int(a["hiz_yuzde"]) / 100))
                    if a.get("ses_yuzde") is not None:
                        c["volume"] = max(0, min(3, int(a["ses_yuzde"]) / 100))
                msg = "Ayarlandı."
            srv.save_project(p)
        actions.append({"type": "reload", "id": p["id"]})
        return msg
    if name == "isler":
        return [{"baslik": j["title"], "durum": j["status"], "yuzde": round(j["progress"] * 100), "mesaj": j["message"]} for j in list(reversed(JOBS.list()))[:10]]
    if name == "son_dosyalar":
        out = []
        for p in srv.all_projects()[:15]:
            for e in (p.get("exports") or [])[-2:]:
                out.append({"proje": p.get("title"), "dosya": e.get("path"), "ad": e.get("name")})
        return out[:20] or "Henüz dışa aktarılmış video yok."
    raise ValueError("Bilinmeyen araç: " + name)


def _load():
    d = read_json(HIST_FILE) or {}
    return d.get("hist") or [], d.get("chat") or []


def _save(hist, chat):
    # geçmiş çok uzamasın: kullanıcı mesajı sınırından kes (araç çağrısı çiftleri bölünmesin)
    if len(hist) > 40:
        cut = len(hist) - 40
        while cut < len(hist) and not (hist[cut].get("role") == "user" and any("text" in p for p in hist[cut].get("parts", []))):
            cut += 1
        hist = hist[cut:]
    write_json(HIST_FILE, {"hist": hist, "chat": chat[-100:]})


def history():
    return _load()[1]


def reset():
    write_json(HIST_FILE, {"hist": [], "chat": []})


def _ctx_text(ctx):
    srv = _srv()
    lines = [f"Şu anki sayfa: {ctx.get('page') or 'bilinmiyor'}"]
    if ctx.get("project"):
        p = srv.load_project(ctx["project"])
        if p:
            import model
            lay = ((p.get("clips") or [{}])[0].get("layout") or {}).get("mode", "-")
            lines.append(f"Açık projenin süresi {model.total_duration(p):.1f} sn, düzeni {dict(split='yuz_oyun', crop='tam_kirp', blur='bulanik', fit='sigdir').get(lay, lay)}")
            lines.append(f"Açık proje: '{p.get('title')}' (proje_id={p['id']}, {len(p.get('clips') or [])} video, biçim {p.get('format')}, "
                         f"altyazı {'var' if any(c.get('captions') for c in p.get('clips') or []) else 'yok'}, "
                         f"dışa aktarım {'var' if p.get('exports') else 'yok'})")
    if ctx.get("kalite"):
        lines.append(f"Kalite sayfasında açık dosya: {ctx['kalite']}")
    lines.append(f"Saat: {time.strftime('%d.%m.%Y %H:%M')}")
    return "\n".join(lines)


def chat(message, ctx):
    with _lock:
        hist, log = _load()
        hist.append({"role": "user", "parts": [{"text": message}]})
        log.append({"rol": "sen", "metin": message, "t": time.time()})
        actions, used = [], []
        reply = ""
        system = SYS + "\n\nDurum:\n" + _ctx_text(ctx)
        try:
            for _ in range(MAX_STEPS):
                c = ai.generate(hist, system=system, tools=TOOLS, temperature=0.5)
                hist.append(c)
                calls = [p["functionCall"] for p in c.get("parts", []) if "functionCall" in p]
                if not calls:
                    reply = ai.text_of(c).strip()
                    break
                resp = []
                for fc in calls:
                    nm, args = fc.get("name"), fc.get("args") or {}
                    try:
                        res = run_tool(nm, args, ctx, actions)
                        used.append(nm)
                    except Exception as e:
                        res = {"hata": str(e)[:300]}
                    part = {"functionResponse": {"name": nm, "response": {"sonuc": json.loads(json.dumps(res, default=str))}}}
                    if fc.get("id"):
                        part["functionResponse"]["id"] = fc["id"]
                    resp.append(part)
                hist.append({"role": "user", "parts": resp})
            else:
                reply = reply or "Bu iş beklediğimden uzun sürdü, adım adım tekrar ister misin?"
        except ai.AIError as e:
            # yarım kalan araç çağrısı geçmişi bozmasın
            while hist and hist[-1].get("role") != "user":
                hist.pop()
            if hist and hist[-1].get("parts") and "text" in hist[-1]["parts"][0]:
                hist.pop()
            _save(hist, log)
            raise
        if not reply:
            reply = "Tamamdır." if used else "Bir şey anlayamadım, tekrar yazar mısın?"
        log.append({"rol": "ai", "metin": reply, "t": time.time(), "araclar": used})
        _save(hist, log)
        return {"reply": reply, "actions": actions, "tools": used}


TOOL_LABEL = {"proje_bilgisi": "Projeye bakılıyor", "altyazi_stili": "Altyazı ayarlanıyor", "yazi_ekle": "Yazı ekleniyor", "yazi_duzenle": "Yazı düzenleniyor", "renk_ayari": "Renk ayarlanıyor", "efekt_ekle": "Efekt ekleniyor", "efektleri_sil": "Siliniyor", "zoom_ekle": "Zoom ekleniyor", "gecis": "Geçiş ayarlanıyor", "bicim_degistir": "Biçim değişiyor", "baslik_degistir": "Ad değişiyor", "ayar_degistir": "Ayar değişiyor", "yuzu_bul": "Yüz aranıyor", "duzen": "Düzen değiştiriliyor", "kes": "Kesiliyor", "hiz_ses": "Ayarlanıyor", "projeleri_listele": "Projeler alınıyor", "proje_ac": "Proje açılıyor", "sayfa_ac": "Sayfa açılıyor", "klip_ara": "Aranıyor",
              "otomatik_edit": "Otomatik edit başlatılıyor", "altyazi_olustur": "Altyazı başlatılıyor", "disa_aktar": "Dışa aktarma başlatılıyor",
              "kalite_artir": "Kalite artırma başlatılıyor", "paylasim_metni": "Paylaşım metni yazılıyor", "paylas": "Paylaşım hazırlanıyor",
              "arka_plan_sil": "Arka plan siliniyor", "kapak_yap": "Kapak açılıyor", "isler": "İşlere bakılıyor", "son_dosyalar": "Dosyalara bakılıyor"}


def chat_stream(message, ctx):
    """Akışlı sohbet: olayları sözlük olarak üretir (text / tool / done / error)."""
    if not _lock.acquire(timeout=120):
        yield {"type": "error", "message": "Asistan önceki mesajla meşgul, birazdan tekrar dene."}
        return
    try:
        hist, log = _load()
        hist.append({"role": "user", "parts": [{"text": message}]})
        log.append({"rol": "sen", "metin": message, "t": time.time()})
        actions, used, reply = [], [], ""
        system = SYS + "\n\nDurum:\n" + _ctx_text(ctx)
        try:
            for _ in range(MAX_STEPS):
                content = None
                step_text = ""
                for kind, val in ai.stream(hist, system=system, tools=TOOLS):
                    if kind == "text":
                        step_text += val
                        yield {"type": "text", "text": val}
                    else:
                        content = val
                hist.append(content)
                calls = [p["functionCall"] for p in content.get("parts", []) if "functionCall" in p]
                if not calls:
                    if step_text:
                        reply = (reply + "\n\n" + step_text).strip() if reply else step_text.strip()
                    break
                if step_text:
                    reply = (reply + "\n\n" + step_text).strip()
                    yield {"type": "text", "text": "\n\n"}
                resp = []
                for fc in calls:
                    nm, args = fc.get("name"), fc.get("args") or {}
                    yield {"type": "tool", "label": TOOL_LABEL.get(nm, nm)}
                    try:
                        res = run_tool(nm, args, ctx, actions)
                        used.append(nm)
                    except Exception as e:
                        res = {"hata": str(e)[:300]}
                    part = {"functionResponse": {"name": nm, "response": {"sonuc": json.loads(json.dumps(res, default=str))}}}
                    if fc.get("id"):
                        part["functionResponse"]["id"] = fc["id"]
                    resp.append(part)
                hist.append({"role": "user", "parts": resp})
                if actions:
                    yield {"type": "actions", "actions": actions}
                    actions = []
        except ai.AIError as e:
            while hist and hist[-1].get("role") != "user":
                hist.pop()
            if hist and hist[-1].get("parts") and "text" in hist[-1]["parts"][0]:
                hist.pop()
            _save(hist, log)
            yield {"type": "error", "message": str(e).replace("KOTA:", "").replace("MODEL:", "").replace("MESGUL:", "")}
            return
        if not reply:
            reply = "Tamamdır." if used else "Bir şey anlayamadım, tekrar yazar mısın?"
            yield {"type": "text", "text": reply}
        log.append({"rol": "ai", "metin": reply, "t": time.time(), "araclar": used})
        _save(hist, log)
        yield {"type": "done", "reply": reply, "actions": actions}
    finally:
        _lock.release()
