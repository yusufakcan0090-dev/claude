/* Kesit Stüdyosu — AE tarzı editör (v2: çok klip, katmanlar, keyframe) */
(() => {
  const E = KS.editor = { project: null, sel: null, selKey: null, history: [], future: [], T: 0, playing: false, tool: 'select', mag: 'fit', scale: 1, qual: 1, open: {}, reveal: {}, zoom: 1, pan: { x: 0, y: 0 } };
  const music = $('#musicAudio');
  const prev = $('#preview'), pctx = prev.getContext('2d', { willReadFrequently: true });
  const giz = $('#gizmo'), gctx = giz.getContext('2d');
  let PW = 540, PH = 960, BW = 1080, BH = 1920, K = .5;

  const FORMATS = { dikey: [1080, 1920, 'Dikey 9:16'], yatay: [1920, 1080, 'Yatay 16:9'], kare: [1080, 1080, 'Kare 1:1'] };
  const DEF_STYLE = { font: 'poppins-black', size: 92, color: '#FFFFFF', hl: '#FFE14D', outline: '#000000', outlineW: 9, shadow: true, y: 68, upper: true, karaoke: true, anim: true, maxWords: 3 };
  const DEF_FX = { preset: 'none', bright: 0, contrast: 0, sat: 0, temp: 0, vignette: false, grain: false, glow: false, rgb: false, sharpen: false, mirror: false, fadeIn: false, fadeOut: false, zooms: [], texts: [], shapes: [], hide: {}, fxLayers: [], transition: { type: 'none', d: .4 }, lut: null };
  const FONT_CSS = { anton: 'Anton', poppins: 'PoppinsXB', 'poppins-black': 'PoppinsBlk', bangers: 'Bangers' };
  const FONT_NAME = { 'poppins-black': 'Poppins Black', poppins: 'Poppins', anton: 'Anton', bangers: 'Bangers' };
  const LABEL = { cap: '#E4D84C', text: '#B53838', shape: '#677DE0', solid: '#B53838', fx: '#8E2C9A', image: '#A9A9CA', pip: '#3DA2A5', video: '#A9CBC7', music: '#B3C7B3', zoom: '#E7C19E' };
  const CAP_PRESETS = [
    { name: 'Sarı Vurgu', s: { font: 'poppins-black', color: '#FFFFFF', hl: '#FFE14D', outline: '#000000', outlineW: 9, size: 92, karaoke: true, upper: true, shadow: true } },
    { name: 'TikTok', s: { font: 'poppins', color: '#FFFFFF', hl: '#22D3EE', outline: '#000000', outlineW: 8, size: 86, karaoke: true, upper: false, shadow: true } },
    { name: 'Komik', s: { font: 'bangers', color: '#FFFFFF', hl: '#3DFFA2', outline: '#000000', outlineW: 10, size: 104, karaoke: true, upper: true, shadow: true } },
    { name: 'Sert', s: { font: 'anton', color: '#FFFFFF', hl: '#FF3B3B', outline: '#000000', outlineW: 8, size: 112, karaoke: true, upper: true, shadow: false } },
    { name: 'Neon', s: { font: 'poppins-black', color: '#FFFFFF', hl: '#FF3D8B', outline: '#5B2BFF', outlineW: 10, size: 92, karaoke: true, upper: true, shadow: true } },
    { name: 'Sade', s: { font: 'poppins', color: '#FFFFFF', hl: '#FFFFFF', outline: '#000000', outlineW: 6, size: 76, karaoke: false, upper: false, shadow: true } },
  ];
  const FX_PRESETS = [['none', 'Normal', ''], ['sinematik', 'Sinematik', 'contrast(1.12) saturate(.88) brightness(.98)'], ['canli', 'Canlı', 'saturate(1.45) contrast(1.08)'], ['sb', 'Siyah-Beyaz', 'grayscale(1) contrast(1.22)'], ['vintage', 'Vintage', 'sepia(.38) contrast(.95) saturate(.85) brightness(1.03)'], ['soguk', 'Soğuk', 'saturate(1.05) hue-rotate(-12deg) brightness(1.02)'], ['sicak', 'Sıcak', 'sepia(.22) saturate(1.2)'], ['neon', 'Neon', 'saturate(1.6) contrast(1.15) hue-rotate(8deg)']];
  const SWATCH = ['#FFFFFF', '#FFE14D', '#FF3D8B', '#22D3EE', '#3DFFA2', '#FF3B3B', '#B388FF', '#FF8A00', '#000000'];
  const TF0 = { x: .5, y: .5, scale: 100, rot: 0, op: 100 };
  const PROPS = [['pos', 'Konum', 'P'], ['scale', 'Ölçek', 'S'], ['rot', 'Döndürme', 'R'], ['op', 'Opaklık', 'T']];
  const IMG_POS = { tl: [.18, .1], tr: [.82, .1], bl: [.18, .9], br: [.82, .9], c: [.5, .5] };
  const SVG = {
    eye: '<svg viewBox="0 0 24 24"><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg>',
    solo: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="6"/></svg>',
    lock: '<svg viewBox="0 0 24 24"><rect x="5" y="11" width="14" height="10"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></svg>',
    watch: '<svg viewBox="0 0 24 24"><circle cx="12" cy="13" r="8"/><path d="M12 9v4l2 2M10 2h4"/></svg>',
    film: '<svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14"/><path d="M7 5v14M17 5v14"/></svg>',
    img: '<svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14"/><path d="m3 16 5-5 4 4 3-3 6 6"/></svg>',
    note: '<svg viewBox="0 0 24 24"><path d="M9 18V5l11-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="17" cy="16" r="3"/></svg>',
    comp: '<svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18"/><path d="M3 9h18M9 21V9"/></svg>',
  };

  /* =========================================================== temel */
  const P = () => E.project;
  const clips = () => P().clips;
  const clipLen = c => Math.max(0, (c.out - c.in) / Math.max(.25, +c.speed || 1));
  const TL = () => { let t = 0; return clips().map(c => { const r = { c, start: t, len: clipLen(c) }; t += r.len; return r; }); };
  const total = () => clips().reduce((s, c) => s + clipLen(c), 0);
  const clipAt = T => { const tl = TL(); return tl.find(r => T >= r.start - 1e-4 && T < r.start + r.len - 1e-4) || tl[tl.length - 1]; };
  const fps = () => Math.round(Math.max(30, ...(P() ? clips().map(c => c.fps || 30) : [30])));
  const fx = () => P().effects;
  /* videonun kendi siyah kenarları atılmış görüntü alanı */
  const cbox = c => c.content || { x: 0, y: 0, w: 1, h: 1 };
  const csize = c => { const b = cbox(c); return [c.width * b.w, c.height * b.h]; };
  const srcRect = (c, r, VW, VH) => { const b = cbox(c); return [(b.x + r.x * b.w) * VW, (b.y + r.y * b.h) * VH, r.w * b.w * VW, r.h * b.h * VH]; };

  /* ---------- dönüştürme + keyframe ---------- */
  const tfDef = (type, o) => {
    if (type === 'text') return { x: .5, y: (o.y ?? 18) / 100 };
    if (type === 'image') { const p = IMG_POS[o.pos || 'tr'] || IMG_POS.tr; return { x: p[0], y: p[1], op: 100 * (o.opacity ?? 1) }; }
    if (type === 'pip') { const w = o.w ?? .4; return { x: (o.x ?? .55) + w / 2, y: (o.y ?? .06) + .15, op: 100 * (o.opacity ?? 1) }; }
    return {};
  };
  const tfOf = (type, o) => Object.assign({}, TF0, tfDef(type, o), o.tf || {});
  const keysOf = (o, p) => ((o.kf || {})[p] || []).slice().sort((a, b) => a.t - b.t);
  const easeF = (u, a, b) => { const oe = a === 'ease' || a === 'out', ie = b === 'ease' || b === 'in'; if (oe && ie) return u * u * (3 - 2 * u); if (oe) return 1 - (1 - u) * (1 - u); if (ie) return u * u; return u; };
  const valAt = (type, o, p, lt) => {
    const ks = keysOf(o, p); if (!ks.length) return tfOf(type, o)[p];
    if (lt <= ks[0].t) return ks[0].v;
    for (let i = 0; i < ks.length - 1; i++) { const a = ks[i], b = ks[i + 1]; if (lt <= b.t) { if (a.ease === 'hold') return a.v; return a.v + (b.v - a.v) * easeF((lt - a.t) / Math.max(1e-6, b.t - a.t), a.ease, b.ease); } }
    return ks[ks.length - 1].v;
  };
  const tfAt = (type, o, lt) => ({ x: valAt(type, o, 'x', lt), y: valAt(type, o, 'y', lt), scale: valAt(type, o, 'scale', lt), rot: valAt(type, o, 'rot', lt), op: valAt(type, o, 'op', lt) });
  const pSub = p => p === 'pos' ? ['x', 'y'] : [p];
  const isAnim = (o, p) => pSub(p).some(k => (o.kf || {})[k] && o.kf[k].length);
  const setProp = (type, o, p, v, lt) => {
    if (isAnim(o, p)) {
      o.kf = o.kf || {}; const t = +lt.toFixed(3);
      pSub(p).forEach((k, i) => { const val = Array.isArray(v) ? v[i] : v, arr = o.kf[k] = o.kf[k] || []; const ex = arr.find(q => Math.abs(q.t - t) < 1 / 60); if (ex) ex.v = val; else arr.push({ t, v: val, ease: 'lin' }); });
    } else { o.tf = Object.assign({}, tfOf(type, o), o.tf || {}); pSub(p).forEach((k, i) => o.tf[k] = Array.isArray(v) ? v[i] : v); }
  };
  const toggleWatch = (type, o, p, lt) => {
    o.kf = o.kf || {};
    if (isAnim(o, p)) pSub(p).forEach(k => { o.tf = Object.assign({}, tfOf(type, o), o.tf || {}); o.tf[k] = valAt(type, o, k, lt); delete o.kf[k]; });
    else pSub(p).forEach(k => o.kf[k] = [{ t: +lt.toFixed(3), v: valAt(type, o, k, lt), ease: 'lin' }]);
  };
  const toggleKeyAt = (type, o, p, lt) => {
    o.kf = o.kf || {}; const t = +lt.toFixed(3), has = (o.kf[pSub(p)[0]] || []).some(q => Math.abs(q.t - t) < 1 / 60);
    pSub(p).forEach(k => {
      const v = valAt(type, o, k, lt), arr = o.kf[k] = o.kf[k] || [];
      if (has) o.kf[k] = arr.filter(q => Math.abs(q.t - t) >= 1 / 60); else arr.push({ t, v, ease: 'lin' });
      if (!o.kf[k].length) { o.tf = Object.assign({}, tfOf(type, o), o.tf || {}); o.tf[k] = v; delete o.kf[k]; }
    });
  };

  /* =========================================================== katmanlar (AE sırası: üstteki önde) */
  E.layers = () => {
    const p = P(), f = fx(), L = [];
    L.push({ type: 'cap', id: 'cap', name: 'Altyazı', obj: null });
    f.texts.forEach(o => L.push({ type: 'text', id: o.id, name: o.text || 'Yazı', obj: o }));
    f.shapes.forEach(o => L.push({ type: 'shape', id: o.id, name: o.name || (o.solid ? 'Düz Renk' : o.kind === 'ellipse' ? 'Elips' : 'Dikdörtgen'), obj: o }));
    f.fxLayers.forEach(o => L.push({ type: 'fx', id: o.id, name: 'Ayar: ' + ((KS.fx.LIST[o.kind] || [o.kind])[0]), obj: o }));
    p.media.images.forEach(o => L.push({ type: 'image', id: o.id, name: o.name || 'Resim', obj: o }));
    p.overlays.forEach(o => L.push({ type: 'pip', id: o.id, name: o.name || 'Video', obj: o }));
    L.push({ type: 'video', id: 'video', name: 'Ana Video', obj: null });
    if (p.media.music) L.push({ type: 'music', id: 'music', name: p.media.music.name || 'Müzik', obj: p.media.music });
    L.push({ type: 'zoom', id: 'zoom', name: 'Zoom Vurguları', obj: null });
    return L;
  };
  const TRANSFORMABLE = ['text', 'shape', 'image', 'pip'];
  const listOf = type => ({ text: fx().texts, shape: fx().shapes, fx: fx().fxLayers, image: P().media.images, pip: P().overlays })[type];
  const selObj = () => { const s = E.sel; if (!s || !P()) return null; if (s.type === 'video') return clips().find(c => c.id === s.id); if (s.type === 'music') return P().media.music; if (s.type === 'zoom') return fx().zooms.find(z => z.id === s.id); const l = listOf(s.type); return l ? l.find(o => o.id === s.id) : null; };
  const hidden = k => !!((fx().hide || {})[k]);

  /* =========================================================== yükleme */
  E.load = async pid => {
    if (E.project && E.project.id === pid) { E.onShow(); return; }
    await E.flush(); E.pause();
    const p = await KS.api('/api/project/' + pid);
    p.style = Object.assign({}, DEF_STYLE, p.style || {});
    p.effects = Object.assign({}, JSON.parse(JSON.stringify(DEF_FX)), p.effects || {});
    ['zooms', 'texts', 'shapes', 'fxLayers'].forEach(k => p.effects[k] = p.effects[k] || []);
    p.effects.transition = Object.assign({ type: 'none', d: .4 }, p.effects.transition || {});
    p.effects.texts.forEach(t => Object.keys({ id: 0, size: 0, color: 0, box: 0, boxColor: 0, anim: 0, upper: 0, font: 0 }).forEach(k => { if (t[k] === undefined) t[k] = { id: 't' + KS.uid(), size: 80, color: '#FFFFFF', box: true, boxColor: '#FF3D8B', anim: 'pop', upper: true, font: 'poppins-black' }[k]; }));
    p.media = Object.assign({ music: null, images: [] }, p.media || {}); p.media.images = p.media.images || [];
    p.overlays = p.overlays || []; p.markers = p.markers || []; p.clips = p.clips || [];
    E.project = p; E.sel = null; E.selKey = null; E.history = []; E.future = []; E.T = 0; E.waves = E.waves || {}; E.imgCache = {};
    pool.forEach(v => { v.pause(); v.remove(); }); pool.clear();
    E.setFormat();
    $('#edTitle').value = p.title;
    KS.fx.lut = null; if (p.effects.lut) KS.fx.loadLut(pid).then(() => E.render());
    E.loadMusic(); E.renderAll(); E.fit();
    clips().forEach(c => E.loadWave(c));
    E.seek(0);
    await document.fonts.ready; E.render();
    KS.api('/api/settings', { son_proje: pid }).catch(() => { });
  };
  E.loadWave = c => { if (E.waves[c.source] !== undefined) return; E.waves[c.source] = null; KS.api(`/api/project/${P().id}/wave/${c.id}`).then(w => { E.waves[c.source] = w; E.drawTimeline(); }).catch(() => { }); };
  E.close = () => { E.pause(); E.project = null; E.showNoProject(); };
  E.onShow = () => setTimeout(() => { if (P()) { E.mag === 'fit' ? E.fit() : E.applyView(); E.sizeTimeline(); E.render(); } else E.showNoProject(); }, 40);
  E.setFormat = () => { const f = FORMATS[P().format] || FORMATS.dikey; BW = f[0]; BH = f[1]; E.resizeCanvas(); };
  E.resizeCanvas = () => { K = .5 * E.qual; PW = Math.round(BW * K); PH = Math.round(BH * K); prev.width = PW; prev.height = PH; };
  E.showNoProject = () => {
    $('#lt-project').innerHTML = `<div class="comp-empty" style="position:static;padding:30px 10px"><b>Açık proje yok</b><span>Yeni bir proje oluştur ya da var olanı aç.</span>
      <button class="btn primary" id="npNew">Yeni Proje (Ctrl+N)</button><button class="btn ghost" id="npOpen">Projeleri Aç</button></div>`;
    $('#npNew').onclick = () => E.newProjectDialog(); $('#npOpen').onclick = () => E.projectsDialog();
    ['#lt-controls', '#rt-subs', '#rt-style', '#rt-fx', '#tlLayers'].forEach(s => $(s).innerHTML = '');
    $('#compEmpty').hidden = true; pctx.clearRect(0, 0, prev.width, prev.height); gctx.clearRect(0, 0, giz.width, giz.height);
    const t = $('#tlCanvas'); t.width = 1; t.height = 1; $('#compTab').textContent = 'Kompozisyon'; $('#tlInfo').textContent = '';
  };
  E.renderAll = () => {
    if (!P()) return E.showNoProject();
    E.renderProject(); E.renderControls(); E.renderFx(); E.renderSubs(); E.renderStyle();
    E.sizeTimeline(); E.updateUndo();
    $('#compTab').textContent = 'Kompozisyon: ' + (P().title || '').slice(0, 40);
    $('#compRes').textContent = `${BW}×${BH} · ${(FORMATS[P().format] || FORMATS.dikey)[2]}`;
    $('#aeFps').textContent = fps() + ' fps';
    $('#compEmpty').hidden = clips().length > 0;
  };

  /* =========================================================== geçmiş & kayıt */
  const KEYS = ['title', 'format', 'clips', 'overlays', 'style', 'effects', 'media', 'markers', 'work'];
  const snap = () => JSON.stringify(KEYS.map(k => P()[k] === undefined ? null : P()[k]));
  const restore = s => { const a = JSON.parse(s); KEYS.forEach((k, i) => { if (a[i] === null && (k === 'work')) delete P()[k]; else P()[k] = a[i]; }); };
  E.change = (fn, { soft } = {}) => {
    if (!P()) return;
    const before = snap(); fn();
    if (snap() === before) return;
    E.history.push(before); if (E.history.length > 150) E.history.shift(); E.future = [];
    E.dirty(); if (!soft) E.renderAll(); E.render(); E.drawTimeline();
  };
  E.beginDrag = () => { if (P()) E._dragSnap = snap(); };
  E.endDrag = () => { if (E._dragSnap && E._dragSnap !== snap()) { E.history.push(E._dragSnap); E.future = []; E.dirty(); } E._dragSnap = null; E.updateUndo(); };
  E.undo = () => { if (!E.history.length) return; E.future.push(snap()); restore(E.history.pop()); E.after(); };
  E.redo = () => { if (!E.future.length) return; E.history.push(snap()); restore(E.future.pop()); E.after(); };
  E.after = () => { E.setFormat(); E.renderAll(); E.applyView(); E.seek(Math.min(E.T, total())); E.dirty(); E.flush().then(E.loadMusic); };
  E.updateUndo = () => { $('#undoBtn').disabled = !E.history.length; $('#redoBtn').disabled = !E.future.length; };
  let saveT = null;
  E.dirty = () => { const s = $('#saveState'); s.classList.add('dirty'); s.lastChild.textContent = 'Kaydediliyor...'; clearTimeout(saveT); saveT = setTimeout(E.flush, 600); E.updateUndo(); };
  E.flush = async () => {
    clearTimeout(saveT); if (!P() || !$('#saveState').classList.contains('dirty')) return;
    const body = {}; KEYS.forEach(k => { if (P()[k] !== undefined) body[k] = P()[k]; });
    try { await KS.api('/api/project/' + P().id, body); $('#saveState').classList.remove('dirty'); $('#saveState').lastChild.textContent = 'Kaydedildi'; }
    catch (e) { $('#saveState').lastChild.textContent = 'Kaydedilemedi!'; }
  };
  window.addEventListener('beforeunload', () => E.flush());
  $('#edTitle').onchange = e => { if (!P()) return; E.change(() => P().title = e.target.value.trim() || 'Kesit', { soft: true }); $('#compTab').textContent = 'Kompozisyon: ' + P().title; };
  $('#edTitle').onkeydown = e => e.stopPropagation();
  $('#undoBtn').onclick = () => E.undo(); $('#redoBtn').onclick = () => E.redo();

  /* =========================================================== video havuzu & oynatma */
  const pool = new Map();
  const vidFor = (kind, o) => {
    const key = kind + '|' + o.source;
    let v = pool.get(key);
    if (!v) {
      v = document.createElement('video'); v.preload = 'auto'; v.playsInline = true; v.src = `/media/${kind}/${P().id}/${o.id}`;
      if (kind === 'overlay') v.dataset.pip = 1;
      v.addEventListener('seeked', () => { if (!E.playing) { E.render(); E.drawSrc && E.drawSrc(); } });
      v.addEventListener('loadeddata', () => { E.render(); E.drawSrc && E.drawSrc(); });
      $('#vidPool').appendChild(v); pool.set(key, v);
    }
    return v;
  };
  E.syncVideos = force => {
    if (!P() || !clips().length) return;
    const r = clipAt(E.T); if (!r) return;
    const v = vidFor('clip', r.c), want = r.c.in + (E.T - r.start) * (r.c.speed || 1);
    v.playbackRate = r.c.speed || 1; v.volume = KS.clamp(r.c.volume ?? 1, 0, 1);
    if (force || Math.abs(v.currentTime - want) > .25) v.currentTime = want;
    pool.forEach(o => { if (o !== v && !o.dataset.pip && !o.paused) o.pause(); });
    E.activeVid = v; E.activeClip = r;
    for (const ov of P().overlays) {
      const pv = vidFor('overlay', ov), on = E.T >= ov.s && E.T < ov.e && !ov.hidden && !hidden('pip'), w = (ov.in || 0) + (E.T - ov.s);
      pv.volume = KS.clamp(ov.volume ?? 1, 0, 1);
      if (!on) { if (!pv.paused) pv.pause(); continue; }
      if (force || Math.abs(pv.currentTime - w) > .3) pv.currentTime = w;
      if (E.playing && pv.paused) pv.play().catch(() => { }); if (!E.playing && !pv.paused) pv.pause();
    }
  };
  E.seek = T => { if (!P()) return; E.T = KS.clamp(T, 0, Math.max(0, total() - .5 / fps())); E.syncVideos(true); E.syncMusic(true); E.render(); E.drawTimeline(); E.highlightCaption(); E.renderControlsLive(); if (!E.playing && (Object.keys(E.reveal).length || Object.values(E.open).some(Boolean))) E.renderTlLayers(); };
  E.play = () => {
    if (!P() || !clips().length) return;
    const wa = P().work; if (E.T >= (wa ? wa.b : total()) - .05) E.T = wa ? wa.a : 0;
    E.playing = true; $('#page-editor').classList.add('playing');
    E.syncVideos(true); E.activeVid.play().catch(() => { }); E.syncMusic(true);
    requestAnimationFrame(loop);
  };
  E.pause = () => { E.playing = false; $('#page-editor').classList.remove('playing'); pool.forEach(v => v.pause()); music.pause(); if (P()) { E.render(); E.drawTimeline(); E.renderControlsLive(); } };
  E.toggle = () => E.playing ? E.pause() : E.play();
  $('#playBtn').onclick = () => E.toggle();
  function loop() {
    if (!E.playing || !P()) return;
    const r = E.activeClip, v = E.activeVid, wb = P().work ? P().work.b : total();
    if (r && v) {
      const T = r.start + (v.currentTime - r.c.in) / (r.c.speed || 1), end = r.start + r.len;
      if (v.currentTime >= r.c.out - .03 || v.ended || T >= end - .02) {
        if (end >= wb - .02) { E.pause(); E.seek(P().work ? P().work.a : Math.max(0, total() - .05)); return; }
        E.T = end + .001; E.syncVideos(true); E.activeVid.play().catch(() => { });
      } else {
        E.T = Math.max(r.start, T);
        if (E.T >= wb) { E.pause(); E.seek(P().work.a); return; }
        if (v.paused) v.play().catch(() => { });
      }
      E.syncVideos(false);
    }
    E.render(); E.drawTimeline(); E.syncMusic(); E.highlightCaption();
    requestAnimationFrame(loop);
  }
  E.loadMusic = () => { const m = P() && P().media.music, src = m ? `/media/file/${P().id}/music?v=${encodeURIComponent(m.path)}` : ''; if (music.dataset.src !== src) { music.dataset.src = src; if (src) music.src = src; else music.removeAttribute('src'); } };
  E.syncMusic = force => {
    const m = P() && P().media.music; if (!m || !music.src) return;
    if (hidden('music') || m.hidden) { if (!music.paused) music.pause(); return; }
    music.volume = KS.clamp(m.vol ?? .25, 0, 1);
    const pos = E.T - (+m.s || 0);
    if (!E.playing || pos < 0) { if (!music.paused) music.pause(); return; }
    const t = pos % (music.duration || 1e9);
    if (force || Math.abs(music.currentTime - t) > .3) music.currentTime = t;
    if (music.paused) music.play().catch(() => { });
  };

  /* =========================================================== kompozisyon çizimi */
  const fxFilter = f => {
    let s = (FX_PRESETS.find(p => p[0] === f.preset) || [])[2] || '';
    if (+f.bright) s += ` brightness(${1 + f.bright / 150})`; if (+f.contrast) s += ` contrast(${1 + f.contrast / 100})`;
    if (+f.sat) s += ` saturate(${Math.max(0, 1 + f.sat / 100)})`; if (+f.temp > 0) s += ` sepia(${f.temp / 300}) saturate(${1 + f.temp / 400})`; if (+f.temp < 0) s += ` hue-rotate(${f.temp / 8}deg)`;
    return s.trim() || 'none';
  };
  function drawClip(x, c, v, filter) {
    const L = c.layout || {}, VW = v.videoWidth || c.width, VH = v.videoHeight || c.height, fmt = P().format || 'dikey';
    const full = srcRect(c, { x: 0, y: 0, w: 1, h: 1 }, VW, VH), [, , CW, CH] = full;
    x.filter = filter;
    if (L.mode === 'crop' && L.crop) x.drawImage(v, ...srcRect(c, L.crop, VW, VH), 0, 0, PW, PH);
    else if (L.mode === 'split' && fmt === 'dikey' && L.face && L.game) {
      const top = Math.round(PH * (L.split ?? .4)); x.drawImage(v, ...srcRect(c, L.face, VW, VH), 0, 0, PW, top); x.drawImage(v, ...srcRect(c, L.game, VW, VH), 0, top, PW, PH - top);
    } else if (L.mode === 'blur') {
      const sc = Math.max(PW / CW, PH / CH); x.filter = (filter === 'none' ? '' : filter) + ' blur(14px) brightness(.9) saturate(1.15)';
      x.drawImage(v, ...full, (PW - CW * sc) / 2, (PH - CH * sc) / 2, CW * sc, CH * sc); x.filter = filter;
      const s2 = Math.min(PW / CW, PH / CH); x.drawImage(v, ...full, (PW - CW * s2) / 2, (PH - CH * s2) / 2, CW * s2, CH * s2);
    } else { const s2 = Math.min(PW / CW, PH / CH); x.drawImage(v, ...full, (PW - CW * s2) / 2, (PH - CH * s2) / 2, CW * s2, CH * s2); }
    x.filter = 'none';
  }
  const noiseC = document.createElement('canvas'); noiseC.width = noiseC.height = 128;
  (() => { const n = noiseC.getContext('2d'), d = n.createImageData(128, 128); for (let i = 0; i < d.data.length; i += 4) { const q = Math.random() * 255; d.data[i] = d.data[i + 1] = d.data[i + 2] = q; d.data[i + 3] = 255; } n.putImageData(d, 0, 0); })();
  function zoomAt(T) { let z = 1, sh = 0; for (const q of fx().zooms) { const a = q.t, b = a + (+q.d || .8); if (T >= a && T <= b) { z += Math.max((+q.z || 1.25) - 1, q.shake ? .06 : 0) * Math.min(1, (T - a) / .12, (b - T) / .2); if (q.shake) sh = 1; } } return { z, sh }; }
  const soloOn = () => E.layers().some(l => l.obj && l.obj.solo);
  const visible = l => !(l.obj && l.obj.hidden) && (!soloOn() || (l.obj && l.obj.solo) || !TRANSFORMABLE.concat('fx').includes(l.type));
  E.boxes = [];
  const chromaC = document.createElement('canvas'), chromaX = chromaC.getContext('2d', { willReadFrequently: true });
  E.render = () => {
    const p = P(); if (!p) return;
    const x = pctx, T = E.T, f = fx();
    x.save(); x.fillStyle = '#000'; x.fillRect(0, 0, PW, PH);
    const r = clips().length ? clipAt(T) : null;
    if (r) {
      const v = vidFor('clip', r.c);
      if (v.readyState >= 2) {
        const { z, sh } = hidden('zoom') ? { z: 1, sh: 0 } : zoomAt(T);
        x.save();
        if (z !== 1 || f.mirror) { x.translate(PW / 2, PH / 2); x.scale(z * (f.mirror ? -1 : 1), z); x.translate(-PW / 2 + (sh ? Math.sin(T * 53) * PW * .012 : 0), -PH / 2 + (sh ? Math.cos(T * 47) * PH * .008 : 0)); }
        drawClip(x, r.c, v, fxFilter(f)); x.restore();
        if (f.lut && KS.fx.lut) KS.fx.applyLut(x, PW, PH, (f.lut.mix ?? 100) / 100);
      }
    }
    if (f.glow) { x.save(); x.globalCompositeOperation = 'screen'; x.globalAlpha = .38; x.filter = 'blur(9px)'; x.drawImage(prev, 0, 0); x.restore(); }
    if (f.rgb) { x.save(); x.globalCompositeOperation = 'screen'; x.globalAlpha = .22; x.drawImage(prev, -3, 0); x.drawImage(prev, 3, 0); x.restore(); }
    if (f.vignette) { const g = x.createRadialGradient(PW / 2, PH / 2, Math.min(PW, PH) * .3, PW / 2, PH / 2, Math.max(PW, PH) * .62); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(0,0,0,.62)'); x.fillStyle = g; x.fillRect(0, 0, PW, PH); }
    if (f.grain) { x.save(); x.globalAlpha = .09; x.globalCompositeOperation = 'overlay'; x.translate(-Math.random() * 128, -Math.random() * 128); x.fillStyle = x.createPattern(noiseC, 'repeat'); x.fillRect(0, 0, PW + 128, PH + 128); x.restore(); }
    E.boxes = [];
    const layers = E.layers().filter(visible);
    // 1) üst videolar ve resimler (alttan üste)
    for (const kind of ['pip', 'image']) {
      if ((kind === 'pip' && hidden('pip')) || (kind === 'image' && hidden('image'))) continue;
      layers.filter(l => l.type === kind).reverse().forEach(l => { const o = l.obj; if (T >= o.s && T <= o.e) drawVisual(x, kind, o, T); });
    }
    // 2) ayar katmanları ve geçişler: altındaki her şeye (video + üst videolar + resimler) etki eder
    if (!hidden('fx')) {
      layers.filter(l => l.type === 'fx').reverse().forEach(({ obj: L }) => { if (T >= L.s && T <= L.e) KS.fx.apply(x, L.kind, T - L.s, Math.max(.05, L.e - L.s), (+L.i || 70) / 100, L.params || {}, PW, PH); });
      const tr = f.transition || {};
      if (tr.type && tr.type !== 'none') { const d = KS.clamp(+tr.d || .4, .15, 1.5); let acc = 0; clips().slice(0, -1).forEach(c => { acc += clipLen(c); if (Math.abs(T - acc) < d / 2) KS.fx.apply(x, 'tr_' + tr.type, T - (acc - d / 2), d, 1, {}, PW, PH); }); }
    }
    // 3) şekiller, altyazı, yazılar
    if (!hidden('text')) layers.filter(l => l.type === 'shape').reverse().forEach(l => { const o = l.obj; if (T >= o.s && T <= o.e) drawVisual(x, 'shape', o, T); });
    if (!hidden('cap')) drawCaption(x, T);
    if (!hidden('text')) layers.filter(l => l.type === 'text').reverse().forEach(l => { const o = l.obj; if (T >= o.s && T <= o.e) drawText(x, o, T); });
    const tot = total(); let fade = 0;
    if (f.fadeIn && T < .5) fade = 1 - T / .5; if (f.fadeOut && T > tot - .6) fade = Math.max(fade, (T - (tot - .6)) / .6);
    if (fade > 0) { x.fillStyle = `rgba(0,0,0,${KS.clamp(fade, 0, 1)})`; x.fillRect(0, 0, PW, PH); }
    x.restore();
    E.drawGizmo();
    const tc = E.tc(T); $('#aeTc').textContent = tc; $('#tcCur').textContent = tc;
  };
  E.tc = T => { const F = fps(), fr = Math.floor((T % 1) * F + 1e-6); return `${Math.floor(T / 3600)}:${String(Math.floor(T % 3600 / 60)).padStart(2, '0')}:${String(Math.floor(T % 60)).padStart(2, '0')}:${String(fr).padStart(2, '0')}`; };
  const hex = h => { h = (h || '#000').replace('#', ''); return [0, 2, 4].map(i => parseInt(h.substr(i, 2), 16) || 0); };
  function drawVisual(x, type, o, T) {
    const tf = tfAt(type, o, T - o.s); let src = null, w = 0, h = 0;
    if (type === 'image') { src = E.getImg(o); if (!src || !src.naturalWidth) return; w = PW * (+o.size || 22) / 100; h = w * src.naturalHeight / src.naturalWidth; }
    else if (type === 'pip') {
      const v = vidFor('overlay', o); if (v.readyState < 2) return;
      w = PW * (o.w ?? .4); h = w * v.videoHeight / v.videoWidth; src = v;
      if (o.chroma) {
        const cw = Math.max(2, Math.round(w)), ch = Math.max(2, Math.round(h)); chromaC.width = cw; chromaC.height = ch; chromaX.drawImage(v, 0, 0, cw, ch);
        const d = chromaX.getImageData(0, 0, cw, ch), a = d.data, [kr, kg, kb] = hex(o.chroma_color || '#00FF00'), sim = (+o.similarity || .3) * 441;
        for (let i = 0; i < a.length; i += 4) { const dist = Math.hypot(a[i] - kr, a[i + 1] - kg, a[i + 2] - kb); if (dist < sim) a[i + 3] = 0; else if (dist < sim + 25) a[i + 3] = (dist - sim) / 25 * 255; }
        chromaX.putImageData(d, 0, 0); src = chromaC;
      }
    } else { w = (o.w ?? .4) * PW; h = (o.h ?? .2) * PH; }
    x.save(); x.translate(tf.x * PW, tf.y * PH); x.rotate(tf.rot * Math.PI / 180); x.scale(tf.scale / 100, tf.scale / 100); x.globalAlpha = KS.clamp(tf.op / 100, 0, 1);
    if (type === 'shape') {
      x.beginPath(); if (o.kind === 'ellipse') x.ellipse(0, 0, w / 2, h / 2, 0, 0, 7); else x.roundRect(-w / 2, -h / 2, w, h, (+o.radius || 0) * Math.min(w, h) / 2);
      if (!o.noFill) { x.fillStyle = o.fill || '#FF3D8B'; x.fill(); } if (+o.strokeW > 0) { x.strokeStyle = o.stroke || '#FFFFFF'; x.lineWidth = o.strokeW * 2 * K; x.stroke(); }
    } else x.drawImage(src, -w / 2, -h / 2, w, h);
    x.restore();
    E.boxes.push({ type, id: o.id, cx: tf.x * PW, cy: tf.y * PH, w: w * tf.scale / 100, h: h * tf.scale / 100, rot: tf.rot });
  }
  E.getImg = im => { if (!E.imgCache[im.id]) { const i = new Image(); i.onload = () => E.render(); i.src = `/media/file/${P().id}/img?id=${im.id}&v=${encodeURIComponent(im.path)}`; E.imgCache[im.id] = i; } return E.imgCache[im.id]; };

  /* --- altyazı --- */
  E.tlCaps = () => {
    const out = [];
    TL().forEach(({ c, start }) => (c.captions || []).forEach((cap, idx) => {
      const sp = c.speed || 1;
      const ws = (cap.words || []).filter(w => { const m = (w.s + w.e) / 2; return m >= c.in - 1e-3 && m <= c.out + 1e-3; }).map(w => ({ w: w.w, s: start + (Math.max(w.s, c.in) - c.in) / sp, e: start + (Math.min(w.e, c.out) - c.in) / sp, p: w.p }));
      if (ws.length) out.push({ clip: c, idx, cap, s: ws[0].s, e: ws[ws.length - 1].e, words: ws });
    }));
    return out.sort((a, b) => a.s - b.s);
  };
  E.capAt = (T, list) => { list = list || E.tlCaps(); for (let i = 0; i < list.length; i++) { const c = list[i], n = list[i + 1]; let end = c.e + .35; if (n) { end = Math.min(end, n.s); if (n.s - c.e < .35) end = n.s; } if (T >= c.s && T < Math.max(end, c.s + .2)) return i; } return -1; };
  function wrapLines(x, words, maxW) { const lines = []; let cur = []; for (const w of words) { if (cur.length && x.measureText(cur.concat(w).map(o => o.t).join(' ')).width > maxW) { lines.push(cur); cur = [w]; } else cur.push(w); } if (cur.length) lines.push(cur); return lines; }
  const popScale = dt => dt < 0 ? 1 : dt < .11 ? .72 + .32 * dt / .11 : dt < .17 ? 1.04 - .04 * (dt - .11) / .06 : 1;
  function drawCaption(x, T) {
    const st = P().style, list = E.tlCaps(), i = E.capAt(T, list); if (i < 0) return;
    const c = list[i], words = c.words.map(w => ({ t: st.upper ? KS.trUpper(w.w) : w.w, s: w.s }));
    let active = 0; words.forEach((w, k) => { if (T >= w.s - 1e-3) active = k; });
    const size = st.size * K; x.save();
    x.font = `${size}px "${FONT_CSS[st.font] || 'PoppinsBlk'}"`; x.textBaseline = 'middle'; x.lineJoin = 'round'; x.miterLimit = 2;
    const lines = wrapLines(x, words, (BW - 140) * K), lh = size * 1.12, cy = PH * st.y / 100, sc = st.anim ? popScale(T - c.s) : 1, tot = lines.length * lh;
    x.translate(PW / 2, cy); x.scale(sc, sc); let maxW = 0;
    lines.forEach((ln, li) => {
      const w = x.measureText(ln.map(o => o.t).join(' ')).width; maxW = Math.max(maxW, w); let xx = -w / 2; const yy = -tot / 2 + lh * li + lh / 2;
      ln.forEach(o => { const tw = x.measureText(o.t).width; if (st.shadow) { x.fillStyle = 'rgba(0,0,0,.55)'; x.fillText(o.t, xx + 2, yy + 2.5); } if (+st.outlineW > 0) { x.strokeStyle = st.outline; x.lineWidth = st.outlineW * 2 * K; x.strokeText(o.t, xx, yy); } x.fillStyle = st.karaoke && words.indexOf(o) === active ? st.hl : st.color; x.fillText(o.t, xx, yy); xx += tw + x.measureText(' ').width; });
    });
    x.restore();
    E.boxes.push({ type: 'cap', id: 'cap', cx: PW / 2, cy, w: maxW + 20, h: tot + 20, rot: 0 });
  }
  function drawText(x, o, T) {
    const lt = T - o.s, raw = o.upper !== false ? KS.trUpper(o.text || '') : (o.text || ''); if (!raw.trim()) return;
    const anim = Object.keys(o.kf || {}).length > 0, tf = tfAt('text', o, lt), size = (+o.size || 80) * K;
    x.save(); x.font = `${size}px "${FONT_CSS[o.font || 'poppins-black']}"`; x.textBaseline = 'middle'; x.lineJoin = 'round';
    let txt = raw, a = 1, ox = 0, sc = 1; const left = o.e - T;
    if (!anim) {
      if (o.anim === 'type') { const n = raw.length, step = Math.min(.06, Math.max(.02, (o.e - o.s) * .4 / Math.max(1, n))); txt = raw.slice(0, Math.max(1, Math.floor(lt / step) + 1)); }
      else if (o.anim === 'slide') { ox = lt < .26 ? -(1 - lt / .26) * (PW / 2 + 350 * K) : 0; if (left < .18) a = left / .18; }
      else if (o.anim === 'fade') a = Math.min(1, lt / .3, left / .3);
      else if (o.anim !== 'none') { sc = lt < .14 ? .6 + .48 * lt / .14 : lt < .22 ? 1.08 - .08 * (lt - .14) / .08 : 1; if (left < .15) a = left / .15; }
    }
    const fw = x.measureText(raw).width;
    x.translate(tf.x * PW + ox, tf.y * PH); x.rotate(tf.rot * Math.PI / 180); x.scale(sc * tf.scale / 100, sc * tf.scale / 100); x.globalAlpha = KS.clamp(a * tf.op / 100, 0, 1);
    if (o.box !== false) { const pad = 18 * K; x.fillStyle = o.boxColor || '#FF3D8B'; x.fillRect(-fw / 2 - pad, -size * .62 - pad * .6, fw + pad * 2, size * 1.24 + pad * 1.2); }
    else { x.strokeStyle = '#000'; x.lineWidth = 14 * K; x.strokeText(txt, -fw / 2, 0); }
    x.fillStyle = o.color || '#FFFFFF'; x.fillText(txt, -fw / 2, 0); x.restore();
    E.boxes.push({ type: 'text', id: o.id, cx: tf.x * PW, cy: tf.y * PH, w: (fw + 36 * K) * tf.scale / 100, h: size * 1.6 * tf.scale / 100, rot: tf.rot });
  }
  E.drawGizmo = () => {
    giz.width = prev.width; giz.height = prev.height; gctx.clearRect(0, 0, giz.width, giz.height);
    if (E.drawRect) { const d = E.drawRect; gctx.strokeStyle = '#2d8ceb'; gctx.lineWidth = 1.5; gctx.setLineDash([5, 4]); if (d.kind === 'ellipse') { gctx.beginPath(); gctx.ellipse((d.x0 + d.x1) / 2, (d.y0 + d.y1) / 2, Math.abs(d.x1 - d.x0) / 2, Math.abs(d.y1 - d.y0) / 2, 0, 0, 7); gctx.stroke(); } else gctx.strokeRect(Math.min(d.x0, d.x1), Math.min(d.y0, d.y1), Math.abs(d.x1 - d.x0), Math.abs(d.y1 - d.y0)); gctx.setLineDash([]); }
    if (!E.sel || E.playing) return;
    const b = E.boxes.find(q => q.type === E.sel.type && q.id === E.sel.id); if (!b) return;
    gctx.save(); gctx.translate(b.cx, b.cy); gctx.rotate(b.rot * Math.PI / 180);
    gctx.strokeStyle = '#2d8ceb'; gctx.lineWidth = 1.2; gctx.strokeRect(-b.w / 2, -b.h / 2, b.w, b.h);
    gctx.fillStyle = '#2d8ceb'; [[-1, -1], [0, -1], [1, -1], [1, 0], [1, 1], [0, 1], [-1, 1], [-1, 0]].forEach(([i, j]) => gctx.fillRect(i * b.w / 2 - 3, j * b.h / 2 - 3, 6, 6));
    gctx.beginPath(); gctx.arc(0, 0, 4, 0, 7); gctx.moveTo(-7, 0); gctx.lineTo(7, 0); gctx.moveTo(0, -7); gctx.lineTo(0, 7); gctx.stroke(); gctx.restore();
  };

  /* =========================================================== kompozisyon görünümü (büyütme, kaydırma, araçlar) */
  const view = $('#compView'), stage = $('#compStage');
  const fitScale = () => Math.min((view.clientWidth - 30) / PW, (view.clientHeight - 30) / PH);
  E.applyView = () => {
    if (!P()) return;
    const s = E.mag === 'fit' ? fitScale() : E.scale; E.scale = s;
    [prev, giz].forEach(c => { c.style.width = PW * s + 'px'; c.style.height = PH * s + 'px'; });
    stage.style.transform = `translate(${-PW * s / 2 + E.pan.x}px,${-PH * s / 2 + E.pan.y}px)`;
    const pct = Math.round(s * K * 100), sel = $('#magSel');
    let opt = sel.querySelector('option[value=custom]'); if (!opt) { sel.insertAdjacentHTML('beforeend', '<option value="custom"></option>'); opt = sel.querySelector('option[value=custom]'); }
    opt.textContent = pct + '%'; sel.value = E.mag === 'fit' ? 'fit' : 'custom';
  };
  E.fit = () => { E.mag = 'fit'; E.pan = { x: 0, y: 0 }; E.applyView(); };
  E.zoomView = (factor, cx, cy) => {
    const vw = view.clientWidth, vh = view.clientHeight, old = E.scale || fitScale(), ns = KS.clamp(old * factor, .05, 16);
    if (cx == null) { cx = vw / 2; cy = vh / 2; }
    const ox = cx - vw / 2 - E.pan.x, oy = cy - vh / 2 - E.pan.y;
    E.pan.x -= ox * (ns / old - 1); E.pan.y -= oy * (ns / old - 1); E.mag = 'custom'; E.scale = ns; E.applyView();
  };
  $('#magSel').onchange = e => { const v = e.target.value; if (v === 'fit') E.fit(); else if (v !== 'custom') { E.mag = 'custom'; E.scale = +v / K; E.pan = { x: 0, y: 0 }; E.applyView(); } };
  $('#qualSel').onchange = e => { E.qual = +e.target.value; const old = E.scale; E.resizeCanvas(); if (E.mag !== 'fit') E.scale = old * (e.target.value == .5 ? 2 : .5); E.applyView(); E.render(); };
  new ResizeObserver(() => { if (P()) E.applyView(); }).observe(view);
  view.addEventListener('wheel', e => {
    if (!P()) return; e.preventDefault();
    if (e.ctrlKey) { const h = hit(...toComp(e)); if (h) { resizeLayer(h, e.deltaY < 0 ? 1 : -1); return; } }
    const rc = view.getBoundingClientRect(); E.zoomView(e.deltaY < 0 ? 1.15 : 1 / 1.15, e.clientX - rc.left, e.clientY - rc.top);
  }, { passive: false });
  const toComp = e => { const r = prev.getBoundingClientRect(); return [(e.clientX - r.left) / r.width * PW, (e.clientY - r.top) / r.height * PH]; };
  function hit(cx, cy) {
    for (let i = E.boxes.length - 1; i >= 0; i--) { const b = E.boxes[i], a = -b.rot * Math.PI / 180, dx = cx - b.cx, dy = cy - b.cy, lx = dx * Math.cos(a) - dy * Math.sin(a), ly = dx * Math.sin(a) + dy * Math.cos(a); if (Math.abs(lx) <= b.w / 2 + 4 && Math.abs(ly) <= b.h / 2 + 4) return b; }
    return null;
  }
  function resizeLayer(h, dir) {
    E.change(() => {
      if (h.type === 'cap') P().style.size = KS.clamp(P().style.size + dir * 4, 30, 220);
      else { const o = listOf(h.type).find(q => q.id === h.id); if (!o || o.locked) return; const lt = E.T - o.s; setProp(h.type, o, 'scale', KS.clamp(valAt(h.type, o, 'scale', lt) + dir * 5, 1, 2000), lt); }
    }, { soft: true });
  }
  E.setTool = t => { E.tool = t; $$('#aeTools button').forEach(b => b.classList.toggle('active', b.dataset.tool === t)); view.className = 'comp-view t-' + t; };
  $$('#aeTools button').forEach(b => b.onclick = () => E.setTool(b.dataset.tool));
  E.setTool('select');
  view.addEventListener('mousedown', e => {
    if (!P()) return;
    const rc = view.getBoundingClientRect(), sx = e.clientX, sy = e.clientY;
    if (e.button === 1 || E.tool === 'hand' || (e.button === 0 && E.spaceHeld)) {
      e.preventDefault(); const p0 = { ...E.pan }; if (E.mag === 'fit') { E.mag = 'custom'; }
      const mv = ev => { E.pan.x = p0.x + ev.clientX - sx; E.pan.y = p0.y + ev.clientY - sy; E.applyView(); };
      const up = () => { removeEventListener('mousemove', mv); removeEventListener('mouseup', up); };
      addEventListener('mousemove', mv); addEventListener('mouseup', up); return;
    }
    if (e.button !== 0) return;
    const [cx, cy] = toComp(e);
    if (E.tool === 'zoom') { E.zoomView(e.altKey ? 1 / 1.5 : 1.5, e.clientX - rc.left, e.clientY - rc.top); return; }
    if (E.tool === 'text') { E.addText(cx / PW, cy / PH); E.setTool('select'); return; }
    if (E.tool === 'rect' || E.tool === 'ellipse') {
      const kind = E.tool; E.drawRect = { kind, x0: cx, y0: cy, x1: cx, y1: cy };
      const mv = ev => { const [x1, y1] = toComp(ev); E.drawRect.x1 = x1; E.drawRect.y1 = y1; E.drawGizmo(); };
      const up = () => { removeEventListener('mousemove', mv); removeEventListener('mouseup', up); const d = E.drawRect; E.drawRect = null; const w = Math.abs(d.x1 - d.x0), h = Math.abs(d.y1 - d.y0); E.addShape(kind, w < 6 ? null : { x: (d.x0 + d.x1) / 2 / PW, y: (d.y0 + d.y1) / 2 / PH, w: w / PW, h: h / PH }); };
      addEventListener('mousemove', mv); addEventListener('mouseup', up); return;
    }
    const h = hit(cx, cy);
    if (!h) { E.select(null); return; }
    E.select({ type: h.type, id: h.id });
    if (h.type === 'cap') {
      E.beginDrag();
      const mv = ev => { const [, y] = toComp(ev); P().style.y = KS.clamp(Math.round(y / PH * 1000) / 10, 3, 97); E.render(); };
      const up = () => { removeEventListener('mousemove', mv); removeEventListener('mouseup', up); E.endDrag(); E.renderStyle(); };
      addEventListener('mousemove', mv); addEventListener('mouseup', up); return;
    }
    const o = listOf(h.type).find(q => q.id === h.id); if (!o || o.locked) return;
    const lt = E.T - o.s, t0 = tfAt(h.type, o, lt); E.beginDrag();
    const mv = ev => {
      const [x1, y1] = toComp(ev);
      if (E.tool === 'rotate') { const a0 = Math.atan2(cy - h.cy, cx - h.cx), a1 = Math.atan2(y1 - h.cy, x1 - h.cx); setProp(h.type, o, 'rot', +(t0.rot + (a1 - a0) * 180 / Math.PI).toFixed(1), lt); }
      else { let nx = t0.x + (x1 - cx) / PW, ny = t0.y + (y1 - cy) / PH; if (ev.shiftKey) { if (Math.abs(x1 - cx) > Math.abs(y1 - cy)) ny = t0.y; else nx = t0.x; } setProp(h.type, o, 'pos', [+nx.toFixed(4), +ny.toFixed(4)], lt); }
      E.render();
    };
    const up = () => { removeEventListener('mousemove', mv); removeEventListener('mouseup', up); E.endDrag(); E.renderControls(); E.sizeTimeline(); };
    addEventListener('mousemove', mv); addEventListener('mouseup', up);
  });
  view.addEventListener('dblclick', e => { if (!P()) return; if (E.tool === 'hand') return E.fit(); const h = hit(...toComp(e)); if (h && h.type === 'text') { E.select(h); E.lt('controls'); setTimeout(() => { const ta = $('#ecText'); if (ta) { ta.focus(); ta.select(); } }, 30); } });
  $('#emptyImport').onclick = () => KS.addFile();

  /* =========================================================== seçim & paneller */
  E.select = sel => {
    E.sel = sel; E.selKey = null;
    if (sel && sel.type === 'cap') E.rt('style'); else if (sel) E.lt('controls');
    E.renderControls(); E.renderTlLayers(); E.drawTimeline(); E.drawGizmo(); E.renderProject();
  };
  E.lt = name => { $$('#leftTabs .ae-tab').forEach(b => b.classList.toggle('active', b.dataset.lt === name)); $$('.lt-panel').forEach(p => p.classList.toggle('active', p.id === 'lt-' + name)); };
  E.rt = name => { $$('#rightTabs .ae-tab').forEach(b => b.classList.toggle('active', b.dataset.rt === name)); $$('.ae-right .rt-panel').forEach(p => p.classList.toggle('active', p.id === 'rt-' + name)); };
  $$('#leftTabs .ae-tab').forEach(b => b.onclick = () => E.lt(b.dataset.lt));
  $$('#rightTabs .ae-tab').forEach(b => b.onclick = () => E.rt(b.dataset.rt));

  /* --- Proje paneli --- */
  const typeIcon = { clip: SVG.film, pip: SVG.film, image: SVG.img, music: SVG.note };
  E.renderProject = () => {
    const p = P(), el = $('#lt-project'); if (!p) return;
    const items = [];
    clips().forEach(c => items.push({ kind: 'clip', sel: { type: 'video', id: c.id }, name: c.name, info: 'Video', dur: clipLen(c) }));
    p.overlays.forEach(o => items.push({ kind: 'pip', sel: { type: 'pip', id: o.id }, name: o.name, info: 'Üst video', dur: o.e - o.s }));
    p.media.images.forEach(o => items.push({ kind: 'image', sel: { type: 'image', id: o.id }, name: o.name, info: 'Resim', dur: o.e - o.s }));
    if (p.media.music) items.push({ kind: 'music', sel: { type: 'music', id: 'music' }, name: p.media.music.name, info: 'Ses', dur: p.media.music.duration || 0 });
    const s = E.sel;
    el.innerHTML = `<div class="proj-prev" style="background-image:url(/thumb/${p.id}?r=${Math.round(p.updated || 0)})">${KS.esc(p.title)} · ${BW}×${BH} · ${KS.fmt(total())}</div>
      <div class="proj-top"><button class="btn primary sm" id="pjImport" title="Ctrl+I">İçe Aktar</button><button class="btn ghost sm" id="pjNew" title="Ctrl+N">Yeni</button><button class="btn ghost sm" id="pjOpen">Projeler</button></div>
      <div class="proj-list"><div class="proj-hdr"><span></span><span>Ad</span><span>Tür</span><span>Süre</span></div>
        <div class="proj-item ${!s ? 'sel' : ''}" data-pi="-1"><i style="color:#ccc">${SVG.comp}</i><span>${KS.esc(p.title)}</span><span>Kompozisyon</span><span>${KS.fmt(total())}</span></div>
        ${items.map((it, i) => `<div class="proj-item ${s && s.type === it.sel.type && s.id === it.sel.id ? 'sel' : ''}" data-pi="${i}" title="${KS.esc(it.name)}"><i>${typeIcon[it.kind]}</i><span>${KS.esc(it.name)}</span><span>${it.info}</span><span>${KS.fmt(it.dur)}</span></div>`).join('')}</div>
      <div class="hint">Dosyaları pencerenin herhangi bir yerine sürükleyebilirsin. Video → ana videonun sonuna. Shift basılıyken bırakırsan üst video olarak eklenir.</div>`;
    $('#pjImport').onclick = () => KS.addFile(); $('#pjNew').onclick = () => E.newProjectDialog(); $('#pjOpen').onclick = () => E.projectsDialog();
    $$('.proj-item', el).forEach(d => {
      d.onclick = () => { const i = +d.dataset.pi; E.select(i < 0 ? null : items[i].sel); };
      d.ondblclick = () => { const i = +d.dataset.pi; if (i < 0) return; const it = items[i]; if (it.kind === 'clip') { const r = TL().find(q => q.c.id === it.sel.id); if (r) E.seek(r.start); } else { const o = selObj(); if (o && o.s != null) E.seek(o.s); } };
    });
  };

  /* --- Efekt Kontrolleri --- */
  const scrub = (id, v, label, step = 1) => `<span class="scrub" data-scrub="${id}" data-v="${v}" data-step="${step}">${label}</span>`;
  const swatches = (cur, key, list = SWATCH) => { cur = cur || '#FFFFFF'; return `<div class="swatches">${list.map(c => `<button class="sw ${cur.toUpperCase() === c ? 'active' : ''}" style="background:${c}" data-k="${key}" data-c="${c}"></button>`).join('')}<label class="sw custom" title="Özel renk"><input type="color" value="${cur}" data-k="${key}"></label></div>`; };
  const tog = (key, label, on) => `<button class="tog ${on ? 'on' : ''}" data-tog="${key}">${label}<i></i></button>`;
  function transformHtml(type, o) {
    const lt = E.T - o.s, t = tfAt(type, o, lt);
    const row = (p, label, valHtml) => { const an = isAnim(o, p), here = keysOf(o, pSub(p)[0]).some(k => Math.abs(k.t - lt) < 1 / 60); return `<div class="prow"><button class="sw-btn ${an ? 'on' : ''}" data-watch="${p}" title="Kronometre: animasyonu aç/kapat">${SVG.watch}</button><span>${label}</span><span class="kn">${valHtml}${an ? `<button data-kprev="${p}" title="Önceki keyframe (J)">◀</button><button data-kadd="${p}" title="Keyframe ekle/kaldır"><span class="kd ${here ? 'on' : ''}"></span></button><button data-knext="${p}" title="Sonraki keyframe (K)">▶</button>` : ''}</span></div>`; };
    return `<details class="ec-sec" open><summary>Dönüştür <span class="hint" style="margin-left:auto">P S R T</span></summary><div class="ec-body">
      ${row('pos', 'Konum', scrub('x', t.x * BW, Math.round(t.x * BW)) + ',' + scrub('y', t.y * BH, Math.round(t.y * BH)))}
      ${row('scale', 'Ölçek', scrub('scale', t.scale, t.scale.toFixed(1) + '%', .5))}
      ${row('rot', 'Döndürme', scrub('rot', t.rot, '0x' + (t.rot >= 0 ? '+' : '') + t.rot.toFixed(1) + '°', .5))}
      ${row('op', 'Opaklık', scrub('op', t.op, Math.round(t.op) + '%', .5))}
      <div class="mini-btns"><span class="hint">Geçiş:</span>${[['lin', 'Doğrusal'], ['ease', 'Easy Ease (F9)'], ['hold', 'Hold']].map(([k, n]) => `<button class="chip" data-ease="${k}">${n}</button>`).join('')}</div>
      <button class="btn ghost sm" data-tfreset>Dönüştürmeyi sıfırla</button></div></details>`;
  }
  E.renderControls = () => {
    const el = $('#lt-controls'); if (!P()) return;
    const s = E.sel, o = selObj();
    if (!s || (!o && s.type !== 'cap')) { el.innerHTML = '<div class="hint" style="padding:12px">Bir katman seç (timeline\'da ya da kompozisyonda tıkla). Özellikleri burada görünür.</div>'; return; }
    const l = E.layers().find(q => q.type === s.type && q.id === s.id);
    let h = `<div class="ec-head"><i style="width:10px;height:10px;background:${LABEL[s.type] || '#888'}"></i><b>${KS.esc(s.type === 'video' ? o.name : (l ? l.name : ''))}</b></div>`;
    if (s.type === 'cap') h += '<div class="hint" style="padding:8px">Altyazı ayarları sağdaki <b>Karakter</b> sekmesinde.</div>';
    else if (s.type === 'video') h += clipControls(o);
    else if (s.type === 'text') h += `<details class="ec-sec" open><summary>Yazı</summary><div class="ec-body">
        <textarea class="inp" id="ecText" spellcheck="false" rows="2">${KS.esc(o.text)}</textarea>
        <div class="font-grid">${Object.keys(FONT_CSS).map(f => `<button class="font-opt ${(o.font || 'poppins-black') === f ? 'active' : ''}" data-tfont="${f}" style="font-family:'${FONT_CSS[f]}';font-size:14px">${FONT_NAME[f]}</button>`).join('')}</div>
        <div class="prow"><span></span><span>Boyut</span>${scrub('tsize', o.size, Math.round(o.size) + ' px')}</div>
        <div class="style-sec"><h4>Renk</h4>${swatches(o.color, 'o.color')}</div>
        <div class="toggles">${tog('o.box', 'Arka kutu', o.box !== false)}${tog('o.upper', 'BÜYÜK HARF', o.upper !== false)}</div>
        ${o.box !== false ? `<div class="style-sec"><h4>Kutu rengi</h4>${swatches(o.boxColor || '#FF3D8B', 'o.boxColor', ['#FF3D8B', '#2D8CEB', '#000000', '#FFE14D', '#22D3EE', '#FF3B3B', '#3DFFA2'])}</div>` : ''}
        <div class="mini-btns"><span class="hint">Giriş:</span>${[['pop', 'Pop'], ['slide', 'Kayma'], ['fade', 'Solma'], ['type', 'Daktilo'], ['none', 'Yok']].map(([k, n]) => `<button class="chip ${(o.anim || 'pop') === k ? 'on' : ''}" data-tanim="${k}">${n}</button>`).join('')}</div>
        <div class="hint">Keyframe kullanırsan giriş animasyonu devre dışı kalır.</div></div></details>` + transformHtml('text', o);
    else if (s.type === 'shape') h += `<details class="ec-sec" open><summary>${o.solid ? 'Düz Renk' : 'Şekil'}</summary><div class="ec-body">
        ${o.solid ? '' : `<div class="mini-btns">${[['rect', 'Dikdörtgen'], ['ellipse', 'Elips']].map(([k, n]) => `<button class="chip ${o.kind === k ? 'on' : ''}" data-skind="${k}">${n}</button>`).join('')}</div>`}
        <div class="prow"><span></span><span>Boyut</span><span>${scrub('sw', o.w * BW, Math.round(o.w * BW))} × ${scrub('sh', o.h * BH, Math.round(o.h * BH))}</span></div>
        ${o.kind === 'rect' && !o.solid ? `<div class="prow"><span></span><span>Köşe yuvarlaklığı</span>${scrub('srad', (o.radius || 0) * 100, Math.round((o.radius || 0) * 100) + '%')}</div>` : ''}
        <div class="style-sec"><h4>Dolgu</h4>${swatches(o.fill || '#FF3D8B', 'o.fill')}</div>
        ${o.solid ? '' : `<div class="toggles">${tog('o.noFill', 'Dolgusuz', o.noFill)}</div><div class="prow"><span></span><span>Kontur kalınlığı</span>${scrub('ssw', o.strokeW || 0, (o.strokeW || 0) + ' px')}</div><div class="style-sec"><h4>Kontur</h4>${swatches(o.stroke || '#FFFFFF', 'o.stroke')}</div>`}</div></details>` + transformHtml('shape', o);
    else if (s.type === 'image') h += `<details class="ec-sec" open><summary>Resim</summary><div class="ec-body"><div class="prow"><span></span><span>Temel genişlik</span>${scrub('isize', o.size || 22, Math.round(o.size || 22) + '%')}</div></div></details>` + transformHtml('image', o);
    else if (s.type === 'pip') h += `<details class="ec-sec" open><summary>Üst Video</summary><div class="ec-body">
        <div class="toggles">${tog('o.chroma', 'Yeşil ekranı sil', o.chroma)}</div>
        ${o.chroma ? `<div class="style-sec"><h4>Silinecek renk</h4>${swatches(o.chroma_color || '#00FF00', 'o.chroma_color', ['#00FF00', '#00B140', '#0047BB', '#000000', '#FFFFFF'])}</div><div class="prow"><span></span><span>Benzerlik</span>${scrub('psim', (o.similarity || .3) * 100, Math.round((o.similarity || .3) * 100) + '%')}</div>` : ''}
        <div class="prow"><span></span><span>Ses</span>${scrub('pvol', (o.volume ?? 1) * 100, Math.round((o.volume ?? 1) * 100) + '%')}</div>
        <div class="prow"><span></span><span>Temel genişlik</span>${scrub('pw', (o.w ?? .4) * 100, Math.round((o.w ?? .4) * 100) + '%')}</div>
        <div class="prow"><span></span><span>Videonun başı</span>${scrub('pin', o.in || 0, KS.fmt(o.in || 0, true), .05)}</div></div></details>` + transformHtml('pip', o);
    else if (s.type === 'fx') h += `<details class="ec-sec" open><summary>${KS.esc((KS.fx.LIST[o.kind] || [o.kind])[0])}</summary><div class="ec-body">
        <div class="prow"><span></span><span>Şiddet</span>${scrub('fi', o.i ?? 70, Math.round(o.i ?? 70) + '%')}</div>
        ${(KS.fx.PARAMS[o.kind] || []).map(([k, lab]) => `<div class="style-sec"><h4>${lab}</h4>${swatches(o.params[k], 'p.' + k, ['#FF3D8B', '#FF8A00', '#FFE14D', '#22D3EE', '#2D8CEB', '#3DFFA2', '#2B1055', '#FFFFFF'])}</div>`).join('')}
        ${o.kind === 'dirblur' ? `<div class="prow"><span></span><span>Yön</span>${scrub('fang', o.params.angle || 0, (o.params.angle || 0) + '°')}</div>` : ''}
        <div class="hint">Ayar katmanı: altındaki her şeye (video, üst videolar, resimler) etki eder.</div></div></details>`;
    else if (s.type === 'music') h += `<details class="ec-sec" open><summary>Ses</summary><div class="ec-body"><div class="prow"><span></span><span>Ses seviyesi</span>${scrub('mvol', (o.vol ?? .25) * 100, Math.round((o.vol ?? .25) * 100) + '%')}</div><button class="btn ghost sm" data-mstart>Müzik şimdi başlasın</button><div class="hint">Konuşma duyulsun diye %20–30 iyi olur.</div></div></details>`;
    else if (s.type === 'zoom') h += `<details class="ec-sec" open><summary>Zoom Vurgusu</summary><div class="ec-body"><div class="prow"><span></span><span>Güç</span>${scrub('zz', ((o.z || 1.25) - 1) * 100, Math.round(((o.z || 1.25) - 1) * 100) + '%')}</div><div class="prow"><span></span><span>Süre</span>${scrub('zd', o.d || .8, (+o.d || .8).toFixed(2) + ' sn', .02)}</div><div class="toggles">${tog('o.shake', 'Sarsıntı', o.shake)}</div></div></details>`;
    el.innerHTML = h;
    bindControls(el, s, o);
  };
  E.renderControlsLive = () => { if (E._dragSnap || !E.sel || !TRANSFORMABLE.includes(E.sel.type)) return; if ($('#lt-controls').contains(document.activeElement)) return; E.renderControls(); };
  function clipControls(c) {
    const fmt = P().format || 'dikey', L = c.layout || {};
    const modes = fmt === 'dikey' ? [['split', 'Yüz + Oyun'], ['crop', 'Tam Kırp'], ['blur', 'Bulanık Arka'], ['fit', 'Sığdır']] : [['fit', 'Sığdır'], ['crop', 'Kırp'], ['blur', 'Bulanık Arka']];
    return `<details class="ec-sec" open><summary>Kadraj</summary><div class="ec-body">
      <div class="mini-btns">${modes.map(([k, n]) => `<button class="chip ${L.mode === k ? 'on' : ''}" data-cmode="${k}">${n}</button>`).join('')}</div>
      <div class="src-wrap" id="srcWrap"><canvas id="srcCanvas"></canvas>${L.mode === 'split' ? '<div class="rect face" data-r="face"><b>YÜZ</b><i class="h"></i></div><div class="rect game" data-r="game"><b>OYUN</b><i class="h"></i></div>' : ''}${L.mode === 'crop' ? '<div class="rect crop" data-r="crop"><b>KADRAJ</b><i class="h"></i></div>' : ''}</div>
      ${c.content ? '<div class="hint">Videonun kendi siyah kenarları otomatik kesildi.</div>' : ''}
      ${L.mode === 'split' ? `<div class="prow"><span></span><span>Yüz alanı</span>${scrub('csplit', (L.split ?? .4) * 100, Math.round((L.split ?? .4) * 100) + '%')}</div>` : ''}
      <div class="mini-btns"><button class="btn ghost sm" data-cl-all>Tüm kliplere uygula</button><button class="btn ghost sm" data-cl-def>Varsayılan yap</button></div></div></details>
      <details class="ec-sec" open><summary>Klip</summary><div class="ec-body">
      <div class="prow"><span></span><span>Hız</span>${scrub('cspeed', (c.speed || 1) * 100, Math.round((c.speed || 1) * 100) + '%')}</div>
      <div class="prow"><span></span><span>Ses</span>${scrub('cvol', (c.volume ?? 1) * 100, Math.round((c.volume ?? 1) * 100) + '%')}</div>
      <div class="prow"><span></span><span>Giriş / Çıkış</span><span class="hint">${KS.fmt(c.in, true)} – ${KS.fmt(c.out, true)}</span></div>
      <button class="btn ghost sm" data-csubs>Bu klibin altyazısını çıkar</button></div></details>`;
  }
  function bindControls(el, s, o) {
    $$('[data-scrub]', el).forEach(sp => sp.onmousedown = e => {
      e.preventDefault(); const x0 = e.clientX, v0 = +sp.dataset.v, step = +sp.dataset.step; let moved = false; E.beginDrag();
      const mv = ev => { const dx = ev.clientX - x0; if (Math.abs(dx) > 2) moved = true; if (moved) applyScrub(sp.dataset.scrub, v0 + dx * step * (ev.shiftKey ? 10 : ev.ctrlKey ? .1 : 1), s, o, true); };
      const up = () => {
        removeEventListener('mousemove', mv); removeEventListener('mouseup', up); E.endDrag();
        if (!moved) { const inp = document.createElement('input'); inp.className = 'scrub-in'; inp.value = (+v0).toFixed(2).replace(/\.00$/, ''); sp.replaceWith(inp); inp.focus(); inp.select(); inp.onkeydown = ev => { if (ev.key === 'Enter') inp.blur(); if (ev.key === 'Escape') { inp.value = v0; inp.blur(); } ev.stopPropagation(); }; inp.onblur = () => { const v = parseFloat(inp.value.replace(',', '.')); E.change(() => { if (!isNaN(v)) applyScrub(sp.dataset.scrub, v, s, o, false); }); }; }
        else { E.renderControls(); E.sizeTimeline(); }
      };
      addEventListener('mousemove', mv); addEventListener('mouseup', up);
    });
    const lt = o && o.s != null ? E.T - o.s : 0, type = s.type;
    $$('[data-watch]', el).forEach(b => b.onclick = () => E.change(() => toggleWatch(type, o, b.dataset.watch, lt)));
    $$('[data-kadd]', el).forEach(b => b.onclick = () => E.change(() => toggleKeyAt(type, o, b.dataset.kadd, lt)));
    $$('[data-kprev],[data-knext]', el).forEach(b => b.onclick = () => { const p = b.dataset.kprev || b.dataset.knext, ks = keysOf(o, pSub(p)[0]).map(k => k.t + o.s), t = b.dataset.kprev ? ks.filter(k => k < E.T - 1e-3).pop() : ks.find(k => k > E.T + 1e-3); if (t != null) E.seek(t); });
    $$('[data-ease]', el).forEach(b => b.onclick = () => E.change(() => Object.values(o.kf || {}).forEach(arr => arr.forEach(k => k.ease = b.dataset.ease))));
    $$('[data-tfreset]', el).forEach(b => b.onclick = () => E.change(() => { o.tf = {}; o.kf = {}; }));
    const ta = $('#ecText', el); if (ta) { ta.onfocus = E.beginDrag; ta.oninput = () => { o.text = ta.value; E.render(); }; ta.onblur = () => { E.endDrag(); E.renderTlLayers(); E.drawTimeline(); }; ta.onkeydown = e => e.stopPropagation(); }
    $$('[data-tfont]', el).forEach(b => b.onclick = () => E.change(() => o.font = b.dataset.tfont));
    $$('[data-tanim]', el).forEach(b => b.onclick = () => E.change(() => o.anim = b.dataset.tanim));
    $$('[data-skind]', el).forEach(b => b.onclick = () => E.change(() => o.kind = b.dataset.skind));
    const setKey = (k, v) => { if (k.startsWith('o.')) o[k.slice(2)] = v; else if (k.startsWith('p.')) o.params[k.slice(2)] = v; };
    $$('.sw[data-c]', el).forEach(b => b.onclick = () => E.change(() => setKey(b.dataset.k, b.dataset.c)));
    $$('input[type=color]', el).forEach(i => i.onchange = () => E.change(() => setKey(i.dataset.k, i.value.toUpperCase())));
    $$('[data-tog]', el).forEach(b => b.onclick = () => E.change(() => { const k = b.dataset.tog.slice(2); o[k] = (k === 'box' || k === 'upper') ? o[k] === false : !o[k]; }));
    $$('[data-cmode]', el).forEach(b => b.onclick = () => E.change(() => { o.layout = Object.assign({}, o.layout, { mode: b.dataset.cmode }); fixLayout(o); }));
    $$('[data-cl-all]', el).forEach(b => b.onclick = () => E.change(() => clips().forEach(c => { if (c !== o) { c.layout = JSON.parse(JSON.stringify(o.layout)); fixLayout(c); } })));
    $$('[data-cl-def]', el).forEach(b => b.onclick = () => KS.api('/api/defaults', { layout: o.layout }).then(() => KS.toast('Yeni kliplerde bu kadraj kullanılacak', 'ok')));
    $$('[data-csubs]', el).forEach(b => b.onclick = () => E.transcribe([o.id]));
    $$('[data-mstart]', el).forEach(b => b.onclick = () => E.change(() => o.s = +E.T.toFixed(3)));
    if (s.type === 'video') setupSrc(o);
  }
  function applyScrub(k, v, s, o, live) {
    const lt = o && o.s != null ? E.T - o.s : 0, type = s.type, C = (a, b) => KS.clamp(v, a, b);
    switch (k) {
      case 'x': setProp(type, o, 'pos', [v / BW, tfAt(type, o, lt).y], lt); break;
      case 'y': setProp(type, o, 'pos', [tfAt(type, o, lt).x, v / BH], lt); break;
      case 'scale': setProp(type, o, 'scale', C(0, 2000), lt); break;
      case 'rot': setProp(type, o, 'rot', v, lt); break;
      case 'op': setProp(type, o, 'op', C(0, 100), lt); break;
      case 'tsize': o.size = Math.round(C(10, 400)); break;
      case 'sw': o.w = C(2, BW * 4) / BW; break; case 'sh': o.h = C(2, BH * 4) / BH; break;
      case 'srad': o.radius = C(0, 100) / 100; break; case 'ssw': o.strokeW = Math.round(C(0, 60)); break;
      case 'isize': o.size = C(1, 300); break;
      case 'psim': o.similarity = C(1, 90) / 100; break; case 'pvol': o.volume = C(0, 200) / 100; break; case 'pw': o.w = C(2, 300) / 100; break;
      case 'pin': o.in = C(0, Math.max(0, (o.src_dur || 0) - .2)); break;
      case 'fi': o.i = Math.round(C(0, 100)); break; case 'fang': o.params.angle = Math.round(C(0, 180)); break;
      case 'mvol': o.vol = C(0, 200) / 100; break;
      case 'zz': o.z = 1 + C(1, 100) / 100; break; case 'zd': o.d = C(.1, 5); break;
      case 'csplit': o.layout.split = C(20, 70) / 100; fixLayout(o); break;
      case 'cspeed': o.speed = C(25, 400) / 100; break; case 'cvol': o.volume = C(0, 200) / 100; break;
    }
    if (live) { E.render(); E.drawTimeline(); if (k === 'csplit') placeRects(o); }
  }
  /* --- kadraj (klip başına; videonun siyah kenarları hariç alan) --- */
  const ASPECT = c => { const r = (c.layout || {}).split ?? .4; return { face: BW / (BH * r), game: BW / (BH * (1 - r)), crop: BW / BH }; };
  function fixLayout(c) {
    const L = c.layout = Object.assign({ mode: 'fit', split: .4, face: { x: 0, y: 0, w: .3, h: .3 }, game: { x: .2, y: 0, w: .6, h: 1 }, crop: { x: .34, y: 0, w: .32, h: 1 } }, c.layout || {});
    const A = ASPECT(c), [W, H] = csize(c);
    ['face', 'game', 'crop'].forEach(k => { const r = L[k] = Object.assign({ x: 0, y: 0, w: .5, h: .5 }, L[k]); r.h = r.w * W / (A[k] * H); if (r.h > 1) { r.h = 1; r.w = A[k] * H / W; } if (r.w > 1) { r.w = 1; r.h = r.w * W / (A[k] * H); } r.x = KS.clamp(r.x, 0, 1 - r.w); r.y = KS.clamp(r.y, 0, 1 - r.h); });
    if ((P().format || 'dikey') !== 'dikey' && L.mode === 'split') L.mode = 'blur';
  }
  function placeRects(c) { $$('#srcWrap .rect').forEach(el => { const r = c.layout[el.dataset.r]; el.style.left = r.x * 100 + '%'; el.style.top = r.y * 100 + '%'; el.style.width = r.w * 100 + '%'; el.style.height = r.h * 100 + '%'; }); }
  function setupSrc(c) {
    const cv = $('#srcCanvas'); if (!cv) return; const v = vidFor('clip', c), [CW, CH] = csize(c);
    E.drawSrc = () => { const wrap = $('#srcWrap'); if (!wrap || !cv.isConnected) return; const w = wrap.clientWidth || 260; cv.width = w * 2; cv.height = Math.round(w * 2 * CH / CW); if (v.readyState >= 2) cv.getContext('2d').drawImage(v, ...srcRect(c, { x: 0, y: 0, w: 1, h: 1 }, v.videoWidth, v.videoHeight), 0, 0, cv.width, cv.height); };
    E.drawSrc(); placeRects(c);
    $$('#srcWrap .rect').forEach(el => el.addEventListener('mousedown', e => {
      e.preventDefault(); e.stopPropagation();
      const key = el.dataset.r, r = c.layout[key], wr = $('#srcWrap').getBoundingClientRect(), resize = e.target.classList.contains('h'), sx = e.clientX, sy = e.clientY, o0 = { ...r }, A = ASPECT(c)[key];
      E.beginDrag();
      const mv = ev => { const dx = (ev.clientX - sx) / wr.width, dy = (ev.clientY - sy) / wr.height; if (resize) { let w = KS.clamp(o0.w + dx, .05, 1 - o0.x), h = w * CW / (A * CH); if (o0.y + h > 1) { h = 1 - o0.y; w = h * A * CH / CW; } r.w = w; r.h = h; } else { r.x = KS.clamp(o0.x + dx, 0, 1 - r.w); r.y = KS.clamp(o0.y + dy, 0, 1 - r.h); } placeRects(c); E.render(); };
      const up = () => { removeEventListener('mousemove', mv); removeEventListener('mouseup', up); E.endDrag(); };
      addEventListener('mousemove', mv); addEventListener('mouseup', up);
    }));
  }

  /* --- Efektler ve Ön Ayarlar --- */
  E.renderFx = () => {
    const f = fx(), el = $('#rt-fx'), q = E.fxSearch || '';
    const cats = Object.entries(KS.fx.LIST).reduce((m, [k, v]) => ((m[v[1]] = m[v[1]] || []).push([k, v[0]]), m), {});
    const match = n => !q || KS.trLower(n).includes(KS.trLower(q)), op = q ? 'open' : '';
    el.innerHTML = `<div class="fxp-search"><input class="inp" id="fxSearch" placeholder="Ara (glitch, parlama, sarsıntı...)" value="${KS.esc(q)}"></div>
      <div class="fxp-tree">
        <details open><summary>Renk Ön Ayarları (tüm video)</summary>${FX_PRESETS.filter(p => match(p[1])).map(([k, n]) => `<div class="fxp-item ${f.preset === k ? 'on' : ''}" data-preset="${k}">${f.preset === k ? '● ' : ''}${n}</div>`).join('')}</details>
        ${Object.entries(cats).map(([cat, items]) => { const its = items.filter(([, n]) => match(n)); return its.length ? `<details ${op}><summary>${KS.fx.ICON[cat] || ''} ${cat}</summary>${its.map(([k, n]) => `<div class="fxp-item" data-fxadd="${k}" title="Oynatma çizgisine ayar katmanı olarak ekle">${n}</div>`).join('')}</details>` : ''; }).join('')}
        <details ${op}><summary>Geçişler (kesimlerde)</summary>${KS.fx.TRANS.filter(([, n]) => match(n)).map(([k, n]) => `<div class="fxp-item ${f.transition.type === k ? 'on' : ''}" data-trans="${k}">${f.transition.type === k ? '● ' : ''}${n}</div>`).join('')}</details>
        <details ${op}><summary>Zoom Vurgusu</summary><div class="fxp-item" data-zoomadd="0">Zoom (punch)</div><div class="fxp-item" data-zoomadd="1">Sarsıntılı zoom</div></details>
        <details><summary>Tüm Videoya</summary><div style="padding:6px"><div class="toggles">${[['vignette', 'Vinyet'], ['grain', 'Film greni'], ['glow', 'Parlama'], ['rgb', 'RGB kayması'], ['sharpen', 'Keskinleştir'], ['mirror', 'Ayna'], ['fadeIn', 'Açılış fade'], ['fadeOut', 'Kapanış fade']].map(([k, n]) => tog(k, n, f[k])).join('')}</div></div></details>
        <details><summary>Renk Düzeltme</summary><div style="padding:6px">${[['bright', 'Parlaklık', -50, 50], ['contrast', 'Kontrast', -50, 50], ['sat', 'Doygunluk', -100, 100], ['temp', 'Sıcaklık', -100, 100]].map(([k, l, a, b]) => `<div class="field"><label>${l} <b id="fv_${k}">${f[k]}</b></label><input type="range" min="${a}" max="${b}" value="${f[k]}" data-frng="${k}"></div>`).join('')}<button class="btn ghost sm" id="fxReset">Sıfırla</button></div></details>
        <details><summary>LUT (.cube)</summary><div style="padding:6px">${f.lut ? `<div class="prow"><span></span><span>${KS.esc(f.lut.name)}</span><button class="del-btn" id="lutDel">${KS.icon.trash}</button></div><div class="field"><label>Etki <b id="lutV">%${f.lut.mix ?? 100}</b></label><input type="range" min="0" max="100" value="${f.lut.mix ?? 100}" id="lutMix"></div>` : '<button class="btn ghost sm" id="lutAdd">LUT yükle</button>'}</div></details>
      </div>
      ${f.transition.type !== 'none' ? `<div class="field"><label>Geçiş süresi <b id="trV">${(+f.transition.d).toFixed(2)} sn</b></label><input type="range" min="15" max="120" value="${Math.round(f.transition.d * 100)}" id="trRange"></div>` : ''}`;
    $$('#rt-fx input[type=range]').forEach(KS.paintRange);
    const s = $('#fxSearch'); s.oninput = () => { E.fxSearch = s.value; const pos = s.selectionStart; E.renderFx(); const n = $('#fxSearch'); n.focus(); n.setSelectionRange(pos, pos); }; s.onkeydown = e => e.stopPropagation();
    $$('[data-preset]', el).forEach(b => b.onclick = () => E.change(() => f.preset = b.dataset.preset));
    $$('[data-fxadd]', el).forEach(b => b.onclick = () => E.addFx(b.dataset.fxadd));
    $$('[data-trans]', el).forEach(b => b.onclick = () => E.change(() => f.transition.type = b.dataset.trans));
    $$('[data-zoomadd]', el).forEach(b => b.onclick = () => E.addZoom(b.dataset.zoomadd === '1'));
    $$('[data-tog]', el).forEach(b => b.onclick = () => E.change(() => f[b.dataset.tog] = !f[b.dataset.tog]));
    $$('[data-frng]', el).forEach(r => { r.onpointerdown = E.beginDrag; r.oninput = () => { f[r.dataset.frng] = +r.value; $('#fv_' + r.dataset.frng).textContent = r.value; E.render(); }; r.onchange = () => E.endDrag(); });
    const rs = $('#fxReset'); if (rs) rs.onclick = () => E.change(() => Object.assign(f, { bright: 0, contrast: 0, sat: 0, temp: 0 }));
    const tr = $('#trRange'); if (tr) { tr.onpointerdown = E.beginDrag; tr.oninput = () => { f.transition.d = tr.value / 100; $('#trV').textContent = (tr.value / 100).toFixed(2) + ' sn'; E.render(); }; tr.onchange = () => E.endDrag(); }
    const la = $('#lutAdd'); if (la) la.onclick = () => KS.addFile();
    const ld = $('#lutDel'); if (ld) ld.onclick = async () => { await E.flush(); await KS.api(`/api/project/${P().id}/lut`, {}); E.change(() => f.lut = null); KS.fx.lut = null; E.render(); };
    const lm = $('#lutMix'); if (lm) { lm.onpointerdown = E.beginDrag; lm.oninput = () => { f.lut.mix = +lm.value; $('#lutV').textContent = '%' + lm.value; E.render(); }; lm.onchange = () => E.endDrag(); }
  };

  /* --- Altyazı --- */
  const subsJob = () => (KS.state.jobs || []).find(j => j.kind === 'altyazi' && (j.status === 'calisiyor' || j.status === 'bekliyor') && P() && j.title === 'Altyazı: ' + P().title);
  E.renderSubs = () => {
    const el = $('#rt-subs'), list = E.tlCaps(), job = subsJob(), p = P();
    const running = job || clips().some(c => c.subs_status === 'calisiyor');
    if (!list.length) {
      el.innerHTML = `<div class="subs-empty"><b style="color:#ddd;font-size:14px">${running ? 'Altyazı çıkarılıyor...' : 'Otomatik altyazı'}</b>
        <span>${running ? 'Konuşmalar yazıya dökülüyor.' : clips().length ? 'Konuşmaları Türkçe yazıya döküp ekleyeyim.' : 'Önce video ekle.'}</span>
        ${running ? `<div class="progress"><i id="subsProg" style="width:${Math.round((job ? job.progress : .05) * 100)}%"></i></div><small id="subsMsg">${KS.esc(job ? job.message : '')}</small>` : clips().length ? '<button class="btn primary" id="subsGo">Altyazı Çıkar</button>' : ''}
        ${clips().some(c => c.subs_status === 'hata') && !running ? '<small style="color:#e8920d">Son denemede hata oldu, tekrar dene.</small>' : ''}</div>`;
      const b = $('#subsGo'); if (b) b.onclick = () => E.transcribe(); return;
    }
    const flagged = list.reduce((n, c) => n + c.words.filter(w => w.p < .55).length, 0), mw = p.style.maxWords || 3;
    const missing = clips().filter(c => c.has_audio && !(c.captions || []).length && c.subs_status !== 'calisiyor').length;
    el.innerHTML = `<div class="subs-tools">${flagged ? `<button class="chip warn" id="nextFlag">⚠ ${flagged} kontrol et</button>` : '<span class="chip" style="color:#4aa44c">✓ Temiz</span>'}
        <button class="chip" id="capRedo">Yeniden çıkar</button>${missing ? `<button class="chip" id="capMiss">+ ${missing} klip için çıkar</button>` : ''}<button class="chip" id="capDict">Sözlük</button></div>
      <div class="subs-tools"><span class="hint">Ekranda kelime:</span>${[1, 2, 3, 4].map(n => `<button class="chip ${n === mw ? 'on' : ''}" data-mw="${n}">${n}</button>`).join('')}</div>
      <div class="cap-list" id="capList">${list.map((c, i) => `<div class="cap" data-ci="${i}"><span class="ct">${KS.fmt(c.s, true)}</span><div class="tx" contenteditable="true" spellcheck="false">${c.cap.words.map(w => w.p < .55 ? `<span class="fl">${KS.esc(w.w)}</span>` : KS.esc(w.w)).join(' ')}</div><button class="x" title="Sil">${KS.icon.x}</button></div>`).join('')}</div>`;
    $('#capRedo').onclick = async () => { if (await KS.confirm('Altyazıyı baştan çıkar?', 'Yaptığın düzeltmeler silinecek.', 'Baştan çıkar', true)) E.transcribe(clips().map(c => c.id)); };
    const cm = $('#capMiss'); if (cm) cm.onclick = () => E.transcribe();
    $('#capDict').onclick = () => KS.go('settings');
    const nf = $('#nextFlag'); if (nf) nf.onclick = E.nextFlag;
    $$('[data-mw]', el).forEach(b => b.onclick = async () => { await E.flush(); const before = snap(), r = await KS.api(`/api/project/${p.id}/rechunk`, { maxWords: +b.dataset.mw }); E.history.push(before); r.clips.forEach(x => { const c = clips().find(q => q.id === x.id); if (c) c.captions = x.captions; }); p.style.maxWords = +b.dataset.mw; E.renderSubs(); E.render(); E.drawTimeline(); E.updateUndo(); });
    $$('.cap', el).forEach(row => {
      const c = list[+row.dataset.ci], tx = $('.tx', row);
      $('.ct', row).onclick = () => E.seek(c.s + .01);
      tx.onfocus = () => { if (E.playing) E.pause(); if (E.T < c.s || E.T > c.e) E.seek(c.s + .01); tx.dataset.orig = tx.innerText; };
      tx.onkeydown = e => { if (e.key === 'Enter') { e.preventDefault(); tx.blur(); } if (e.key === 'Escape') { tx.innerText = tx.dataset.orig; tx.blur(); } e.stopPropagation(); };
      tx.onblur = () => { if (tx.innerText.trim() !== (tx.dataset.orig || '').trim()) editCaption(c, tx.innerText); };
      $('.x', row).onclick = () => E.change(() => c.clip.captions.splice(c.idx, 1));
    });
  };
  function editCaption(c, text) {
    const toks = text.replace(/\s+/g, ' ').trim().split(' ').filter(Boolean), cap = c.cap;
    if (!toks.length) return E.change(() => c.clip.captions.splice(c.idx, 1));
    let learn = null;
    E.change(() => {
      if (toks.length === cap.words.length) { const d = []; cap.words.forEach((w, k) => { if (w.w !== toks[k]) { d.push([w.w, toks[k]]); w.w = toks[k]; w.p = 1; } }); if (d.length === 1) learn = d[0]; }
      else { const tot = toks.reduce((s, t) => s + t.length + 1, 0), span = cap.e - cap.s; let t = cap.s; cap.words = toks.map(tk => { const dd = span * (tk.length + 1) / tot, w = { w: tk, s: +t.toFixed(3), e: +(t + dd).toFixed(3), p: 1 }; t += dd; return w; }); }
    });
    if (learn) { const cl = s => s.replace(/[.,!?;:…"'()]/g, ''), [a, b] = [cl(learn[0]), cl(learn[1])]; if (a && b && KS.trLower(a) !== KS.trLower(b)) KS.toast(`"<b>${KS.esc(a)}</b>" → "<b>${KS.esc(b)}</b>" düzeltmesini hatırlayayım mı?`, '', [{ label: 'Hatırla', primary: true, fn: async () => { await E.flush(); const r = await KS.api('/api/fixes', { add: { [a]: b }, project: P().id }); KS.state.settings.duzeltmeler = r.duzeltmeler; (r.clips || []).forEach(x => { const cc = clips().find(q => q.id === x.id); if (cc) cc.captions = x.captions; }); E.renderSubs(); E.render(); } }], 6000); }
  }
  E.nextFlag = () => { const list = E.tlCaps(), fl = []; list.forEach((c, i) => c.words.forEach(w => { if (w.p < .55) fl.push([i, w.s]); })); if (!fl.length) return KS.toast('Kontrol edilecek kelime kalmadı', 'ok', [], 1500); const n = fl.find(x => x[1] > E.T + .05) || fl[0]; E.rt('subs'); E.seek(n[1] + .01); setTimeout(() => { const row = $(`.cap[data-ci="${n[0]}"]`); if (row) { row.scrollIntoView({ block: 'center' }); $('.tx', row).focus(); } }, 60); };
  E.transcribe = async ids => {
    if (!clips().length) return KS.toast('Önce video ekle', 'err');
    await E.flush();
    const r = await KS.api(`/api/project/${P().id}/transcribe`, { clips: ids || null });
    clips().forEach(c => { if (ids ? ids.includes(c.id) : !(c.captions || []).length) { c.subs_status = 'calisiyor'; if (ids) c.captions = []; } });
    KS.trackJob(r.job); E.rt('subs'); E.renderSubs(); E.render(); E.drawTimeline();
  };
  E.highlightCaption = () => { if (!P()) return; const i = E.capAt(E.T); if (i === E._lastCap) return; E._lastCap = i; $$('#capList .cap.now').forEach(r => r.classList.remove('now')); const row = $(`#capList .cap[data-ci="${i}"]`); if (row) { row.classList.add('now'); if (!row.contains(document.activeElement)) row.scrollIntoView({ block: 'nearest' }); } };
  KS.hooks.jobTick.push(() => { if (!P() || E.tlCaps().length) return; const j = subsJob(), bar = $('#subsProg'); if (j && bar) { bar.style.width = Math.round(j.progress * 100) + '%'; $('#subsMsg').textContent = j.message; } else if (j && !bar) E.renderSubs(); });
  KS.hooks.jobDone.push(async j => {
    if (!P() || !j.result || j.result.project !== P().id) return;
    const fresh = await KS.api('/api/project/' + P().id);
    if (j.kind === 'altyazi') { fresh.clips.forEach(fc => { const c = clips().find(q => q.id === fc.id); if (c) { c.captions = fc.captions; c.words = fc.words; c.subs_status = fc.subs_status; } }); E.renderSubs(); E.render(); E.drawTimeline(); }
    if ((j.kind === 'an' || j.kind === 'indir') && j.result.added) { const known = new Set(clips().map(c => c.id)); fresh.clips.filter(c => !known.has(c.id)).forEach(c => { clips().push(c); E.loadWave(c); }); E.renderAll(); E.render(); E.dirty(); }
  });
  KS.hooks.jobDone.push(j => { if (j.kind === 'altyazi' && j.status === 'hata' && P()) { clips().forEach(c => { if (c.subs_status === 'calisiyor') c.subs_status = 'hata'; }); E.renderSubs(); } });

  /* --- Karakter (altyazı stili) --- */
  E.renderStyle = () => {
    const st = P().style, el = $('#rt-style');
    el.innerHTML = `<div class="style-sec"><h4>Hazır stiller</h4><div class="preset-grid">${CAP_PRESETS.map((pr, i) => { const s = pr.s, act = ['font', 'color', 'hl', 'outline'].every(k => (st[k] || '').toString().toUpperCase() === (s[k] || '').toString().toUpperCase()); return `<button class="preset ${act ? 'active' : ''}" data-cp="${i}"><div class="cap-preset" style="font-family:'${FONT_CSS[s.font]}';color:${s.color};-webkit-text-stroke:${Math.min(3, s.outlineW / 3)}px ${s.outline};paint-order:stroke fill">${s.upper ? 'BU ÇOK' : 'Bu çok'}&nbsp;<span style="color:${s.karaoke ? s.hl : s.color}">${s.upper ? 'İYİ' : 'iyi'}</span></div><span>${pr.name}</span></button>`; }).join('')}</div></div>
      <div class="font-grid">${Object.keys(FONT_CSS).map(f => `<button class="font-opt ${st.font === f ? 'active' : ''}" data-font="${f}" style="font-family:'${FONT_CSS[f]}';font-size:15px">${FONT_NAME[f]}</button>`).join('')}</div>
      <div class="prow"><span></span><span>Boyut</span>${scrub('csize', st.size, st.size + ' px')}</div>
      <div class="prow"><span></span><span>Yükseklik (kompozisyonda sürükle)</span>${scrub('cy', st.y, '%' + Math.round(st.y), .2)}</div>
      <div class="prow"><span></span><span>Kenar kalınlığı</span>${scrub('cow', st.outlineW, st.outlineW + ' px', .2)}</div>
      <div class="style-sec"><h4>Yazı rengi</h4>${swatches(st.color, 'color')}</div>
      <div class="style-sec"><h4>Vurgu rengi (konuşulan kelime)</h4>${swatches(st.hl, 'hl')}</div>
      <div class="style-sec"><h4>Kenar rengi</h4>${swatches(st.outline, 'outline', ['#000000', '#FFFFFF', '#5B2BFF', '#FF3D8B', '#1A1A2E'])}</div>
      <div class="toggles">${tog('upper', 'BÜYÜK HARF', st.upper)}${tog('karaoke', 'Kelime vurgusu', st.karaoke)}${tog('anim', 'Pop animasyon', st.anim)}${tog('shadow', 'Gölge', st.shadow)}</div>
      <button class="btn ghost sm" id="styleDefault">Bu stili varsayılan yap</button>`;
    $$('[data-cp]', el).forEach(b => b.onclick = () => E.change(() => Object.assign(st, CAP_PRESETS[+b.dataset.cp].s)));
    $$('[data-font]', el).forEach(b => b.onclick = () => E.change(() => st.font = b.dataset.font));
    $$('.sw[data-c]', el).forEach(b => b.onclick = () => E.change(() => st[b.dataset.k] = b.dataset.c));
    $$('input[type=color]', el).forEach(i => i.onchange = () => E.change(() => st[i.dataset.k] = i.value.toUpperCase()));
    $$('[data-tog]', el).forEach(b => b.onclick = () => E.change(() => st[b.dataset.tog] = !st[b.dataset.tog]));
    $$('[data-scrub]', el).forEach(sp => sp.onmousedown = e => {
      e.preventDefault(); const x0 = e.clientX, v0 = +sp.dataset.v, step = +sp.dataset.step, k = sp.dataset.scrub; E.beginDrag();
      const mv = ev => { const v = v0 + (ev.clientX - x0) * step * (ev.shiftKey ? 10 : 1); if (k === 'csize') st.size = Math.round(KS.clamp(v, 30, 220)); if (k === 'cy') st.y = KS.clamp(+v.toFixed(1), 3, 97); if (k === 'cow') st.outlineW = Math.round(KS.clamp(v, 0, 20)); E.render(); };
      const up = () => { removeEventListener('mousemove', mv); removeEventListener('mouseup', up); E.endDrag(); E.renderStyle(); };
      addEventListener('mousemove', mv); addEventListener('mouseup', up);
    });
    $('#styleDefault').onclick = () => KS.api('/api/defaults', { style: st }).then(() => KS.toast('Yeni kliplerde bu stil kullanılacak', 'ok'));
  };

  /* =========================================================== katman ekleme */
  const needClips = () => { if (!clips().length) { KS.toast('Önce video ekle (Ctrl+I)', 'err'); return true; } return false; };
  E.addText = (cx, cy) => {
    if (needClips()) return;
    const t = E.T, o = { id: 't' + KS.uid(), text: 'YAZI', s: +t.toFixed(3), e: +Math.min(total(), t + 3).toFixed(3), size: 80, color: '#FFFFFF', box: true, boxColor: '#FF3D8B', anim: 'pop', upper: true, font: 'poppins-black', tf: { x: cx ?? .5, y: cy ?? .18 } };
    E.change(() => fx().texts.unshift(o)); E.select({ type: 'text', id: o.id });
    setTimeout(() => { const ta = $('#ecText'); if (ta) { ta.focus(); ta.select(); } }, 40);
  };
  E.addShape = (kind, box, solid) => {
    if (needClips()) return;
    const t = solid ? 0 : E.T, o = { id: 's' + KS.uid(), kind: kind || 'rect', solid: !!solid, s: +t.toFixed(3), e: +(solid ? total() : Math.min(total(), t + 3)).toFixed(3), w: box ? box.w : (solid ? 1 : .4), h: box ? box.h : (solid ? 1 : .2), fill: solid ? '#000000' : '#FF3D8B', stroke: '#FFFFFF', strokeW: 0, radius: 0, tf: { x: box ? box.x : .5, y: box ? box.y : .5, op: solid ? 60 : 100 } };
    E.change(() => fx().shapes.unshift(o)); E.select({ type: 'shape', id: o.id });
  };
  E.addFx = kind => {
    if (needClips()) return;
    const def = KS.fx.LIST[kind]; if (!def) return; const t = E.T;
    const o = { id: 'f' + KS.uid(), kind, s: +t.toFixed(3), e: +Math.min(total(), t + def[2]).toFixed(3), i: 70, params: {} };
    (KS.fx.PARAMS[kind] || []).forEach(([k, , v]) => o.params[k] = v);
    E.change(() => fx().fxLayers.unshift(o)); E.select({ type: 'fx', id: o.id });
  };
  E.addZoom = shake => { if (needClips()) return; const z = { id: 'z' + KS.uid(), t: +E.T.toFixed(3), d: shake ? .9 : .8, z: shake ? 1.2 : 1.3, shake }; E.change(() => fx().zooms.push(z)); E.select({ type: 'zoom', id: z.id }); };
  E.addMusic = async f => { E.change(() => P().media.music = { path: f.path, name: f.name, vol: .25, s: +E.T.toFixed(3), duration: f.duration || 0 }); await E.flush(); E.loadMusic(); E.select({ type: 'music', id: 'music' }); };
  E.addImage = async f => { const o = { id: 'i' + KS.uid(), path: f.path, name: f.name, s: +E.T.toFixed(3), e: +Math.max(E.T + 1, total()).toFixed(3), size: 22, tf: { x: .82, y: .1 } }; E.change(() => P().media.images.unshift(o)); await E.flush(); E.render(); E.select({ type: 'image', id: o.id }); };
  E.addLut = async f => { await E.flush(); try { const r = await KS.api(`/api/project/${P().id}/lut`, { path: f.path }); E.change(() => fx().lut = r.lut); await KS.fx.loadLut(P().id); E.render(); KS.toast('LUT yüklendi: ' + KS.esc(f.name), 'ok'); } catch (e) { KS.toast(KS.esc(e.message), 'err'); } };
  E.addVideo = async (f, asOverlay) => {
    await E.flush();
    try {
      if (asOverlay && clips().length) { const r = await KS.api(`/api/project/${P().id}/overlay`, { path: f.path, at: E.T }); P().overlays.unshift(r.overlay); E.renderAll(); E.select({ type: 'pip', id: r.overlay.id }); E.render(); return; }
      const close = KS.toast('Video ekleniyor...', '', [], 0);
      const r = await KS.api('/api/local/project', { path: f.path, title: f.title, project: P().id });
      const fresh = await KS.api('/api/project/' + P().id), c = fresh.clips.find(q => q.id === r.clip); close();
      if (c) { const first = !clips().length; clips().push(c); E.loadWave(c); E.renderAll(); E.fit(); E.seek(first ? 0 : E.T); KS.kickJobs(); }
    } catch (e) { KS.toast(KS.esc(e.message), 'err'); }
  };

  /* =========================================================== kesme / düzenleme */
  E.split = () => {
    const s = E.sel;
    if (s && ['text', 'shape', 'fx', 'image', 'pip'].includes(s.type)) {
      const o = selObj(); if (!o || E.T <= o.s + .05 || E.T >= o.e - .05) return KS.toast('Oynatma çizgisini katmanın içine getir', '', [], 1500);
      const n = JSON.parse(JSON.stringify(o)), cut = +E.T.toFixed(3); n.id = o.id[0] + KS.uid();
      E.change(() => { n.s = cut; o.e = cut; if (s.type === 'pip') n.in = (o.in || 0) + (cut - o.s); if (n.kf) Object.values(n.kf).forEach(a => a.forEach(k => k.t = +(k.t - (cut - o.s)).toFixed(3))); const L = listOf(s.type); L.splice(L.indexOf(o), 0, n); });
      return;
    }
    if (!clips().length) return;
    const r = clipAt(E.T), off = (E.T - r.start) * (r.c.speed || 1);
    if (off < .05 || r.c.out - (r.c.in + off) < .05) return KS.toast('Oynatma çizgisini bir klibin içine getir', '', [], 1500);
    let nid;
    E.change(() => { const a = r.c, b = JSON.parse(JSON.stringify(a)); b.id = nid = 'c' + KS.uid(); const cut = +(a.in + off).toFixed(3); b.in = cut; a.out = cut; clips().splice(clips().indexOf(a) + 1, 0, b); });
    E.select({ type: 'video', id: nid });
  };
  E.deleteSel = () => {
    if (E.selKey) { const { type, id, prop, t } = E.selKey, o = listOf(type).find(q => q.id === id); if (o) E.change(() => pSub(prop).forEach(k => { o.kf[k] = (o.kf[k] || []).filter(q => Math.abs(q.t - t) > 1e-3); if (!o.kf[k].length) { o.tf = Object.assign({}, tfOf(type, o), o.tf || {}); delete o.kf[k]; } })); E.selKey = null; return; }
    const s = E.sel; if (!s) return;
    const o = selObj(); if (o && o.locked) return KS.toast('Katman kilitli', '', [], 1200);
    E.change(() => {
      if (s.type === 'video') { const i = clips().findIndex(c => c.id === s.id); if (i >= 0) clips().splice(i, 1); }
      else if (s.type === 'music') P().media.music = null;
      else if (s.type === 'zoom') fx().zooms = fx().zooms.filter(z => z.id !== s.id);
      else if (s.type !== 'cap') { const L = listOf(s.type), i = L.findIndex(q => q.id === s.id); if (i >= 0) L.splice(i, 1); }
    });
    if (s.type === 'music') { music.pause(); E.loadMusic(); }
    E.sel = null; E.renderAll(); E.seek(Math.min(E.T, total()));
  };
  E.duplicate = () => {
    const s = E.sel, o = selObj(); if (!s || !o || ['cap', 'music'].includes(s.type)) return;
    const n = JSON.parse(JSON.stringify(o)); n.id = (o.id || 'x')[0] + KS.uid();
    E.change(() => { if (s.type === 'video') clips().splice(clips().indexOf(o) + 1, 0, n); else if (s.type === 'zoom') fx().zooms.push(n); else { const L = listOf(s.type); L.splice(L.indexOf(o), 0, n); } });
    E.select({ type: s.type, id: n.id });
  };
  E.layerOrder = dir => { const s = E.sel; if (!s || !listOf(s.type)) return; const L = listOf(s.type), i = L.findIndex(q => q.id === s.id), j = dir === 'front' ? 0 : dir === 'back' ? L.length - 1 : i + (dir === 'up' ? -1 : 1); if (i < 0 || j < 0 || j >= L.length || i === j) return; E.change(() => { const [o] = L.splice(i, 1); L.splice(j, 0, o); }); };
  E.inOut = (which, trim) => {
    const s = E.sel, o = selObj(); if (!s || !o || o.locked) return;
    if (s.type === 'video') { const r = TL().find(q => q.c === o); if (!r || !trim) return; const off = (E.T - r.start) * (o.speed || 1); E.change(() => { if (which === 'in') o.in = KS.clamp(+(o.in + off).toFixed(3), 0, o.out - .1); else o.out = KS.clamp(+(o.in + off).toFixed(3), o.in + .1, o.src_dur); }); return; }
    if (o.s == null) return; const T = +E.T.toFixed(3);
    E.change(() => { if (trim) { if (which === 'in') o.s = Math.min(T, o.e - .05); else o.e = Math.max(T, o.s + .05); } else { const len = o.e - o.s; if (which === 'in') { o.s = T; o.e = T + len; } else { o.e = T; o.s = T - len; } } });
  };
  $('#splitBtn').onclick = () => E.split(); $('#delBtn').onclick = () => E.deleteSel(); $('#dupBtn').onclick = () => E.duplicate();
  $('#silenceBtn').onclick = () => {
    if (!P()) return;
    if (!clips().some(c => (c.captions || []).length)) return KS.toast('Boşlukları bulmak için önce altyazı çıkarılmalı', 'err');
    const out = [];
    clips().forEach(c => {
      const ws = (c.captions || []).flatMap(cp => cp.words).filter(w => w.e > c.in && w.s < c.out).sort((a, b) => a.s - b.s);
      if (!ws.length) { out.push(c); return; }
      const iv = []; ws.forEach(w => { const a = Math.max(c.in, w.s - .18), b = Math.min(c.out, w.e + .25); if (iv.length && a - iv[iv.length - 1][1] < .45) iv[iv.length - 1][1] = Math.max(iv[iv.length - 1][1], b); else iv.push([a, b]); });
      iv.filter(([a, b]) => b - a > .15).forEach(([a, b], k) => { const n = k ? JSON.parse(JSON.stringify(c)) : c; if (k) n.id = 'c' + KS.uid(); n.in = +a.toFixed(3); n.out = +b.toFixed(3); out.push(n); });
    });
    const before = total(); E.change(() => P().clips = out);
    KS.toast(`Boşluklar kırpıldı: ${KS.fmt(before)} → ${KS.fmt(total())}`, 'ok', [{ label: 'Geri al', fn: E.undo }]);
  };

  /* =========================================================== ZAMAN ÇİZELGESİ */
  const tlc = $('#tlCanvas'), tl = tlc.getContext('2d'), scroll = $('#tlScroll');
  const RH = { cap: 20, text: 20, shape: 20, fx: 20, image: 20, pip: 22, video: 36, music: 20, zoom: 18, sub: 18 };
  const RULER = 26;
  E.rows = () => {
    if (!P()) return [];
    const rows = [], showProps = l => E.reveal[l.id] || (E.open[l.id] ? PROPS.map(p => p[0]) : null);
    E.layers().forEach((l, i) => { rows.push({ ...l, num: i + 1, h: RH[l.type] }); if (TRANSFORMABLE.includes(l.type)) { const ps = showProps(l); if (ps && ps.length) ps.forEach(p => rows.push({ sub: true, prop: p, h: RH.sub, type: l.type, id: l.id, obj: l.obj })); } });
    let y = RULER; rows.forEach(r => { r.y0 = y; r.y1 = y + r.h; y += r.h; }); E._rowsH = y + 10; return rows;
  };
  const pps = () => (tlc.clientWidth - 20) / Math.max(1, total() || 10);
  const tx2 = t => 10 + t * pps(), x2t = x => KS.clamp((x - 10) / pps(), 0, total());
  E.sizeTimeline = () => {
    if (!P()) return; const rows = E.rows(), vw = scroll.clientWidth || 800, w = Math.max(vw, Math.round((vw - 20) * E.zoom + 20)), h = Math.max(E._rowsH, scroll.clientHeight - 2);
    tlc.style.width = w + 'px'; tlc.style.height = h + 'px'; tlc.width = w * devicePixelRatio; tlc.height = h * devicePixelRatio;
    E.renderTlLayers(rows); E.drawTimeline();
  };
  new ResizeObserver(() => E.sizeTimeline()).observe(scroll);
  const zr = $('#zoomRange');
  zr.oninput = () => { if (!P()) return; const t = E.T, rel = tx2(t) - scroll.scrollLeft; E.zoom = +zr.value; E.sizeTimeline(); scroll.scrollLeft = tx2(t) - rel; };
  scroll.addEventListener('scroll', () => { $('#tlLayers').scrollTop = scroll.scrollTop; E.drawTimeline(); });
  scroll.addEventListener('wheel', e => {
    if (!P()) return;
    if (e.shiftKey || Math.abs(e.deltaX) > Math.abs(e.deltaY)) { e.preventDefault(); scroll.scrollLeft += (e.deltaX || e.deltaY); return; }
    if (e.ctrlKey) return; // Ctrl+tekerlek: dikey kaydır
    e.preventDefault(); const r = tlc.getBoundingClientRect(), mx = e.clientX - r.left, t = x2t(mx), rel = mx - scroll.scrollLeft;
    E.zoom = KS.clamp(E.zoom * (e.deltaY < 0 ? 1.18 : 1 / 1.18), 1, 60); zr.value = E.zoom; KS.paintRange(zr); E.sizeTimeline(); scroll.scrollLeft = tx2(t) - rel;
  }, { passive: false });
  $('#tlLayers').addEventListener('wheel', e => { scroll.scrollTop += e.deltaY; }, { passive: true });

  E.renderTlLayers = rows => {
    const el = $('#tlLayers'); if (!P()) return; rows = rows || E.rows(); const s = E.sel;
    el.innerHTML = `<div class="tl-lrow hdr" style="height:${RULER}px"><span class="c" title="Görünürlük">${SVG.eye}</span><span class="c" title="Solo">${SVG.solo}</span><span class="c" title="Kilit">${SVG.lock}</span><span style="width:24px"></span><span class="num">#</span><span class="tw"></span><span class="nm">Katman Adı</span></div>` +
      rows.map((r, ri) => {
        if (r.sub) {
          const o = r.obj, t = tfAt(r.type, o, E.T - o.s), an = isAnim(o, r.prop);
          const val = r.prop === 'pos' ? `${Math.round(t.x * BW)},${Math.round(t.y * BH)}` : r.prop === 'scale' ? t.scale.toFixed(1) + '%' : r.prop === 'rot' ? '0x' + (t.rot >= 0 ? '+' : '') + t.rot.toFixed(1) + '°' : Math.round(t.op) + '%';
          return `<div class="tl-lrow sub" style="height:${r.h}px" data-ri="${ri}"><span class="nm"><button class="sw-btn" data-twatch="${ri}" style="color:${an ? '#2d8ceb' : '#777'};width:16px;display:inline-grid;vertical-align:middle">${SVG.watch}</button> ${PROPS.find(p => p[0] === r.prop)[1]}</span><span class="val" style="color:#3fa9ff;font:11px ui-monospace,Consolas,monospace">${val}</span></div>`;
        }
        const o = r.obj, isSel = s && s.type === r.type && (s.id === r.id || r.type === 'video'), can = !!o && r.type !== 'music';
        const hk = { cap: 'cap', music: 'music', zoom: 'zoom' }[r.type], off = can ? o.hidden : (hk && hidden(hk));
        return `<div class="tl-lrow ${isSel ? 'sel' : ''}" style="height:${r.h}px" data-ri="${ri}">
          <span class="c ${off ? 'off' : ''}" data-eye="${ri}" title="Göster/gizle">${SVG.eye}</span>
          <span class="c ${can && o.solo ? 'solo-on' : ''}" data-solo="${ri}" title="Solo">${can ? SVG.solo : ''}</span>
          <span class="c ${can && o.locked ? 'lock-on' : ''}" data-lock="${ri}" title="Kilit">${can ? SVG.lock : ''}</span>
          <span class="lab" style="background:${o && o.solid ? LABEL.solid : LABEL[r.type]}"></span><span class="num">${r.num}</span>
          <span class="tw" data-twirl="${ri}">${TRANSFORMABLE.includes(r.type) ? (E.open[r.id] || E.reveal[r.id] ? '▼' : '▶') : ''}</span>
          <span class="nm" title="${KS.esc(r.name)}">${KS.esc(r.name)}</span></div>`;
      }).join('');
    el.scrollTop = scroll.scrollTop;
    $$('.tl-lrow[data-ri]', el).forEach(d => { const r = rows[+d.dataset.ri]; d.onmousedown = e => { if (e.target.closest('[data-eye],[data-solo],[data-lock],[data-twirl],[data-twatch]')) return; if (r.type === 'video') { const c = clips().length ? clipAt(E.T).c : null; E.select(c ? { type: 'video', id: c.id } : null); } else E.select({ type: r.type, id: r.id }); }; });
    $$('[data-eye]', el).forEach(b => b.onclick = () => { const r = rows[+b.dataset.eye]; E.change(() => { if (r.obj && r.type !== 'music') r.obj.hidden = !r.obj.hidden; else { const k = { cap: 'cap', music: 'music', zoom: 'zoom' }[r.type]; if (k) { fx().hide = Object.assign({}, fx().hide); fx().hide[k] = !fx().hide[k]; } } }); });
    $$('[data-solo]', el).forEach(b => b.onclick = () => { const r = rows[+b.dataset.solo]; if (r.obj && r.type !== 'music') E.change(() => r.obj.solo = !r.obj.solo); });
    $$('[data-lock]', el).forEach(b => b.onclick = () => { const r = rows[+b.dataset.lock]; if (r.obj && r.type !== 'music') E.change(() => r.obj.locked = !r.obj.locked); });
    $$('[data-twirl]', el).forEach(b => b.onclick = () => { const r = rows[+b.dataset.twirl]; if (!TRANSFORMABLE.includes(r.type)) return; if (E.reveal[r.id]) delete E.reveal[r.id]; else E.open[r.id] = !E.open[r.id]; E.sizeTimeline(); });
    $$('[data-twatch]', el).forEach(b => b.onclick = () => { const r = rows[+b.dataset.twatch]; E.change(() => toggleWatch(r.type, r.obj, r.prop, E.T - r.obj.s)); });
  };

  const rr = (x, a, b, y0, y1, fill) => { x.fillStyle = fill; x.fillRect(a, y0, Math.max(2, b - a), y1 - y0); };
  E.drawTimeline = () => {
    const p = P(); if (!p || tlc.width < 2) return;
    const x = tl, W = tlc.clientWidth, H = tlc.clientHeight, D = total() || 10, rows = E.rows(), sy = scroll.scrollTop, s = E.sel;
    x.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0); x.clearRect(0, 0, W, H);
    rows.forEach((r, i) => { x.fillStyle = r.sub ? '#191919' : (i % 2 ? '#1d1d1d' : '#202020'); x.fillRect(0, r.y0, W, r.h); x.fillStyle = '#141414'; x.fillRect(0, r.y1 - 1, W, 1); });
    const bar = (r, a, b, label, color, sel) => {
      const y0 = r.y0 + 2, y1 = r.y1 - 3; rr(x, tx2(a), tx2(b), y0, y1, color);
      if (sel) { x.strokeStyle = '#fff'; x.lineWidth = 1.5; x.strokeRect(tx2(a) + .5, y0 + .5, tx2(b) - tx2(a) - 1, y1 - y0 - 1); }
      x.save(); x.beginPath(); x.rect(tx2(a), y0, tx2(b) - tx2(a), y1 - y0); x.clip(); x.fillStyle = '#101010'; x.font = '11px Segoe UI'; x.fillText(label || '', tx2(a) + 5, y1 - 5); x.restore();
    };
    rows.forEach(r => {
      if (r.y1 < sy + RULER || r.y0 > sy + H) return;
      const o = r.obj;
      if (r.sub) { keysOf(o, pSub(r.prop)[0]).forEach(k => { const xx = tx2(o.s + k.t), yy = (r.y0 + r.y1) / 2, sk = E.selKey && E.selKey.id === r.id && E.selKey.prop === r.prop && Math.abs(E.selKey.t - k.t) < 1e-3; x.save(); x.translate(xx, yy); x.rotate(Math.PI / 4); x.fillStyle = sk ? '#2d8ceb' : (k.ease === 'hold' ? '#e8920d' : k.ease && k.ease !== 'lin' ? '#e4d84c' : '#c8c8c8'); x.fillRect(-4, -4, 8, 8); x.strokeStyle = '#000'; x.strokeRect(-4, -4, 8, 8); x.restore(); }); return; }
      x.globalAlpha = o && (o.hidden || (soloOn() && TRANSFORMABLE.concat('fx').includes(r.type) && !o.solo)) ? .35 : 1;
      if (r.type === 'video') {
        let acc = 0;
        clips().forEach((c, i) => {
          const L = clipLen(c), a = tx2(acc), b = tx2(acc + L), sel = s && s.type === 'video' && s.id === c.id;
          rr(x, a, b, r.y0 + 2, r.y1 - 3, sel ? '#7fa8c9' : (i % 2 ? '#93b6b2' : '#a9cbc7'));
          const wv = E.waves[c.source];
          if (wv && wv.length && c.src_dur) { x.save(); x.beginPath(); x.rect(a, r.y0 + 2, b - a, r.y1 - r.y0 - 5); x.clip(); x.fillStyle = 'rgba(30,50,60,.45)'; const mid = (r.y0 + r.y1) / 2 + 3, hh = (r.y1 - r.y0) / 2 - 6, n = wv.length, i0 = Math.floor(c.in / c.src_dur * n), i1 = Math.ceil(c.out / c.src_dur * n), bw = Math.max(1, (b - a) / Math.max(1, i1 - i0)); for (let k = i0; k < i1; k++) { const hgt = Math.max(1, (wv[k] || 0) * hh); x.fillRect(a + (k - i0) * bw, mid - hgt, Math.max(1, bw - .3), hgt * 2); } x.restore(); }
          x.save(); x.beginPath(); x.rect(a, r.y0, b - a, r.h); x.clip(); x.fillStyle = '#0d1a1a'; x.font = '11px Segoe UI'; x.fillText(c.name + ((c.speed || 1) !== 1 ? `  ${Math.round(c.speed * 100)}%` : ''), a + 5, r.y0 + 14); x.restore();
          if (sel) { x.strokeStyle = '#fff'; x.lineWidth = 1.5; x.strokeRect(a + .5, r.y0 + 2.5, b - a - 1, r.y1 - r.y0 - 5); }
          if (E.dragClip && E.dragClip.ins === i) { x.fillStyle = '#2d8ceb'; x.fillRect(a - 2, r.y0, 4, r.h); }
          acc += L;
        });
        if (E.dragClip && E.dragClip.ins === clips().length) { x.fillStyle = '#2d8ceb'; x.fillRect(tx2(acc) - 2, r.y0, 4, r.h); }
        if (fx().transition.type !== 'none') { let a2 = 0; clips().slice(0, -1).forEach(c => { a2 += clipLen(c); x.save(); x.translate(tx2(a2), (r.y0 + r.y1) / 2); x.rotate(Math.PI / 4); x.fillStyle = LABEL.fx; x.fillRect(-5, -5, 10, 10); x.restore(); }); }
      } else if (r.type === 'cap') E.tlCaps().forEach(c => rr(x, tx2(c.s), tx2(c.e), r.y0 + 3, r.y1 - 4, c.words.some(w => w.p < .55) ? '#e8920d' : LABEL.cap));
      else if (r.type === 'music') bar(r, o.s || 0, D, o.name, LABEL.music, s && s.type === 'music');
      else if (r.type === 'zoom') fx().zooms.forEach(z => { const a = tx2(z.t), b = Math.max(a + 6, tx2(z.t + (+z.d || .8))); rr(x, a, b, r.y0 + 3, r.y1 - 3, s && s.type === 'zoom' && s.id === z.id ? '#fff' : LABEL.zoom); });
      else if (o) {
        bar(r, o.s, o.e, r.name, o.solid ? LABEL.solid : LABEL[r.type], s && s.type === r.type && s.id === r.id);
        if (!(E.open[r.id] || E.reveal[r.id])) { const ts = new Set(); Object.values(o.kf || {}).forEach(a => a.forEach(k => ts.add(+k.t.toFixed(3)))); ts.forEach(t => { x.fillStyle = '#e4d84c'; x.save(); x.translate(tx2(o.s + t), r.y1 - 6); x.rotate(Math.PI / 4); x.fillRect(-2.5, -2.5, 5, 5); x.restore(); }); }
        if (o.locked) { x.fillStyle = 'rgba(0,0,0,.35)'; x.fillRect(tx2(o.s), r.y0 + 2, tx2(o.e) - tx2(o.s), r.h - 5); }
      }
      x.globalAlpha = 1;
    });
    // cetvel (yapışkan)
    x.fillStyle = '#262626'; x.fillRect(0, sy, W, RULER);
    const wa = p.work || { a: 0, b: D };
    x.fillStyle = '#5f6c7d'; x.fillRect(tx2(wa.a), sy, tx2(wa.b) - tx2(wa.a), 6); x.fillStyle = '#9aa8ba'; x.fillRect(tx2(wa.a) - 2, sy, 4, 6); x.fillRect(tx2(wa.b) - 2, sy, 4, 6);
    const F = fps(), step = [1 / F, .25, .5, 1, 2, 5, 10, 15, 30, 60, 120].find(q => q * pps() > 60) || 300;
    x.font = '10px Consolas, monospace';
    for (let t = 0; t <= D + 1e-6; t += step) { const xx = tx2(t); x.fillStyle = '#9a9a9a'; x.fillRect(xx, sy + 16, 1, 10); x.fillText(step < 1 ? E.tc(t).slice(-5) : KS.fmt(t), xx + 3, sy + 17); }
    x.fillStyle = '#555'; for (let t = 0; t <= D; t += step / 5) x.fillRect(tx2(t), sy + 21, 1, 5);
    (p.markers || []).forEach(m => { const xx = tx2(m.t); x.fillStyle = '#e4d84c'; x.beginPath(); x.moveTo(xx - 5, sy + 7); x.lineTo(xx + 5, sy + 7); x.lineTo(xx, sy + 14); x.closePath(); x.fill(); });
    const ph = tx2(E.T);
    x.fillStyle = '#2d8ceb'; x.fillRect(ph - .5, sy, 1.5, H);
    x.beginPath(); x.moveTo(ph - 6, sy + 8); x.lineTo(ph + 6, sy + 8); x.lineTo(ph + 6, sy + 18); x.lineTo(ph, sy + 25); x.lineTo(ph - 6, sy + 18); x.closePath(); x.fill();
    if (E.playing && (ph > scroll.scrollLeft + scroll.clientWidth - 40 || ph < scroll.scrollLeft)) scroll.scrollLeft = ph - 60;
    $('#tlInfo').textContent = `${clips().length} klip · ${KS.fmt(total())}`;
  };

  const rowAt = (rows, y) => rows.find(r => y >= r.y0 && y < r.y1);
  tlc.addEventListener('mousedown', e => {
    if (!P()) return;
    const rc = tlc.getBoundingClientRect(), mx = e.clientX - rc.left, my = e.clientY - rc.top, rows = E.rows(), t = x2t(mx), near = tt => Math.abs(tx2(tt) - mx) < 6;
    if (e.button !== 0) return;
    if (my < scroll.scrollTop + RULER) {
      if (E.playing) E.pause(); E.seek(t);
      const mv = ev => E.seek(x2t(ev.clientX - rc.left)), up = () => { removeEventListener('mousemove', mv); removeEventListener('mouseup', up); };
      addEventListener('mousemove', mv); addEventListener('mouseup', up); return;
    }
    const r = rowAt(rows, my); let drag = null;
    if (r && r.sub) {
      const o = r.obj, k = keysOf(o, pSub(r.prop)[0]).find(q => near(o.s + q.t));
      if (k) { E.selKey = { type: r.type, id: r.id, prop: r.prop, t: k.t }; E.sel = { type: r.type, id: r.id }; drag = { kind: 'key', o, prop: r.prop, t0: k.t, mx0: mx }; } else { E.selKey = null; E.seek(t); }
    } else if (r && r.type === 'video') {
      let acc = 0;
      for (const c of clips()) { const L = clipLen(c); if (near(acc) && acc > 0) { drag = { kind: 'cin', c, i0: c.in, mx0: mx }; break; } if (near(acc)) { drag = { kind: 'cin', c, i0: c.in, mx0: mx }; break; } if (near(acc + L)) { drag = { kind: 'cout', c, o0: c.out, mx0: mx }; break; } if (t >= acc && t < acc + L) { drag = { kind: 'cmove', c, mx0: mx }; E.sel = { type: 'video', id: c.id }; break; } acc += L; }
      if (!drag) E.sel = null; E.seek(t);
    } else if (r && r.type === 'zoom') { const z = fx().zooms.find(q => t >= q.t - 6 / pps() && t <= q.t + Math.max(6 / pps(), +q.d || .8)); if (z) { E.sel = { type: 'zoom', id: z.id }; drag = { kind: 'zoom', o: z, t0: z.t, mx0: mx }; } else E.seek(t); }
    else if (r && r.type === 'music' && r.obj) { E.sel = { type: 'music', id: 'music' }; drag = { kind: 'mus', o: r.obj, s0: r.obj.s || 0, mx0: mx }; }
    else if (r && r.type === 'cap') { const i = E.capAt(t); E.sel = { type: 'cap', id: 'cap' }; E.seek(t); if (i >= 0) { E.rt('subs'); setTimeout(() => { const row = $(`.cap[data-ci="${i}"]`); if (row) row.scrollIntoView({ block: 'center' }); }, 30); } }
    else if (r && r.obj && r.obj.s != null) { const o = r.obj; E.sel = { type: r.type, id: r.id }; if (!o.locked) { if (near(o.s)) drag = { kind: 'oS', o }; else if (near(o.e)) drag = { kind: 'oE', o }; else if (t >= o.s && t <= o.e) drag = { kind: 'oM', o, s0: o.s, e0: o.e, mx0: mx }; } if (!drag) E.seek(t); }
    else { E.sel = null; E.seek(t); }
    E.renderControls(); E.renderTlLayers(); E.renderProject(); E.drawTimeline(); E.drawGizmo();
    if (!drag) return;
    if (E.playing) E.pause(); E.beginDrag();
    const cuts = () => clips().reduce((a, c) => (a.push(a[a.length - 1] + clipLen(c)), a), [0]);
    const snapT = tt => { for (const q of [E.T, ...cuts()]) if (Math.abs(tx2(q) - tx2(tt)) < 6) return q; return tt; };
    const mv = ev => {
      const m2 = ev.clientX - rc.left, t2 = x2t(m2), d = drag, dt = (m2 - (d.mx0 ?? m2)) / pps();
      if (d.kind === 'key') { const nt = +KS.clamp(d.t0 + dt, 0, d.o.e - d.o.s).toFixed(3); pSub(d.prop).forEach(k => { const q = (d.o.kf[k] || []).find(z => Math.abs(z.t - E.selKey.t) < 1e-3); if (q) q.t = nt; }); E.selKey.t = nt; }
      if (d.kind === 'cin') d.c.in = +KS.clamp(d.i0 + dt * (d.c.speed || 1), 0, d.c.out - .1).toFixed(3);
      if (d.kind === 'cout') d.c.out = +KS.clamp(d.o0 + dt * (d.c.speed || 1), d.c.in + .1, d.c.src_dur).toFixed(3);
      if (d.kind === 'cmove' && Math.abs(m2 - d.mx0) > 5) { let acc = 0, ins = clips().length; for (let i = 0; i < clips().length; i++) { const L = clipLen(clips()[i]); if (t2 < acc + L / 2) { ins = i; break; } acc += L; } d.ins = ins; E.dragClip = { ins }; }
      if (d.kind === 'zoom') d.o.t = +KS.clamp(snapT(d.t0 + dt), 0, total() - .05).toFixed(3);
      if (d.kind === 'mus') d.o.s = +KS.clamp(snapT(d.s0 + dt), 0, total() - .2).toFixed(3);
      if (d.kind === 'oM') { const len = d.e0 - d.s0, s2 = KS.clamp(snapT(d.s0 + dt), 0, Math.max(0, total() - len)); d.o.s = +s2.toFixed(3); d.o.e = +(s2 + len).toFixed(3); }
      if (d.kind === 'oS') { const ns = +KS.clamp(snapT(t2), 0, d.o.e - .05).toFixed(3), sh = ns - d.o.s; if (d.o.kf) Object.values(d.o.kf).forEach(a => a.forEach(k => k.t = +(k.t - sh).toFixed(3))); if (d.o.in != null && E.sel.type === 'pip') d.o.in = Math.max(0, (d.o.in || 0) + sh); d.o.s = ns; }
      if (d.kind === 'oE') d.o.e = +KS.clamp(snapT(t2), d.o.s + .05, total()).toFixed(3);
      E.render(); E.drawTimeline();
    };
    const up = () => {
      removeEventListener('mousemove', mv); removeEventListener('mouseup', up);
      if (drag.kind === 'cmove' && drag.ins != null) { const i = clips().indexOf(drag.c); let j = drag.ins; if (j > i) j--; if (j !== i) { clips().splice(i, 1); clips().splice(j, 0, drag.c); } }
      E.dragClip = null; E.endDrag(); E.renderAll(); E.seek(Math.min(E.T, total()));
    };
    addEventListener('mousemove', mv); addEventListener('mouseup', up);
  });
  tlc.addEventListener('mousemove', e => {
    if (!P() || e.buttons) return;
    const rc = tlc.getBoundingClientRect(), mx = e.clientX - rc.left, my = e.clientY - rc.top, r = rowAt(E.rows(), my), near = tt => Math.abs(tx2(tt) - mx) < 6; let cur = 'default';
    if (my < scroll.scrollTop + RULER) cur = 'col-resize';
    else if (r && r.type === 'video') { let acc = 0; for (const c of clips()) { const L = clipLen(c); if (near(acc) || near(acc + L)) cur = 'ew-resize'; acc += L; } if (cur === 'default') cur = 'grab'; }
    else if (r && !r.sub && r.obj && r.obj.s != null) { if (near(r.obj.s) || near(r.obj.e)) cur = 'ew-resize'; else if (x2t(mx) >= r.obj.s && x2t(mx) <= r.obj.e) cur = 'grab'; }
    tlc.style.cursor = cur;
  });
  tlc.addEventListener('contextmenu', e => { e.preventDefault(); if (!E.selKey) return; E.ctx(e.clientX, e.clientY, [['Doğrusal', () => setEase('lin')], ['Easy Ease (F9)', () => setEase('ease')], ['Easy Ease Giriş (Shift+F9)', () => setEase('in')], ['Easy Ease Çıkış (Ctrl+Shift+F9)', () => setEase('out')], ['Hold (Ctrl+Alt+H)', () => setEase('hold')], null, ['Keyframe sil', E.deleteSel]]); });
  function setEase(kind) {
    const s = E.selKey, apply = (o, ft) => Object.values(o.kf || {}).forEach(a => a.forEach(k => { if (ft == null || Math.abs(k.t - ft) < 1e-3) k.ease = kind; }));
    if (s) { const o = listOf(s.type).find(q => q.id === s.id); if (o) E.change(() => apply(o, s.t)); return; }
    const o = selObj(); if (o && E.sel && TRANSFORMABLE.includes(E.sel.type)) E.change(() => apply(o, null));
  }
  E.setEase = setEase;
  E.ctx = (x, y, items) => {
    $$('.ctx-menu').forEach(m => m.remove());
    const m = document.createElement('div'); m.className = 'ctx-menu'; m.style.left = x + 'px'; m.style.top = y + 'px';
    items.forEach(it => { if (!it) { m.appendChild(document.createElement('hr')); return; } const d = document.createElement('div'); d.textContent = it[0]; d.onclick = () => { m.remove(); it[1](); }; m.appendChild(d); });
    document.body.appendChild(m); setTimeout(() => addEventListener('mousedown', function h(ev) { if (!m.contains(ev.target)) { m.remove(); removeEventListener('mousedown', h); } }), 0);
  };

  /* =========================================================== proje pencereleri */
  E.newProjectDialog = () => {
    let fmt = KS.state.settings.son_bicim || 'dikey';
    const md = KS.modal(`<h2>Yeni Kompozisyon</h2><p class="msub">Ad ve biçim seç. Biçimi sonra Kompozisyon Ayarları'ndan (Ctrl+K) değiştirebilirsin.</p>
      <div class="field"><label>Kompozisyon adı</label><input class="inp" id="npName" value="Kompozisyon ${(KS.state.projects || []).length + 1}"></div>
      <div class="opt-group" style="margin-top:12px"><label>Biçim</label><div class="opts" id="npFmt">${Object.entries(FORMATS).map(([k, v]) => `<button class="opt" data-v="${k}"><b>${v[2].split(' ')[0]}</b><small>${v[2].split(' ')[1]} · ${v[0]}×${v[1]}</small></button>`).join('')}</div></div>
      <div class="mfoot"><button class="btn ghost" data-close>Vazgeç</button><button class="btn primary" id="npGo">Tamam</button></div>`);
    const paint = () => $$('#npFmt .opt', md.el).forEach(b => b.classList.toggle('active', b.dataset.v === fmt)); paint();
    $$('#npFmt .opt', md.el).forEach(b => b.onclick = () => { fmt = b.dataset.v; paint(); });
    const nm = $('#npName', md.el); nm.select(); nm.onkeydown = e => { if (e.key === 'Enter') $('#npGo', md.el).click(); e.stopPropagation(); };
    $('#npGo', md.el).onclick = async () => { md.close(); const r = await KS.api('/api/project/new', { title: nm.value, format: fmt }); KS.state.settings.son_bicim = fmt; await KS.refresh(); KS.openProject(r.project); };
  };
  E.compSettings = () => {
    if (!P()) return; let fmt = P().format || 'dikey';
    const md = KS.modal(`<h2>Kompozisyon Ayarları</h2><p class="msub">Biçim değişince kadrajlar yeni biçime göre ayarlanır.</p>
      <div class="field"><label>Ad</label><input class="inp" id="csName" value="${KS.esc(P().title)}"></div>
      <div class="opt-group" style="margin-top:12px"><label>Biçim</label><div class="opts" id="csFmt">${Object.entries(FORMATS).map(([k, v]) => `<button class="opt" data-v="${k}"><b>${v[2].split(' ')[0]}</b><small>${v[2].split(' ')[1]} · ${v[0]}×${v[1]}</small></button>`).join('')}</div></div>
      <div class="summary"><span>Süre: <b>${KS.fmt(total())}</b></span><span>Kare hızı: <b>${fps()} fps</b></span><span>Klip: <b>${clips().length}</b></span></div>
      <div class="mfoot"><button class="btn ghost" data-close>Vazgeç</button><button class="btn primary" id="csGo">Tamam</button></div>`);
    const paint = () => $$('#csFmt .opt', md.el).forEach(b => b.classList.toggle('active', b.dataset.v === fmt)); paint();
    $$('#csFmt .opt', md.el).forEach(b => b.onclick = () => { fmt = b.dataset.v; paint(); });
    $('#csName', md.el).onkeydown = e => e.stopPropagation();
    $('#csGo', md.el).onclick = () => {
      const nm = $('#csName', md.el).value.trim(); md.close();
      E.change(() => { if (nm) P().title = nm; if (P().format !== fmt) { P().format = fmt; E.setFormat(); clips().forEach(c => { c.layout = Object.assign({}, c.layout || {}, { mode: fmt === 'dikey' ? ((c.layout || {}).mode === 'split' ? 'split' : 'blur') : 'fit' }); fixLayout(c); }); } });
      $('#edTitle').value = P().title; E.setFormat(); E.fit(); E.renderAll(); E.render();
    };
  };
  E.projectsDialog = async () => {
    await KS.refresh(); const list = KS.state.projects || [];
    const md = KS.modal(`<h2>Projeler</h2><p class="msub">${list.length} proje</p>
      <div class="proj-list" style="max-height:52vh;overflow:auto"><div class="proj-hdr" style="grid-template-columns:64px 1fr 90px 60px 28px"><span></span><span>Ad</span><span>Biçim</span><span>Süre</span><span></span></div>
      ${list.map(p => `<div class="proj-item" style="grid-template-columns:64px 1fr 90px 60px 28px;padding:4px 6px" data-open="${p.id}"><img src="/thumb/${p.id}" style="width:60px;height:34px;object-fit:cover;background:#111" onerror="this.style.visibility='hidden'"><span>${KS.esc(p.title)}<br><small style="color:#888">${p.clips} klip · ${KS.ago(p.updated || p.created)}</small></span><span>${(FORMATS[p.format] || FORMATS.dikey)[2]}</span><span>${KS.fmt(p.duration)}</span><button class="del-btn" data-del="${p.id}">${KS.icon.trash}</button></div>`).join('') || '<div class="hint" style="padding:10px">Henüz proje yok.</div>'}</div>
      <div class="mfoot"><button class="btn ghost" data-close>Kapat</button><button class="btn primary" id="pdNew">Yeni Proje</button></div>`, { wide: true });
    $$('[data-open]', md.el).forEach(d => d.onclick = e => { if (e.target.closest('[data-del]')) return; md.close(); KS.openProject(d.dataset.open); });
    $$('[data-del]', md.el).forEach(b => b.onclick = async e => { e.stopPropagation(); if (!await KS.confirm('Projeyi sil?', 'Düzenlemeler silinecek. Dışa aktardığın videolar silinmez.', 'Sil', true)) return; await KS.api('/api/project/' + b.dataset.del + '?dosya=1', undefined, 'DELETE'); if (P() && P().id === b.dataset.del) E.close(); await KS.refresh(); E.projectsDialog(); });
    $('#pdNew', md.el).onclick = () => { md.close(); E.newProjectDialog(); };
  };

  /* --- Dışa aktar (Ctrl+M) --- */
  $('#exportBtn').onclick = () => E.exportDialog();
  $('#compSettingsBtn').onclick = () => E.compSettings();
  E.exportDialog = () => {
    if (!P()) return KS.toast('Önce bir proje aç', 'err'); if (!clips().length) return KS.toast('Önce video ekle', 'err');
    const s = KS.state.settings, o = { cozunurluk: +s.cozunurluk || 1080, fps: String(s.fps || 'kaynak'), kalite: s.kalite || 'yuksek', ses_dengele: s.ses_dengele !== false, work: false }, src = fps(), wa = P().work;
    const md = KS.modal(`<h2>Dışa Aktar</h2><p class="msub">${BW}×${BH} · ${(FORMATS[P().format] || FORMATS.dikey)[2]} · ${KS.fmt(total())}</p>
      <div class="opt-group"><label>Çözünürlük</label><div class="opts" id="oRes">${[[720, '720p', 'Hızlı'], [1080, '1080p', 'Full HD'], [1440, '2K', '1440p']].map(([v, a, b]) => `<button class="opt" data-v="${v}"><b>${a}</b><small>${b}</small></button>`).join('')}</div></div>
      <div class="opt-group"><label>Kare hızı</label><div class="opts" id="oFps">${[['kaynak', 'Orijinal', src + ' FPS'], ['30', '30', 'FPS'], ['60', '60', 'FPS'], ['90', '90', 'FPS']].map(([v, a, b]) => `<button class="opt" data-v="${v}"><b>${a}</b><small>${b}</small></button>`).join('')}</div></div>
      <div class="note" id="fpsNote" hidden></div>
      <div class="opt-group"><label>Kalite</label><div class="opts" id="oQ"><button class="opt" data-v="yuksek"><b>Yüksek</b><small>Önerilen</small></button><button class="opt" data-v="normal"><b>Normal</b><small>Küçük dosya</small></button></div></div>
      <div class="toggles" style="margin-bottom:10px"><button class="tog ${o.ses_dengele ? 'on' : ''}" id="oLoud">Sesi dengele<i></i></button>${wa ? `<button class="tog" id="oWork">Sadece çalışma alanı (${KS.fmt(wa.a)}–${KS.fmt(wa.b)})<i></i></button>` : ''}</div>
      <div class="mfoot"><button class="btn ghost" data-close>Vazgeç</button><button class="btn primary" id="oGo">Dışa Aktar</button></div>`);
    const paint = () => { $$('#oRes .opt', md.el).forEach(b => b.classList.toggle('active', +b.dataset.v === o.cozunurluk)); $$('#oFps .opt', md.el).forEach(b => b.classList.toggle('active', b.dataset.v === o.fps)); $$('#oQ .opt', md.el).forEach(b => b.classList.toggle('active', b.dataset.v === o.kalite)); const n = $('#fpsNote', md.el), f = +o.fps; if (o.fps !== 'kaynak' && f > src + 1) { n.hidden = false; n.textContent = `Video ${src} FPS. ${f} FPS için ara kare üretilecek: daha akıcı ama dışa aktarma birkaç kat uzun sürer.`; } else n.hidden = true; };
    $$('#oRes .opt', md.el).forEach(b => b.onclick = () => { o.cozunurluk = +b.dataset.v; paint(); });
    $$('#oFps .opt', md.el).forEach(b => b.onclick = () => { o.fps = b.dataset.v; paint(); });
    $$('#oQ .opt', md.el).forEach(b => b.onclick = () => { o.kalite = b.dataset.v; paint(); });
    $('#oLoud', md.el).onclick = e => { o.ses_dengele = !o.ses_dengele; e.currentTarget.classList.toggle('on', o.ses_dengele); };
    const ow = $('#oWork', md.el); if (ow) ow.onclick = e => { o.work = !o.work; e.currentTarget.classList.toggle('on', o.work); };
    $('#oGo', md.el).onclick = async () => { md.close(); await E.flush(); const r = await KS.api(`/api/project/${P().id}/export`, { ...o, work: o.work && wa ? wa : null }); Object.assign(KS.state.settings, { cozunurluk: o.cozunurluk, fps: o.fps, kalite: o.kalite, ses_dengele: o.ses_dengele }); KS.trackJob(r.job); KS.openJobs(); KS.toast('Dışa aktarma başladı.'); };
    paint();
  };

  /* =========================================================== MENÜ ÇUBUĞU */
  function setWork(w) { if (!P()) return; E.change(() => { const wa = Object.assign({ a: 0, b: total() }, P().work || {}); wa[w] = +E.T.toFixed(3); if (wa.b <= wa.a) { if (w === 'a') wa.b = total(); else wa.a = 0; } P().work = wa; }); }
  E.maxPanel = () => {
    const ae = $('.ae'); if (ae.classList.contains('ae-max')) { ae.classList.remove('ae-max'); $$('.ae-max-target').forEach(x => x.classList.remove('ae-max-target')); setTimeout(() => { E.applyView(); E.sizeTimeline(); }, 30); return; }
    const h = document.querySelector('.ae-panel:hover'); if (!h) return; ae.classList.add('ae-max'); h.classList.add('ae-max-target'); setTimeout(() => { E.fit(); E.sizeTimeline(); }, 30);
  };
  const shortcutsModal = () => KS.modal(`<h2>Klavye Kısayolları</h2><p class="msub">After Effects ile aynı</p>${KS.shortcutsHtml()}<div class="mfoot"><button class="btn primary" data-close>Tamam</button></div>`, { wide: true });
  const MENU = () => [
    ['Dosya', [['Yeni Proje...', 'Ctrl+N', E.newProjectDialog], ['Projeleri Aç...', '', E.projectsDialog], null, ['İçe Aktar...', 'Ctrl+I', () => KS.addFile()], null, ['Kaydet', 'Ctrl+S', () => { $('#saveState').classList.add('dirty'); E.flush(); }], ['Dışa Aktar...', 'Ctrl+M', E.exportDialog]]],
    ['Düzenle', [['Geri Al', 'Ctrl+Z', E.undo], ['Yinele', 'Ctrl+Shift+Z', E.redo], null, ['Çoğalt', 'Ctrl+D', E.duplicate], ['Katmanı Böl', 'Ctrl+Shift+D', E.split], ['Sil', 'Delete', E.deleteSel], null, ['Seçimi kaldır', 'F2', () => E.select(null)]]],
    ['Kompozisyon', [['Kompozisyon Ayarları...', 'Ctrl+K', E.compSettings], null, ['Çalışma alanı başı', 'B', () => setWork('a')], ['Çalışma alanı sonu', 'N', () => setWork('b')], ['Çalışma alanını kaldır', '', () => E.change(() => delete P().work)], null, ['Oynat / Durdur', 'Boşluk', E.toggle]]],
    ['Katman', [['Yeni → Yazı', 'Ctrl+Alt+Shift+T', () => E.addText()], ['Yeni → Düz Renk', 'Ctrl+Y', () => E.addShape('rect', null, true)], ['Yeni → Ayar Katmanı', 'Ctrl+Alt+Y', () => E.addFx('glow')], ['Yeni → Dikdörtgen', 'Q', () => E.addShape('rect')], ['Yeni → Elips', 'Q', () => E.addShape('ellipse')], null, ['Öne getir', 'Ctrl+Shift+]', () => E.layerOrder('front')], ['Bir öne', 'Ctrl+]', () => E.layerOrder('up')], ['Bir geri', 'Ctrl+[', () => E.layerOrder('down')], ['En geriye', 'Ctrl+Shift+[', () => E.layerOrder('back')], null, ['Keyframe: Easy Ease', 'F9', () => setEase('ease')], ['Keyframe: Hold', 'Ctrl+Alt+H', () => setEase('hold')]]],
    ['Efekt', [['Zoom vurgusu', '', () => E.addZoom(false)], ['Sarsıntılı zoom', '', () => E.addZoom(true)], null, ...Object.entries(KS.fx.LIST).slice(0, 14).map(([k, v]) => [v[0], '', () => E.addFx(k)]), null, ['Tüm efektler...', '', () => E.rt('fx')]]],
    ['Görünüm', [['Yakınlaştır', '.', () => E.zoomView(1.25)], ['Uzaklaştır', ',', () => E.zoomView(.8)], ['Sığdır', 'Shift+/', E.fit], null, ['Tam kalite', '', () => { $('#qualSel').value = '1'; $('#qualSel').onchange({ target: $('#qualSel') }); }], ['Yarım kalite', '', () => { $('#qualSel').value = '0.5'; $('#qualSel').onchange({ target: $('#qualSel') }); }], null, ['Paneli büyüt', '`', E.maxPanel]]],
    ['Pencere', [['Proje', '', () => E.lt('project')], ['Efekt Kontrolleri', 'F3', () => E.lt('controls')], ['Efektler ve Ön Ayarlar', '', () => E.rt('fx')], ['Altyazı', '', () => E.rt('subs')], ['Karakter', '', () => E.rt('style')]]],
    ['Yardım', [['Klavye kısayolları', 'F1', shortcutsModal]]],
  ];
  const mb = $('#aeMenubar');
  (() => {
    const menus = MENU();
    mb.innerHTML = menus.map(([n, items], i) => `<div class="mi" data-mi="${i}">${n}<div class="ae-drop">${items.map((it, j) => it ? `<div data-mj="${j}">${it[0]}<span>${it[1]}</span></div>` : '<hr>').join('')}</div></div>`).join('');
    $$('.mi', mb).forEach(m => {
      m.onmousedown = e => { if (e.target.closest('[data-mj]')) return; const open = m.classList.contains('open'); $$('.mi', mb).forEach(x => x.classList.remove('open')); if (!open) m.classList.add('open'); };
      m.onmouseenter = () => { if ($('.mi.open', mb)) { $$('.mi', mb).forEach(x => x.classList.remove('open')); m.classList.add('open'); } };
      $$('[data-mj]', m).forEach(d => d.onclick = () => { $$('.mi', mb).forEach(x => x.classList.remove('open')); const it = MENU()[+m.dataset.mi][1][+d.dataset.mj]; if (!P() && !['Yeni Proje...', 'Projeleri Aç...', 'İçe Aktar...', 'Klavye kısayolları'].includes(it[0])) return KS.toast('Önce bir proje aç', '', [], 1500); it[2](); });
    });
  })();
  addEventListener('mousedown', e => { if (!e.target.closest('#aeMenubar')) $$('.mi', mb).forEach(x => x.classList.remove('open')); });

  /* =========================================================== KISAYOLLAR (After Effects ile aynı) */
  const frame = () => 1 / fps();
  const jumpKey = dir => {
    const pts = new Set((P().markers || []).map(m => m.t)), o = selObj();
    const ls = o && o.kf ? [o] : [...fx().texts, ...fx().shapes, ...P().media.images, ...P().overlays];
    ls.forEach(l => Object.values(l.kf || {}).forEach(a => a.forEach(k => pts.add(+(l.s + k.t).toFixed(3)))));
    const arr = [...pts].sort((a, b) => a - b), t = dir < 0 ? arr.filter(q => q < E.T - 1e-3).pop() : arr.find(q => q > E.T + 1e-3); if (t != null) E.seek(t);
  };
  const toggleKeyProp = p => { const s = E.sel, o = selObj(); if (!s || !o || !TRANSFORMABLE.includes(s.type)) return; E.change(() => { if (!isAnim(o, p)) toggleWatch(s.type, o, p, E.T - o.s); else toggleKeyAt(s.type, o, p, E.T - o.s); }); E.reveal[s.id] = [...new Set([...(E.reveal[s.id] || []), p])]; E.sizeTimeline(); };
  const revealProp = (p, add) => { const s = E.sel; if (!s || !TRANSFORMABLE.includes(s.type)) return; const cur = E.reveal[s.id] || []; E.reveal[s.id] = add ? [...new Set([...cur, p])] : (cur.length === 1 && cur[0] === p ? [] : [p]); if (!E.reveal[s.id].length) delete E.reveal[s.id]; E.open[s.id] = false; E.sizeTimeline(); };
  E.onKey = e => {
    const k = e.key, kl = k.toLowerCase(), c = e.ctrlKey || e.metaKey, sh = e.shiftKey, alt = e.altKey, code = e.code, stop = () => e.preventDefault();
    if (c && kl === 'n') { stop(); return E.newProjectDialog(); }
    if (c && kl === 'i') { stop(); return KS.addFile(); }
    if (k === 'F1') { stop(); return shortcutsModal(); }
    if (!P()) return;
    if (k === ' ') { stop(); if (!e.repeat) E.toggle(); return; }
    if (c && alt && sh && kl === 't') { stop(); return E.addText(); }
    if (c && alt && kl === 'y') { stop(); return E.addFx('glow'); }
    if (c && alt && kl === 'h') { stop(); return setEase('hold'); }
    if (c && sh && kl === 'z') { stop(); return E.redo(); }
    if (c && sh && kl === 'd') { stop(); return E.split(); }
    if (c && sh && code === 'BracketRight') { stop(); return E.layerOrder('front'); }
    if (c && sh && code === 'BracketLeft') { stop(); return E.layerOrder('back'); }
    if (c && sh && k === 'F9') { stop(); return setEase('out'); }
    if (c) {
      if (kl === 'z') { stop(); return E.undo(); } if (kl === 'y') { stop(); return E.addShape('rect', null, true); }
      if (kl === 'd') { stop(); return E.duplicate(); } if (kl === 's') { stop(); $('#saveState').classList.add('dirty'); return E.flush().then(() => KS.toast('Kaydedildi', 'ok', [], 1000)); }
      if (kl === 'm' || kl === 'e') { stop(); return E.exportDialog(); } if (kl === 'k') { stop(); return E.compSettings(); } if (kl === 't') { stop(); return E.setTool('text'); }
      if (code === 'BracketRight') { stop(); return E.layerOrder('up'); } if (code === 'BracketLeft') { stop(); return E.layerOrder('down'); }
      if (k === 'ArrowRight') { stop(); return E.seek(E.T + frame()); } if (k === 'ArrowLeft') { stop(); return E.seek(E.T - frame()); }
      return;
    }
    if (alt && sh && ['p', 's', 'r', 't'].includes(kl)) { stop(); return toggleKeyProp({ p: 'pos', s: 'scale', r: 'rot', t: 'op' }[kl]); }
    if (alt && code === 'BracketLeft') { stop(); return E.inOut('in', true); }
    if (alt && code === 'BracketRight') { stop(); return E.inOut('out', true); }
    if (k === 'F9') { stop(); return setEase(sh ? 'in' : 'ease'); }
    if (k === 'F2') return E.select(null);
    if (k === 'F3') { stop(); return E.lt('controls'); }
    if (k === 'Delete' || k === 'Backspace') { stop(); return E.deleteSel(); }
    if (k === 'PageDown') { stop(); return E.seek(E.T + frame() * (sh ? 10 : 1)); }
    if (k === 'PageUp') { stop(); return E.seek(E.T - frame() * (sh ? 10 : 1)); }
    if (k === 'ArrowRight' && !alt) { stop(); return E.seek(E.T + frame() * (sh ? 10 : 1)); }
    if (k === 'ArrowLeft' && !alt) { stop(); return E.seek(E.T - frame() * (sh ? 10 : 1)); }
    if (k === 'Home') { stop(); return E.seek(0); } if (k === 'End') { stop(); return E.seek(total()); }
    if (code === 'BracketLeft' && !alt) return E.inOut('in', false);
    if (code === 'BracketRight' && !alt) return E.inOut('out', false);
    if (code === 'NumpadMultiply') { stop(); return E.change(() => P().markers.push({ t: +E.T.toFixed(3) })); }
    if (k === '=' || k === '+' || code === 'NumpadAdd') { zr.value = Math.min(60, E.zoom * 1.4); zr.oninput(); KS.paintRange(zr); return; }
    if (k === '-' || code === 'NumpadSubtract') { zr.value = Math.max(1, E.zoom / 1.4); zr.oninput(); KS.paintRange(zr); return; }
    if (k === '.') return E.zoomView(1.25); if (k === ',') return E.zoomView(.8);
    if (k === '?' || (sh && code === 'Slash')) return E.fit();
    if (code === 'Backquote') { stop(); return E.maxPanel(); }
    if (sh) { if (['p', 's', 'r', 't'].includes(kl)) return revealProp({ p: 'pos', s: 'scale', r: 'rot', t: 'op' }[kl], true); return; }
    if (alt) return;
    switch (kl) {
      case 'v': return E.setTool('select'); case 'h': return E.setTool('hand'); case 'z': return E.setTool('zoom'); case 'w': return E.setTool('rotate');
      case 'q': return E.setTool(E.tool === 'rect' ? 'ellipse' : 'rect');
      case 'p': return revealProp('pos'); case 's': return revealProp('scale'); case 'r': return revealProp('rot'); case 't': return revealProp('op');
      case 'u': { const s = E.sel, o = selObj(); if (s && o && TRANSFORMABLE.includes(s.type)) { const an = PROPS.map(p => p[0]).filter(p => isAnim(o, p)); if (E.reveal[s.id] && E.reveal[s.id].join() === an.join()) delete E.reveal[s.id]; else E.reveal[s.id] = an; E.sizeTimeline(); } return; }
      case 'b': return setWork('a'); case 'n': return setWork('b');
      case 'i': { const o = selObj(); if (o && o.s != null) E.seek(o.s); else if (E.sel && E.sel.type === 'video') { const r = TL().find(q => q.c.id === E.sel.id); if (r) E.seek(r.start); } return; }
      case 'o': { const o = selObj(); if (o && o.e != null) E.seek(o.e - .001); else if (E.sel && E.sel.type === 'video') { const r = TL().find(q => q.c.id === E.sel.id); if (r) E.seek(r.start + r.len - .001); } return; }
      case 'j': return jumpKey(-1); case 'k': return jumpKey(1);
      case 'escape': return E.select(null);
    }
  };
  addEventListener('keydown', e => { if (e.key === ' ' && KS.page === 'editor') E.spaceHeld = !(/INPUT|TEXTAREA/.test(document.activeElement?.tagName) || document.activeElement?.isContentEditable); });
  addEventListener('keyup', e => { if (e.key === ' ') E.spaceHeld = false; });
  E.showNoProject();
})();
