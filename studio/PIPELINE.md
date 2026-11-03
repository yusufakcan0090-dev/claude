# Ferman Tarih — Reels üretim talimatı

Bu dosya, @fermantarih Instagram hesabı için otomatik çalışan görevin adım adım talimatıdır.
Her çalıştırma temiz bir oturumda başlar; ihtiyacın olan her şey bu depodadır.

## Hesap
- Instagram: @fermantarih ("Ferman Tarih"), tarihin unutulan sayfaları.
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
2. **Duygu ya da tartışma:** Türk/İslam dünyası, kimlik, gurur, unutulan kardeşlik, adaletsizlik gibi izleyicinin
   kendini ilgili hissedeceği bir açı. Salt "şu oldu, sonra şu oldu" anlatımı YOK.
3. **Az bilinen konu** ya da bilinen bir konuya şaşırtıcı bir açı. Okulda herkesin öğrendiği konuyu düz anlatma.
4. **Kapanış:** Bugüne bağlanan, yorum yazdıran kısa bir soru veya vurucu cümle; son karede siyah ekranda büyük yazı.
5. Görüş içerse bile olgular doğru ve kaynaklı olur (kural 1); hakaret/aşağılama yok, gurura hitap edip ikna eden dil.

## Adımlar
1. `topics.md` dosyasını oku; daha önce işlenen konuları tekrarlama. Yakın tarihli bir yıl dönümü
   (paylaşım gününe denk gelen) varsa onu tercih et.
2. Konu seç: Türk ve İslam tarihinin az bilinen, şaşırtıcı, tek cümlede anlatılabilen bir olayı/kişisi/
   nesnesi. Çeşitlilik: Osmanlı, Selçuklu, Orta Asya, Endülüs, Memlük, Babür, Altın Orda, bilim tarihi,
   gündelik hayat, haritalar, bayraklar vb. Sadece savaş anlatma.
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
    Cuma 18:00**. Gönderi olmayan en yakın paylaşım gününü seç (aynı güne ikinci gönderi koyma).
    `createScheduledPost` ile REEL olarak planla (autoPublish true, isAiGenerated true).
    **Hikâye (STORY):** Metricool ücretsiz planı ayda en fazla **20** yayınlanmış gönderiye izin verir
    (Reels ve hikâye ayrı sayılır, ayın 1'inde sıfırlanır). Bu yüzden hikâye **sadece Çarşamba** paylaşılan
    videolar için yapılır: aynı videoyu aynı gün **21:00**'e STORY olarak planla (instagramData.type "STORY",
    açıklama metni yok, isAiGenerated true). Önce `topics.md`'deki "Gönderi" sütunundan o ay planlanan/yayınlanan
    toplam gönderiyi say; hikâyeyle birlikte toplam **19'u geçecekse** hikâyeyi atla. Instagram dışında
    platform kullanılmaz (TikTok/YouTube yok).
11. `topics.md`'ye satır ekle: paylaşım tarihi, konu, dosya adı, kaynaklar, gönderi sayısı (Reels=1,
    Reels+Story=2). Commit + push.
12. Kullanıcıya kısa bildirim: hangi konu, hangi gün/saat, Metricool planlayıcı linki. Kullanıcı
    beğenmezse paylaşımdan önce Metricool'dan silebilir.

## Bir şey ters giderse
- ElevenLabs kredisi bittiyse ya da "busy" hatası verdiyse: videoyu üretme, kullanıcıya bildir.
- Metricool medya hatası verirse: raw linki tekrar kontrol et; düzelmezse kullanıcıya bildir, tekrar tekrar deneme.
- Doğrulanamayan bir konuda ısrar etme; başka konu seç.
