# Ferman Tarih — Kaydırmalı gönderi (carousel) talimatı

Kullanıcının isteği: Metricool'un aylık **20** paylaşım hakkı tam kullanılsın. Reels'ler (Pzt/Çar/Cum 18:00,
`PIPELINE.md`) önceliklidir; kalan haklar kaydırmalı gönderilerle doldurulur. Gönderiler ElevenLabs kredisi harcamaz.

## Takvim
- **Salı 18:00** ve **Cumartesi 10:00** (Europe/Istanbul). Görev Pazartesi ve Cuma öğlen çalışır, ertesi günü planlar.

## 20 sınırı kontrolü (her seferinde, ZORUNLU)
1. `getScheduledPosts` ile hedef gönderinin olduğu ayın 1'i 00:00 – son günü 23:59 aralığını çek (brand 7819032).
   `draft: true` olanları SAYMA. Yayınlanmış (PUBLISHED) + bekleyen (PENDING) her gönderi 1 sayılır
   (kaydırmalı gönderi de tek gönderi sayılır).
2. O ayın, hedef tarihten sonra kalan ve henüz Metricool'da Reels'i olmayan **Pazartesi/Çarşamba/Cuma**
   günlerini say (bunlar ileride Reels'e ayrılan haklar).
3. Hedef gün/saatte (Salı 18:00 veya Cumartesi 10:00) zaten bir POST varsa (ör. elle planlanmış) **hiçbir şey
   üretme**, sessizce bitir.
4. `sayılan + ayrılan Reels + 1 ≤ 20` ise planla; değilse **planlama**, kullanıcıya kısa bilgi ver ve dur.
   Reels'in hakkını asla yeme.

## İçerik kuralları
- `PIPELINE.md`'deki **doğruluk, konu seçimi, "herkesin bildiği konu yasak", "seri yok"** kuralları aynen geçerli.
  Konular dünya tarihinden (Fransa, Almanya/Nazi dönemi, Sovyetler, Rusya, dünya savaşları, Soğuk Savaş vb.);
  Osmanlı/Türk konusu en fazla 4 gönderide 1. `topics.md`'deki Reels ve gönderi konularını tekrarlama.
- Kaydırmalı gönderi Reels'ten farklı bir hikâye anlatır; aynı hafta Reels'le aynı konu olmaz.
- **6–8 sayfa, 1080x1350.** Yapı:
  1. Kapak: koyu zemin, merak uyandıran 2–3 satırlık kanca + büyük mühür başlık + bir görsel. İnsanı kaydırtmalı.
  2–(n-1). Her sayfada TEK bir fikir: kısa başlık (kırmızı), bir görsel (çizim/mühür/basit harita/ikon),
     en fazla ~35 kelime metin. Sayı ve tarihler büyük mühürle vurgulanır.
  n. Son sayfa koyu zemin: "SİZCE?" + yorum yazdıran soru + "@fermantarih" takip çağrısı.
- **Tasarım: "GİZLİ DOSYA" (`dosya.py`).** Kullanıcı eski parşömen tasarımını yeterince çarpıcı bulmadı; artık
  sadece `dosya.py` kullanılır (`carousel.py` ESKİ, kullanma). Unsurlar: koyu zemin + kırmızı ışık, Inter Display Black
  dev başlıklar (krem/kırmızı), kırmızı etiket şeridi (`kicker`), manila klasör (`folder`), "ÇOK GİZLİ" tarzı damga
  (`stamp`), kâğıt sayfa (`paper_tex` + `place`), daktilo metni ve `**kelime**` ile sarı fosfor vurgusu (`rich_text`),
  polaroid çizimler (`polaroid`, `art_canvas`), ataç, DEV kırmızı rakamlar (200–400 px), alt bilgide kırmızı "kaydır" düğmesi.
  Koyu sayfa ile kâğıt sayfayı dönüşümlü kullan; her gönderide en az 2 dev rakam/tarih sayfası olsun.
- Görseller kodla çizilir (`dosya.py` + çizimler için `make.py`'deki `stamp_card`, `make_flag` vb.).
  Gerçek fotoğraf, film karesi, başkasının çizimi kullanılmaz. Nazi sembolleri (gamalı haç, SS rünleri) çizilmez.
  Emoji görsele yazılmaz (font desteklemiyor); emoji sadece açıklama metninde olur.
- Örnek (yeni tasarım): `c_2026-11-07_hayalet_ordu.py` (önizleme: `posts/_onizleme_hayalet_ordu.png`). Yeni gönderi için bunu kopyala: `c_YYYY-MM-DD_konu.py`.
- Render'dan sonra `dosya.contact_sheet` ile kontakt sayfası üretip **bak** (koyu zeminde fosforlu kelime okunuyor mu, taşan yazı,
  çakışan görsel, alt bilgiye binen öğe var mı); sorun varsa düzelt.

## Yayın
1. Görseller `posts/YYYY-MM-DD_konu/1.jpg … n.jpg`. Commit + push; her raw linkin 200 döndüğünü kontrol et:
   `https://raw.githubusercontent.com/yusufakcan0090-dev/claude/main/posts/<klasör>/<i>.jpg`
2. Metricool `createScheduledPost`: providers instagram, `instagramData.type: "POST"`, `isAiGenerated: false`
   (kodla çizilmiş illüstrasyon, gerçekçi YZ görseli değil), media = sayfa linkleri sırayla.
   Açıklama: ilk satır merak uyandıran tek cümle + anahtar kelime, 1–2 cümle özet, "Kaydır ve hikâyenin tamamını oku →",
   `Kaynak: …`, 4–6 etiket. `firstCommentText`: tartışma başlatan kısa bir soru.
3. `topics.md`'ye satır ekle (Gönderi sütunu = 1, konu başına "[Gönderi]" yaz). Commit + push.
4. Kullanıcıya kısa Türkçe mesaj (SendUserMessage): konu, gün/saat, Metricool planlayıcı linki, kontakt sayfası
   görselini `SendUserFile` ile gönder; beğenmezse Metricool'dan silebileceğini söyle.
