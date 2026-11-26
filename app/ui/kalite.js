/* Kesit Stüdyosu — Kalite Artır (yapay zekâ ile netleştirme, önce/sonra önizleme) */
(() => {
  const Q = KS.kalite = { src: null, opts: null, split: .5, zoom: 1, pan: { x: 0, y: 0 } };
  const view = $('#kqView'), stage = $('#kqStage'), aImg = $('#kqAfter'), bImg = $('#kqBefore'), bWrap = $('#kqBeforeWrap'), handle = $('#kqHandle');
  const MODELS = [['hizli', 'Hızlı', 'Video için hızlı yapay zekâ'], ['gercek', 'En iyi', 'Gerçek görüntü, en net (yavaş)'], ['anime', 'Anime', 'Çizgi film / anime'], ['klasik', 'Klasik', 'Yapay zekâsız, çok hızlı']];
  const TARGETS = [['kaynak', 'Aynı'], ['720', '720p'], ['1080', '1080p'], ['1440', '2K'], ['2160', '4K']];
  const FPS = [['kaynak', 'Aynı'], ['30', '30'], ['60', '60'], ['90', '90'], ['120', '120']];
  const fmt = s => { s = Math.max(0, s || 0); return `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`; };

  Q.load = async path => {
    try {
      const r = await KS.api('/api/kalite/info?path=' + encodeURIComponent(path));
      Q.src = r; Q.opts = Object.assign({}, DEF, r.opts, { bas: 0, bit: 0 });
      $('#kqName').textContent = `${r.name} · ${r.width}×${r.height} · ${Math.round(r.fps)} FPS · ${fmt(r.duration)}`;
      const t = $('#kqT'); t.max = Math.max(.1, r.duration - .05).toFixed(2); t.value = Math.min(r.duration / 3, r.duration).toFixed(2); KS.paintRange(t);
      $('#kqDur').textContent = fmt(r.duration);
      $('#kqEmpty').hidden = true;
      Q.renderSide(); Q.preview();
    } catch (e) { KS.toast(KS.esc(e.message), 'err'); }
  };
  $('#kqPick').onclick = async () => { try { const f = await KS.api('/api/pick_any', {}); if (f && f.path) { if (f.kind && f.kind !== 'video') return KS.toast('Bir video seç', 'err'); Q.load(f.path); } } catch (e) { KS.toast(KS.esc(e.message), 'err'); } };

  /* --- ayarlar --- */
  const seg = (key, list, cur) => `<div class="seg kq-seg" data-k="${key}">${list.map(([v, n, tip]) => `<button data-v="${v}" class="${String(cur) === String(v) ? 'on' : ''}" ${tip ? `title="${tip}"` : ''}>${n}</button>`).join('')}</div>`;
  const sl = (key, label, min, max, cur, hint) => `<div class="kq-sl"><div><span>${label}</span><b id="kqv_${key}">${cur}</b></div><input type="range" min="${min}" max="${max}" value="${cur}" data-r="${key}">${hint ? `<small>${hint}</small>` : ''}</div>`;
  const DEF = { model: 'hizli', olcek: 2, hedef: '1080', keskin: 45, gurultu: 25, blok: true, parlak: 0, kontrast: 0, doygun: 0, fps: 'kaynak', fps_ai: true,
    yuz: false, yuz_guc: 70, ai_guc: 100, detay: 0, yumusat: 0, bant: false, sicaklik: 0, golge: 0, parlak_alan: 0, gamma: 0, vinyet: 0, gren: 0, oto_renk: false,
    kalite: 'yuksek', codec: 'h264', bicim: 'kaynak', bas: 0, bit: 0, ses: true, ses_temizle: false, ses_dengele: false };
  Q.DEF = DEF;
  const NOPV = new Set(['fps', 'fps_ai', 'kalite', 'codec', 'bas', 'bit', 'ses', 'ses_temizle', 'ses_dengele']);
  const chk = (key, label) => `<label class="ae-chk kq-chk"><input type="checkbox" data-c="${key}" ${Q.opts[key] ? 'checked' : ''}>${label}</label>`;
  Q.open = Q.open || { ai: true, net: true };
  const grp = (id, title, body) => `<details class="kq-g" data-g="${id}" ${Q.open[id] ? 'open' : ''}><summary>${title}</summary><div class="kq-gb">${body}</div></details>`;
  Q.renderSide = () => {
    const o = Q.opts, el = $('#kqSide');
    if (!o) { el.innerHTML = ''; return; }
    Object.keys(DEF).forEach(k => { if (o[k] === undefined) o[k] = DEF[k]; });
    const m = MODELS.find(x => x[0] === o.model) || MODELS[0], dur = Q.src ? Q.src.duration : 0, keep = el.scrollTop;
    el.innerHTML = `<div class="kq-scroll">
      ${grp('ai', 'Yapay zekâ ve çözünürlük', `${seg('model', MODELS, o.model)}<small class="kq-note">${m[2]}</small>
        ${o.model === 'hizli' ? `<div class="kq-h">Yapay zekâ büyütme</div>${seg('olcek', [['2', '2x'], ['4', '4x (daha net, yavaş)']], o.olcek)}` : ''}
        ${o.model !== 'klasik' ? sl('ai_guc', 'Yapay zekâ gücü (azaltınca daha doğal)', 0, 100, o.ai_guc) : ''}
        <div class="kq-h">Çıkış çözünürlüğü</div>${seg('hedef', TARGETS, o.hedef)}
        <div class="kq-h">Biçim (ekran şekli)</div>${seg('bicim', [['kaynak', 'Videonun kendisi'], ['9:16k', 'Reels 9:16 (doldur)'], ['9:16b', 'Reels 9:16 (bulanık arka)'], ['4:5k', '4:5 gönderi'], ['1:1k', 'Kare']], o.bicim)}
        <small class="kq-note">${Q.src ? `Videon ${Q.src.width}×${Q.src.height} (${Q.ratio()}). ` : ''}Reels/TikTok için 9:16 seç: "doldur" kenarlardan biraz kırpar, "bulanık arka" hiçbir şeyi kesmez.</small>`)}
      ${grp('yuz', 'Yüz netleştirme', `${chk('yuz', 'Yüzleri yapay zekâ ile netleştir')}${o.yuz ? sl('yuz_guc', 'Yüz netleştirme gücü', 0, 100, o.yuz_guc) : ''}<small class="kq-note">Bulanık yüzleri (yayıncı, kamera) netleştirir. İlk kullanımda model indirilir (~350 MB).</small>`)}
      ${grp('net', 'Netlik', `${sl('keskin', 'Keskinlik / çizgi netliği', 0, 100, o.keskin)}${sl('detay', 'Detay / doku güçlendirme', 0, 100, o.detay)}
        ${sl('gurultu', 'Gürültü / karıncalanma azaltma', 0, 100, o.gurultu)}${sl('yumusat', 'Kenar yumuşatma (tırtıkları azaltır)', 0, 100, o.yumusat)}
        ${chk('blok', 'Pikselleşme ve kare kare bozulmayı gider')}${chk('bant', 'Renk bantlarını gider (gökyüzü, karanlık sahneler)')}`)}
      ${grp('renk', 'Renk ve görüntü', `${chk('oto_renk', 'Otomatik renk ve ışık düzelt')}
        ${sl('parlak', 'Parlaklık', -50, 50, o.parlak)}${sl('kontrast', 'Kontrast', -50, 50, o.kontrast)}${sl('doygun', 'Renk canlılığı', -100, 100, o.doygun)}
        ${sl('sicaklik', 'Sıcaklık (soğuk ↔ sıcak)', -100, 100, o.sicaklik)}${sl('gamma', 'Gamma (orta tonlar)', -50, 50, o.gamma)}
        ${sl('golge', 'Gölgeler (karanlık alanlar)', -100, 100, o.golge)}${sl('parlak_alan', 'Parlak alanlar', -100, 100, o.parlak_alan)}
        ${sl('vinyet', 'Vinyet (kenar karartma)', 0, 100, o.vinyet)}${sl('gren', 'Film greni', 0, 100, o.gren)}`)}
      ${grp('fps', 'Akıcılık (FPS)', `${seg('fps', FPS, o.fps)}${chk('fps_ai', 'Ara kareleri yapay zekâ ile üret (daha doğal)')}`)}
      ${grp('cikti', 'Çıktı ve ses', `<div class="kq-h">Dosya kalitesi</div>${seg('kalite', [['yuksek', 'Yüksek'], ['normal', 'Normal'], ['kucuk', 'Küçük dosya']], o.kalite)}
        <div class="kq-h">Video formatı</div>${seg('codec', [['h264', 'H.264 (her yerde açılır)'], ['h265', 'H.265 (yarı boyut)']], o.codec)}
        <div class="kq-h">Sadece bir aralığı işle</div>
        <div class="kq-range"><div><span>Başlangıç</span><b>${fmt(o.bas)}</b><button class="btn ghost sm" data-set="bas">Şu anki kare</button></div>
          <div><span>Bitiş</span><b>${o.bit > o.bas ? fmt(o.bit) : 'Sonuna kadar'}</b><button class="btn ghost sm" data-set="bit">Şu anki kare</button></div>
          ${o.bas || o.bit ? '<button class="btn ghost sm" data-set="tum">Tüm videoyu işle</button>' : ''}</div>
        <div class="kq-h">Ses</div>${chk('ses', 'Sesi koru')}${o.ses ? chk('ses_temizle', 'Sesteki uğultu ve cızırtıyı temizle') + chk('ses_dengele', 'Ses seviyesini dengele / yükselt') : ''}`)}
      <small class="kq-note">${Q.src ? Q.estimate() : ''}</small></div>
      <div class="kq-foot"><div class="kq-status" id="kqStatus" hidden><div class="progress"><i id="kqProg"></i></div><span id="kqMsg"></span></div><button class="btn primary glow kq-go" id="kqGo">✨ Kaliteyi Artır</button><button class="btn ghost sm" id="kqReset">Varsayılana döndür</button></div>`;
    $('.kq-scroll', el).scrollTop = keep;
    $$('.kq-g', el).forEach(d => d.addEventListener('toggle', () => { Q.open[d.dataset.g] = d.open; }));
    $$('.kq-seg', el).forEach(g => $$('button', g).forEach(b => b.onclick = () => { const k = g.dataset.k; Q.opts[k] = b.dataset.v; const sc = $('.kq-scroll').scrollTop; Q.renderSide(); $('.kq-scroll').scrollTop = sc; if (!NOPV.has(k)) Q.previewSoon(); }));
    $$('[data-r]', el).forEach(r => { KS.paintRange(r); r.oninput = () => { Q.opts[r.dataset.r] = +r.value; $('#kqv_' + r.dataset.r).textContent = r.value; KS.paintRange(r); }; r.onchange = () => Q.previewSoon(); });
    $$('[data-c]', el).forEach(c => c.onchange = () => { const k = c.dataset.c; Q.opts[k] = c.checked; const sc = $('.kq-scroll').scrollTop; Q.renderSide(); $('.kq-scroll').scrollTop = sc; if (!NOPV.has(k)) Q.previewSoon(); });
    $$('[data-set]', el).forEach(b => b.onclick = () => { const k = b.dataset.set, t = +$('#kqT').value; if (k === 'tum') { Q.opts.bas = 0; Q.opts.bit = 0; } else Q.opts[k] = +t.toFixed(2); if (Q.opts.bit && Q.opts.bit <= Q.opts.bas) Q.opts.bit = 0; const sc = $('.kq-scroll').scrollTop; Q.renderSide(); $('.kq-scroll').scrollTop = sc; });
    $('#kqGo').onclick = Q.start; Q.status();
    $('#kqReset').onclick = () => { Q.opts = Object.assign({}, DEF); Q.renderSide(); Q.previewSoon(); };
  };
  Q.ratio = () => { const w = Q.src.width, h = Q.src.height, r = w / h; const known = [[9 / 16, '9:16 dikey'], [3 / 4, '3:4'], [4 / 5, '4:5'], [1, '1:1 kare'], [16 / 9, '16:9 yatay'], [4 / 3, '4:3']]; const k = known.reduce((b, x) => Math.abs(x[0] - r) < Math.abs(b[0] - r) ? x : b); return Math.abs(k[0] - r) < .03 ? k[1] : r.toFixed(2); };
  Q.estimate = () => {
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
    const n = ++pvN, t = +$('#kqT').value;
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

  /* --- tüm videoyu işle --- */
  Q.start = async () => {
    if (!Q.src) return KS.toast('Önce bir video seç', 'err');
    try {
      const r = await KS.api('/api/kalite/start', { path: Q.src.path, opts: Q.opts });
      KS.trackJob(r.job); KS.openJobs();
      KS.toast('Kalite artırma başladı. Bitince haber vereceğim, bu sırada başka işlere devam edebilirsin.', 'ok');
    } catch (e) { KS.toast(KS.esc(e.message), 'err'); }
  };
  Q.status = () => {
    const st = $('#kqStatus'); if (!st) return;
    const j = (KS.state.jobs || []).find(x => x.kind === 'kalite' && (x.status === 'calisiyor' || x.status === 'bekliyor'));
    st.hidden = !j; if (!j) return;
    $('#kqProg').style.width = Math.round((j.progress || 0) * 100) + '%';
    $('#kqMsg').textContent = `%${Math.round((j.progress || 0) * 100)} · ${j.message || ''}`;
  };
  KS.hooks.jobTick.push(() => Q.status());
  KS.hooks.jobDone.push(j => {
    if (j.kind !== 'kalite' || j.status !== 'bitti' || !j.result) return;
    const res = j.result;
    KS.toast(`Kalite artırıldı: <b>${KS.esc(res.name)}</b>`, 'ok', [
      { label: 'Klasörde göster', fn: () => KS.api('/api/reveal', { path: res.path }) },
      { label: 'Editöre ekle', primary: true, fn: async () => { const f = await KS.api('/api/describe', { path: res.path }); KS.handleFile(f); } },
    ], 0);
  });
  KS.hooks.state.push(() => { if (!Q.opts && KS.state.settings) Q.opts = Object.assign({}, DEF, KS.state.settings.kalite_ayar || {}); });
})();
