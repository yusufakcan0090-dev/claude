/* Kesit Stüdyosu — ortak: api, sayfalar, işler, bildirimler, pencereler, dosya ekleme */
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const KS = window.KS = {
  state: { settings: {}, projects: [], analyses: [], jobs: [], system: {} },
  page: 'finder',
  hooks: { jobDone: [], state: [] },
};

KS.api = async (path, body, method) => {
  const opt = { method: method || (body !== undefined ? 'POST' : 'GET'), headers: {} };
  if (body instanceof FormData) opt.body = body;
  else if (body !== undefined) { opt.headers['Content-Type'] = 'application/json'; opt.body = JSON.stringify(body); }
  const r = await fetch(path, opt);
  let data = null;
  try { data = await r.json(); } catch (e) { data = null; }
  if (!r.ok || (data && data.error)) throw new Error((data && data.error) || ('Sunucu hatası ' + r.status));
  return data;
};

/* ---------- yardımcılar ---------- */
KS.esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
KS.fmt = (sec, ms) => {
  sec = Math.max(0, sec || 0);
  const h = Math.floor(sec / 3600), m = Math.floor(sec % 3600 / 60), s = Math.floor(sec % 60);
  const base = (h ? h + ':' + String(m).padStart(2, '0') : String(m).padStart(2, '0')) + ':' + String(s).padStart(2, '0');
  return ms ? base + '.' + String(Math.floor((sec % 1) * 10)) : base;
};
KS.ago = ts => {
  if (!ts) return '';
  const d = (Date.now() / 1000 - ts);
  if (d < 3600) return Math.max(1, Math.round(d / 60)) + ' dk önce';
  if (d < 86400) return Math.round(d / 3600) + ' saat önce';
  if (d < 86400 * 30) return Math.round(d / 86400) + ' gün önce';
  return new Date(ts * 1000).toLocaleDateString('tr-TR');
};
KS.num = n => n >= 1e6 ? (n / 1e6).toFixed(1) + 'M' : n >= 1e3 ? (n / 1e3).toFixed(1) + 'B' : String(n || 0);
KS.trUpper = s => String(s).replace(/i/g, 'İ').replace(/ı/g, 'I').toUpperCase();
KS.trLower = s => String(s).replace(/I/g, 'ı').replace(/İ/g, 'i').toLowerCase();
KS.clamp = (v, a, b) => Math.max(a, Math.min(b, v));
KS.uid = () => Math.random().toString(36).slice(2, 9);
KS.icon = {
  check: '<svg viewBox="0 0 24 24"><path d="M5 12l5 5L20 7"/></svg>',
  x: '<svg viewBox="0 0 24 24"><path d="M18 6 6 18M6 6l12 12"/></svg>',
  trash: '<svg viewBox="0 0 24 24"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/></svg>',
  spark: '<svg viewBox="0 0 24 24"><path d="m12 3 1.9 5.8L20 11l-6.1 2.2L12 19l-1.9-5.8L4 11l6.1-2.2z"/></svg>',
  film: '<svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="16" rx="3"/><path d="M10 9l5 3-5 3z"/></svg>',
  folder: '<svg viewBox="0 0 24 24"><path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg>',
  play: '<svg viewBox="0 0 24 24"><path d="M7 4v16l13-8z"/></svg>',
  down: '<svg viewBox="0 0 24 24"><path d="M12 3v12M7 10l5 5 5-5M5 21h14"/></svg>',
  plus: '<svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>',
  search: '<svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
};

/* range kaydırıcılarının dolgu rengi */
KS.paintRange = el => {
  const p = ((el.value - el.min) / (el.max - el.min)) * 100;
  el.style.setProperty('--p', p + '%');
};
document.addEventListener('input', e => { if (e.target.type === 'range') KS.paintRange(e.target); });

/* ---------- sayfalar ---------- */
KS.go = page => {
  KS.page = page;
  document.body.classList.toggle('on-editor', page === 'editor');
  document.body.classList.toggle('on-kalite', page === 'kalite');
  if (page === 'kalite' && KS.kalite) KS.kalite.loadYarim();
  const TOOLS = ['vbg', 'kapak', 'kanal'];
  $$('.nav-btn').forEach(b => b.classList.toggle('active', b.dataset.page === page || (b.dataset.page === 'araclar' && TOOLS.includes(page))));
  (KS.hooks.page || []).forEach(f => { try { f(page); } catch (e) { console.error(e); } });
  $$('.page').forEach(p => p.classList.toggle('active', p.id === 'page-' + page));
  if (page === 'settings') KS.renderSettings();
  if (page === 'editor' && KS.editor) KS.editor.onShow();
  if (page === 'kalite' && KS.kalite) setTimeout(KS.kalite.layout, 30);
};
$$('.nav-btn[data-page]').forEach(b => b.onclick = () => KS.go(b.dataset.page));
document.addEventListener('click', e => { const g = e.target.closest('[data-goto]'); if (g) KS.go(g.dataset.goto); });

/* ---------- bildirimler ---------- */
KS.toast = (msg, type = '', actions = [], ms = 4500) => {
  const t = document.createElement('div');
  t.className = 'toast ' + type;
  t.innerHTML = `<div style="flex:1"><div class="tt">${msg}</div>${actions.length ? '<div class="ta"></div>' : ''}</div><button class="icon-btn" style="width:26px;height:26px">${KS.icon.x}</button>`;
  actions.forEach(a => {
    const b = document.createElement('button');
    b.className = 'btn sm ' + (a.primary ? 'primary' : 'ghost');
    b.textContent = a.label;
    b.onclick = () => { a.fn(); close(); };
    $('.ta', t).appendChild(b);
  });
  let closed = false;
  const close = () => { if (closed) return; closed = true; t.classList.add('out'); setTimeout(() => t.remove(), 300); };
  t.querySelector('.icon-btn').onclick = close;
  t.addEventListener('click', e => { if (!e.target.closest('.ta')) close(); });
  const box = $('#toasts');
  box.appendChild(t);
  [...box.children].filter(x => !x.classList.contains('out')).slice(0, -3).forEach(x => x.querySelector('.icon-btn').click());
  setTimeout(close, ms ? (actions.length ? ms * 2 : ms) : 15000);
  return close;
};

/* ---------- pencereler ---------- */
KS.modal = (html, { onClose, wide } = {}) => {
  const root = $('#modalRoot');
  root.innerHTML = '';
  const m = document.createElement('div');
  m.className = 'modal';
  if (wide) m.style.width = 'min(720px,94vw)';
  m.innerHTML = html;
  root.appendChild(m);
  root.classList.add('show');
  const close = () => {
    m.classList.add('out');
    root.classList.remove('show');
    setTimeout(() => { if (root.contains(m)) m.remove(); }, 260);
    document.removeEventListener('keydown', esc, true);
    onClose && onClose();
  };
  const esc = e => { if (e.key === 'Escape') { e.stopPropagation(); close(); } };
  document.addEventListener('keydown', esc, true);
  root.onclick = e => { if (e.target === root) close(); };
  $$('[data-close]', m).forEach(b => b.onclick = close);
  return { el: m, close };
};
KS.confirm = (title, text, okLabel = 'Evet', danger = false) => new Promise(res => {
  let done = false;
  const md = KS.modal(`<h2>${title}</h2><p class="msub">${text}</p>
    <div class="mfoot"><button class="btn ghost" data-close>Vazgeç</button><button class="btn ${danger ? 'danger' : 'primary'}" id="cfOk">${okLabel}</button></div>`,
    { onClose: () => { if (!done) res(false); } });
  $('#cfOk', md.el).onclick = () => { done = true; res(true); md.close(); };
});
KS.modalOpen = () => $('#modalRoot').classList.contains('show');

/* ---------- durum ---------- */
KS.refresh = async () => {
  const s = await KS.api('/api/state');
  Object.assign(KS.state, s);
  KS.applyTheme();
  KS.hooks.state.forEach(f => f());
  if (!KS._tourChecked) { KS._tourChecked = true; if (!KS.state.settings.tur_goruldu) setTimeout(() => KS.tour(), 900); }
  KS.renderJobs();
};

/* ---------- görünüm (tema) ---------- */
KS.applyTheme = () => { document.documentElement.dataset.tema = (KS.state.settings || {}).tema || 'koyu'; };

/* ---------- nasıl kullanılır (4 adım) ---------- */
KS.tour = () => {
  const steps = [
    ['🔎', 'Videoyu bul', 'Klip Bulucu\'da Kick kanal adı yaz (<b>rraenee</b>), bir link yapıştır ya da <b>Keşfet</b>\'ten bir kategoriye tıkla. Bilgisayarındaki videoyu pencereye sürükleyip bırakabilirsin.'],
    ['✨', 'Anları bul ya da indir', 'Uzun yayında <b>Anları Bul</b>\'a bas, en iyi kısımları kendisi seçer. Kısa video ve klipleri <b>⬇</b> ile indir; hepsi editöre gelir.'],
    ['💬', 'Altyazı ve düzenleme', 'Editörde sağ üstteki <b>Altyazı Oluştur</b>\'a bas. Sağdaki <b>Altyazı Stili</b>\'nden renk, yazı tipi ve konum seç. Efektler için <b>Efektler ve Ön Ayarlar</b>\'da bir efekte çift tıkla.'],
    ['🎬', 'Dışa aktar', 'Sağ üstteki <b>Dışa Aktar</b>\'a (Ctrl+M) bas, kaliteyi seç. Video MP4 olarak <b>Videolar</b> klasörüne kaydedilir.'],
  ];
  let i = 0;
  const md = KS.modal('<div id="tourBox"></div>');
  const draw = () => {
    const [ic, t, d] = steps[i];
    $('#tourBox', md.el).innerHTML = `<div class="tour"><div class="tour-ic">${ic}</div><div class="tour-n">Adım ${i + 1} / ${steps.length}</div><h2>${t}</h2><p>${d}</p>
      <div class="tour-dots">${steps.map((_, k) => `<i class="${k === i ? 'on' : ''}"></i>`).join('')}</div>
      <div class="mfoot"><button class="btn ghost" id="tSkip">${i ? 'Geri' : 'Atla'}</button><button class="btn primary" id="tNext">${i === steps.length - 1 ? 'Başla' : 'İleri'}</button></div></div>`;
    $('#tSkip', md.el).onclick = () => { if (i) { i--; draw(); } else done(); };
    $('#tNext', md.el).onclick = () => { if (i < steps.length - 1) { i++; draw(); } else done(); };
  };
  const done = () => { md.close(); KS.api('/api/settings', { tur_goruldu: true }).then(r => KS.state.settings = r).catch(() => { }); };
  draw();
};

/* ---------- işler ---------- */
let jobsOpen = false, lastJobStatus = {}, pollTimer = null;
KS._doneAt = {};
const jobIcon = { indir: '⬇', analiz: '✨', an: '✂', altyazi: '💬', aktar: '🎬', guncelle: '🔄', kalite: '💎', otoedit: '🤖', gorsel: '🖼' };
KS.renderJobs = () => {
  const now = Date.now() / 1000;
  // bitenler 5 sn sonra listeden düşer; hiç iş yoksa kutu tamamen gizlenir
  (KS.state.jobs || []).forEach(j => { if ((j.status === 'bitti' || j.status === 'hata') && !KS._doneAt[j.id]) KS._doneAt[j.id] = now; });
  const jobs = (KS.state.jobs || []).filter(j => j.status === 'calisiyor' || j.status === 'bekliyor' || now - (KS._doneAt[j.id] || now) < 5);
  const dock = $('#jobsDock');
  const running = jobs.filter(j => j.status === 'calisiyor' || j.status === 'bekliyor');
  dock.classList.toggle('has', running.length > 0);
  dock.classList.toggle('only-kq', running.length > 0 && running.every(j => j.kind === 'kalite'));
  dock.classList.toggle('open', jobsOpen && running.length > 0);
  $('#jobsPillText').textContent = running.length ? `${running.length} işlem sürüyor · %${Math.round(running.reduce((s, j) => s + j.progress, 0) / running.length * 100)}` : '';
  const list = $('#jobsList');
  const html = jobs.slice().reverse().map(j => `
    <div class="job ${j.status}" data-id="${j.id}">
      <div class="row"><span class="job-ico">${jobIcon[j.kind] || '•'}</span><span class="jt">${KS.esc(j.title)}</span>
      ${j.status === 'calisiyor' || j.status === 'bekliyor' ? `<button class="jx" title="İptal" data-cancel="${j.id}">${KS.icon.x}</button>` : j.status === 'bitti' ? '<span style="color:var(--green)">✓</span>' : '<span style="color:var(--red)">!</span>'}</div>
      <div class="progress"><i style="width:${Math.round((j.status === 'hata' ? 1 : j.progress) * 100)}%;${j.status === 'hata' ? 'background:var(--red);animation:none' : ''}"></i></div>
      <div class="jm">${KS.esc(j.message)}</div>
    </div>`).join('');
  if (list.dataset.html !== html) { list.innerHTML = html; list.dataset.html = html; }
};
document.addEventListener('mousedown', e => { if (jobsOpen && !e.target.closest('#jobsDock')) { jobsOpen = false; KS.renderJobs(); } });
$('#jobsPill').onclick = () => { jobsOpen = !jobsOpen; KS.renderJobs(); };
$('#jobsList').onclick = e => {
  const c = e.target.closest('[data-cancel]');
  if (c) KS.api(`/api/jobs/${c.dataset.cancel}/cancel`, {}).then(() => KS.toast('İptal ediliyor...'));
};
KS.openJobs = () => { jobsOpen = true; KS.renderJobs(); };

async function pollJobs() {
  try {
    const jobs = await KS.api('/api/jobs');
    KS.state.jobs = jobs;
    let needRefresh = false;
    for (const j of jobs) {
      const prev = lastJobStatus[j.id];
      if (prev && prev !== j.status && (j.status === 'bitti' || j.status === 'hata')) {
        needRefresh = true;
        KS.onJobFinished(j);
      }
      lastJobStatus[j.id] = j.status;
    }
    KS.renderJobs();
    KS.hooks.jobTick && KS.hooks.jobTick.forEach(f => f(jobs));
    if (needRefresh) await KS.refresh();
  } catch (e) { /* sunucu meşgul */ }
  const active = (KS.state.jobs || []).some(j => j.status === 'calisiyor' || j.status === 'bekliyor');
  pollTimer = setTimeout(pollJobs, active ? 600 : 2000);
}
KS.hooks.jobTick = [];
KS.kickJobs = () => { clearTimeout(pollTimer); pollJobs(); };
KS.trackJob = id => { lastJobStatus[id] = 'bekliyor'; KS.kickJobs(); };

KS.onJobFinished = j => {
  KS.hooks.jobDone.forEach(f => f(j));
  if (j.status === 'hata') {
    KS.toast('<b>Olmadı:</b> ' + KS.esc(j.title) + '<br><span style="color:var(--muted);font-size:12px">' + KS.esc(j.message) + '</span>', 'err', [], 9000);
    return;
  }
  const r = j.result || {};
  if (j.kind === 'aktar') {
    KS.toast('🎬 <b>Video hazır!</b><br><span style="color:var(--muted);font-size:12px">' + KS.esc(r.name || '') + '</span>', 'ok', [
      { label: '▶ Oynat', primary: true, fn: () => KS.api('/api/play', { path: r.path }) },
      { label: 'Klasörde göster', fn: () => KS.api('/api/reveal', { path: r.path }) },
    ], 8000);
  } else if (j.kind === 'analiz') {
    KS.toast(`✨ <b>${r.count} an bulundu</b>`, 'ok', [{ label: 'Göster', primary: true, fn: () => { KS.go('finder'); KS.finder.showAnalysis(r.analysis); } }]);
  } else if (j.kind === 'indir' && r.project && r.open) {
    KS.openProject(r.project); KS.toast('MP4 hazır, editörde açıldı.', 'ok');
  } else if ((j.kind === 'an' || j.kind === 'indir') && r.project) {
    KS.toast('✂ <b>Klip hazır</b> — ' + KS.esc(j.title.replace(/^.*?: /, '')), 'ok', [{ label: 'Editörde aç', primary: true, fn: () => KS.openProject(r.project) }]);
  } else if (j.kind === 'altyazi') {
    KS.toast('💬 ' + KS.esc(j.message), 'ok');
  }
};

KS.openProject = async pid => {
  KS.editor._pending = pid;
  KS.go('editor');
  try { await KS.editor.load(pid); } finally { KS.editor._pending = null; }
};

/* ---------- an bulma seçenekleri (her kaynak için aynı pencere) ---------- */
KS.findMoments = src => {
  const s = KS.state.settings;
  const o = { mode: s.an_modu || 'orta', count: s.an_sayisi ?? 20 };
  const md = KS.modal(`<h2>✨ Anları Bul</h2><p class="msub">${KS.esc(src.title || '')}</p>
    <div class="opt-group"><label>An uzunluğu</label><div class="opts" id="fmMode">
      <button class="opt" data-v="kisa"><b>Kısa</b><small>8–20 sn · Shorts/TikTok</small></button>
      <button class="opt" data-v="orta"><b>Orta</b><small>20–40 sn</small></button>
      <button class="opt" data-v="uzun"><b>Uzun</b><small>40–90 sn · hikâye/anı</small></button></div></div>
    <div class="opt-group"><label>Kaç an bulunsun</label><div class="opts" id="fmCount">
      <button class="opt" data-v="10"><b>10</b><small>en iyileri</small></button>
      <button class="opt" data-v="25"><b>25</b><small></small></button>
      <button class="opt" data-v="50"><b>50</b><small></small></button>
      <button class="opt" data-v="0"><b>Hepsi</b><small>sınırsız</small></button></div></div>
    <div class="mfoot"><button class="btn ghost" data-close>Vazgeç</button><button class="btn primary glow" id="fmGo">${KS.icon.spark}Bul</button></div>`);
  const paint = () => {
    $$('#fmMode .opt', md.el).forEach(b => b.classList.toggle('active', b.dataset.v === o.mode));
    $$('#fmCount .opt', md.el).forEach(b => b.classList.toggle('active', +b.dataset.v === +o.count));
  };
  $$('#fmMode .opt', md.el).forEach(b => b.onclick = () => { o.mode = b.dataset.v; paint(); });
  $$('#fmCount .opt', md.el).forEach(b => b.onclick = () => { o.count = +b.dataset.v; paint(); });
  if (![10, 25, 50, 0].includes(+o.count)) o.count = 25;
  paint();
  $('#fmGo', md.el).onclick = async () => {
    md.close();
    try {
      const r = await KS.api('/api/analyze', { ...src, mode: o.mode, count: o.count });
      Object.assign(KS.state.settings, { an_modu: o.mode, an_sayisi: o.count });
      KS.trackJob(r.job); KS.openJobs();
      KS.toast(src.local ? '✨ Anlar aranıyor...' : '✨ Video indiriliyor ve anlar aranıyor. Bitince haber vereceğim.');
    } catch (e) { KS.toast(KS.esc(e.message), 'err'); }
  };
};

/* ---------- sistem çipi ---------- */
KS.loadSystem = async () => {
  try {
    const s = await KS.api('/api/system');
    KS.state.system = s;
    const chip = $('#gpuChip');
    chip.className = 'gpu-chip ' + (s.gpu ? 'ok' : 'warn');
    $('span', chip).textContent = s.gpu ? 'NVIDIA hazır' : s.vendor === 'amd' ? 'AMD hazır' : s.vendor === 'intel' ? 'Intel' : 'GPU yok';
    chip.title = s.gpu ? 'Altyazı ekran kartında hızlı çalışacak' : 'Ekran kartı bulunamadı, altyazı işlemciyle (yavaş) çalışır';
    const base = $('span', chip).textContent;
    clearInterval(KS._chipT);
    KS._chipT = setInterval(async () => { if (document.hidden) return; try { const k = await KS.api('/api/koruma'); $('span', chip).textContent = k.gpu_temp != null ? `${base.replace(' hazır', '').replace('GPU yok', 'GPU')} ${Math.round(k.gpu_temp)}°C` : base; chip.classList.toggle('hot', k.gpu_temp != null && k.gpu_temp >= (k.gpu_limit || 80) - 5); } catch (e) { } }, 3000);
  } catch (e) { }
};

/* =================================================================
   DOSYA EKLEME — tek yer: buton, Ctrl+O, sürükle-bırak
   video -> yeni proje, müzik -> müzik katmanı, resim -> resim katmanı
   ================================================================= */
KS.addFile = async () => {
  try {
    const f = await KS.api('/api/pick_any', {});
    if (f && f.path) KS.handleFile(f);
  } catch (e) { KS.toast(KS.esc(e.message), 'err'); }
};

KS.handleFile = async f => {
  if (f.error) return KS.toast(KS.esc(f.error), 'err');
  if (KS.toolDrop && KS.toolDrop[KS.page]) return KS.toolDrop[KS.page](f);
  if (KS.page === 'kalite' && (f.kind === 'video' || f.kind === 'image') && KS.kalite) return KS.kalite.load(f.path);
  if (KS.page === 'donustur' && KS.donustur && ['video', 'audio', 'image'].includes(f.kind)) return KS.donustur.add([f.path]);
  const ed = KS.editor;
  if (f.kind === 'video') {
    // video direkt eklenir: açık proje varsa ona, yoksa yeni projeye
    const long = (f.duration || 0) > 180, asOv = KS._asOverlay; KS._asOverlay = false;
    const moments = long ? [{ label: '🤖 Otomatik Edit', primary: true, fn: () => KS.autoEdit({ local: true, path: f.path, title: f.title }) }, { label: 'Anları Bul', fn: () => KS.findMoments({ local: true, path: f.path, title: f.title }) }] : [];
    try {
      if (ed && ed.project) {
        KS.go('editor');
        await ed.addVideo(f, asOv);
        if (long) KS.toast(`Uzun bir video (${KS.fmt(f.duration)}). İstersen en iyi anlarını otomatik bulayım.`, '', moments, 8000);
      } else {
        const r = await KS.api('/api/local/project', { path: f.path, title: f.title, format: KS.state.settings.son_bicim });
        if (r.job) { KS.trackJob(r.job); KS.toast('MP4 olmayan video: önce MP4\'e çevriliyor, bitince editörde açılacak.'); return; }
        await KS.refresh(); KS.kickJobs(); await KS.openProject(r.project);
        if (long) KS.toast(`Uzun bir video (${KS.fmt(f.duration)}). İstersen en iyi anlarını otomatik bulayım.`, '', moments, 8000);
      }
    } catch (e) { KS.toast(KS.esc(e.message), 'err'); }
    return;
  }
  if (!ed || !ed.project) {
    KS.toast({ audio: '🎵 Müzik', image: '🖼 Resim', lut: '🎞 LUT' }[f.kind] + ' eklemek için önce editörde bir proje aç.', 'err');
    return;
  }
  if (f.kind === 'lut') return ed.addLut(f);
  if (f.kind === 'audio') ed.addMusic(f);
  else if (f.kind === 'image') ed.addImage(f);
};

/* sürükle-bırak */
let dropPathTimer = null, dropGotPath = false;
const dropOverlay = document.createElement('div');
dropOverlay.className = 'drop-overlay';
dropOverlay.innerHTML = `<div class="drop-box"><div class="drop-ico">${KS.icon.plus}</div><b>Bırak, ekleyeyim</b><span>Video → projeye eklenir · Müzik → müzik katmanı · Resim → resim katmanı · .cube → LUT</span></div>`;
document.body.appendChild(dropOverlay);
let dragDepth = 0, dragHideT = null;
const hideDrop = () => { dragDepth = 0; clearTimeout(dragHideT); dropOverlay.classList.remove('show'); };
const armHide = () => { clearTimeout(dragHideT); dragHideT = setTimeout(hideDrop, 700); };
window.addEventListener('dragenter', e => { if ([...(e.dataTransfer?.types || [])].includes('Files')) { dragDepth++; dropOverlay.classList.add('show'); armHide(); } });
window.addEventListener('dragleave', e => { dragDepth = Math.max(0, dragDepth - 1); if (!dragDepth || !e.relatedTarget) hideDrop(); });
window.addEventListener('dragover', e => { e.preventDefault(); if (dropOverlay.classList.contains('show')) armHide(); });
window.addEventListener('drop', hideDrop, true);
window.addEventListener('dragend', hideDrop, true);
['mousemove', 'mousedown', 'keydown', 'blur', 'focus'].forEach(ev => window.addEventListener(ev, () => { if (dropOverlay.classList.contains('show')) hideDrop(); }, true));
dropOverlay.addEventListener('click', hideDrop);
KS.hideDrop = hideDrop;
window.addEventListener('drop', e => {
  e.preventDefault();
  dragDepth = 0; dropOverlay.classList.remove('show');
  const files = [...(e.dataTransfer?.files || [])];
  if (!files.length) return;
  // pywebview gerçek dosya yolunu Python'dan gönderir (KS.onDropPath). Gelmezse yükleyerek ekle.
  dropGotPath = false;
  clearTimeout(dropPathTimer);
  dropPathTimer = setTimeout(async () => {
    if (dropGotPath) return;
    for (const file of files) {
      const close = KS.toast(`⬆ ${KS.esc(file.name)} ekleniyor...`, '', [], 0);
      try {
        const fd = new FormData(); fd.append('file', file);
        const f = await KS.api('/api/upload', fd);
        close(); KS.handleFile(f);
      } catch (err) { close(); KS.toast(KS.esc(err.message), 'err'); }
    }
  }, 450);
});
KS.onDropPath = async paths => {
  hideDrop();
  dropGotPath = true;
  for (const p of [].concat(paths)) {
    try { KS.handleFile(await KS.api('/api/describe', { path: p })); }
    catch (e) { KS.toast(KS.esc(e.message), 'err'); }
  }
};

/* ---------- genel kısayollar ---------- */
// Türkçe klavyede I tuşu 'ı' verir; harf tuşlarını fiziksel tuştan oku
KS.keyOf = e => { if (/^Key[A-Z]$/.test(e.code || '')) return e.code.slice(3).toLowerCase(); const k = e.key || ''; return (k === 'ı' || k === 'İ') ? 'i' : k.toLowerCase(); };
document.addEventListener('keydown', e => {
  if (KS.modalOpen()) return;
  const typing = /INPUT|TEXTAREA|SELECT/.test(document.activeElement?.tagName) || document.activeElement?.isContentEditable;
  const k = KS.keyOf(e);
  if ((e.ctrlKey || e.metaKey) && (k === 'o' || (k === 'i' && KS.page !== 'editor'))) { e.preventDefault(); KS.addFile(); return; }
  if (typing) return;
  if (e.altKey && k === '1') { KS.go('finder'); e.preventDefault(); }
  if (e.altKey && k === '2') { KS.go('editor'); e.preventDefault(); }
  if (e.altKey && k === '3') { KS.go('settings'); e.preventDefault(); }
  if (KS.page === 'editor' && KS.editor) KS.editor.onKey(e);
});

/* =================================================================
   AYARLAR
   ================================================================= */
KS.renderSettings = () => {
  const s = KS.state.settings, sys = KS.state.system || {}, up = KS.state.update || {};
  const fixes = Object.entries(s.duzeltmeler || {});
  const row = (title, desc, ctrl) => `<div class="st-row"><div class="st-t"><b>${title}</b>${desc ? `<span>${desc}</span>` : ''}</div><div class="st-c">${ctrl}</div></div>`;
  $('#settingsGrid').innerHTML = `<div class="st-wrap">
    <div class="st-sec"><h3>Genel</h3>
      ${row('Kayıt klasörü', KS.esc(s.cikti_klasoru || ''), '<button class="btn ghost sm" id="setOutOpen">Aç</button><button class="btn ghost sm" id="setOutBtn">Değiştir</button>')}
      ${row('Görünüm', 'Programın renkleri', `<div class="seg" id="setTheme">${[['koyu', 'Koyu'], ['dahakoyu', 'Daha koyu'], ['acik', 'Açık']].map(([v, n]) => `<button data-v="${v}" class="${(s.tema || 'koyu') === v ? 'on' : ''}">${n}</button>`).join('')}</div>`)}
      ${row('Programı paylaş', 'Arkadaşına bu linki at: indirip çift tıklaması yeter', '<button class="btn ghost sm" id="setShareLink">Linki kopyala</button>')}
      ${row('Otomatik güncelleme', s.oto_guncelle !== false ? 'Açık · yeni sürüm gelince boşta olduğun bir anda kendisi kurar' : 'Kapalı · yeni sürüm gelince sadece haber verir', `<label class="ae-chk"><input type="checkbox" id="setAutoUpd" ${s.oto_guncelle !== false ? 'checked' : ''}> Açık</label>`)}
      ${row('Güncelleme', up.available ? `Yeni sürüm hazır: v${KS.esc(up.latest)}` : (up.current ? `v${KS.esc(up.current)} · güncel` : KS.esc(($('#verTag') || {}).textContent || 'Kontrol edilmedi')), `<button class="btn ${up.available ? 'primary' : 'ghost'} sm" id="setUpd">${up.available ? 'Güncelle' : 'Kontrol et'}</button>`)}
    </div>
    <div class="st-sec"><h3>Yapay Zekâ</h3>
      ${row('Gemini anahtarı', s.gemini_anahtar ? '✓ Bağlı · asistan, otomatik edit ve paylaşım metni açık' : 'Ücretsiz alınır: Google AI Studio → Create API key', `<input class="inp" id="setKey" type="password" value="${KS.esc(s.gemini_anahtar || '')}" placeholder="AIza..."><button class="btn primary sm" id="setKeySave">Kaydet</button>`)}
      ${row('Anahtar nasıl alınır?', 'Google hesabınla giriş yap, "Create API key"e bas, kopyala', '<button class="btn ghost sm" id="setKeyGet">AI Studio\'yu aç</button>' + (s.gemini_anahtar ? '<button class="btn ghost sm" id="setKeyDel">Kaldır</button>' : ''))}
    </div>
    <div class="st-sec"><h3>Altyazı</h3>
      ${row('Otomatik altyazı', 'Klip inince altyazıyı kendisi çıkarsın', `<button class="sw-tog ${s.oto_altyazi ? 'on' : ''}" id="setAuto"><i></i></button>`)}
      ${row('Hız / doğruluk', '', `<div class="seg" id="setModel"><button data-v="large-v3" class="${s.whisper_model !== 'turbo' ? 'on' : ''}">En doğru</button><button data-v="turbo" class="${s.whisper_model === 'turbo' ? 'on' : ''}">Daha hızlı</button></div>`)}
      ${row('İsimler', 'Videolarda geçen isimler doğru yazılsın', `<input class="inp" id="setNames" value="${KS.esc(s.ipucu_isimler || '')}" placeholder="RRaenee, Animeci">`)}
      <details class="st-more"><summary>Düzeltme sözlüğü <b>${fixes.length || ''}</b></summary>
        <div class="fix-list">${fixes.length ? fixes.map(([x, y]) => `<div class="fix"><span>${KS.esc(x)}</span><span>→</span><span>${KS.esc(y)}</span><button class="del-btn" data-fixdel="${KS.esc(x)}">${KS.icon.x}</button></div>`).join('') : '<p class="hint">Henüz yok. Editörde bir kelimeyi düzeltince eklemeyi önereceğim.</p>'}</div>
        <div class="fix-add"><input class="inp" id="fixA" placeholder="yanlış"><input class="inp" id="fixB" placeholder="doğru"><button class="btn primary sm" id="fixAdd">Ekle</button></div>
      </details>
    </div>
    <div class="st-sec"><h3>Donanım koruması</h3>
      ${row('Yük seviyesi', 'Ağır işlerde (kalite artırma, arka plan silme) ekran kartı ve işlemci ne kadar zorlansın', `<div class="seg" id="setKor">${[['sessiz', '🌙 Sessiz'], ['dengeli', '⚖️ Dengeli'], ['tam', '🚀 Tam güç']].map(([v, n]) => `<button data-v="${v}" class="${((s.koruma || {}).mod || 'dengeli') === v ? 'on' : ''}">${n}</button>`).join('')}</div>`)}
      ${row('Şu an', 'Canlı takip (2 saniyede bir)', '<span class="st-live" id="setKorLive">okunuyor...</span>')}
      ${row('Sıcaklık sınırı', 'Ekran kartı bu sıcaklığa gelince iş durur, soğuyunca devam eder', `<span class="st-kor"><input type="range" min="60" max="90" id="setKorLim" value="${(s.koruma || {}).gpu_limit || 80}"><b id="setKorV">${(s.koruma || {}).gpu_limit || 80}°C</b></span>`)}
    </div>
    <div class="st-sec"><h3>Yardım</h3>
      ${row('Nasıl kullanılır?', '4 adımda kısa anlatım', '<button class="btn ghost sm" id="setTour">Göster</button>')}
      ${row('Klavye kısayolları', 'After Effects ile aynı', '<button class="btn ghost sm" id="setKeys">Göster</button>')}
      <div class="st-sys"><span class="${sys.gpu || sys.vendor ? 'ok' : 'no'}" title="${KS.esc(sys.gpu_name || '')}">● Ekran kartı: ${sys.gpu ? 'NVIDIA (hızlı altyazı)' : sys.vendor === 'amd' ? 'AMD' : sys.vendor === 'intel' ? 'Intel' : 'yok'}</span><span class="${sys.ffmpeg ? 'ok' : 'no'}">● FFmpeg ${sys.ffmpeg ? 'hazır' : 'yok'}</span><span class="${sys.ytdlp ? 'ok' : 'no'}">● İndirici ${sys.ytdlp ? 'hazır' : 'yok'}</span></div>
    </div></div>`;
  const save = patch => KS.api('/api/settings', patch).then(r => { KS.state.settings = r; });
  $('#setOutBtn').onclick = async () => { const r = await KS.api('/api/pick_folder', {}); if (r.path) { await save({ cikti_klasoru: r.path }); KS.renderSettings(); } };
  $('#setOutOpen').onclick = () => KS.api('/api/reveal', { path: s.cikti_klasoru }).catch(() => KS.toast('Klasör henüz yok, ilk videoda oluşacak.'));
  $('#setShareLink').onclick = async () => { if (await KS.copy('https://github.com/yusufakcan0090-dev/claude/raw/kesit-studyosu/KesitStudyosu_Kurulum.exe')) KS.toast('Link kopyalandı. Arkadaşın indirip çift tıklasın.', 'ok'); };
  $('#setAutoUpd').onchange = e => save({ oto_guncelle: e.target.checked }).then(KS.renderSettings);
  $('#setUpd').onclick = () => up.available ? KS.updateDialog() : KS.checkUpdate(true, true).then(KS.renderSettings);
  $$('#setModel button').forEach(b => b.onclick = () => save({ whisper_model: b.dataset.v }).then(KS.renderSettings));
  $('#setNames').onchange = e => save({ ipucu_isimler: e.target.value });
  $('#setAuto').onclick = () => save({ oto_altyazi: !s.oto_altyazi }).then(KS.renderSettings);
  $$('#setTheme button').forEach(b => b.onclick = () => save({ tema: b.dataset.v }).then(() => { KS.applyTheme(); KS.renderSettings(); }));
  $$('#setKor button').forEach(b => b.onclick = () => save({ koruma: { ...(s.koruma || {}), mod: b.dataset.v, gpu_limit: { sessiz: 72, dengeli: 80, tam: 86 }[b.dataset.v] } }).then(KS.renderSettings));
  { const r = $('#setKorLim'); KS.paintRange(r); r.oninput = () => { $('#setKorV').textContent = r.value + '°C'; KS.paintRange(r); }; r.onchange = () => save({ koruma: { ...(s.koruma || {}), gpu_limit: +r.value } }); }
  clearInterval(KS._korT); const korLive = async () => { const el = $('#setKorLive'); if (!el || KS.page !== 'settings') return clearInterval(KS._korT); try { const k = await KS.api('/api/koruma'); el.innerHTML = [k.gpu_temp != null ? `<span class="kq-live"></span>Ekran kartı <b>${Math.round(k.gpu_temp)}°C</b>${k.gpu_util != null ? ' · %' + Math.round(k.gpu_util) : ''}` : 'Ekran kartı sıcaklığı okunamıyor', k.cpu_temp != null ? `İşlemci <b>${k.cpu_temp}°C</b>` : ''].filter(Boolean).join(' · '); } catch (e) { } };
  korLive(); KS._korT = setInterval(korLive, 2000);
  $('#setTour').onclick = () => KS.tour();
  $('#setKey').addEventListener('keydown', e => e.stopPropagation());
  $('#setKeySave').onclick = () => KS.ai.saveKey($('#setKey').value, $('#setKeySave'));
  $('#setKeyGet').onclick = () => KS.openUrl('https://aistudio.google.com/apikey');
  if ($('#setKeyDel')) $('#setKeyDel').onclick = () => save({ gemini_anahtar: '' }).then(KS.renderSettings);
  $('#setKeys').onclick = () => KS.modal(`<h2>Klavye Kısayolları</h2><p class="msub">After Effects ile aynı</p>${KS.shortcutsHtml()}<div class="mfoot"><button class="btn primary" data-close>Tamam</button></div>`, { wide: true });
  $('#fixAdd').onclick = async () => {
    const x = $('#fixA').value.trim(), y = $('#fixB').value.trim();
    if (!x || !y) return;
    const r = await KS.api('/api/fixes', { add: { [x]: y } });
    KS.state.settings.duzeltmeler = r.duzeltmeler; KS.renderSettings(); $('.st-more').open = true;
  };
  $$('[data-fixdel]').forEach(b => b.onclick = async () => {
    const r = await KS.api('/api/fixes', { remove: [b.dataset.fixdel] });
    KS.state.settings.duzeltmeler = r.duzeltmeler; KS.renderSettings(); $('.st-more').open = true;
  });
};

KS.shortcuts = [
  ['V', 'Seçim aracı'], ['H', 'El aracı (kaydır)'], ['Z', 'Yakınlaştırma aracı (Alt ile uzaklaş)'], ['W', 'Döndürme aracı'], ['Q', 'Dikdörtgen / Elips aracı'], ['Ctrl + T', 'Yazı aracı'],
  ['Boşluk', 'Oynat / durdur'], ['PageUp / PageDown', '1 kare geri / ileri'], ['Shift + PageUp / PageDown', '10 kare geri / ileri'], ['Home / End', 'Başa / sona git'],
  ['I / O', 'Katmanın başına / sonuna git'], ['J / K', 'Önceki / sonraki keyframe veya işaret'], ['B / N', 'Çalışma alanı başı / sonu'], ['Num *', 'İşaret (marker) ekle'],
  ['P S R T', 'Konum / Ölçek / Döndürme / Opaklık göster'], ['U', 'Animasyonlu özellikleri göster'], ['Alt + Shift + P/S/R/T', 'Keyframe ekle'],
  ['F9', 'Easy Ease'], ['Shift + F9', 'Easy Ease giriş'], ['Ctrl + Shift + F9', 'Easy Ease çıkış'], ['Ctrl + Alt + H', 'Hold keyframe'],
  ['Ctrl + Shift + D', 'Katmanı böl'], ['Ctrl + D', 'Çoğalt'], ['Delete', 'Sil'], ['[ / ]', 'Katmanın başını / sonunu buraya taşı'], ['Alt + [ / ]', 'Katmanı buradan kırp'],
  ['Ctrl + ] / [', 'Katmanı bir öne / geri'], ['Ctrl + Shift + ] / [', 'En öne / en geriye'],
  ['Ctrl + Alt + Shift + T', 'Yeni yazı katmanı'], ['Ctrl + Y', 'Yeni düz renk'], ['Ctrl + Alt + Y', 'Yeni ayar katmanı'],
  ['Ctrl + N', 'Yeni proje'], ['Ctrl + I', 'İçe aktar'], ['Ctrl + K', 'Kompozisyon ayarları'], ['Ctrl + M', 'Dışa aktar'], ['Ctrl + S', 'Kaydet'],
  ['Ctrl + Z / Ctrl + Shift + Z', 'Geri al / yinele'], ['= / −', 'Timeline yakınlaş / uzaklaş'], ['. / ,', 'Görüntüyü yakınlaş / uzaklaş'], ['Shift + /', 'Görüntüyü sığdır'],
  ['Tekerlek (görüntüde)', 'İmlecin olduğu yere zoom'], ['Orta tuş / Boşluk + sürükle', 'Görüntüyü kaydır'], ['Ctrl + Tekerlek', 'Seçili yazıyı büyüt / küçült'], ['`', 'Paneli büyüt'], ['F1', 'Kısayollar'],
];
KS.shortcutsHtml = () => `<div class="kbd-list">${KS.shortcuts.map(([k, d]) => `<span>${k.split(' ').map(x => /^[+/]$|^\/$/.test(x) ? x : `<kbd>${x}</kbd>`).join(' ')}</span><span style="color:var(--muted);font-size:13px">${d}</span>`).join('')}</div>`;

/* ---------- otomatik güncelleme ---------- */
KS.checkUpdate = async (force, manual) => {
  try {
    const u = await KS.api('/api/update/check' + (force ? '?force=1' : ''));
    KS.state.update = u;
    $('#verTag').textContent = 'v' + (u.current || '');
    $('#updBtn').hidden = !u.available;
    if (u.available && !manual && (KS.state.settings || {}).oto_guncelle !== false) {
      // otomatik kurulacak; bildirim yerine sessizce bekle
    } else if (u.available && !manual) {
      KS.toast(`✨ <b>Yeni sürüm var: v${KS.esc(u.latest)}</b>`, '', [{ label: 'Neler yeni?', primary: true, fn: KS.updateDialog }], 9000);
    } else if (manual) {
      if (u.available) KS.updateDialog();
      else if (u.error) KS.toast('Güncelleme kontrol edilemedi. İnternetini kontrol et.', 'err');
      else KS.toast('✓ En güncel sürümü kullanıyorsun (v' + KS.esc(u.current) + ')', 'ok');
    }
  } catch (e) { if (manual) KS.toast(KS.esc(e.message), 'err'); }
};
KS.updateDialog = () => {
  const u = KS.state.update || {};
  const md = KS.modal(`<h2>✨ Yeni sürüm: v${KS.esc(u.latest)}</h2><p class="msub">Şu an v${KS.esc(u.current)} kullanıyorsun. Projelerin ve ayarların korunur.</p>
    <div class="notes">${(u.notes || []).map(n => `<div>${KS.esc(n)}</div>`).join('')}</div>
    <div class="mfoot"><button class="btn ghost" data-close>Sonra</button><button class="btn primary glow" id="updGo">${KS.icon.down}Şimdi güncelle</button></div>`);
  $('#updGo', md.el).onclick = async () => {
    md.close();
    if (KS.editor && KS.editor.flush) await KS.editor.flush();
    const r = await KS.api('/api/update/apply', {});
    KS.trackJob(r.job); KS.openJobs();
    KS.toast('⬇ Güncelleme indiriliyor...');
  };
};
$('#updBtn').onclick = KS.updateDialog;
KS.hooks.jobDone.push(j => {
  if (j.kind !== 'guncelle' || j.status !== 'bitti') return;
  const ov = document.createElement('div');
  ov.className = 'restart-ov';
  ov.innerHTML = `<div><div class="spin" style="width:42px;height:42px;border-width:4px"></div><b>Güncellendi! Yeniden başlatılıyor...</b><span style="color:var(--muted)">Pencere birazdan kapanıp yeni sürümle açılacak.</span></div>`;
  document.body.appendChild(ov);
  setTimeout(() => KS.api('/api/restart', {}).catch(() => { }), 800);
});

/* ---------- tam otomatik güncelleme: boşta olunca kendisi kurar ---------- */
KS._lastInput = Date.now();
['keydown', 'mousedown', 'wheel'].forEach(ev => addEventListener(ev, () => { KS._lastInput = Date.now(); }, true));
KS._autoUpd = false;
KS.autoUpdateTick = async () => {
  const s = KS.state.settings || {};
  if (s.oto_guncelle === false || KS._autoUpd) return;
  const u = KS.state.update;
  if (!u || !u.available) return;
  const busy = (KS.state.jobs || []).some(j => j.status === 'calisiyor' || j.status === 'bekliyor');
  const typing = Date.now() - KS._lastInput < 45000;
  const modal = $('#modalRoot') && $('#modalRoot').classList.contains('show');
  const chatting = KS.ai && KS.ai.busy;
  if (busy || typing || modal || chatting) return;  // iş varken ya da kullanırken bölme
  KS._autoUpd = true;
  try {
    if (KS.editor && KS.editor.flush) await KS.editor.flush();
    KS.toast(`✨ Yeni sürüm v${KS.esc(u.latest)} kuruluyor... Program birazdan kendini yenileyecek.`, '', [], 8000);
    const r = await KS.api('/api/update/apply', {});
    KS.trackJob(r.job);
  } catch (e) { KS._autoUpd = false; }
};
setInterval(() => KS.checkUpdate(true, false), 15 * 60 * 1000);  // açıkken de 15 dakikada bir bak
setInterval(() => KS.autoUpdateTick(), 20 * 1000);

/* ---------- başlat ---------- */
window.addEventListener('load', async () => {
  try { await KS.refresh(); } catch (e) { KS.toast('Sunucuya bağlanılamadı: ' + KS.esc(e.message), 'err'); }
  KS.loadSystem();
  pollJobs();
  setTimeout(() => KS.checkUpdate(false, false), 2500);
  $$('input[type=range]').forEach(KS.paintRange);
});
