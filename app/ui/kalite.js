/* Kesit Stüdyosu — Kalite Artır (yapay zekâ ile netleştirme, önce/sonra önizleme) */
(() => {
  const Q = KS.kalite = { src: null, opts: null, split: .5, zoom: 1, pan: { x: 0, y: 0 } };
  const view = $('#kqView'), stage = $('#kqStage'), aImg = $('#kqAfter'), bImg = $('#kqBefore'), bWrap = $('#kqBeforeWrap'), handle = $('#kqHandle');
  const MODELS = [['hizli', 'Hızlı', 'Video için hızlı yapay zekâ'], ['gercek', 'En iyi', 'Gerçek görüntü, en net (yavaş)'], ['anime_pro', 'Anime Pro', 'Anime ve çizgi film için en iyisi: çizgiler temiz ve keskin, renkler düz ve pürüzsüz (Real-CUGAN). İlk kullanımda ~55 MB iner.'], ['anime', 'Anime (eski)', 'Çizgi film / anime, Real-ESRGAN'], ['klasik', 'Klasik', 'Yapay zekâsız, çok hızlı']];
  /* tek tıkla en iyi sonuç */
  const PRESETS = {
    anime: ['🎌 Anime', 'Anime / çizgi film için en iyi', { model: 'anime_pro', keskin: 70, detay: 0, gurultu: 35, yumusat: 25, blok: true, bant: true, yuz: false, doygun: 8, kontrast: 4, oto_renk: false, ai_guc: 100, gren: 0 }],
    gercek: ['🎥 Gerçek video', 'Yayın, vlog, film için en iyi', { model: 'gercek', keskin: 60, detay: 25, gurultu: 25, yumusat: 0, blok: true, bant: false, yuz: true, yuz_guc: 60, doygun: 5, kontrast: 0, oto_renk: false, ai_guc: 85, gren: 0 }],
    eski: ['📼 Düşük kalite', 'Eski, bulanık, çok sıkıştırılmış videolar', { model: 'gercek', keskin: 55, detay: 15, gurultu: 55, yumusat: 15, blok: true, bant: true, yuz: true, yuz_guc: 75, doygun: 10, kontrast: 5, oto_renk: true, ai_guc: 100, gren: 0 }],
    hizli: ['⚡ Hızlı', 'Çabuk bitsin, yine iyi görünsün', { model: 'hizli', olcek: 2, keskin: 50, detay: 10, gurultu: 25, yumusat: 0, blok: true, bant: false, yuz: false, doygun: 0, kontrast: 0, oto_renk: false, ai_guc: 100, gren: 0 }],
  };
  const TARGETS = [['kaynak', 'Aynı'], ['720', '720p'], ['1080', '1080p'], ['1440', '2K'], ['2160', '4K']];
  const FPS = [['kaynak', 'Aynı'], ['30', '30'], ['60', '60'], ['90', '90'], ['120', '120']];
  const fmt = s => { s = Math.max(0, s || 0); return `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`; };

  Q.load = async path => {
    try {
      const r = await KS.api('/api/kalite/info?path=' + encodeURIComponent(path));
      if (Q.brush) { Q.brush = null; mask = null; bBox.hidden = true; }
      Q.src = r; Q.opts = Object.assign({}, DEF, r.opts, { bas: 0, bit: 0 });
      $('#page-kalite').classList.toggle('kq-photo', !!r.image);
      $('#kqName').textContent = r.image ? `${r.name} · ${r.width}×${r.height} · Fotoğraf` : `${r.name} · ${r.width}×${r.height} · ${Math.round(r.fps)} FPS · ${fmt(r.duration)}`;
      const t = $('#kqT'); t.max = Math.max(.1, r.duration - .05).toFixed(2); t.value = Math.min(r.duration / 3, r.duration).toFixed(2); KS.paintRange(t);
      $('#kqDur').textContent = fmt(r.duration);
      $('#kqEmpty').hidden = true;
      Q.renderSide(); Q.preview();
    } catch (e) { KS.toast(KS.esc(e.message), 'err'); }
  };
  $('#kqPick').onclick = async () => { try { const f = await KS.api('/api/pick_any', {}); if (f && f.path) { if (f.kind && f.kind !== 'video' && f.kind !== 'image') return KS.toast('Bir video ya da fotoğraf seç', 'err'); Q.load(f.path); } } catch (e) { KS.toast(KS.esc(e.message), 'err'); } };

  /* --- ayarlar --- */
  const seg = (key, list, cur) => `<div class="seg kq-seg" data-k="${key}">${list.map(([v, n, tip]) => `<button data-v="${v}" class="${String(cur) === String(v) ? 'on' : ''}" ${tip ? `title="${tip}"` : ''}>${n}</button>`).join('')}</div>`;
  const sl = (key, label, min, max, cur, hint) => `<div class="kq-sl"><div><span>${label}</span><b id="kqv_${key}">${cur}</b></div><input type="range" min="${min}" max="${max}" value="${cur}" data-r="${key}">${hint ? `<small>${hint}</small>` : ''}</div>`;
  const DEF = { model: 'hizli', olcek: 2, hedef: '1080', keskin: 45, gurultu: 25, blok: true, parlak: 0, kontrast: 0, doygun: 0, fps: 'kaynak', fps_ai: true,
    yuz: false, yuz_guc: 70, ai_guc: 100, detay: 0, yumusat: 0, bant: false, sicaklik: 0, golge: 0, parlak_alan: 0, gamma: 0, vinyet: 0, gren: 0, oto_renk: false,
    kalite: 'yuksek', codec: 'h264', bicim: 'kaynak', bas: 0, bit: 0, ses: true, ses_temizle: false, ses_dengele: false };
  Q.DEF = DEF;
  const NOPV = new Set(['fps', 'fps_ai', 'kalite', 'codec', 'bas', 'bit', 'ses', 'ses_temizle', 'ses_dengele']);
  const chk = (key, label) => `<label class="ae-chk kq-chk"><input type="checkbox" data-c="${key}" ${Q.opts[key] ? 'checked' : ''}>${label}</label>`;
  Q.open = Q.open || { ai: true, net: true, gorsel: true };
  const grp = (id, title, body) => `<details class="kq-g" data-g="${id}" ${Q.open[id] ? 'open' : ''}><summary>${title}</summary><div class="kq-gb">${body}</div></details>`;
  Q.renderSide = () => {
    const o = Q.opts, el = $('#kqSide');
    if (!o) { el.innerHTML = ''; return; }
    Object.keys(DEF).forEach(k => { if (o[k] === undefined) o[k] = DEF[k]; });
    const m = MODELS.find(x => x[0] === o.model) || MODELS[0], dur = Q.src ? Q.src.duration : 0, keep = el.scrollTop, img = !!(Q.src && Q.src.image);
    const what = img ? 'Fotoğrafın' : 'Videonun', TG = img ? [['kaynak', 'Aynı'], ['x2', '2 kat'], ['x4', '4 kat'], ['1080', '1080p'], ['2160', '4K']] : TARGETS;
    const curP = Object.keys(PRESETS).find(k => Object.entries(PRESETS[k][2]).every(([a, b]) => o[a] === b));
    el.innerHTML = `<div class="kq-scroll">
      <div class="kq-presets"><div class="kq-h">Hazır ayar · tek tıkla en iyi sonuç</div><div class="kq-pre">${Object.entries(PRESETS).map(([k, v]) => `<button class="${k === curP ? 'on' : ''}" data-pre="${k}" title="${v[1]}"><b>${v[0]}</b><small>${v[1]}</small></button>`).join('')}</div></div>
      ${img ? grp('gorsel', 'Görsel araçları', Q.brush ? `<small class="kq-note">Silmek istediğin yeri <b>fareyle boya</b> (kırmızı). Sonra "Boyanan yeri sil"e bas.</small>
          ${sl('fircaBoy', 'Fırça boyutu', 5, 200, Q.brush.size)}
          <div class="kq-tools"><button class="btn primary sm" id="kqInp">🩹 Boyanan yeri sil</button><button class="btn ghost sm" id="kqBClr">Temizle</button><button class="btn ghost sm" id="kqBOff">Vazgeç</button></div>`
        : `<div class="kq-tools"><button class="btn ghost sm" id="kqBg">✂️ Arka planı sil</button><button class="btn ghost sm" id="kqBOn">🩹 Nesne sil (fırça)</button></div>
          <small class="kq-note">Bilgisayarında, ücretsiz yapay zekâ ile çalışır. İlk kullanımda model iner (~170-200 MB). Sonuç ayrı bir dosya olarak kaydedilir.</small>`) : ''}
      ${grp('ai', 'Yapay zekâ ve çözünürlük', `${seg('model', MODELS, o.model)}<small class="kq-note">${m[2]}</small>
        ${o.model === 'hizli' ? `<div class="kq-h">Yapay zekâ büyütme</div>${seg('olcek', [['2', '2x'], ['4', '4x (daha net, yavaş)']], o.olcek)}` : ''}
        ${o.model !== 'klasik' ? sl('ai_guc', 'Yapay zekâ gücü (azaltınca daha doğal)', 0, 100, o.ai_guc) : ''}
        <div class="kq-h">Çıkış çözünürlüğü</div>${seg('hedef', TG, o.hedef)}
        <div class="kq-h">Biçim (ekran şekli)</div>${seg('bicim', [['kaynak', what + ' kendisi'], ['9:16k', 'Reels 9:16 (doldur)'], ['9:16b', 'Reels 9:16 (bulanık arka)'], ['4:5k', '4:5 gönderi'], ['1:1k', 'Kare']], o.bicim)}
        <small class="kq-note">${Q.src ? `${img ? 'Fotoğrafın' : 'Videon'} ${Q.src.width}×${Q.src.height} (${Q.ratio()}). ` : ''}Reels/TikTok için 9:16 seç: "doldur" kenarlardan biraz kırpar, "bulanık arka" hiçbir şeyi kesmez.</small>`)}
      ${grp('yuz', 'Yüz netleştirme', `${chk('yuz', 'Yüzleri yapay zekâ ile netleştir')}${o.yuz ? sl('yuz_guc', 'Yüz netleştirme gücü', 0, 100, o.yuz_guc) : ''}<small class="kq-note">Bulanık yüzleri (yayıncı, kamera) netleştirir. İlk kullanımda model indirilir (~350 MB).</small>`)}
      ${grp('net', 'Netlik', `${sl('keskin', 'Keskinlik / çizgi netliği', 0, 100, o.keskin)}${sl('detay', 'Detay / doku güçlendirme', 0, 100, o.detay)}
        ${sl('gurultu', 'Gürültü / karıncalanma azaltma', 0, 100, o.gurultu)}${sl('yumusat', 'Kenar yumuşatma (tırtıkları azaltır)', 0, 100, o.yumusat)}
        ${chk('blok', 'Pikselleşme ve kare kare bozulmayı gider')}${chk('bant', 'Renk bantlarını gider (gökyüzü, karanlık sahneler)')}`)}
      ${grp('renk', 'Renk ve görüntü', `${chk('oto_renk', 'Otomatik renk ve ışık düzelt')}
        ${sl('parlak', 'Parlaklık', -50, 50, o.parlak)}${sl('kontrast', 'Kontrast', -50, 50, o.kontrast)}${sl('doygun', 'Renk canlılığı', -100, 100, o.doygun)}
        ${sl('sicaklik', 'Sıcaklık (soğuk ↔ sıcak)', -100, 100, o.sicaklik)}${sl('gamma', 'Gamma (orta tonlar)', -50, 50, o.gamma)}
        ${sl('golge', 'Gölgeler (karanlık alanlar)', -100, 100, o.golge)}${sl('parlak_alan', 'Parlak alanlar', -100, 100, o.parlak_alan)}
        ${sl('vinyet', 'Vinyet (kenar karartma)', 0, 100, o.vinyet)}${sl('gren', 'Film greni', 0, 100, o.gren)}`)}
      ${img ? grp('cikti', 'Kayıt', `<div class="kq-h">Dosya biçimi</div>${seg('foto_bicim', [['png', 'PNG (kayıpsız)'], ['jpg', 'JPG (küçük)'], ['webp', 'WebP']], o.foto_bicim || 'png')}`) : ''}
      ${img ? '' : grp('fps', 'Akıcılık (FPS)', `${seg('fps', FPS, o.fps)}${chk('fps_ai', 'Ara kareleri yapay zekâ ile üret (daha doğal)')}`)}
      ${img ? '' : grp('cikti', 'Çıktı ve ses', `<div class="kq-h">Dosya kalitesi</div>${seg('kalite', [['yuksek', 'Yüksek'], ['normal', 'Normal'], ['kucuk', 'Küçük dosya']], o.kalite)}
        <div class="kq-h">Video formatı</div>${seg('codec', [['h264', 'H.264 (her yerde açılır)'], ['h265', 'H.265 (yarı boyut)']], o.codec)}
        <div class="kq-h">Sadece bir aralığı işle</div>
        <div class="kq-range"><div><span>Başlangıç</span><b>${fmt(o.bas)}</b><button class="btn ghost sm" data-set="bas">Şu anki kare</button></div>
          <div><span>Bitiş</span><b>${o.bit > o.bas ? fmt(o.bit) : 'Sonuna kadar'}</b><button class="btn ghost sm" data-set="bit">Şu anki kare</button></div>
          ${o.bas || o.bit ? '<button class="btn ghost sm" data-set="tum">Tüm videoyu işle</button>' : ''}</div>
        <div class="kq-h">Ses</div>${chk('ses', 'Sesi koru')}${o.ses ? chk('ses_temizle', 'Sesteki uğultu ve cızırtıyı temizle') + chk('ses_dengele', 'Ses seviyesini dengele / yükselt') : ''}`)}
      <small class="kq-note">${Q.src ? Q.estimate() : ''}</small></div>
      <div class="kq-foot"><button class="btn primary glow kq-go" id="kqGo">✨ ${img ? 'Fotoğrafı İyileştir' : 'Kaliteyi Artır'}</button><button class="btn ghost sm" id="kqReset">Varsayılana döndür</button></div>`;
    $('.kq-scroll', el).scrollTop = keep;
    $$('.kq-g', el).forEach(d => d.addEventListener('toggle', () => { Q.open[d.dataset.g] = d.open; }));
    $$('[data-pre]', el).forEach(b => b.onclick = () => { Object.assign(Q.opts, PRESETS[b.dataset.pre][2]); const sc = $('.kq-scroll').scrollTop; Q.renderSide(); $('.kq-scroll').scrollTop = sc; Q.previewSoon(); });
    $$('.kq-seg', el).forEach(g => $$('button', g).forEach(b => b.onclick = () => { const k = g.dataset.k; Q.opts[k] = b.dataset.v; const sc = $('.kq-scroll').scrollTop; Q.renderSide(); $('.kq-scroll').scrollTop = sc; if (!NOPV.has(k)) Q.previewSoon(); }));
    $$('[data-r]', el).forEach(r => { KS.paintRange(r); r.oninput = () => { Q.opts[r.dataset.r] = +r.value; $('#kqv_' + r.dataset.r).textContent = r.value; KS.paintRange(r); }; r.onchange = () => Q.previewSoon(); });
    $$('[data-c]', el).forEach(c => c.onchange = () => { const k = c.dataset.c; Q.opts[k] = c.checked; const sc = $('.kq-scroll').scrollTop; Q.renderSide(); $('.kq-scroll').scrollTop = sc; if (!NOPV.has(k)) Q.previewSoon(); });
    $$('[data-set]', el).forEach(b => b.onclick = () => { const k = b.dataset.set, t = +$('#kqT').value; if (k === 'tum') { Q.opts.bas = 0; Q.opts.bit = 0; } else Q.opts[k] = +t.toFixed(2); if (Q.opts.bit && Q.opts.bit <= Q.opts.bas) Q.opts.bit = 0; const sc = $('.kq-scroll').scrollTop; Q.renderSide(); $('.kq-scroll').scrollTop = sc; });
    $('#kqGo').onclick = Q.start; Q.status();
    if ($('#kqBg')) $('#kqBg').onclick = async () => { try { const r = await KS.api('/api/gorsel/arkaplan', { path: Q.src.path }); KS.trackJob(r.job); } catch (e) { KS.toast(KS.esc(e.message), 'err'); } };
    if ($('#kqBOn')) $('#kqBOn').onclick = () => Q.brushOn();
    if ($('#kqBOff')) $('#kqBOff').onclick = () => Q.brushOff();
    if ($('#kqBClr')) $('#kqBClr').onclick = () => Q.brushClear();
    if ($('#kqInp')) $('#kqInp').onclick = () => Q.inpaint();
    const fb = $('[data-r="fircaBoy"]'); if (fb) fb.oninput = () => { Q.brush.size = +fb.value; $('#kqv_fircaBoy').textContent = fb.value; KS.paintRange(fb); };
    $('#kqReset').onclick = () => { Q.opts = Object.assign({}, DEF); Q.renderSide(); Q.previewSoon(); };
  };
  Q.ratio = () => { const w = Q.src.width, h = Q.src.height, r = w / h; const known = [[9 / 16, '9:16 dikey'], [3 / 4, '3:4'], [4 / 5, '4:5'], [1, '1:1 kare'], [16 / 9, '16:9 yatay'], [4 / 3, '4:3']]; const k = known.reduce((b, x) => Math.abs(x[0] - r) < Math.abs(b[0] - r) ? x : b); return Math.abs(k[0] - r) < .03 ? k[1] : r.toFixed(2); };
  Q.estimate = () => {
    if (Q.src.image) { const o = Q.opts; return o.model === 'klasik' && !o.yuz ? 'Birkaç saniyede biter.' : 'Ekran kartına göre birkaç saniye ile 1 dakika arası sürer.'; }
    const s = Q.src, o = Q.opts, d = (o.bit > o.bas ? o.bit : s.duration) - (o.bas || 0), fr = d * s.fps;
    if (o.model === 'klasik' && !o.yuz && (o.fps === 'kaynak' || !o.fps_ai)) return `İşlenecek: ${fmt(d)} · Tahmini süre: ${Math.max(1, Math.round(d / 40))} dk civarı.`;
    const per = o.model === 'klasik' ? 0 : (o.model === 'hizli' ? (o.olcek == 4 ? .12 : .05) : .35) * Math.max(1, s.width * s.height / 2073600);
    const rife = (o.fps !== 'kaynak' && o.fps_ai ? .03 : 0) + (o.yuz ? .08 : 0);
    const min = Math.max(1, Math.round(fr * (per + rife) / 60));
    return `İşlenecek: ${fmt(d)} · Tahmini süre: ~${min} dk (ekran kartına göre değişir). Uzun videolarda önce kısa bir aralık dene.`;
  };

  /* --- önizleme --- */
  let pvT = null, pvN = 0;
  Q.previewSoon = () => { clearTimeout(pvT); pvT = setTimeout(Q.preview, 450); };
  Q.preview = async () => {
    if (!Q.src) return;
    const n = ++pvN, t = Q.src.image ? 0 : +$('#kqT').value;
    $('#kqLoad').hidden = false; $('#kqLoadT').textContent = Q.src.ai_tools || Q.opts.model === 'klasik' ? 'Önizleme hazırlanıyor...' : 'İlk seferde yapay zekâ aracı indiriliyor (~50 MB)...';
    try {
      const r = await KS.api('/api/kalite/preview', { path: Q.src.path, t, opts: Q.opts });
      if (n !== pvN) return;
      Q.src.ai_tools = true;
      const v = Date.now();
      await Promise.all([[aImg, 'sonra'], [bImg, 'once']].map(([img, nm]) => new Promise(res => { img.onload = img.onerror = res; img.src = `/media/kalite/${r.key}/${nm}.jpg?v=${v}`; })));
      Q.w = r.w; Q.h = r.h;
      stage.hidden = false; handle.hidden = false; $('#kqTagL').hidden = false; $('#kqTagR').hidden = false;
      $('#kqTagR').textContent = r.ai ? 'SONRA (yapay zekâ)' : (Q.opts.model === 'klasik' ? 'SONRA (klasik)' : 'SONRA (klasik — ekran kartında yapay zekâ çalışmadı)');
      Q.layout();
    } catch (e) { if (n === pvN) KS.toast(KS.esc(e.message), 'err'); }
    finally { if (n === pvN) $('#kqLoad').hidden = true; }
  };
  const tIn = $('#kqT');
  tIn.oninput = () => { $('#kqTime').textContent = fmt(+tIn.value); KS.paintRange(tIn); };
  tIn.onchange = () => Q.preview();

  /* --- karşılaştırma görünümü: kaydırma çizgisi, yakınlaştırma, sürükleme --- */
  Q.layout = () => {
    if (!Q.w) return;
    const vw = view.clientWidth, vh = view.clientHeight, fit = Math.min(vw / Q.w, vh / Q.h), s = fit * Q.zoom;
    const w = Q.w * s, h = Q.h * s;
    const maxX = Math.max(0, (w - vw) / 2), maxY = Math.max(0, (h - vh) / 2);
    Q.pan.x = KS.clamp(Q.pan.x, -maxX, maxX); Q.pan.y = KS.clamp(Q.pan.y, -maxY, maxY);
    const left = (vw - w) / 2 + Q.pan.x, top = (vh - h) / 2 + Q.pan.y;
    Object.assign(stage.style, { width: w + 'px', height: h + 'px', left: left + 'px', top: top + 'px' });
    [aImg, bImg].forEach(i => { i.style.width = w + 'px'; i.style.height = h + 'px'; });
    // çizgi ekranda sabit; "önce" tarafı çizginin solu
    const lx = vw * Q.split;
    bWrap.style.width = Math.max(0, lx - left) + 'px';
    handle.style.left = lx + 'px';
    const pix = Q.zoom > 1 ? 'pixelated' : 'auto'; aImg.style.imageRendering = bImg.style.imageRendering = Q.zoom >= 4 ? pix : 'auto';
  };
  new ResizeObserver(() => Q.layout()).observe(view);
  $$('#kqZoom button').forEach(b => b.onclick = () => { Q.zoom = +b.dataset.z; Q.pan = { x: 0, y: 0 }; $$('#kqZoom button').forEach(x => x.classList.toggle('on', x === b)); Q.layout(); });
  view.addEventListener('wheel', e => {
    if (!Q.w) return; e.preventDefault();
    const r = view.getBoundingClientRect(), cx = e.clientX - r.left - r.width / 2, cy = e.clientY - r.top - r.height / 2, old = Q.zoom;
    Q.zoom = KS.clamp(Q.zoom * (e.deltaY < 0 ? 1.25 : .8), 1, 8);
    Q.pan.x = cx - (cx - Q.pan.x) * Q.zoom / old; Q.pan.y = cy - (cy - Q.pan.y) * Q.zoom / old;
    $$('#kqZoom button').forEach(x => x.classList.toggle('on', +x.dataset.z === Q.zoom)); Q.layout();
  }, { passive: false });
  view.addEventListener('mousedown', e => {
    if (!Q.w) return; e.preventDefault();
    const r = view.getBoundingClientRect(), onHandle = Math.abs(e.clientX - r.left - r.width * Q.split) < 14 || e.target.closest('#kqHandle');
    const sx = e.clientX, sy = e.clientY, p0 = { ...Q.pan };
    const mv = ev => {
      if (onHandle || Q.zoom === 1 || e.button === 0 && !e.shiftKey && Q.zoom === 1) { Q.split = KS.clamp((ev.clientX - r.left) / r.width, 0, 1); }
      else { Q.pan.x = p0.x + ev.clientX - sx; Q.pan.y = p0.y + ev.clientY - sy; }
      Q.layout();
    };
    const up = () => { removeEventListener('mousemove', mv); removeEventListener('mouseup', up); };
    addEventListener('mousemove', mv); addEventListener('mouseup', up);
    if (onHandle || Q.zoom === 1) mv(e);
  });

  /* --- nesne silme fırçası (fotoğraf) --- */
  const bBox = $('#kqBrush'), bCv = $('#kqBCanvas');
  let mask = null, bImgEl = null;
  Q.brushOn = () => {
    if (!Q.src || !Q.src.image) return;
    Q.open.gorsel = true;
    Q.brush = { size: (Q.brush && Q.brush.size) || 40 };
    mask = document.createElement('canvas'); mask.width = Q.src.width; mask.height = Q.src.height;
    const mc = mask.getContext('2d'); mc.fillStyle = '#000'; mc.fillRect(0, 0, mask.width, mask.height);
    bImgEl = new Image(); bImgEl.onload = () => Q.brushDraw(); bImgEl.src = '/media/kalite_src?path=' + encodeURIComponent(Q.src.path);
    bCv.width = Q.src.width; bCv.height = Q.src.height;
    bBox.hidden = false; stage.hidden = true; handle.hidden = true; $('#kqTagL').hidden = $('#kqTagR').hidden = true;
    Q.brushFit(); Q.renderSide();
  };
  Q.brushOff = () => { Q.brush = null; mask = null; bBox.hidden = true; stage.hidden = false; handle.hidden = false; $('#kqTagL').hidden = $('#kqTagR').hidden = false; Q.renderSide(); };
  Q.brushClear = () => { if (!mask) return; const mc = mask.getContext('2d'); mc.fillStyle = '#000'; mc.fillRect(0, 0, mask.width, mask.height); Q.brushDraw(); };
  Q.brushFit = () => {
    if (!Q.brush) return;
    const vw = view.clientWidth, vh = view.clientHeight, s = Math.min(vw / bCv.width, vh / bCv.height);
    Object.assign(bCv.style, { width: bCv.width * s + 'px', height: bCv.height * s + 'px' });
  };
  new ResizeObserver(() => Q.brushFit()).observe(view);
  Q.brushDraw = () => {
    const c = bCv.getContext('2d');
    c.clearRect(0, 0, bCv.width, bCv.height);
    if (bImgEl && bImgEl.complete) c.drawImage(bImgEl, 0, 0, bCv.width, bCv.height);
    if (!mask) return;
    // maske: kırmızı yarı saydam
    const t = document.createElement('canvas'); t.width = mask.width; t.height = mask.height; const tc = t.getContext('2d');
    tc.drawImage(mask, 0, 0); tc.globalCompositeOperation = 'source-in';
    const d = tc.getImageData(0, 0, t.width, t.height), px = d.data;
    for (let i = 0; i < px.length; i += 4) { const v = px[i]; px[i] = 255; px[i + 1] = 40; px[i + 2] = 40; px[i + 3] = v * .55; }
    tc.putImageData(d, 0, 0); c.drawImage(t, 0, 0);
  };
  let painting = false, last = null;
  const toImg = e => { const r = bCv.getBoundingClientRect(); return { x: (e.clientX - r.left) * bCv.width / r.width, y: (e.clientY - r.top) * bCv.height / r.height, k: bCv.width / r.width }; };
  const stroke = (a, b) => {
    const mc = mask.getContext('2d'); mc.strokeStyle = '#fff'; mc.fillStyle = '#fff'; mc.lineCap = 'round'; mc.lineJoin = 'round';
    mc.lineWidth = Q.brush.size * b.k; mc.beginPath(); mc.moveTo(a.x, a.y); mc.lineTo(b.x, b.y); mc.stroke();
    mc.beginPath(); mc.arc(b.x, b.y, Q.brush.size * b.k / 2, 0, Math.PI * 2); mc.fill();
  };
  let rafB = 0; const redraw = () => { if (!rafB) rafB = requestAnimationFrame(() => { rafB = 0; Q.brushDraw(); }); };
  bCv.addEventListener('mousedown', e => { if (!Q.brush || e.button !== 0) return; e.preventDefault(); e.stopPropagation(); painting = true; last = toImg(e); stroke(last, last); redraw(); });
  addEventListener('mousemove', e => { if (!painting) return; const p = toImg(e); stroke(last, p); last = p; redraw(); });
  addEventListener('mouseup', () => { painting = false; });
  bBox.addEventListener('wheel', e => e.stopPropagation(), { passive: true });
  Q.inpaint = async () => {
    if (!mask) return;
    try {
      const r = await KS.api('/api/gorsel/nesne', { path: Q.src.path, mask: mask.toDataURL('image/png') });
      KS.trackJob(r.job); Q.brushOff();
    } catch (e) { KS.toast(KS.esc(e.message), 'err'); }
  };

  /* --- tüm videoyu işle --- */
  Q.start = async () => {
    if (!Q.src) return KS.toast('Önce bir video ya da fotoğraf seç', 'err');
    if (Q.job()) return;
    try {
      const r = await KS.api('/api/kalite/start', { path: Q.src.path, opts: Q.opts });
      KS.trackJob(r.job); Q.status();
    } catch (e) { KS.toast(KS.esc(e.message), 'err'); }
  };

  /* --- çalışan iş kartı: yüzde, kalan süre, bitiş saati, duraklat / iptal --- */
  const dur = s => {
    s = Math.max(0, Math.round(s || 0));
    if (s < 60) return `${s} sn`;
    const h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60), sec = s % 60;
    return h ? `${h} sa ${m} dk` : `${m} dk ${String(sec).padStart(2, '0')} sn`;
  };
  const clock = s => { const d = new Date(Date.now() + s * 1000); return d.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' }); };
  Q.job = () => (KS.state.jobs || []).find(x => (x.kind === 'kalite' || x.kind === 'gorsel') && (x.status === 'calisiyor' || x.status === 'bekliyor'));
  Q.yarim = [];
  Q.loadYarim = async () => { try { Q.yarim = await KS.api('/api/kalite/yarim'); } catch (e) { Q.yarim = []; } Q.status(); };
  Q.status = () => {
    const box = $('#kqJob'); if (!box) return;
    const j = Q.job(), go = $('#kqGo');
    if (go) go.hidden = !!j;
    if (!j && Q.done) {
      box.hidden = false;
      if (box.dataset.mode !== 'done') {
        const res = Q.done; box.dataset.mode = 'done'; box.dataset.html = ''; box.classList.remove('paused');
        box.innerHTML = `<div class="kq-y kq-done"><div class="kq-y-t"><b>✓ Bitti</b><span>${KS.esc(res.name)}</span></div><div class="kq-pbar"><i style="width:100%;background:#3fb56b"></i></div>
          <div class="kq-run-btns"><button class="btn primary" id="kqDAdd">Editöre ekle</button><button class="btn ghost" id="kqDShow">Klasörde göster</button></div>
          <button class="btn ghost sm" id="kqDOk">Tamam</button></div>`;
        $('#kqDShow', box).onclick = () => KS.api('/api/reveal', { path: res.path });
        $('#kqDAdd', box).onclick = async () => { const f = await KS.api('/api/describe', { path: res.path }); Q.done = null; Q.status(); KS.handleFile(f); };
        $('#kqDOk', box).onclick = () => { Q.done = null; Q.status(); };
      }
      return;
    }
    if (!j) {
      box.classList.remove('paused');
      if (!Q.yarim.length) { box.hidden = true; box.innerHTML = ''; box.dataset.mode = ''; return; }
      box.hidden = false;
      const html = Q.yarim.map(u => `<div class="kq-y"><div class="kq-y-t"><b>⏸ Yarım kaldı</b><span>${KS.esc(u.name)}</span></div>
        <div class="kq-pbar"><i style="width:${Math.round(u.progress * 100)}%"></i></div>
        <div class="kq-y-i">%${Math.round(u.progress * 100)} bitti${u.total > 1 ? ` · ${u.done}/${u.total} parça hazır` : ''} · kaldığı yerden devam eder</div>
        <div class="kq-run-btns"><button class="btn primary" data-devam="${u.id}">▶ Devam et</button><button class="btn ghost" data-sil="${u.id}">Sil</button></div></div>`).join('');
      if (box.dataset.html !== html) {
        box.innerHTML = html; box.dataset.html = html; box.dataset.mode = 'y';
        $$('[data-devam]', box).forEach(b => b.onclick = async () => { try { const r = await KS.api('/api/kalite/devam', { id: b.dataset.devam }); Q.yarim = Q.yarim.filter(x => x.id !== b.dataset.devam); KS.trackJob(r.job); box.dataset.html = ''; Q.status(); } catch (e) { KS.toast(KS.esc(e.message), 'err'); } });
        $$('[data-sil]', box).forEach(b => b.onclick = async () => { if (!await KS.confirm('Yarım kalan işi sil?', 'Şimdiye kadar işlenen kısım silinir, baştan başlaman gerekir.', 'Sil', true)) return; await KS.api('/api/kalite/sil', { id: b.dataset.sil }); Q.yarim = Q.yarim.filter(x => x.id !== b.dataset.sil); box.dataset.html = ''; Q.status(); });
      }
      return;
    }
    box.hidden = false;
    if (box.dataset.mode !== 'run' || box.dataset.jid !== j.id) {
      box.dataset.mode = 'run'; box.dataset.jid = j.id; box.dataset.html = '';
      box.innerHTML = `<div class="kq-run">
        <div class="kq-run-top"><div><span class="kq-run-t" id="kqRunT"></span><small id="kqRunN"></small></div><b class="kq-run-p" id="kqRunP">%0</b></div>
        <div class="kq-pbar big"><i id="kqProg"></i></div>
        <div class="kq-run-grid"><div><small>Kalan süre</small><b id="kqEta">hesaplanıyor…</b></div><div><small>Bitiş saati</small><b id="kqEnd">—</b></div>
          <div><small>Geçen süre</small><b id="kqEl">0 sn</b></div><div><small>Parça</small><b id="kqPart">—</b></div></div>
        <div class="kq-run-msg" id="kqMsg"></div>
        <div class="kq-run-btns"><button class="btn ghost" id="kqPause"></button><button class="btn ghost kq-x" id="kqCancel">✕ İptal</button></div>
        <small class="kq-run-note">Uygulamayı kapatırsan iş duraklar; tekrar açınca kaldığı yerden devam edebilirsin.</small></div>`;
      $('#kqPause', box).onclick = async () => { const jj = Q.job(); if (!jj) return; jj.paused = !jj.paused; Q.status(); await KS.api(`/api/jobs/${jj.id}/pause`, { pause: jj.paused }); };
      $('#kqCancel', box).onclick = async () => { const jj = Q.job(); if (!jj) return; if (!await KS.confirm('Kalite artırma iptal edilsin mi?', 'Şimdiye kadar işlenen kısım silinir.', 'İptal et', true)) return; await KS.api(`/api/jobs/${jj.id}/cancel`, {}); };
    }
    const ex = j.extra || {}, p = Math.round((j.progress || 0) * 1000) / 10, wait = j.status === 'bekliyor';
    box.classList.toggle('paused', !!j.paused);
    $('#kqRunT').textContent = j.paused ? '⏸ Duraklatıldı' : wait ? 'Sırada bekliyor' : /^Fotoğraf: /.test(j.title) ? 'Fotoğraf iyileştiriliyor' : j.kind === 'gorsel' ? j.title.split(':')[0] : 'Kalite artırılıyor';
    $('#kqRunN').textContent = j.title.replace(/^[^:]+: /, '');
    $('#kqRunP').textContent = `%${p.toFixed(p < 10 ? 1 : 0)}`;
    $('#kqProg').style.width = p + '%';
    const eta = ex.eta;
    $('#kqEta').textContent = j.paused ? 'duraklatıldı' : eta != null ? '~' + dur(eta) : 'hesaplanıyor…';
    $('#kqEnd').textContent = !j.paused && eta != null ? clock(eta) : '—';
    $('#kqEl').textContent = dur(ex.elapsed);
    $('#kqPart').textContent = ex.parca || '—';
    $('#kqMsg').textContent = j.paused ? 'Ekran kartı serbest. Devam ettiğinde kaldığı yerden sürer.' : (ex.asama || j.message || '');
    $('#kqPause').textContent = j.paused ? '▶ Devam et' : '⏸ Duraklat';
    $('#kqPause').classList.toggle('primary', !!j.paused); $('#kqPause').classList.toggle('ghost', !j.paused);
  };
  KS.hooks.jobTick.push(() => Q.status());
  KS.hooks.jobDone.push(j => {
    if (j.kind !== 'kalite' || j.status !== 'bitti' || !j.result) return;
    const res = j.result;
    Q.done = res; Q.status();
    if (KS.page === 'kalite') return;
    KS.toast(`Kalite artırıldı: <b>${KS.esc(res.name)}</b>`, 'ok', [
      { label: 'Klasörde göster', fn: () => KS.api('/api/reveal', { path: res.path }) },
      { label: 'Editöre ekle', primary: true, fn: async () => { const f = await KS.api('/api/describe', { path: res.path }); KS.handleFile(f); } },
    ], 0);
  });
  KS.hooks.state.push(() => { if (!Q.opts && KS.state.settings) Q.opts = Object.assign({}, DEF, KS.state.settings.kalite_ayar || {}); });
  KS.hooks.jobDone.push(j => { if (j.kind === 'kalite') Q.loadYarim(); });
  Q.loadYarim();
})();
