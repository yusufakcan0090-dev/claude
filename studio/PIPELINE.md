# Ferman Tarih — Reels üretim talimatı

Bu dosya, @fermantarih Instagram hesabı için otomatik çalışan görevin adım adım talimatıdır.
Her çalıştırma temiz bir oturumda başlar; ihtiyacın olan her şey bu depodadır.

## Hesap
- Instagram: @fermantarih ("Ferman Tarih"), dünya tarihinin unutulan sayfaları (sadece Osmanlı değil).
- Metricool brand id: `7819032`, saat dilimi `Europe/Istanbul`.
- Ses: ElevenLabs, voice_id `1Q43BQXKZsbWRTD3NUlZ` (kullanıcının onayladığı "Evren" sesi), model `eleven_v4`.
- Görsel tarz: parşömen harita, balmumu/kırmızı mühürler, dalgalanan bayraklar, toz efekti, 1080x1920, 60 fps.
  Örnekler: `make.py` (Osmanlı–Kaşgar, harita ağırlıklı), `bayrak.py` (Gök Bayrak, yazı/bayrak ağırlıklı).

## Kurallar (pazarlıksız)
1. **Doğruluk:** Her olgu en az iki güvenilir kaynakla doğrulanır (TDV İslâm Ansiklopedisi, Britannica,
   Wikipedia + o maddenin kaynakları, akademik makale). Emin olunmayan sayı, tarih, alıntı videoya girmez.
   Uydurma alıntı, uydurma rakam yok.
2. **Ton:** Merak uyandırıcı ama saygılı. Nefret söylemi, bir halkı/dini aşağılama, şiddeti övme yok.
   Kanlı/şiddet görüntüsü çizme. Güncel siyasette taraf tutan propaganda dili yok; olgular + kaynak.
3. **Telif:** Film/belgesel görüntüsü, başkasının çizimi, şarkı sözü kullanılmaz. Her şey kodla çizilir.
4. **Süre:** 30–45 saniye. Metin ~70–100 kelime. İlk 2 saniyede güçlü bir kanca.
5. **Kredi:** ElevenLabs ücretsiz plan (ayda 10.000 kredi). Her video için **tek** seslendirme
   (`generations_count: 1`). Asla yeniden deneme amaçlı ikinci üretim başlatma.
6. **Açıklama:** Kısa kanca cümlesi, 1–2 cümle özet, izleyiciye bir soru, kaynak satırı (`Kaynak: ...`) ve
   5–8 Türkçe etiket (#tarih #türktarihi #fermantarih + konuya özel). Kullanıcının isteğiyle açıklamaya
   ElevenLabs/seslendirme satırı **eklenmez**.
7. **Yapay zekâ etiketi:** Metricool gönderisinde `instagramData.isAiGenerated: true`.

## Hikâye tarzı (kullanıcının beğendiği videolar örnek alınır)
Kullanıcı kendi yönlendirdiği videoları beğeniyor, salt bilgi anlatan videoları ("Piri Reis haritası", 2026-11-09)
ilgi çekici bulmuyor. Her video şu üç örneğe benzemeli:
- **Gök Bayrak** (`bayrak.py`): "Bu bayrağı tanıyor musun? Türk bayrağına benziyor… ama MAVİ." → izleyiciye
  doğrudan soru, görsel bir sürpriz, sonunda duygusal/düşündürücü soru ("Bir bayrak yasaklanabilir… Ya bir milletin hafızası?").
- **Biz Türk'üz** (`turk.py`): "Osmanlı torunuyuz… diyorsun." → izleyicinin bir inancına meydan okuma, net bir görüş,
  güçlü kapanış ("Ne mutlu Türk'üm diyene").
- **Osmanlı'nın unutulan müttefiki** (`make.py`): "Osmanlı Çin'e karşı savaşan bir Türk devletine silah gönderdi." →
  şaşırtıcı bir olgu, sonunda bugüne bağlanan soru ("Osmanlı o gün sahip çıktı… Ya bugün?").

Zorunlu kalıp:
1. **Güçlü açılış:** İlk 2 saniye merak uyandırsın (soru, şaşırtıcı bir iddia, çarpıcı bir tarih/olay olabilir).
   Tarihler ve yıllar serbest; önemli olan izleyicinin kaydırmadan durması.
2. **Duygu ya da tartışma:** İhanet, kahramanlık, adaletsizlik, inanılmaz şans, gizli kalmış gerçek gibi izleyiciyi
   içine çeken bir açı. Salt "şu oldu, sonra şu oldu" anlatımı YOK.
3. **Herkesin bildiği konu YASAK.** Kullanıcı açıkça istedi. Test: konu lise tarih kitabında, popüler bir filmde ya da
   "ilginç bilgiler" listelerinde sık geçiyorsa SEÇME (ör. Piri Reis haritası, Titanik, Hitler'in intiharı, Napolyon'un
   boyu, Berlin Duvarı'nın yıkılışı, Çernobil'in kendisi). Ünlü bir olayın **pek bilinmeyen bir detayı** olabilir.
4. **Seri YOK.** Kullanıcı seri istemiyor: her video kendi başına tamamdır; "Bölüm 1", "devamı yarın", "seri" ifadesi
   kullanılmaz, videolar birbirinin devamı olmaz.
5. **Kapanış:** Yorum yazdıran kısa bir soru veya vurucu cümle; son karede siyah ekranda büyük yazı.
6. **Doğruluk her şeyden önce:** Videodaki HER tarih, sayı, isim ve iddia iki güvenilir kaynakla doğrulanır (kural 1).
   Şehir efsanesi, tartışmalı ya da kaynağı belirsiz "ilginç bilgi"ler kullanılmaz; emin değilsen o cümleyi çıkar
   ya da konuyu değiştir. Hakaret/aşağılama yok.

## İzlenme odaklı ek kurallar (kullanıcı tam yetki verdi: "videolar izlensin yeter")
- **Ne tuttuğunu ölç:** Her çalıştırmanın başında Metricool'dan son 30 günün Reels istatistiklerini oku
  (`getAnalyticsDataByMetrics`, brandId 7819032, metrikler: IGRE01 tarih, IGRE03 içerik, IGRE23 izlenme,
  IGRE11 erişim, IGRE27 izlenme oranı/retention, IGRE28 ilk 3 sn'yi geçenler, IGRE21 paylaşım, IGRE12 kaydetme,
  IGRE07 yorum). Sonuçları `stats.md`'ye tablo olarak yaz (eski satırları güncelle). Yayınlanmış video yoksa atla.
- **Öğren ve uygula:** `stats.md`'de en çok izlenen / en yüksek retention'lı videoların konu türüne, açılış
  cümlesine ve süresine bak; yeni videoyu bunlara benzet. IGRE28 düşükse (izleyiciler 3 sn'de kaçıyor) açılışı
  daha sert yap; retention düşükse videoyu kısalt (30–35 sn). Bu kararı `stats.md`'nin sonuna 1–2 satır not et.
- **Ekranda ilk karede büyük yazı:** İlk 0.3 saniyede ekranda kancayı özetleyen 2–4 kelimelik büyük bir yazı olsun
  (sesi kapalı izleyenler için). Boş/sakin açılış karesi yok.
- **Kapak:** Gönderide `videoCoverMilliseconds` ile kapak olarak ilk sahnenin büyük yazısının tam okunduğu anı seç
  (ör. 1500). Profil ızgarasında güzel görünsün.
- **Açıklama ilk satırı:** Instagram'da sadece ilk ~125 karakter görünür; ilk satır merak uyandıran tek bir cümle
  olsun ve konunun anahtar kelimesini (ör. "Stalin", "Napolyon", "Gestapo") içersin (Instagram aramasında çıkmak için).
- **Etiketler:** 4–6 etiket; 2 geniş (#tarih #fermantarih), 2–4 konuya özel (#ikincidünyasavaşı #sovyetler gibi).
  30 etiket doldurma.
- **İlk yorum:** `firstCommentText` ile izleyiciyi tartışmaya sokan kısa bir soru yaz (ör. "Sizce bu plan
  işleseydi tarih nasıl değişirdi? 👇").

## Adımlar
1. `topics.md` dosyasını oku; daha önce işlenen konuları (Reels ve [Gönderi] satırları) tekrarlama. Yakın tarihli bir yıl dönümü
   (paylaşım gününe denk gelen) varsa onu tercih et. Ardından yukarıdaki "Ne tuttuğunu ölç" adımını yap.
2. Konu seç: **Dünya tarihinden** az bilinen, şaşırtıcı, tek cümlede anlatılabilen bir olay/kişi/nesne.
   Kullanıcı Osmanlı ağırlığından sıkıldı: **Osmanlı/Türk konusu en fazla 4 videoda 1** olsun (topics.md'ye bak).
   Öncelikli alanlar: **Fransa** (devrim, Napolyon, sömürgeler), **Almanya ve Nazi dönemi**, **Sovyetler Birliği**,
   **Rusya** (Çarlık, devrim), İkinci ve Birinci Dünya Savaşı, Soğuk Savaş; ayrıca İngiltere, Japonya, Amerika,
   Roma, Moğollar vb. Casusluk, gizli operasyonlar, çılgın planlar, şaşırtıcı tesadüfler, unutulan kahramanlar,
   diktatörlerin az bilinen yanları iyi çalışır. Ardışık iki video aynı ülke/dönemden olmasın.
   **Nazi/Sovyet konularında:** rejimi, ideolojiyi veya liderlerini öven/özendiren dil YOK; olaylar olgularla ve
   eleştirel mesafeyle anlatılır. Gamalı haç ve SS rünleri gibi Nazi sembolleri **çizilmez** (Instagram bunları
   kaldırabiliyor); yerine harita, tarih, belge, mühür kullanılır. Holokost gibi trajediler hafife alınmaz,
   "eğlenceli bilgi" diye sunulmaz.
3. Araştır ve doğrula (kural 1). Kaynak linklerini not et.
4. Metni yaz (Türkçe). eleven_v4 ses etiketleri kullanılabilir: `[dramatically]`, `[sad]`, `[softly]`,
   `[short pause]`, `[pause]`. Sayıları rakamla yaz.
5. Seslendir: `creative_generate_speech` (voice_id ve model yukarıda, generations_count 1), bitene kadar
   `creative_get_flow_run_status` ile bekle, `content_url`'i `curl` ile indir.
6. Cümle zamanlarını çıkar:
   `ffmpeg -i ses.mp3 -af silencedetect=noise=-38dB:d=0.25 -f null -`
7. Sahneleri yaz: `bayrak.py`'yi kopyalayıp yeni bir dosya yap (ör. `v_2026-11-04_konu.py`), sahne
   fonksiyonlarını ve `SCENES` sürelerini cümle zamanlarına göre ayarla. `make.py`'deki yardımcıları kullan
   (harita: `render_map`, `camera`, `P`, `to_screen`; mühür: `stamp_card`, `paste_pop`; bayrak:
   `make_flag`, `wave_flag`). Önce `frames` moduyla 5–7 kare çizip **bak**; çakışan yazı, taşan metin varsa düzelt.
8. Render: her sahneyi paralel render et, `concat` ile birleştir, `caps.py` ile altyazı göm
   (SRT'yi cümle zamanlarından üret).
   **Müzik YOK, yumuşak ses efektleri VAR:** Kullanıcı arka plan müziğini istemiyor (kulağı rahatsız ediyor),
   ama yumuşak efekt istiyor. `audio.py` içindeki `effects` + `mix_fx` kullanılır; `score`/`mix` KULLANILMAZ:
   ```python
   from audio import effects, mix_fx
   e = effects(toplam_sure, starts=[sahne başlangıçları], impacts=[(mühür/vuruş anı, 0.5–1.5), ...],
               final_hit=<son vurucu yazının anı>, seed=<her videoda farklı>)
   mix_fx("ses.mp3", e, "karisim.m4a")   # efektler konuşmanın altında, -14 LUFS
   ```
   `impacts` olarak videodaki `IMPACTS` anlarını (sahne başlangıcı + yerel süre) kullan. Efekt seviyesini
   (fx_db=-14) yükseltme; kullanıcı yüksek arka plan sesinden rahatsız oluyor.
9. Videoyu `videos/YYYY-MM-DD_konu.mp4` olarak depoya ekle, commit + push. Herkese açık link:
   `https://raw.githubusercontent.com/yusufakcan0090-dev/claude/main/videos/<dosya>`
   Linki `curl -o /dev/null -w "%{http_code}"` ile kontrol et (200 olmalı).
10. Metricool: önce `getScheduledPosts` ile önümüzdeki 7 güne bak. Paylaşım günleri **Pazartesi, Çarşamba,
    Cuma 10:00** (Metricool verisine göre Instagram'da en iyi saat 10:00). Gönderi olmayan en yakın paylaşım gününü seç (aynı güne ikinci gönderi koyma).
    `createScheduledPost` ile REEL olarak planla (autoPublish true, isAiGenerated true).
    **Hikâye (STORY) YOK.** Kullanıcı hikâye istemiyor; her şey sadece REEL olarak paylaşılır
    (aylık 20 gönderi sınırı böylece rahat kalır). Instagram dışında platform kullanılmaz (TikTok/YouTube yok).
11. `topics.md`'ye satır ekle: paylaşım tarihi, konu, dosya adı, kaynaklar, gönderi sayısı (Reels=1). Commit + push.
12. Kullanıcıya kısa bildirim: hangi konu, hangi gün/saat, Metricool planlayıcı linki. Kullanıcı
    beğenmezse paylaşımdan önce Metricool'dan silebilir.

## Bir şey ters giderse
- ElevenLabs kredisi bittiyse ya da "busy" hatası verdiyse: videoyu üretme, kullanıcıya bildir.
- Metricool medya hatası verirse: raw linki tekrar kontrol et; düzelmezse kullanıcıya bildir, tekrar tekrar deneme.
- Doğrulanamayan bir konuda ısrar etme; başka konu seç.
