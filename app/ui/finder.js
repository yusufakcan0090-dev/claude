/* Klip Bulucu */
(() => {
  const F = KS.finder = { videos: [], clips: [], selClips: new Set(), analysis: null, selMoments: new Set(), slug: '' };

  /* ---------- sekmeler ---------- */
  const tabs = $('#finderTabs');
  const ink = $('.tab-ink', tabs);
  const setInk = () => { const a = $('.tab.active', tabs); if (a) { ink.style.left = a.offsetLeft + 'px'; ink.style.width = a.offsetWidth + 'px'; } };
  F.tab = name => {
    $$('.tab', tabs).forEach(t => t.classList.toggle('active', t.dataset.tab === name));
    $$('#page-finder .tab-panel').forEach(p => p.classList.toggle('active', p.id === 'tab-' + name));
    setInk();
    $('#clipsBar').classList.toggle('show', name === 'clips' && F.selClips.size > 0);
    if (name === 'moments') F.renderAnalyses();
    if (name === 'projects') F.renderProjects();
  };
  $$('.tab', tabs).forEach(t => t.onclick = () => F.tab(t.dataset.tab));
  window.addEventListener('resize', setInk);
  setTimeout(setInk, 50);

  /* ---------- arama ---------- */
  const input = $('#channelInput');
  const skel = n => Array.from({ length: n }, (_, i) => `<div class="skel skel-card" style="animation-delay:${i * .05}s"></div>`).join('');
  const emptyHtml = (title, text, icon = KS.icon.search) => `<div class="empty"><div class="ico">${icon}</div><div class="big">${title}</div>${text}</div>`;

  F.search = async () => {
    const q = input.value.trim();
    if (!q) { input.focus(); return; }
    // Kick tek video / klip linki
    if (/kick\.com\/[\w-]+\/videos\/[0-9a-f-]{36}/i.test(q)) return F.directLink(q, 'vod');
    if (/clip_[\w-]+/i.test(q)) return F.directLink(q, 'clip');
    $('#videosGrid').innerHTML = skel(8);
    $('#clipsGrid').innerHTML = skel(8); $('#shortsGrid').innerHTML = skel(8);
    F.tab('videos');
    $('#searchBtn').disabled = true;
    try {
      const r = await KS.api('/api/kick/list', { channel: q });
      if (r.single) {
        $('#videosGrid').innerHTML = ''; F.renderVideos();
        return F.directLink(r.single.url, r.single.duration && r.single.duration < 90 ? 'clip' : 'other', r.single.title, r.single);
      }
      F.source = r.source; F.listTitle = r.title;
      F.slug = r.slug; F.videos = r.videos; F.shorts = r.shorts || []; F.clips = r.clips; F.selClips.clear();
      KS.state.settings.son_kanal = r.slug;
      F.renderVideos(); F.renderShorts(); F.renderClips(); F.renderRecent();
      const sg = $('#suggestRow'), sug = (r.suggest || []).filter(Boolean);
      sg.hidden = !sug.length && !r.kick;
      sg.innerHTML = (r.kick ? `<span class="ex-l">Kick'te bulunan: <b style="color:#53fc18">${KS.esc(r.kick)}</b></span>` : '') + (sug.length ? `<span class="ex-l">${r.kick ? ' · ' : ''}Benzer Kick kanalları:</span>` + sug.map(s => `<button data-sg="${KS.esc(s)}">🟢 ${KS.esc(s)}</button>`).join('') : '');
      $$('[data-sg]', sg).forEach(b => b.onclick = () => { input.value = b.dataset.sg; input.dispatchEvent(new Event('input')); F.search(); });
      if (!r.videos.length && r.clips.length) F.tab('clips');
      if (r.errors.length) KS.toast(KS.esc(r.errors.join(' · ')), 'err', [], 7000);
    } catch (e) {
      $('#videosGrid').innerHTML = emptyHtml('Kanal bulunamadı', KS.esc(e.message));
      $('#clipsGrid').innerHTML = ''; $('#shortsGrid').innerHTML = '';
    } finally { $('#searchBtn').disabled = false; }
  };
  $('#searchBtn').onclick = F.search;
  const badge = $('#srcBadge');
  input.addEventListener('input', () => {
    const q = input.value.trim().toLowerCase();
    let b = ['ARA', ''];
    if (/kick\.com/.test(q) || (q && !q.includes(' ') && !q.includes('.') && !q.includes('/'))) b = ['KICK', 'kick'];
    if (/youtu\.?be/.test(q) || (q.includes(' ') && !/^https?:/.test(q))) b = ['YOUTUBE', 'yt'];
    if (/twitch\.tv/.test(q)) b = ['TWITCH', 'tw'];
    if (/^https?:/.test(q) && b[1] === '') b = ['LİNK', 'link'];
    badge.textContent = b[0]; badge.className = 'kick-badge ' + b[1];
  });
  input.onkeydown = e => { if (e.key === 'Enter') F.search(); };
  $('#localBtn').onclick = KS.addFile;

  /* indirilen klipler nereye gitsin? açık proje varsa sor */
  F.target = () => new Promise(res => {
    const ed = KS.editor;
    if (!ed || !ed.project) return res(null);
    const md = KS.modal(`<h2>Nereye eklensin?</h2><p class="msub">Editörde açık proje: <b>${KS.esc(ed.project.title)}</b></p>
      <div class="big-choice"><button id="tgA"><span class="e">➕</span><b>Açık projeye ekle</b><small>Videonun sonuna eklenir.</small></button>
      <button id="tgB"><span class="e">📁</span><b>Ayrı proje</b><small>Her klip kendi projesinde.</small></button></div>`);
    let done = false; const fin = v => { if (done) return; done = true; md.close(); res(v); };
    $('#tgA', md.el).onclick = () => fin(ed.project.id); $('#tgB', md.el).onclick = () => fin(null);
    const t = setInterval(() => { if (!md.el.isConnected) { clearInterval(t); if (!done) { done = true; res(undefined); } } }, 300);
  });
  const dl = async body => { const project = await F.target(); if (project === undefined) return null; return KS.api('/api/kick/clip', { ...body, project }); };

  F.directLink = (url, type, title, info) => {
    const md = KS.modal(`<h2>${type === 'clip' ? 'Klip linki' : 'Video linki'}</h2><p class="msub" style="word-break:break-all">${KS.esc(title || url)}${info && info.duration ? ' · ' + KS.fmt(info.duration) : ''}</p>
      <div class="big-choice">
        <button id="dlA" ${type === 'clip' ? 'style="opacity:.5"' : ''}><span class="e">✨</span><b>Anları Bul</b><small>Uzun yayınsa en iyi anları bulayım.</small></button>
        <button id="dlB"><span class="e">✂️</span><b>İndir ve Düzenle</b><small>Kısa bir klipse direkt indirip editöre koyayım.</small></button>
      </div>`);
    $('#dlA', md.el).onclick = () => { md.close(); setTimeout(() => KS.findMoments({ url, title: title || 'Video' }), 280); };
    $('#dlB', md.el).onclick = async () => { md.close(); await new Promise(r => setTimeout(r, 260)); const r = await dl({ url, title: title || (type === 'clip' ? 'Kick klip' : 'Video') }); if (!r) return; r.jobs.forEach(KS.trackJob); KS.openJobs(); };
  };

  /* keşfet: isim yazmadan YouTube'da kategori araması */
  const EXPLORE = [
    ['😂 Komik anlar', 'komik anlar türkçe'], ['🎙 Talk show kesitleri', 'talk show komik kesitler türkçe'], ['📺 Okan Bayülgen', 'okan bayülgen komik kesit'],
    ['🤍 Beyaz Show', 'beyaz show komik anlar'], ['🎤 Stand-up', 'stand up türkçe komik'], ['🎧 Podcast kesitleri', 'podcast kesit türkçe'],
    ['🎮 Yayıncı komik anlar', 'yayıncı komik anlar türkçe'], ['🟢 Kick komik anlar', 'kick yayıncı komik anlar'], ['🟣 Twitch komik anlar', 'twitch türkiye komik anlar'],
    ['📖 Yayıncı anıları', 'yayıncı anısını anlatıyor'], ['👻 Korku hikayeleri', 'yaşanmış korku hikayesi anlatıyor'], ['🕹 Oyun komik anlar', 'oyun komik anlar türkçe'],
    ['🎤 Sokak röportajı', 'sokak röportajı komik'], ['📹 Kamera şakası', 'kamera şakası türkçe'], ['😳 Tepki videoları', 'tepki videosu türkçe komik'],
    ['⚽ Futbol komik anlar', 'futbol komik anlar türkçe'], ['🐶 Komik hayvanlar', 'komik hayvan videoları'], ['🎬 Efsane sahneler', 'türk dizi efsane sahneler'],
    ['🗣 Ünlü röportajları', 'ünlü röportaj komik anlar'], ['😡 Sinir krizi anlar', 'yayıncı sinirlendi anlar'], ['🔥 Viral videolar', 'türkiye viral video'],
  ];
  $('#exploreChips').innerHTML = '<span class="ex-l">Keşfet:</span>' + EXPLORE.map(([n, q], i) => `<button data-ex="${i}">${n}</button>`).join('');
  $$('#exploreChips [data-ex]').forEach(b => b.onclick = () => { const q = EXPLORE[+b.dataset.ex][1]; $$('#exploreChips button').forEach(x => x.classList.toggle('on', x === b)); input.value = q; input.dispatchEvent(new Event('input')); F.search(); });

  F.renderRecent = () => {
    const s = KS.state.settings.son_kanal;
    $('#recentChannel').innerHTML = s ? `Son: <button>${KS.esc(s)}</button>` : '';
    const b = $('#recentChannel button');
    if (b) b.onclick = () => { input.value = s; F.search(); };
  };

  /* ---------- yayın kayıtları ---------- */
  F.renderVideos = (list = F.videos, gid = 'videosGrid', cid = 'cntVideos', isShort = false) => {
    const g = $('#' + gid);
    $('#' + cid).textContent = list.length || '';
    if (!list.length) {
      if (isShort) { g.innerHTML = emptyHtml('Shorts yok', 'YouTube\'da bir şey ara ya da bir YouTube kanal linki yapıştır, kısa videolar burada çıkar.'); return; }
      g.innerHTML = emptyHtml('Ne arıyorsun?', 'Kick kanal adı yaz (<b>rraenee</b>), YouTube/Twitch linki yapıştır<br>ya da YouTube\'da ara (<b>okan bayülgen kesit</b>, <b>yayıncı anıları</b>).<br>Bilgisayarındaki videoyu da ekleyebilirsin.');
      return;
    }
    g.innerHTML = list.map((v, i) => `
      <div class="card" style="animation-delay:${Math.min(i, 12) * .04}s" data-i="${i}">
        <div class="thumb">${v.thumbnail ? `<img src="${KS.esc(v.thumbnail)}" loading="lazy" onerror="this.remove()">` : ''}
          <span class="badge br">${KS.fmt(v.duration)}</span>
          ${v.availability === 'subscriber_only' ? '<span class="badge tl lock">🔒 Abonelere özel</span>' : ''}</div>
        <div class="card-body">
          <div class="card-title">${KS.esc(v.title)}</div>
          <div class="card-meta">${v.channel ? `<span>${KS.esc(v.channel)}</span>` : ''}${v.timestamp ? `<span>${KS.ago(v.timestamp)}</span>` : ''}${v.views ? `<span>👁 ${KS.num(v.views)}</span>` : ''}</div>
          <div class="card-actions">${isShort ? `<button class="btn primary glow sm" style="flex:1" data-dl="${i}">${KS.icon.down}İndir ve Düzenle</button>` : `<button class="btn primary glow sm" style="flex:1" data-an="${i}">${KS.icon.spark}Anları Bul</button>`}
            ${!isShort && v.duration && v.duration < 600 ? `<button class="btn ghost sm" data-dl="${i}" title="Kısa video: direkt indir ve düzenle">${KS.icon.down}</button>` : ''}</div>
        </div>
      </div>`).join('');
    $$('[data-an]', g).forEach(b => b.onclick = e => {
      e.stopPropagation();
      const v = list[+b.dataset.an];
      KS.findMoments({ url: v.url, title: v.title });
    });
    $$('[data-dl]', g).forEach(b => b.onclick = async e => {
      e.stopPropagation();
      const v = list[+b.dataset.dl];
      const r = await dl({ url: v.url, title: v.title }); if (!r) return;
      r.jobs.forEach(KS.trackJob); KS.openJobs();
      KS.toast('⬇ İndiriliyor, editörde hazır olacak.');
    });
  }
  F.shorts = [];
  F.renderShorts = () => F.renderVideos(F.shorts, 'shortsGrid', 'cntShorts', true);
;

  /* ---------- izleyici klipleri ---------- */
  F.clipSort = 'new';
  $$('#clipSort button').forEach(b => b.onclick = () => { F.clipSort = b.dataset.s; $$('#clipSort button').forEach(x => x.classList.toggle('active', x === b)); F.selClips.clear(); F.renderClips(); });
  F.renderClips = () => {
    const g = $('#clipsGrid');
    F.clips.sort(F.clipSort === 'pop' ? (a, b) => (b.views || 0) - (a.views || 0) : (a, b) => (b.timestamp || 0) - (a.timestamp || 0));
    $('#cntClips').textContent = F.clips.length || '';
    if (!F.clips.length) { g.innerHTML = emptyHtml('Klip yok', 'Bu kanalda izleyicilerin kestiği klip bulunamadı.', KS.icon.film); return; }
    g.innerHTML = F.clips.map((c, i) => `
      <div class="card ${F.selClips.has(i) ? 'sel' : ''}" style="animation-delay:${Math.min(i, 12) * .04}s" data-ci="${i}">
        <span class="check">${KS.icon.check}</span>
        <div class="thumb">${c.thumbnail ? `<img src="${KS.esc(c.thumbnail)}" loading="lazy" onerror="this.remove()">` : ''}
          <span class="badge br">${KS.fmt(c.duration)}</span><span class="badge tr">👁 ${KS.num(c.views)}</span></div>
        <div class="card-body"><div class="card-title">${KS.esc(c.title)}</div><div class="card-meta"><span>${KS.ago(c.timestamp)}</span></div></div>
      </div>`).join('');
    $$('[data-ci]', g).forEach(card => card.onclick = () => {
      const i = +card.dataset.ci;
      F.selClips.has(i) ? F.selClips.delete(i) : F.selClips.add(i);
      card.classList.toggle('sel');
      F.updateClipBar();
    });
    F.updateClipBar();
  };
  F.updateClipBar = () => {
    $('#clipsSelCount').textContent = F.selClips.size;
    $('#clipsBar').classList.toggle('show', F.selClips.size > 0 && $('#tab-clips').classList.contains('active'));
  };
  $('#clipsSelAll').onclick = () => {
    if (F.selClips.size === F.clips.length) F.selClips.clear(); else F.clips.forEach((_, i) => F.selClips.add(i));
    F.renderClips();
  };
  $('#clipsDownload').onclick = async () => {
    const items = [...F.selClips].map(i => ({ url: F.clips[i].url, title: F.clips[i].title }));
    const r = await dl({ items }); if (!r) return;
    r.jobs.forEach(KS.trackJob);
    F.selClips.clear(); F.renderClips(); KS.openJobs();
    KS.toast(`⬇ ${items.length} klip indiriliyor. Altyazıları da otomatik çıkacak.`);
  };

  /* ---------- bulunan anlar ---------- */
  F.renderAnalysisList = () => {
    const list = KS.state.analyses || [];
    $('#cntMoments').textContent = list.length || '';
    const el = $('#analysisList');
    el.innerHTML = list.map(a => `<button class="an-item ${F.analysis && F.analysis.id === a.id ? 'active' : ''}" data-aid="${a.id}">
      <div class="t">${KS.esc(a.title)}</div><div class="m">${a.count} an · ${KS.fmt(a.duration)} · ${KS.ago(a.created)}</div>
      <span class="x del-btn" data-adel="${a.id}" title="Sil">${KS.icon.x}</span></button>`).join('');
    $$('[data-aid]', el).forEach(b => b.onclick = e => { if (!e.target.closest('[data-adel]')) F.showAnalysis(b.dataset.aid); });
    $$('[data-adel]', el).forEach(b => b.onclick = async e => {
      e.stopPropagation();
      if (!await KS.confirm('Analizi sil?', 'Bulunan anlar ve önizleme dosyası silinecek. Hazırladığın projeler kalır.', 'Sil', true)) return;
      await KS.api('/api/analysis/' + b.dataset.adel, undefined, 'DELETE');
      if (F.analysis && F.analysis.id === b.dataset.adel) F.analysis = null;
      await KS.refresh();
    });
  };
  F.renderAnalyses = () => {
    const list = KS.state.analyses || [];
    F.renderAnalysisList();
    if (!list.length) {
      F.analysis = null;
      $('#analysisMain').innerHTML = emptyHtml('Henüz an aranmadı', 'Bir yayının "Anları Bul" butonuna bas ya da bilgisayarından uzun bir video ekle.', KS.icon.spark);
      return;
    }
    if (!F.analysis || !list.some(a => a.id === F.analysis.id)) F.showAnalysis(list[0].id);
  };

  F.showAnalysis = async aid => {
    F.tab('moments');
    const a = await KS.api('/api/analysis/' + aid);
    F.analysis = a; F.selMoments.clear(); F.playing = null;
    $$('.an-item').forEach(b => b.classList.toggle('active', b.dataset.aid === aid));
    const main = $('#analysisMain');
    main.innerHTML = `
      <div class="an-head">
        <div class="an-preview"><video id="anVideo" src="/media/analysis/${a.id}" preload="metadata" controls></video><span class="lbl" id="anLbl">Önizleme (düşük kalite)</span></div>
        <div class="an-side">
          <h3>${KS.esc(a.title)}</h3>
          <div class="hint">Grafikteki tepeler sesin patladığı yerler. Bir ana tıkla, önizlemede oynasın.</div>
          <div class="curve" id="curve"><canvas></canvas></div>
          <div class="an-actions">
            <button class="btn ghost sm" id="mSelAll">Tümünü seç</button>
            <button class="btn ghost sm" id="mSelTop">En iyi 5'i seç</button>
            <div class="spacer"></div>
            <button class="btn primary glow" id="mGo" disabled>${KS.icon.down}Seçilenleri Hazırla</button>
          </div>
        </div>
      </div>
      <svg width="0" height="0" style="position:absolute"><defs><linearGradient id="ringGrad"><stop offset="0" stop-color="#7c5cff"/><stop offset="1" stop-color="#ff3d8b"/></linearGradient></defs></svg>
      <div class="moments-grid" id="momentsGrid"></div>`;
    F.renderMoments();
    F.drawCurve();
    const v = $('#anVideo');
    v.ontimeupdate = () => {
      if (F.playing && v.currentTime >= F.playing.end) { v.pause(); }
      F.drawCurve();
    };
    $('#curve').onclick = e => {
      const r = e.currentTarget.getBoundingClientRect();
      const t = (e.clientX - r.left) / r.width * a.duration;
      // en yakın an
      let best = null, bd = 1e9;
      a.moments.forEach(m => { const d = Math.abs(m.peak - t); if (d < bd) { bd = d; best = m; } });
      if (best && bd < a.duration * 0.02) F.playMoment(best); else { v.currentTime = t; v.play(); F.playing = null; }
    };
    $('#mSelAll').onclick = () => { if (F.selMoments.size === a.moments.length) F.selMoments.clear(); else a.moments.forEach(m => F.selMoments.add(m.id)); F.renderMoments(); };
    $('#mSelTop').onclick = () => { F.selMoments.clear(); a.moments.slice().sort((x, y) => y.score - x.score).slice(0, 5).forEach(m => F.selMoments.add(m.id)); F.renderMoments(); };
    $('#mGo').onclick = async () => {
      const ms = a.moments.filter(m => F.selMoments.has(m.id));
      const project = await F.target(); if (project === undefined) return;
      const r = await KS.api('/api/moments', { analysis: a.id, moments: ms, project });
      r.jobs.forEach(KS.trackJob); KS.openJobs();
      KS.toast(`✂ ${ms.length} an yüksek kalitede indiriliyor. Altyazılar da otomatik çıkacak.`);
      F.selMoments.clear(); F.renderMoments();
    };
    window.addEventListener('resize', F.drawCurve);
  };

  F.renderMoments = () => {
    const a = F.analysis; if (!a) return;
    const g = $('#momentsGrid');
    if (!a.moments.length) { g.innerHTML = emptyHtml('An bulunamadı', 'Bu videoda belirgin bir ses patlaması yok gibi.'); return; }
    g.innerHTML = a.moments.map((m, i) => `
      <div class="mcard ${F.selMoments.has(m.id) ? 'sel' : ''} ${F.playing && F.playing.id === m.id ? 'playing' : ''}" data-mid="${m.id}" style="animation-delay:${Math.min(i, 15) * .035}s">
        <div class="ring"><svg viewBox="0 0 58 58"><circle class="bgc" cx="29" cy="29" r="25"/><circle class="fg" cx="29" cy="29" r="25" data-score="${m.score}"/></svg><b>${m.score}</b></div>
        <div class="mc-info"><div class="lab">${KS.esc(m.label)}</div>
          <div class="tm">${KS.fmt(m.start)} → ${KS.fmt(m.end)} · ${Math.round(m.end - m.start)} sn</div>
          <div class="mc-adj">
            <button data-adj="s-5" title="5 sn daha erken başla">◀ -5</button><button data-adj="s+5" title="5 sn daha geç başla">+5 ▶</button>
            <span style="width:6px"></span>
            <button data-adj="e-5" title="5 sn erken bitir">◀ -5</button><button data-adj="e+5" title="5 sn uzat">+5 ▶</button>
          </div></div>
        <span class="rank">#${i + 1}</span><span class="tick">${KS.icon.check}</span>
      </div>`).join('');
    requestAnimationFrame(() => $$('.ring .fg', g).forEach(c => c.style.strokeDashoffset = 157 - 157 * (+c.dataset.score / 100)));
    $$('.mcard', g).forEach(card => {
      const m = a.moments.find(x => x.id === card.dataset.mid);
      card.onclick = e => {
        if (e.target.closest('[data-adj]')) return;
        if (e.target.closest('.tick')) { F.toggleMoment(m.id); return; }
        F.playMoment(m);
      };
      $('.tick', card).onclick = e => { e.stopPropagation(); F.toggleMoment(m.id); };
      $$('[data-adj]', card).forEach(b => b.onclick = e => {
        e.stopPropagation();
        const [k, d] = [b.dataset.adj[0], +b.dataset.adj.slice(1)];
        if (k === 's') m.start = KS.clamp(m.start + d, 0, m.end - 3); else m.end = KS.clamp(m.end + d, m.start + 3, a.duration);
        $('.tm', card).textContent = `${KS.fmt(m.start)} → ${KS.fmt(m.end)} · ${Math.round(m.end - m.start)} sn`;
        F.drawCurve();
      });
    });
    $('#mGo').disabled = !F.selMoments.size;
    $('#mGo').innerHTML = `${KS.icon.down}${F.selMoments.size ? F.selMoments.size + ' anı hazırla' : 'Seçilenleri Hazırla'}`;
  };
  F.toggleMoment = id => { F.selMoments.has(id) ? F.selMoments.delete(id) : F.selMoments.add(id); F.renderMoments(); };
  F.playMoment = m => {
    const v = $('#anVideo'); if (!v) return;
    F.playing = m;
    v.currentTime = m.start; v.play();
    $('#anLbl').textContent = `${m.label} · ${KS.fmt(m.start)}`;
    $$('.mcard').forEach(c => c.classList.toggle('playing', c.dataset.mid === m.id));
  };

  F.drawCurve = () => {
    const a = F.analysis, wrap = $('#curve'); if (!a || !wrap) return;
    const c = $('canvas', wrap), dpr = devicePixelRatio || 1;
    const W = wrap.clientWidth, H = wrap.clientHeight;
    c.width = W * dpr; c.height = H * dpr;
    const x = c.getContext('2d'); x.scale(dpr, dpr);
    const pts = a.curve || [];
    const grd = x.createLinearGradient(0, 0, W, 0);
    grd.addColorStop(0, '#7c5cff'); grd.addColorStop(1, '#ff3d8b');
    // seçili an bölgeleri
    a.moments.forEach(m => {
      const x0 = m.start / a.duration * W, x1 = m.end / a.duration * W;
      x.fillStyle = F.selMoments.has(m.id) ? 'rgba(255,61,139,.22)' : (F.playing && F.playing.id === m.id ? 'rgba(34,211,238,.2)' : 'rgba(255,255,255,.05)');
      x.fillRect(x0, 0, Math.max(2, x1 - x0), H);
    });
    x.beginPath(); x.moveTo(0, H);
    pts.forEach((v, i) => x.lineTo(i / (pts.length - 1) * W, H - 6 - v * (H - 18)));
    x.lineTo(W, H); x.closePath();
    const fill = x.createLinearGradient(0, 0, 0, H); fill.addColorStop(0, 'rgba(195,75,255,.55)'); fill.addColorStop(1, 'rgba(124,92,255,.03)');
    x.fillStyle = fill; x.fill();
    x.beginPath(); pts.forEach((v, i) => { const px = i / (pts.length - 1) * W, py = H - 6 - v * (H - 18); i ? x.lineTo(px, py) : x.moveTo(px, py); });
    x.strokeStyle = grd; x.lineWidth = 1.6; x.stroke();
    // an noktaları
    a.moments.forEach((m, i) => {
      const px = m.peak / a.duration * W;
      x.fillStyle = '#fff'; x.beginPath(); x.arc(px, 9, 3.5, 0, 7); x.fill();
      x.font = '700 10px Segoe UI'; x.fillStyle = 'rgba(255,255,255,.7)'; x.fillText('#' + (i + 1), px + 5, 13);
    });
    const v = $('#anVideo');
    if (v && v.currentTime) { const px = v.currentTime / a.duration * W; x.fillStyle = '#22d3ee'; x.fillRect(px - 1, 0, 2, H); }
  };

  /* ---------- projeler ---------- */
  F.renderProjects = () => {
    const list = KS.state.projects || [];
    $('#cntProjects').textContent = list.length || '';
    const g = $('#projectsGrid');
    if (!list.length) { g.innerHTML = emptyHtml('Proje yok', 'Hazırladığın klipler burada durur.', KS.icon.film); return; }
    const badge = p => p.subs_status === 'hazir' ? '<span class="badge tl ok">💬 Altyazı hazır</span>' :
      p.subs_status === 'calisiyor' ? '<span class="badge tl run">💬 Altyazı çıkıyor...</span>' :
        p.subs_status === 'hata' ? '<span class="badge tl err">Altyazı hatası</span>' : '';
    g.innerHTML = list.map((p, i) => `
      <div class="card" data-pid="${p.id}" style="animation-delay:${Math.min(i, 12) * .04}s">
        <span class="del"><button class="del-btn" data-pdel="${p.id}" title="Sil">${KS.icon.trash}</button></span>
        <div class="thumb"><img src="/thumb/${p.id}" loading="lazy" onerror="this.remove()">${badge(p)}<span class="badge br">${KS.fmt(p.duration)}</span>
          ${(p.exports || []).length ? `<span class="badge tr" style="right:46px">🎬 ${(p.exports || []).length}</span>` : ''}</div>
        <div class="card-body"><div class="card-title">${KS.esc(p.title)}</div><div class="card-meta"><span>${KS.ago(p.updated || p.created)}</span><span>${{ dikey: 'Dikey', yatay: 'Yatay', kare: 'Kare' }[p.format] || 'Dikey'} · ${p.clips ?? 1} klip</span></div></div>
      </div>`).join('');
    $$('[data-pid]', g).forEach(c => c.onclick = e => { if (!e.target.closest('[data-pdel]')) KS.openProject(c.dataset.pid); });
    $$('[data-pdel]', g).forEach(b => b.onclick = async e => {
      e.stopPropagation();
      if (!await KS.confirm('Projeyi sil?', 'Düzenlemeler silinecek. Dışa aktardığın videolar silinmez.', 'Sil', true)) return;
      await KS.api('/api/project/' + b.dataset.pdel + '?dosya=1', undefined, 'DELETE');
      if (KS.editor.project && KS.editor.project.id === b.dataset.pdel) KS.editor.close();
      await KS.refresh();
    });
  };

  // açılışta yazı yazmadan son kanalın en yeni videoları ve klipleri otomatik gelsin
  KS.hooks.state.push(() => {
    if (F._auto || !KS.state.settings) return; F._auto = true;
    if (!input.value.trim()) { input.value = KS.state.settings.son_kanal || 'rraenee'; input.dispatchEvent(new Event('input')); F.search(); }
  });
  KS.hooks.state.push(() => {
    $('#cntProjects').textContent = (KS.state.projects || []).length || '';
    $('#cntMoments').textContent = (KS.state.analyses || []).length || '';
    if ($('#tab-projects').classList.contains('active')) F.renderProjects();
    if ($('#tab-moments').classList.contains('active')) F.renderAnalyses();
    if (!F.videos.length) F.renderVideos();
    F.renderRecent();
  });
  // proje listesi altyazı durumu canlı güncellensin
  KS.hooks.jobDone.push(j => { if (j.kind === 'altyazi' && $('#tab-projects').classList.contains('active')) setTimeout(F.renderProjects, 300); });
})();
