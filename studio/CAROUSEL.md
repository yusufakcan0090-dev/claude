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
- **6–8 sayfa, 1080x1350. AZ YAZI, ÇOK GÖRSEL** (kullanıcı isteği). Her sayfa: 2–4 kelimelik dev başlık veya dev
  rakam + büyük bir çizim + en fazla TEK kısa satır (alt siyah şeritte, ≤7 kelime). Paragraf YOK.
  1. Kapak: çarpıcı 2 kelimelik başlık + büyük çizim + küçük etiket (yıl · konu) + alt şeritte kanca cümlesi.
  2–(n-1). Sayfa başına TEK fikir; en az 2 sayfa dev rakam/tarih (200–300 px).
  n. Son sayfa: "SİZCE?" + kısa soru + "TAKİP ET @fermantarih" düğmesi.
- **Tasarım: SAVAŞ AFİŞİ (`poster.py`).** `dosya.py` ve `carousel.py` ESKİ, kullanma. Unsurlar: güneş ışını zemin (`rays`),
  yarım ton nokta deseni (`halftone`), kırmızı/siyah/krem/hardal palet, Inter Display Black dev başlık (`title`),
  etiket (`tag`), damga (`stamp`), alt siyah şerit (`band` + `line`), siluet çizimler (`tank`, `soldier`, `pump`,
  `halftrack_speaker`, `radio_tower`, `waves`; gerekirse poster.py'ye aynı tarzda yeni siluet ekle), `put` ile yerleştir.
  Zemin rengini sayfadan sayfaya değiştir (kırmızı / krem / hardal / siyah).
- Görseller kodla çizilir. Gerçek fotoğraf, film karesi, başkasının çizimi kullanılmaz. Nazi sembolleri (gamalı haç,
  SS rünleri) çizilmez. Emoji görsele yazılmaz; emoji sadece açıklama metninde olur.
- Örnek: `c_2026-11-07_hayalet_ordu.py` (önizleme: `posts/_onizleme_hayalet_ordu.png`). Yeni gönderi için kopyala: `c_YYYY-MM-DD_konu.py`.
- Render'dan sonra `poster.contact_sheet` ile kontakt sayfası üretip **bak** (yazı çizimle/damgayla çakışıyor mu, taşan yazı,
  alt şeride binen öğe var mı); sorun varsa düzelt.

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
