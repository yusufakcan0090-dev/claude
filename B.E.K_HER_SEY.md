# B.E.K: Uygulamanın her şeyi

**B.E.K** = **B**ul · **E**ditle · **K**aliteyi artır (eski adı: Kesit Stüdyosu)
Sürüm: **1.13.3** · Tarih: 27.11.2026 · Sahibi: Yusuf Akcan (Animeci)

---

## 1. Ne işe yarar?

Kick/YouTube yayınlarından ve videolardan kesit (klip) çıkaran, düzenleyen ve kalitesini yapay zekâ ile artıran Windows masaüstü programı.

| Bölüm | Ne yapar |
|---|---|
| **Bul** | Kick/YouTube yayınlarını listeler, indirir; sesin heyecanlı yerlerinden en iyi anları bulur |
| **Editör** | After Effects tarzı editör: çok klip, katmanlar, keyframe, efektler/geçişler, Türkçe otomatik altyazı, LUT, yüzü kadraja alma, dışa aktarma (dikey/yatay/kare) |
| **Kalite** | Video ve fotoğrafı yapay zekâ ile büyütür, netleştirir, gürültü/blok temizler, yüz düzeltir, FPS artırır |
| **Dönüştür** | Video, ses ve fotoğrafı başka biçimlere çevirir (MP4, MOV, WebM, GIF, MP3, WAV, JPG, PNG, WebP...) |
| **Araçlar** | Video Arka Plan Sil · Kapak Stüdyosu · Kanal Analizi |
| **Ayarlar** | Yapay zekâ anahtarı, çıktı klasörü, otomatik güncelleme, donanım koruması, programı paylaşma |
| **Asistan** | Gemini ile sohbet: editörde yapılabilen her şeyi yapar (altyazı stili, yazılar, renk, efekt, zoom, geçiş, biçim, her ayar), otomatik edit, altyazı, dışa aktarma, kalite artırma, kapak/yüz/arka plan |

---

## 2. Özellikler (ayrıntılı)

### Bul (Klip Bulucu)
- Kick kanal adı ya da link ile yayın/klip listesi (yt-dlp + curl_cffi), YouTube desteği
- İndirme; yt-dlp ffmpeg'i göremezse kendi ffmpeg'ini indirir
- Ses enerjisine göre heyecanlı an tespiti (analyzer.py), anları seçip projeye aktarma

### Editör
- Çok videolu zaman çizelgesi (model.py), katmanlar (yazı, resim, şekil), konum/ölçek/döndürme/opaklık keyframe'leri (anim.py)
- Zamanlı efektler ve geçişler (fxlib.py, canlı önizleme fx.js)
- Türkçe otomatik altyazı: faster-whisper (NVIDIA ekran kartında hızlı) + yazım düzeltme (transcribe.py)
- "🎯 Yüzü bul": YuNet ile yüzü bulup kadrajı ayarlar (face_find.py)
- Dışa aktarma: orijinal çözünürlükte ya da Reels/Shorts biçimlerinde (exporter.py)

### Kalite Artır
- **Büyütme:** 1x / 2x (önerilen) / 3x / 4x / Özel (genişlik × yükseklik). Altında sonuç boyutu ve 4K/2K etiketi yazar
- **Yapay zekâ modelleri (4):** Anime (videoda Real-CUGAN Pro, fotoğrafta Waifu2x CUnet), Gerçek görüntü (UltraSharp), Hızlı (realesr-animevideov3), Yapay zekâsız (klasik)
  - Yapay zekâ gereken büyütmeye göre 2x / 3x / 4x çalışır
- **Anime modeli ek olarak:** çizgi koyulaştırma (Anime4K yöntemi), canlılık + derinlik, daha güçlü netlik
- **Varsayılanlar:** süper örnekleme açık, keskinlik 65, detay 35, gürültü 25, kenar yumuşatma 25, titreme 30
- **Netlik:** süper örnekleme (çizgiler pürüzsüz), keskinlik (kenar maskeli iki katmanlı), detay, gürültü, kenar yumuşatma, titreme giderme, blok/bant temizleme
- **Yüz:** GFPGAN / CodeFormer ile yüz düzeltme
- **Renk:** otomatik renk, parlaklık, kontrast, canlılık, sıcaklık, gamma, gölge/parlak alan, vinyet, gren
- **FPS:** 30/60/90/120/Özel, RIFE yapay zekâ ara kare; düşürme de çalışır
- **Çıktı:** kalite (Üst düzey = x265 10-bit / x264 düşük CRF), kayıpsız ara kareler, H.264/H.265, ses temizleme/dengeleme
- **Serbest ayar:** CRF, kodlama hızı, 10-bit, ses kbps, yapay zekâ parça boyutu
- **⭐ Benim ayarlarım:** ayarları isimle kaydet, tek tıkla uygula. Hazır ayarlar kaldırıldı
- Her bölümde **↺ Sıfırla**
- Önce/sonra önizleme, yakınlaştırma (yumuşak; "▦ Piksel" ile piksel görünümü), fotoğrafta fırça ile nesne silme
- Parça parça işleme: duraklat, iptal; program kapanınca kaldığı yerden devam (durum.json)
- Dosya adı gerçek boyutu gösterir: `video_2K.mp4`, `foto_4K.jpg`

### Donanım koruması (guard.py)
- Ekran kartı sıcaklığını (nvidia-smi) ve okunabiliyorsa işlemci sıcaklığını izler
- **Sessiz** (72°C, aralıklı mola, işlemcinin yarısı), **Dengeli** (80°C, varsayılan), **Tam güç** (86°C); sınır elle 60–90°C ayarlanabilir
- Sınır aşılınca iş donar, soğuyunca kaldığı yerden devam eder
- Ağır işler düşük öncelikte çalışır, bilgisayar donmaz
- Sıcaklık Kalite'de, Ayarlar'da ve sol alttaki göstergede 2 saniyede bir canlı gösterilir

### Araçlar
- **Video Arka Plan Sil:** Yeşil perde olmadan kişiyi ayırır (RVM) ya da her şeyi ayırır (IS-Net). Arkaya renk, bulanık, resim ya da video koyar; şeffaf WebM/MOV çıkarabilir. Kenar yumuşatma/daraltma, önce-sonra önizleme
- **Kapak Stüdyosu:** Videodan kare seçme, kişiyi otomatik kesme (beyaz çerçeve, parlama, gölge), 4 şablon, Türkçe karakterli 8 yazı tipi, *yıldızlı kelime* vurgusu, emoji, ok, daire. Sürükle/büyüt/döndür, geri al (Ctrl+Z), YouTube 16:9 / Shorts 9:16 / kare; JPG 2 MB altı ya da PNG. Yapay zekâ yazı önerisi
- **Kanal Analizi:** YouTube kanalının son 20/50/100 videosu: en iyi gün ve saat, Shorts mı uzun mu, en iyi süre, en çok tutanlar, yükselenler, tutan başlık kelimeleri, etkileşim, yükleme sıklığı, sıralanabilir tablo, kural tabanlı öneriler ve yapay zekâ yorumu

### Diğer
- **Otomatik güncelleme:** 15 dakikada bir GitHub'a bakar; iş yokken, 45 saniye dokunulmamışsa, pencere açık değilse kendisi kurar
- **Süren işler:** sol menünün altında yüzde gösteren halka; tıklayınca iş listesi açılır
- **Paylaşma:** Ayarlar → "Programı paylaş" kurulum linkini kopyalar

---

## 3. Kurulum ve paylaşma
- Kurulum dosyası: `BEK_Kurulum.exe` (~0,9 MB). Link:
  https://github.com/yusufakcan0090-dev/claude/raw/kesit-studyosu/BEK_Kurulum.exe
  Eski link (`KesitStudyosu_Kurulum.exe`) de çalışır.
- Kurulum `%LOCALAPPDATA%\KesitStudyosu` klasörüne Python ortamını, paketleri ve ffmpeg'i kurar. Masaüstüne "B.E.K" kısayolu koyar.
- İmzasız: Windows "Bilinmeyen yayımcı" derse **Ek bilgi → Yine de çalıştır**.
- Yapay zekâ modelleri ilk kullanımda iner (`bin/ai`).
- Elle kurulum: `KUR.bat` → `BASLAT.bat`. Sorun olursa `SORUN_GIDER.bat` (konsollu açar). İndirme bozulursa `GUNCELLE.bat` (yt-dlp günceller).

## 4. Güncelleme gönderme (geliştirici)
1. `app/version.json` → sürümü artır, `notes`'a kısa Türkçe madde ekle
2. `bash kur/derle.sh` → `BEK_Kurulum.exe` + eski adlı kopya (NSIS / makensis gerekir)
3. `git commit` + `git push origin HEAD:kesit-studyosu`
4. Kurulu tüm bilgisayarlar kendisi günceller (updater.py; `veri/`, `.venv/`, `bin/` klasörlerine dokunmaz)

- Depo: `yusufakcan0090-dev/claude`, dal: `kesit-studyosu`
- Ayarlar ve projeler: kurulum klasöründe `veri/`
- Çıktılar: `Videolar\Kesit Studyosu` (Ayarlar'dan değişir)

## 5. Gereksinimler
- Windows 10/11, internet (ilk kurulum, indirme, yapay zekâ modelleri, Gemini)
- NVIDIA ekran kartı önerilir (altyazı + yapay zekâ çok daha hızlı). Kalite yapay zekâsı Vulkan ile AMD/Intel'de de çalışır
- Python paketleri: flask, numpy, yt-dlp, curl_cffi, deno, faster-whisper, pywebview (+ NVIDIA için cublas/cudnn). onnxruntime ve opencv gerektiğinde ayrı kurulur
- Dış araçlar: ffmpeg, Real-ESRGAN / Real-CUGAN (ncnn-vulkan), RIFE, ONNX modelleri (GFPGAN, CodeFormer, YuNet, RVM, IS-Net, LaMa)
- Gemini anahtarı (isteğe bağlı): Asistan, otomatik edit, başlık/açıklama, kapak yazısı, kanal yorumu

---

## 6. Dosya yapısı

```
BEK_Kurulum.exe, KesitStudyosu_Kurulum.exe   kurulum dosyaları
KUR.bat, BASLAT.bat, GUNCELLE.bat, SORUN_GIDER.bat, kurulum.py
requirements.txt, requirements-nvidia.txt, README.md, OKU_BENI.txt
kur/   kurulum.nsi (NSIS), arayuz.ps1 (kurulum penceresi), isci.ps1 (kurulum işçisi), derle.sh
app/
  main.py          başlatıcı: pencere "B.E.K", masaüstü kısayolu, simge, görev çubuğu kimliği (Animeci.BEK)
  server.py        Flask sunucusu, tüm /api uçları
  core.py          ayarlar, iş sistemi (Job: duraklat/iptal/ilerleme/ETA), ffmpeg yardımcıları
  updater.py       otomatik güncelleme
  model.py         proje modeli (çok klip zaman çizelgesi)
  anim.py          keyframe/dönüştürme
  fxlib.py         efekt ve geçişler
  exporter.py      dışa aktarma
  analyzer.py      heyecanlı an bulma
  transcribe.py    Türkçe altyazı (faster-whisper)
  kick.py          Kick/YouTube listeleme, indirme (yt-dlp)
  enhance.py       Kalite Artır motoru
  face_worker.py   yüz düzeltme işçisi (GFPGAN/CodeFormer)
  face_find.py     yüz bulma (YuNet)
  guard.py         donanım koruması
  convert.py       Dönüştür
  imgtools.py      fotoğraf arka plan/nesne silme, kapak kişi kesme
  img_worker.py    IS-Net / LaMa işçisi
  vbg.py           Video Arka Plan Sil
  vmatte_worker.py RVM / IS-Net video işçisi
  kanal.py         Kanal Analizi
  ai.py            Gemini bağlantısı (akış, model yarışı)
  assistant.py     Asistan ve araçları
  version.json     sürüm ve yenilikler
  ui/
    index.html, style.css
    app.js         ortak: sayfa geçişi, işler, ayarlar, güncelleme
    finder.js      Bul
    editor.js, fx.js   Editör
    kalite.js      Kalite
    donustur.js    Dönüştür
    araclar.js     Araç merkezi + ortak arayüz kiti (KS.ui)
    vbg.js         Video Arka Plan Sil
    kapak.js       Kapak Stüdyosu
    kanal.js       Kanal Analizi
    ai.js          Asistan
    fonts/         kapak yazı tipleri (Anton, Bebas Neue, Montserrat Black, Archivo Black, Bangers, Luckiest Guy, Bowlby One SC, Rubik Mono One)
    logo.png, logo512.png, icon.ico, bek_simge.ico
```

---

## 7. API uçları (server.py)

**Genel:** GET /api/state · GET /api/jobs · POST /api/jobs/<id>/cancel · POST /api/jobs/<id>/pause · GET /api/system · GET /api/version · POST /api/settings · POST /api/restart · POST /api/defaults · POST /api/fixes

**Güncelleme:** GET /api/update/check · POST /api/update/apply

**Bul:** POST /api/kick/list · POST /api/kick/clip · POST /api/analyze · GET/DELETE /api/analysis/<aid> · POST /api/moments · POST /api/local/project

**Proje/Editör:** POST /api/project/new · GET/POST/DELETE /api/project/<pid> · POST …/overlay · …/transcribe · …/rechunk · …/lut · GET …/lutdata · GET …/wave/<cid> · POST …/export · POST …/yuzbul · POST …/paylasim · GET …/frames · GET /media/kapak/<pid>/<name>

**Kalite:** POST /api/kalite/preview · GET /media/kalite/<key>/<name> · POST /api/kalite/start · GET /api/kalite/yarim · POST /api/kalite/devam · POST /api/kalite/sil · GET /api/kalite/info · GET /media/kalite_src · GET /api/koruma

**Yapay zekâ:** POST /api/ai/test · GET/POST /api/ai/chat · POST /api/ai/stream · POST /api/ai/reset · POST /api/ai/meta/<pid> · POST /api/autoedit

**Görsel/Araçlar:** POST /api/gorsel/arkaplan · POST /api/gorsel/nesne · POST /api/vbg/preview · GET /media/vbg/<name> · POST /api/vbg/start · POST /api/kapak/kare · POST /api/kapak/kareler · POST /api/kapak/kes · POST /api/kapak/yazi · POST /api/kanal/start · GET /api/kanal/sonuc · POST /api/kanal/ai

**Dönüştür:** POST /api/donustur/pick · POST /api/donustur/info · POST /api/donustur

**Dosya/Sistem:** POST /api/snapshot · POST /api/open_url · POST /api/share/open · POST /api/reveal · POST /api/play · POST /api/pick_any · POST /api/pick_folder · POST /api/describe · POST /api/upload · GET /media/video

---

## 8. Önemli ayarlar (veri/ayarlar)
- `cikti_klasoru`: çıktıların gideceği klasör
- `whisper_model`: altyazı modeli (large-v3)
- `gemini_key`: yapay zekâ anahtarı
- `oto_guncelle`: otomatik güncelleme (varsayılan açık)
- `kalite_ayar`: son Kalite ayarları
- `kalite_benim`: kayıtlı "Benim ayarlarım"
- `koruma`: {mod: sessiz/dengeli/tam, gpu_limit}
- `vbg_ayar`: son arka plan silme ayarları
- `kanal_son`: son bakılan kanallar
- `tema`, `tur_goruldu`

---

## 9. Sürüm geçmişi (özet)
- **1.12.x:** Görev çubuğu simgesi (AppUserModelID); B.E.K adı ve "bek" logosu, BEK_Kurulum.exe; serbest büyütme (1x–4x/Özel); süper örnekleme; 4 modele inen sade model kartları; hazır ayarlar kaldırıldı; bölüm bölüm sıfırlama; canlı sıcaklık; işler sol menüde halka; FPS düşürme ve dosya adı düzeltmeleri; masaüstü simgesi yenileme
- **1.11.0:** Araçlar (Video Arka Plan Sil, Kapak Stüdyosu, Kanal Analizi), Kalite serbest ayar, Donanım koruması
- **1.10.x:** Dönüştür, otomatik güncelleme, tek dosya kurulum (.exe), Kalite yeniden tasarım, üst düzey kalite (UltraSharp, CUGAN Pro, CodeFormer, kayıpsız, titreme giderme)
- **1.9.x ve öncesi:** Yapay zekâ asistanı, otomatik edit, başlık/açıklama, fotoğraf araçları, Kalite Artır (duraklat/devam), orijinal çözünürlükte dışa aktarma, AE tarzı editör, Kick/YouTube bulucu, Türkçe altyazı

---

## 10. Yeni sohbette devam etmek için prompt

```
B.E.K projesine devam ediyoruz. Bana "çarım 👑" diye hitap et, Türkçe ve kısa konuş.
Depo: yusufakcan0090-dev/claude, dal: kesit-studyosu. Güncel sürüm 1.13.3.
Güncelleme: app/version.json sürüm+not → bash kur/derle.sh → commit → git push origin HEAD:kesit-studyosu (programlar kendisi günceller).
Bilgisayarımdaki klasöre (C:\Users\yusuf\Desktop\KesitStudyosu) dosya yazma; sadece okuyabilirsin.
Dosya yapısı ve özellikler için depodaki B.E.K_HER_SEY.md'yi oku.
Kurallar: "başla" demeden uygulamaya geçme; istemediğim şeyi yapma; hataları kendin bul ve düzelt; göndermeden test et;
After Effects'i bilgisayarımda kontrol etme; telefonuma bildirim gönderme; tasarım güzel ve sade olsun, açıklamalar çok kısa.
```
