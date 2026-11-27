/* Video Arka Plan Sil */
(() => {
  const U = KS.ui, host = $('#tVbg');
  const V = { src: null, bg: null, job: null, result: null, t: 0, pv: null, pvBusy: false, showOrig: false };
  const o = { kind: 'insan', mode: 'renk', color: '#00ff00', feather: 1, shrink: 0, seffaf_bicim: 'webm' };
  let inited = false, pvN = 0, pvT = null;
  const fmtT = s => { s = Math.max(0, s || 0); return `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`; };
  const COLORS = [['#00ff00', 'Yeşil perde'], ['#0047ff', 'Mavi perde'], ['#000000', 'Siyah'], ['#ffffff', 'Beyaz'], ['#ff2d55', 'Kırmızı'], ['#7b5cff', 'Mor']];

  const render = () => {
    const j = U.findJob(V.job), run = U.running(j);
    const d = V.src ? V.src.duration || 0 : 0;
    host.innerHTML = `${U.head('Video Arka Plan Sil', 'Yeşil perde olmadan kişiyi videodan ayır; arkasına renk, bulanık, resim, video koy ya da şeffaf yap.',
      `<span class="kq-name">${V.src ? KS.esc(V.src.name) : ''}</span><button class="btn ghost" id="vbPick">Video seç</button>`)}
    <div class="tk">
      <div class="tk-main">
        <div class="tk-view vb-view" id="vbView">
          ${!V.src ? `<div class="tk-empty"><div class="big">🟩</div><b>Bir video sürükle ya da "Video seç"e bas</b><span>Kişi otomatik bulunur, saç telleri dahil temiz ayrılır.</span></div>`
            : `<img class="vb-img" id="vbImg" src="${V.showOrig ? '' : (V.pv || '')}" ${V.pv && !V.showOrig ? '' : 'hidden'}><video class="vb-img" id="vbOrig" src="${U.media(V.src.path)}" muted preload="auto" ${V.showOrig || !V.pv ? '' : 'hidden'}></video>
               <span class="kq-tag l">${V.showOrig ? 'ÖNCE' : 'SONRA'}</span>
               <div class="kq-load" id="vbLoad" ${V.pvBusy ? '' : 'hidden'}><div class="spin"></div><span>Önizleme hazırlanıyor...</span></div>`}
        </div>
        ${V.src ? `<div class="kq-bar"><span>${fmtT(V.t)}</span><input type="range" id="vbT" min="0" max="${d.toFixed(2)}" step="0.04" value="${V.t}"><span>${fmtT(d)}</span>
          <button class="btn ghost sm" id="vbCmp">${V.showOrig ? 'Sonrayı göster' : 'Öncesini göster'}</button></div>` : ''}
      </div>
      <div class="tk-side"><div class="tk-scroll">
        ${U.grp('Neyi ayırsın?', '🎯', `<div class="tk-cards">${[['insan', '🧍 Kişi', 'En iyi ve hızlı. Saç telleri dahil temiz.'], ['genel', '🐾 Her şey', 'Hayvan, nesne, ürün. Daha yavaş.']].map(([v, n, x]) => `<button data-kind="${v}" class="${o.kind === v ? 'on' : ''}"><b>${n}</b><small>${x}</small></button>`).join('')}</div>`)}
        ${U.grp('Arkaya ne gelsin?', '🎨', `<div class="tk-cards vb-modes">${[['renk', '🟩 Renk', 'Yeşil perde ya da düz renk'], ['bulanik', '🌫️ Bulanık', 'Arka plan bulanıklaşır'], ['resim', '🖼️ Resim', 'Kendi resmin'], ['video', '🎬 Video', 'Başka bir video'], ['seffaf', '◻️ Şeffaf', 'Montaj programında kullan']].map(([v, n, x]) => `<button data-mode="${v}" class="${o.mode === v ? 'on' : ''}"><b>${n}</b><small>${x}</small></button>`).join('')}</div>
          ${o.mode === 'renk' ? `<div class="vb-colors">${COLORS.map(([c, n]) => `<button data-col="${c}" title="${n}" class="${o.color.toLowerCase() === c ? 'on' : ''}" style="background:${c}"></button>`).join('')}<label class="vb-custom" title="Başka renk"><input type="color" id="vbColor" value="${o.color}">🎨</label></div>` : ''}
          ${o.mode === 'resim' || o.mode === 'video' ? (V.bg ? `<div class="tk-file">${o.mode === 'resim' ? '🖼️' : '🎬'}<span>${KS.esc(V.bg.name)}</span><button class="btn ghost sm" id="vbBg">Değiştir</button></div>` : `<button class="btn ghost" id="vbBg">+ ${o.mode === 'resim' ? 'Resim' : 'Video'} seç</button>`) : ''}
          ${o.mode === 'seffaf' ? `${U.h('Dosya türü')}${U.seg('seffaf_bicim', [['webm', 'WebM (küçük, web)'], ['mov', 'MOV ProRes (Premiere, AE, CapCut)']], o.seffaf_bicim)}` : ''}`)}
        ${U.grp('Kenarlar', '✂️', `${U.sl('feather', 'Kenar yumuşatma', 0, 6, o.feather, 0.5)}${U.sl('shrink', 'Kenarı içeri al (arka plan sızıyorsa artır)', -3, 3, o.shrink)}`, false)}
        ${V.result ? `<div class="tk-file">✅<span>${KS.esc(V.result.name)}</span><button class="btn ghost sm" id="vbShow">Klasörde göster</button><button class="btn ghost sm" id="vbEd">Editöre ekle</button></div>` : ''}
      </div>
      <div class="tk-foot">${j && j.status !== 'bitti' ? U.jobCard(j) : ''}${V.src && !run ? `<div class="kq-est">⏱ ${est()}</div>` : ''}
        <button class="btn primary glow kq-go" id="vbGo" ${!V.src || run ? 'disabled' : ''}>${run ? 'Siliniyor...' : '🟩 Arka planı sil'}</button></div></div>
    </div>`;
    bind();
  };
  const est = () => {
    const d = V.src.duration || 0, px = (V.src.width || 1280) * (V.src.height || 720) / 2073600;
    const per = o.kind === 'insan' ? 0.06 : 0.45;
    const m = Math.max(1, Math.round(d * 30 * per * Math.max(.5, px) / 60));
    return `Tahmini süre: ~${m} dk (ekran kartına göre değişir).`;
  };

  const bind = () => {
    U.bind(host, o, (k, full) => { if (full) { render(); pvSoon(); } });
    $('#vbPick', host).onclick = async () => { const f = await U.pick(['video']); if (f) load(f); };
    $$('[data-kind]', host).forEach(b => b.onclick = () => { o.kind = b.dataset.kind; render(); pvSoon(); });
    $$('[data-mode]', host).forEach(b => b.onclick = () => { o.mode = b.dataset.mode; if ((o.mode === 'resim' && V.bg && V.bg.kind !== 'image') || (o.mode === 'video' && V.bg && V.bg.kind !== 'video')) V.bg = null; render(); pvSoon(); });
    $$('[data-col]', host).forEach(b => b.onclick = () => { o.color = b.dataset.col; render(); pvSoon(); });
    const ci = $('#vbColor', host); if (ci) ci.onchange = () => { o.color = ci.value; render(); pvSoon(); };
    const bgb = $('#vbBg', host); if (bgb) bgb.onclick = async () => { const f = await U.pick([o.mode === 'resim' ? 'image' : 'video']); if (f) { V.bg = f; render(); pvSoon(); } };
    const tr = $('#vbT', host); if (tr) { KS.paintRange(tr); tr.oninput = () => { V.t = +tr.value; KS.paintRange(tr); tr.previousElementSibling.textContent = fmtT(V.t); const vv = $('#vbOrig', host); if (vv) vv.currentTime = V.t; }; tr.onchange = () => pvSoon(); }
    const cmp = $('#vbCmp', host); if (cmp) cmp.onclick = () => { V.showOrig = !V.showOrig; render(); const vv = $('#vbOrig', host); if (vv) vv.currentTime = V.t; };
    const vv = $('#vbOrig', host); if (vv) vv.onloadedmetadata = () => { vv.currentTime = V.t; };
    $('#vbGo', host).onclick = start;
    const sh = $('#vbShow', host); if (sh) sh.onclick = () => KS.api('/api/reveal', { path: V.result.path });
    const ed = $('#vbEd', host); if (ed) ed.onclick = async () => { const f = await KS.api('/api/describe', { path: V.result.path }); KS.go('editor'); KS.handleFile(f); };
  };

  const pvSoon = () => { clearTimeout(pvT); pvT = setTimeout(preview, 350); };
  const preview = async () => {
    if (!V.src) return;
    if ((o.mode === 'resim' || o.mode === 'video') && !V.bg) return;
    const n = ++pvN; V.pvBusy = true; const ld = $('#vbLoad', host); if (ld) ld.hidden = false;
    try {
      const r = await KS.api('/api/vbg/preview', { path: V.src.path, t: V.t, o: { ...o, bg: V.bg ? V.bg.path : '' } });
      if (n !== pvN) return;
      V.pv = r.url; V.showOrig = false;
    } catch (e) { if (n === pvN) KS.toast(KS.esc(e.message), 'err'); }
    if (n === pvN) { V.pvBusy = false; render(); }
  };
  const load = f => { V.src = f; V.t = Math.min(2, (f.duration || 0) / 3); V.pv = null; V.result = null; render(); KS.api('/api/kalite/info?path=' + encodeURIComponent(f.path)).then(i => { V.src.width = i.width; V.src.height = i.height; V.src.duration = i.duration || V.src.duration; render(); }).catch(() => { }); preview(); };
  const start = async () => {
    if ((o.mode === 'resim' || o.mode === 'video') && !V.bg) return KS.toast(o.mode === 'resim' ? 'Arka plan için bir resim seç' : 'Arka plan için bir video seç', 'err');
    try { const r = await KS.api('/api/vbg/start', { path: V.src.path, o: { ...o, bg: V.bg ? V.bg.path : '' } }); V.job = r.job; V.result = null; KS.trackJob(r.job); render(); }
    catch (e) { KS.toast(KS.esc(e.message), 'err'); }
  };
  KS.hooks.jobTick.push(() => { if (KS.page === 'vbg' && U.running(U.findJob(V.job))) { const f = $('.tk-foot', host), j = U.findJob(V.job); if (f) { const c = f.querySelector('.tk-job'); c ? c.outerHTML = U.jobCard(j) : f.insertAdjacentHTML('afterbegin', U.jobCard(j)); } } });
  KS.hooks.jobDone.push(j => {
    if (j.kind !== 'vbg' || j.id !== V.job) return;
    if (j.status === 'bitti') { V.result = j.result; KS.toast('🟩 Arka plan silindi: ' + KS.esc(j.result.name), 'ok', [{ label: 'Klasörde göster', primary: true, fn: () => KS.api('/api/reveal', { path: j.result.path }) }]); }
    if (KS.page === 'vbg') render();
  });
  KS.hooks.page.push(p => { if (p === 'vbg') { if (!inited) { Object.assign(o, KS.state.settings.vbg_ayar || {}); inited = true; } render(); } });
  KS.toolDrop.vbg = f => { if (f.kind === 'video') load(f); else if (f.kind === 'image') { o.mode = 'resim'; V.bg = f; render(); pvSoon(); } };
})();
