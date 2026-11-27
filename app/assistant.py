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

SYS = """Sen Kesit Stüdyosu'nun içindeki yapay zekâ asistanısın. Kesit Stüdyosu; Kick ve YouTube yayınlarından klip bulan,
en iyi anları kesen, Türkçe altyazı ekleyen, After Effects benzeri editörü olan, video/fotoğraf kalitesini artıran bir Windows programı.
Kullanıcı Türkçe konuşur; sen de kısa, samimi ve net Türkçe cevap verirsin (genelde 1-4 cümle).
Kurallar:
- İşi yapmak için araçları kullan; araçla yapabileceğin bir şeyi kullanıcıya "şunu yap" diye anlatma.
- Uzun işler (otomatik edit, altyazı, dışa aktarma, kalite artırma) arka planda başlar; başlattığını ve bitince haber geleceğini söyle.
- Hangi projeden bahsedildiği belli değilse önce açık projeyi kullan; o da yoksa projeleri listeleyip sor.
- Dosya yolu ya da proje kimliği uydurma; araçlardan gelen bilgileri kullan.
- Sıfırdan resim üretemezsin (ücretli). Arka plan silme, nesne silme (Kalite sayfasında fırçayla) ve videodan kapak resmi yapılabilir.
- Paylaşım: program videoyu ve açıklamayı hazırlar, yükleme sayfasını açar; son "Paylaş" tuşuna kullanıcı basar (platformlar otomatik paylaşıma izin vermiyor).
- Ham proje kimliği gibi teknik şeyleri kullanıcıya gösterme, başlıkla anlat."""

S = "string"
TOOLS = [
    {"name": "projeleri_listele", "description": "Kullanıcının projelerini (video düzenleme projeleri) en yeniden eskiye listeler.", },
    {"name": "proje_ac", "description": "Bir projeyi editörde açar.", "parameters": {"type": "object", "properties": {"proje_id": {"type": S}}, "required": ["proje_id"]}},
    {"name": "sayfa_ac", "description": "Programda bir sayfaya geçer.", "parameters": {"type": "object", "properties": {"sayfa": {"type": S, "enum": ["bul", "editor", "kalite", "ayarlar"], "description": "bul=Klip Bulucu"}}, "required": ["sayfa"]}},
    {"name": "klip_ara", "description": "Kick/YouTube'da kanal, klip ya da konu arar (örn. 'rraenee', 'komik anlar'). Sonuçları Klip Bulucu'da da gösterir.", "parameters": {"type": "object", "properties": {"sorgu": {"type": S}}, "required": ["sorgu"]}},
    {"name": "otomatik_edit", "description": "Bir yayından/videodan en iyi anları seçip her biri için hazır kısa video projesi (altyazılı) oluşturur. Kaynak: video bağlantısı (Kick/YouTube), bilgisayardaki dosya yolu ya da 'acik_proje'.",
     "parameters": {"type": "object", "properties": {"kaynak": {"type": S}, "adet": {"type": "integer", "description": "kaç video (1-10), varsayılan 3"},
                                                     "bicim": {"type": S, "enum": ["dikey", "kaynak", "yatay", "kare"], "description": "dikey=Reels/Shorts 9:16, kaynak=videonun kendi boyutu"},
                                                     "altyazi": {"type": "boolean"}}, "required": ["kaynak"]}},
    {"name": "altyazi_olustur", "description": "Projedeki videoların Türkçe altyazısını çıkarır.", "parameters": {"type": "object", "properties": {"proje_id": {"type": S}}, "required": ["proje_id"]}},
    {"name": "disa_aktar", "description": "Projeyi MP4 olarak dışa aktarır.", "parameters": {"type": "object", "properties": {"proje_id": {"type": S}, "cozunurluk": {"type": "integer", "description": "720, 1080 ya da 1440"}, "fps": {"type": S, "description": "'kaynak' ya da 30/60"}}, "required": ["proje_id"]}},
    {"name": "kalite_artir", "description": "Bir video ya da fotoğrafın kalitesini yapay zekâ ile artırır.", "parameters": {"type": "object", "properties": {"dosya": {"type": S, "description": "dosya yolu"}, "mod": {"type": S, "enum": ["hizli", "en_iyi", "anime", "klasik"]}, "cozunurluk": {"type": S, "enum": ["kaynak", "720", "1080", "1440", "2160", "x2", "x4"]}, "yuz": {"type": "boolean"}, "fps": {"type": S, "enum": ["kaynak", "30", "60"]}}, "required": ["dosya"]}},
    {"name": "paylasim_metni", "description": "Proje için YouTube Shorts, TikTok ve Instagram Reels başlık/açıklama/etiket yazar.", "parameters": {"type": "object", "properties": {"proje_id": {"type": S}, "not": {"type": S, "description": "isteğe bağlı ek istek (ton, vurgu)"}}, "required": ["proje_id"]}},
    {"name": "paylas", "description": "Paylaşım penceresini açar: dışa aktarılmış videoyu ve metni hazırlar, platformun yükleme sayfasını açar.", "parameters": {"type": "object", "properties": {"proje_id": {"type": S}, "platform": {"type": S, "enum": ["youtube", "tiktok", "instagram"]}}, "required": ["proje_id"]}},
    {"name": "arka_plan_sil", "description": "Fotoğrafın arka planını siler (şeffaf PNG).", "parameters": {"type": "object", "properties": {"dosya": {"type": S}}, "required": ["dosya"]}},
    {"name": "kapak_yap", "description": "Proje için kapak resmi (thumbnail) penceresini açar.", "parameters": {"type": "object", "properties": {"proje_id": {"type": S}}, "required": ["proje_id"]}},
    {"name": "isler", "description": "Çalışan ve son biten işleri (indirme, altyazı, dışa aktarma...) gösterir.", },
    {"name": "son_dosyalar", "description": "Son dışa aktarılan videoların ve kalite artırılmış dosyaların yollarını listeler.", },
]


def _srv():
    import server
    return server


def _pid(srv, a, ctx):
    pid = (a.get("proje_id") or "").strip()
    if pid in ("", "acik_proje", "acik", "current") and ctx.get("project"):
        pid = ctx["project"]
    p = srv.load_project(pid) if pid else None
    if not p:
        raise ValueError("Proje bulunamadı. Önce projeleri_listele ile doğru projeyi seç.")
    return p


def run_tool(name, a, ctx, actions):
    srv = _srv()
    if name == "projeleri_listele":
        return [{"proje_id": p["id"], "baslik": p.get("title"), "sure_sn": round(p.get("duration") or 0, 1), "klip": p.get("clips"),
                 "altyazi": p.get("subs_status"), "disa_aktarildi": bool(p.get("exports")), "bicim": p.get("format")}
                for p in srv.all_projects()[:20]]
    if name == "proje_ac":
        p = _pid(srv, a, ctx)
        actions.append({"type": "open_project", "id": p["id"]})
        return f"'{p.get('title')}' editörde açıldı."
    if name == "sayfa_ac":
        pg = {"bul": "finder", "editor": "editor", "kalite": "kalite", "ayarlar": "settings"}.get(a.get("sayfa"), "finder")
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
        j = JOBS.start("otoedit", "Otomatik edit: " + title[:36], srv.job_autoedit, src, local, title, n, fmt, a.get("altyazi", True))
        return {"is": j.id, "durum": f"Otomatik edit başladı ({n} video). Bitince projeler açılır."}
    if name == "altyazi_olustur":
        p = _pid(srv, a, ctx)
        j = srv.start_transcribe(p["id"], p.get("title") or "")
        return {"is": j.id, "durum": "Altyazı çıkarılıyor."}
    if name == "disa_aktar":
        p = _pid(srv, a, ctx)
        opts = {"cozunurluk": int(a.get("cozunurluk") or 1080), "fps": str(a.get("fps") or "kaynak")}
        j = JOBS.start("aktar", "Dışa aktar: " + p["title"][:40], srv.job_export, p["id"], opts, heavy=True)
        return {"is": j.id, "durum": "Dışa aktarma başladı."}
    if name == "kalite_artir":
        import enhance
        f = (a.get("dosya") or "").strip()
        if not Path(f).exists():
            raise ValueError("Dosya bulunamadı: " + f)
        img = enhance.is_image(f)
        o = {"model": {"hizli": "hizli", "en_iyi": "gercek", "anime": "anime", "klasik": "klasik"}.get(a.get("mod") or ("en_iyi" if img else "hizli"), "hizli"),
             "hedef": a.get("cozunurluk") or ("x2" if img else "1080"), "yuz": bool(a.get("yuz")), "fps": a.get("fps") or "kaynak"}
        fn = enhance.process_image if img else enhance.process
        j = JOBS.start("kalite", ("Fotoğraf: " if img else "Kalite: ") + Path(f).stem[:40], fn, f, o, heavy=True)
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
        return {"is": j.id, "durum": "Arka plan siliniyor."}
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


TOOL_LABEL = {"projeleri_listele": "Projeler alınıyor", "proje_ac": "Proje açılıyor", "sayfa_ac": "Sayfa açılıyor", "klip_ara": "Aranıyor",
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
