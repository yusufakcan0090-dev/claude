/* Kesit Stüdyosu — Editör */
(() => {
  const E = KS.editor = { project: null, sel: null, history: [], future: [], zoom: 1 };
  const video = $('#srcVideo'), music = $('#musicAudio');
  const prev = $('#preview'), pctx = prev.getContext('2d');
  const PW = 540, PH = 960, K = 0.5; // önizleme = 1080x1920'nin yarısı

  const DEF_STYLE = { font: 'poppins-black', size: 92, color: '#FFFFFF', hl: '#FFE14D', outline: '#000000', outlineW: 9, shadow: true, y: 68, upper: true, karaoke: true, anim: true, maxWords: 3 };
  const DEF_FX = { preset: 'none', bright: 0, contrast: 0, sat: 0, temp: 0, vignette: false, grain: false, glow: false, rgb: false, sharpen: false, mirror: false, speed: 1, fadeIn: false, fadeOut: false, zooms: [], texts: [], hide: {}, fxLayers: [], transition: { type: 'none', d: .4 }, lut: null };
  const DEF_LAYOUT = { mode: 'split', split: 0.4, face: { x: 0, y: 0, w: .3, h: .3 }, game: { x: .2, y: 0, w: .6, h: 1 }, crop: { x: .34, y: 0, w: .32, h: 1 } };
  const FONT_CSS = { anton: 'Anton', poppins: 'PoppinsXB', 'poppins-black': 'PoppinsBlk', bangers: 'Bangers' };
  const FONT_NAME = { 'poppins-black': 'Poppins Black', poppins: 'Poppins', anton: 'Anton', bangers: 'Bangers' };

  const CAP_PRESETS = [
    { name: 'Sarı Vurgu', s: { font: 'poppins-black', color: '#FFFFFF', hl: '#FFE14D', outline: '#000000', outlineW: 9, size: 92, karaoke: true, upper: true, shadow: true } },
    { name: 'TikTok', s: { font: 'poppins', color: '#FFFFFF', hl: '#22D3EE', outline: '#000000', outlineW: 8, size: 86, karaoke: true, upper: false, shadow: true } },
    { name: 'Komik', s: { font: 'bangers', color: '#FFFFFF', hl: '#3DFFA2', outline: '#000000', outlineW: 10, size: 104, karaoke: true, upper: true, shadow: true } },
    { name: 'Sert', s: { font: 'anton', color: '#FFFFFF', hl: '#FF3B3B', outline: '#000000', outlineW: 8, size: 112, karaoke: true, upper: true, shadow: false } },
    { name: 'Neon', s: { font: 'poppins-black', color: '#FFFFFF', hl: '#FF3D8B', outline: '#5B2BFF', outlineW: 10, size: 92, karaoke: true, upper: true, shadow: true } },
    { name: 'Sade', s: { font: 'poppins', color: '#FFFFFF', hl: '#FFFFFF', outline: '#000000', outlineW: 6, size: 76, karaoke: false, upper: false, shadow: true } },
  ];
  const FX_PRESETS = [
    ['none', 'Normal', ''], ['sinematik', 'Sinematik', 'contrast(1.12) saturate(.88) brightness(.98)'],
    ['canli', 'Canlı', 'saturate(1.45) contrast(1.08)'], ['sb', 'Siyah-Beyaz', 'grayscale(1) contrast(1.22)'],
    ['vintage', 'Vintage', 'sepia(.38) contrast(.95) saturate(.85) brightness(1.03)'], ['soguk', 'Soğuk', 'saturate(1.05) hue-rotate(-12deg) brightness(1.02)'],
    ['sicak', 'Sıcak', 'sepia(.22) saturate(1.2)'], ['neon', 'Neon', 'saturate(1.6) contrast(1.15) hue-rotate(8deg)'],
  ];
  const SWATCH = ['#FFFFFF', '#FFE14D', '#FF3D8B', '#22D3EE', '#3DFFA2', '#FF3B3B', '#B388FF', '#FF8A00', '#000000'];

  /* ====================================================== yükleme */
  E.load = async pid => {
    if (E.project && E.project.id === pid) { E.onShow(); return; }
    await E.flush();
    const p = await KS.api('/api/project/' + pid);
    p.style = Object.assign({}, DEF_STYLE, p.style || {});
    p.effects = Object.assign({}, DEF_FX, p.effects || {});
    p.effects.zooms = (p.effects.zooms || []).map(z => Object.assign({ id: 'z' + KS.uid(), d: .8, z: 1.25, shake: false }, z));
    p.effects.texts = (p.effects.texts || []).map(t => Object.assign({ id: 't' + KS.uid(), y: 18, size: 80, color: '#FFFFFF', box: true, boxColor: '#FF3D8B', anim: 'pop', upper: true, font: 'poppins-black' }, t));
    p.layout = Object.assign({}, DEF_LAYOUT, p.layout || {});
    p.effects.fxLayers = (p.effects.fxLayers || []).map(f => Object.assign({ id: 'f' + KS.uid(), i: 70, params: {} }, f));
    p.effects.transition = Object.assign({ type: 'none', d: .4 }, p.effects.transition || {});
    p.media = Object.assign({ music: null, images: [] }, p.media || {});
    p.media.images = (p.media.images || []).map(im => Object.assign({ id: 'i' + KS.uid(), name: (im.path || '').split(/[\\/]/).pop(), s: 0, e: p.duration, pos: 'tr', size: 22, opacity: 1 }, im));
    if (p.media.music) p.media.music = Object.assign({ name: (p.media.music.path || '').split(/[\\/]/).pop(), vol: .25, s: 0 }, p.media.music);
    p.captions = p.captions || [];
    E.project = p; E.sel = null; E.history = []; E.future = []; E.wave = null;
    $('#editorEmpty').hidden = true; $('#editor').hidden = false;
    $('#edTitle').value = p.title;
    video.src = '/media/project/' + pid;
    video.load();
    E.loadMusic();
    E.imgCache = {};
    E.fixRects();
    KS.fx.lut = null; if (p.effects.lut) KS.fx.loadLut(pid).then(() => E.render());
    E.renderAll();
    KS.api(`/api/project/${pid}/wave`).then(w => { E.wave = w; E.drawTimeline(); });
    await document.fonts.ready;
    E.render();
  };
  E.close = () => {
    E.project = null; video.removeAttribute('src'); video.load();
    $('#editorEmpty').hidden = false; $('#editor').hidden = true;
  };
  E.onShow = () => { setTimeout(() => { E.sizeTimeline(); E.drawSrc(); E.render(); E.setRtInk(); }, 60); };
  E.renderAll = () => {
    E.renderLayout(); E.renderSubs(); E.renderStyle(); E.renderFx(); E.renderLayers(); E.renderTlLayers();
    $('#compTab').textContent = 'Kompozisyon: ' + (E.project.title || '').slice(0, 28);
    const rs = { 720: '720×1280', 1080: '1080×1920', 1440: '1440×2560' }[+KS.state.settings.cozunurluk || 1080];
    $('#compRes').textContent = rs + ' · ' + Math.round(E.project.fps || 30) + ' fps';
    $('#aeFps').textContent = Math.round(E.project.fps || 30) + ' fps';
    $('#tlCompName').textContent = (E.project.title || '').slice(0, 30);
    E.sizeTimeline(); E.updateUndo(); E.setRtInk();
  };

  video.addEventListener('loadeddata', () => { E.drawSrc(); E.render(); });
  video.addEventListener('seeked', () => { E.drawSrc(); E.render(); E.drawTimeline(); E.renderFxThumbs(); });

  /* ====================================================== geçmiş & kayıt */
  const snap = () => JSON.stringify(['segments', 'layout', 'style', 'captions', 'effects', 'media'].map(k => E.project[k]));
  const restore = s => { const a = JSON.parse(s);['segments', 'layout', 'style', 'captions', 'effects', 'media'].forEach((k, i) => E.project[k] = a[i]); };
  E.change = (fn, { soft } = {}) => {
    const before = snap();
    fn();
    if (snap() === before) return;
    E.history.push(before); if (E.history.length > 120) E.history.shift();
    E.future = [];
    E.dirty(); if (!soft) E.renderAll(); E.render(); E.drawTimeline();
  };
  E.beginDrag = () => { E._dragSnap = snap(); };
  E.endDrag = () => {
    if (E._dragSnap && E._dragSnap !== snap()) { E.history.push(E._dragSnap); E.future = []; E.dirty(); E.updateUndo(); }
    E._dragSnap = null;
  };
  E.undo = () => { if (!E.history.length) return; E.future.push(snap()); restore(E.history.pop()); E.after(); KS.toast('↶ Geri alındı', '', [], 1200); };
  E.redo = () => { if (!E.future.length) return; E.history.push(snap()); restore(E.future.pop()); E.after(); };
  E.after = () => { E.fixRects(); E.renderAll(); E.render(); E.drawTimeline(); E.dirty(); E.flush().then(E.loadMusic); };
  E.updateUndo = () => { $('#undoBtn').disabled = !E.history.length; $('#redoBtn').disabled = !E.future.length; };

  let saveT = null;
  E.dirty = () => {
    $('#saveState').classList.add('dirty'); $('#saveState').lastChild.textContent = 'Kaydediliyor...';
    clearTimeout(saveT); saveT = setTimeout(E.flush, 650);
    E.updateUndo();
  };
  E.flush = async () => {
    clearTimeout(saveT);
    const p = E.project; if (!p) return;
    if (!$('#saveState').classList.contains('dirty')) return;
    try {
      await KS.api('/api/project/' + p.id, { title: p.title, segments: p.segments, layout: p.layout, style: p.style, captions: p.captions, effects: p.effects, media: p.media });
      $('#saveState').classList.remove('dirty'); $('#saveState').lastChild.textContent = 'Kaydedildi';
    } catch (e) { $('#saveState').lastChild.textContent = 'Kaydedilemedi!'; }
  };
  window.addEventListener('beforeunload', () => E.flush());
  $('#edTitle').onchange = e => { E.project.title = e.target.value.trim() || 'Kesit'; E.dirty(); };
  $('#undoBtn').onclick = E.undo; $('#redoBtn').onclick = E.redo;
  $('#edBack').onclick = () => { KS.go('finder'); KS.finder.tab('projects'); };
  $('#helpBtn').onclick = () => KS.modal(`<h2>Kısayollar</h2><p class="msub">İşini hızlandıran tuşlar</p>${KS.shortcutsHtml()}<div class="mfoot"><button class="btn primary" data-close>Tamam</button></div>`);

  /* ====================================================== zaman yardımcıları */
  const segs = () => E.project.segments.slice().sort((a, b) => a.start - b.start);
  const speed = () => KS.clamp(+E.project.effects.speed || 1, .5, 2);
  const outDur = () => segs().reduce((s, g) => s + g.end - g.start, 0) / speed();
  const mapClamp = t => { let off = 0; for (const s of segs()) { if (t <= s.end + 1e-3) return off + Math.max(0, Math.min(t, s.end) - s.start); off += s.end - s.start; } return off; };
  const toOut = t => mapClamp(t) / speed();
  const cutTimes = () => { const out = []; let acc = 0; const ss = segs(); for (let i = 0; i < ss.length - 1; i++) { acc += ss[i].end - ss[i].start; out.push(acc / speed()); } return out; };
  const inSeg = t => segs().find(s => t >= s.start - 1e-3 && t < s.end - 1e-3);
  const now = () => video.currentTime || 0;
  E.seek = t => { video.currentTime = KS.clamp(t, 0, E.project.duration - 0.02); E.render(); E.drawTimeline(); E.syncMusic(true); };

  /* ====================================================== oynatma */
  E.play = () => {
    if (!E.project) return;
    const t = now();
    const ss = segs();
    if (!inSeg(t)) { const nx = ss.find(s => s.start > t) || ss[0]; video.currentTime = nx.start; }
    if (t >= ss[ss.length - 1].end - 0.05) video.currentTime = ss[0].start;
    video.playbackRate = speed();
    video.play().catch(() => { }); $("#page-editor").classList.add("playing");
    E.syncMusic(true);
    loop();
  };
  E.pause = () => { video.pause(); music.pause(); $('#page-editor').classList.remove('playing'); E.render(); E.drawTimeline(); };
  E.toggle = () => video.paused ? E.play() : E.pause();
  $('#playBtn').onclick = E.toggle;
  $('#prevSeg').onclick = () => { const t = now(), ss = segs(); const p = ss.filter(s => s.start < t - 0.3).pop(); E.seek(p ? p.start : 0); };
  $('#nextSeg').onclick = () => { const t = now(); const n = segs().find(s => s.start > t + 0.05); if (n) E.seek(n.start); };
  function loop() {
    if (video.paused) { $('#page-editor').classList.remove('playing'); return; }
    const t = now(), ss = segs();
    const cur = inSeg(t);
    if (!cur) {
      const nx = ss.find(s => s.start > t);
      if (nx) video.currentTime = nx.start; else { E.pause(); video.currentTime = ss[ss.length - 1].end - 0.03; }
    }
    E.render(); E.drawTimeline(); E.syncMusic(); E.highlightCaption();
    requestAnimationFrame(loop);
  }
  E.loadMusic = () => {
    const m = E.project && E.project.media.music;
    const src = m ? `/media/file/${E.project.id}/music?v=${encodeURIComponent(m.path)}` : '';
    if (music.dataset.src !== src) { music.dataset.src = src; if (src) music.src = src; else music.removeAttribute('src'); }
  };
  E.syncMusic = force => {
    const m = E.project && E.project.media.music;
    if (!m || !music.src) return;
    if (hidden('music')) { if (!music.paused) music.pause(); return; }
    music.volume = KS.clamp(+m.vol || .25, 0, 1);
    const pos = toOut(now()) - toOut(+m.s || 0);
    if (video.paused || pos < 0) { if (!music.paused) music.pause(); return; }
    const dur = music.duration || 1e9;
    const target = pos % dur;
    if (force || Math.abs(music.currentTime - target) > 0.3) music.currentTime = target;
    if (music.paused) music.play().catch(() => { });
  };

  /* ====================================================== önizleme çizimi */
  const noise = document.createElement('canvas'); noise.width = noise.height = 160;
  (() => { const x = noise.getContext('2d'), d = x.createImageData(160, 160); for (let i = 0; i < d.data.length; i += 4) { const v = Math.random() * 255; d.data[i] = d.data[i + 1] = d.data[i + 2] = v; d.data[i + 3] = 255; } x.putImageData(d, 0, 0); })();
  const fxFilter = fx => {
    const pre = (FX_PRESETS.find(p => p[0] === fx.preset) || [])[2] || '';
    let f = pre;
    if (+fx.bright) f += ` brightness(${1 + fx.bright / 150})`;
    if (+fx.contrast) f += ` contrast(${1 + fx.contrast / 100})`;
    if (+fx.sat) f += ` saturate(${Math.max(0, 1 + fx.sat / 100)})`;
    if (+fx.temp > 0) f += ` sepia(${fx.temp / 300}) saturate(${1 + fx.temp / 400})`;
    if (+fx.temp < 0) f += ` hue-rotate(${fx.temp / 8}deg)`;
    return f.trim() || 'none';
  };
  const px = (r, W, H) => [r.x * W, r.y * H, r.w * W, r.h * H];

  function drawLayout(x, filter) {
    const p = E.project, L = p.layout, W = video.videoWidth || p.width, H = video.videoHeight || p.height;
    x.filter = filter;
    if (L.mode === 'crop') {
      x.drawImage(video, ...px(L.crop, W, H), 0, 0, PW, PH);
    } else if (L.mode === 'blur') {
      const sc = Math.max(PW / W, PH / H);
      x.filter = (filter === 'none' ? '' : filter) + ' blur(14px) brightness(.9) saturate(1.15)';
      x.drawImage(video, (PW - W * sc) / 2, (PH - H * sc) / 2, W * sc, H * sc);
      x.filter = filter;
      const fh = PW * H / W;
      x.drawImage(video, 0, (PH - fh) / 2, PW, fh);
    } else {
      const top = Math.round(PH * L.split);
      x.drawImage(video, ...px(L.face, W, H), 0, 0, PW, top);
      x.drawImage(video, ...px(L.game, W, H), 0, top, PW, PH - top);
    }
    x.filter = 'none';
  }

  function zoomAt(tOut) {
    let z = 1, shake = 0;
    for (const zz of E.project.effects.zooms) {
      const a = toOut(zz.t), b = a + (+zz.d || .8);
      if (tOut >= a && tOut <= b) {
        const env = Math.min(1, (tOut - a) / .12, (b - tOut) / .2);
        z += Math.max((+zz.z || 1.25) - 1, zz.shake ? .06 : 0) * env;
        if (zz.shake) shake = 1;
      }
    }
    return { z, shake };
  }

  E.capBoxes = []; E.textBoxes = [];
  E.render = () => {
    const p = E.project; if (!p || !video.videoWidth) return;
    const fx = p.effects, x = pctx, t = now(), tOut = toOut(t);
    x.save();
    x.fillStyle = '#000'; x.fillRect(0, 0, PW, PH);
    // zoom & sarsıntı (videoya uygulanır, yazılara değil)
    const { z, shake } = hidden('zoom') ? { z: 1, shake: 0 } : zoomAt(tOut);
    x.save();
    if (z !== 1 || fx.mirror) {
      x.translate(PW / 2, PH / 2);
      x.scale(z * (fx.mirror ? -1 : 1), z);
      x.translate(-PW / 2 + (shake ? Math.sin(tOut * 53) * PW * .012 : 0), -PH / 2 + (shake ? Math.cos(tOut * 47) * PH * .008 : 0));
    }
    drawLayout(x, fxFilter(fx));
    x.restore();
    if (fx.lut && KS.fx.lut) KS.fx.applyLut(x, PW, PH, (fx.lut.mix ?? 100) / 100);
    if (fx.glow) { x.save(); x.globalCompositeOperation = 'screen'; x.globalAlpha = .38; x.filter = 'blur(9px)'; x.drawImage(prev, 0, 0); x.restore(); }
    if (fx.rgb) { x.save(); x.globalCompositeOperation = 'screen'; x.globalAlpha = .22; x.drawImage(prev, -3, 0); x.drawImage(prev, 3, 0); x.restore(); }
    if (fx.sharpen) { x.save(); x.globalAlpha = .12; x.globalCompositeOperation = 'overlay'; x.drawImage(prev, 0, 0); x.restore(); }
    if (fx.vignette) { const g = x.createRadialGradient(PW / 2, PH / 2, PH * .25, PW / 2, PH / 2, PH * .62); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(0,0,0,.62)'); x.fillStyle = g; x.fillRect(0, 0, PW, PH); }
    if (fx.grain) { x.save(); x.globalAlpha = .09; x.globalCompositeOperation = 'overlay'; const ox = Math.random() * 160, oy = Math.random() * 160; x.translate(-ox, -oy); x.fillStyle = x.createPattern(noise, 'repeat'); x.fillRect(0, 0, PW + 160, PH + 160); x.restore(); }
    // zamanlı efektler ve geçişler
    if (!hidden('fx')) {
      for (const L of fx.fxLayers) {
        if (t < L.s || t > L.e) continue;
        const a = toOut(L.s), D = Math.max(.05, toOut(L.e) - a);
        KS.fx.apply(x, L.kind, tOut - a, D, (+L.i || 70) / 100, L.params || {}, PW, PH);
      }
      const tr = fx.transition || {};
      if (tr.type && tr.type !== 'none') {
        const d = KS.clamp(+tr.d || .4, .15, 1.5);
        for (const T of cutTimes()) if (Math.abs(tOut - T) < d / 2) KS.fx.apply(x, 'tr_' + tr.type, tOut - (T - d / 2), d, 1, {}, PW, PH);
      }
    }
    // resim katmanları
    for (const im of p.media.images) {
      if (t < im.s || t > im.e || hidden('image')) continue;
      const img = E.getImg(im); if (!img || !img.naturalWidth) continue;
      const w = PW * (+im.size || 22) / 100, h = w * img.naturalHeight / img.naturalWidth, m = 20;
      const pos = { tl: [m, m], tr: [PW - w - m, m], bl: [m, PH - h - m], br: [PW - w - m, PH - h - m], c: [(PW - w) / 2, (PH - h) / 2] }[im.pos || 'tr'];
      x.globalAlpha = KS.clamp(+im.opacity || 1, 0, 1); x.drawImage(img, pos[0], pos[1], w, h); x.globalAlpha = 1;
    }
    // altyazı & yazılar
    E.capBoxes = []; E.textBoxes = [];
    if (!hidden('cap')) drawCaption(x, t);
    if (!hidden('text')) drawTexts(x, t, tOut);
    // fade
    const total = outDur();
    let fade = 0;
    if (fx.fadeIn && tOut < .5) fade = 1 - tOut / .5;
    if (fx.fadeOut && tOut > total - .6) fade = Math.max(fade, (tOut - (total - .6)) / .6);
    if (fade > 0) { x.fillStyle = `rgba(0,0,0,${KS.clamp(fade, 0, 1)})`; x.fillRect(0, 0, PW, PH); }
    if (E.dragY != null) { x.strokeStyle = 'rgba(255,255,255,.8)'; x.setLineDash([8, 6]); x.lineWidth = 2; x.beginPath(); x.moveTo(10, E.dragY); x.lineTo(PW - 10, E.dragY); x.stroke(); x.setLineDash([]); }
    x.restore();
    $('#tcCur').textContent = KS.fmt(tOut); $('#tcDur').textContent = KS.fmt(outDur());
    const fps = Math.round(p.fps || 30), fr = Math.floor((tOut % 1) * fps);
    $('#aeTc').textContent = `${Math.floor(tOut / 3600)}:${String(Math.floor(tOut % 3600 / 60)).padStart(2, '0')}:${String(Math.floor(tOut % 60)).padStart(2, '0')}:${String(fr).padStart(2, '0')}`;
  };
  E.getImg = im => {
    E.imgCache = E.imgCache || {};
    if (!E.imgCache[im.id]) { const i = new Image(); i.onload = () => E.render(); i.src = `/media/file/${E.project.id}/img?id=${im.id}&v=${encodeURIComponent(im.path)}`; E.imgCache[im.id] = i; }
    return E.imgCache[im.id];
  };

  function wrapLines(x, words, maxW) {
    const lines = []; let cur = [];
    for (const w of words) {
      const test = cur.concat(w).map(o => o.t).join(' ');
      if (cur.length && x.measureText(test).width > maxW) { lines.push(cur); cur = [w]; } else cur.push(w);
    }
    if (cur.length) lines.push(cur);
    return lines;
  }
  function popScale(dt) { if (dt < 0) return 1; if (dt < .11) return .72 + .32 * dt / .11; if (dt < .17) return 1.04 - .04 * (dt - .11) / .06; return 1; }

  function capWindow(i) {
    const c = E.project.captions[i], n = E.project.captions[i + 1];
    let end = c.e + .35;
    if (n) { end = Math.min(end, n.s); if (n.s - c.e < .35) end = n.s; }
    return [c.s, Math.max(end, c.s + .2)];
  }
  E.capAt = t => { const cs = E.project.captions; for (let i = 0; i < cs.length; i++) { const [a, b] = capWindow(i); if (t >= a && t < b) return i; } return -1; };

  function drawCaption(x, t) {
    const p = E.project, st = p.style;
    const i = E.capAt(t); if (i < 0) return;
    const c = p.captions[i];
    const words = (c.words || []).map(w => ({ t: st.upper ? KS.trUpper(w.w) : w.w, s: w.s }));
    if (!words.length) return;
    let active = -1; words.forEach((w, k) => { if (t >= w.s - 1e-3) active = k; }); if (active < 0) active = 0;
    const size = st.size * K;
    x.save();
    x.font = `${size}px "${FONT_CSS[st.font] || 'PoppinsBlk'}"`;
    x.textBaseline = 'middle'; x.lineJoin = 'round'; x.miterLimit = 2;
    const lines = wrapLines(x, words, (1080 - 140) * K);
    const lh = size * 1.12, cy = PH * st.y / 100, sc = st.anim ? popScale(t - c.s) : 1;
    const totalH = lines.length * lh;
    x.translate(PW / 2, cy); x.scale(sc, sc);
    let maxW = 0;
    lines.forEach((ln, li) => {
      const text = ln.map(o => o.t).join(' ');
      const w = x.measureText(text).width; maxW = Math.max(maxW, w);
      let xx = -w / 2; const yy = -totalH / 2 + lh * li + lh / 2;
      ln.forEach(o => {
        const tw = x.measureText(o.t).width;
        if (st.shadow) { x.fillStyle = 'rgba(0,0,0,.55)'; x.fillText(o.t, xx + 2, yy + 2.5); }
        if (+st.outlineW > 0) { x.strokeStyle = st.outline; x.lineWidth = st.outlineW * 2 * K; x.strokeText(o.t, xx, yy); }
        x.fillStyle = st.karaoke && words.indexOf(o) === active ? st.hl : st.color;
        x.fillText(o.t, xx, yy);
        xx += tw + x.measureText(' ').width;
      });
    });
    x.restore();
    E.capBoxes.push({ y0: cy - totalH / 2 - 10, y1: cy + totalH / 2 + 10, x0: PW / 2 - maxW / 2 - 10, x1: PW / 2 + maxW / 2 + 10 });
  }

  function drawTexts(x, t, tOut) {
    for (const tx of E.project.effects.texts) {
      if (t < tx.s || t > tx.e || !(tx.text || '').trim()) continue;
      const raw = tx.upper !== false ? KS.trUpper(tx.text) : tx.text;
      const size = (+tx.size || 80) * K, cy = PH * (+tx.y || 18) / 100, dt = toOut(t) - toOut(tx.s);
      x.save();
      x.font = `${size}px "${FONT_CSS[tx.font || 'poppins-black']}"`;
      x.textBaseline = 'middle'; x.lineJoin = 'round';
      let txt = raw, alpha = 1, ox = 0, sc = 1;
      const left = toOut(tx.e) - tOut;
      if (tx.anim === 'type') { const n = raw.length, step = Math.min(.06, Math.max(.02, (toOut(tx.e) - toOut(tx.s)) * .4 / Math.max(1, n))); txt = raw.slice(0, Math.max(1, Math.floor(dt / step) + 1)); }
      else if (tx.anim === 'slide') { ox = dt < .26 ? -(1 - dt / .26) * (PW / 2 + 350 * K) : 0; if (left < .18) alpha = left / .18; }
      else if (tx.anim === 'fade') { alpha = Math.min(1, dt / .3, left / .3); }
      else { sc = dt < .14 ? .6 + .48 * dt / .14 : dt < .22 ? 1.08 - .08 * (dt - .14) / .08 : 1; if (left < .15) alpha = left / .15; }
      x.globalAlpha = KS.clamp(alpha, 0, 1);
      const fullW = x.measureText(raw).width, w = x.measureText(txt).width;
      x.translate(PW / 2 + ox, cy); x.scale(sc, sc);
      if (tx.box !== false) {
        const pad = 18 * K;
        x.fillStyle = tx.boxColor || '#FF3D8B';
        x.beginPath(); x.roundRect(-fullW / 2 - pad, -size * .62 - pad * .6, fullW + pad * 2, size * 1.24 + pad * 1.2, 6); x.fill();
      } else { x.strokeStyle = '#000'; x.lineWidth = 7 * 2 * K; x.strokeText(txt, -fullW / 2, 0); }
      x.fillStyle = tx.color || '#FFFFFF';
      x.fillText(txt, -fullW / 2, 0);
      x.restore();
      E.textBoxes.push({ id: tx.id, y0: cy - size, y1: cy + size, x0: PW / 2 - fullW / 2 - 20, x1: PW / 2 + fullW / 2 + 20 });
    }
  }

  /* --- önizlemede altyazı / yazıyı sürükleyerek yerleştir --- */
  const toCanvas = e => { const r = prev.getBoundingClientRect(); return [(e.clientX - r.left) / r.width * PW, (e.clientY - r.top) / r.height * PH]; };
  const hitText = (cx, cy) => {
    const tb = E.textBoxes.slice().reverse().find(b => cy >= b.y0 && cy <= b.y1 && cx >= b.x0 && cx <= b.x1);
    if (tb) return { kind: 'text', id: tb.id };
    const cb = E.capBoxes.find(b => cy >= b.y0 && cy <= b.y1 && cx >= b.x0 && cx <= b.x1);
    if (cb) return { kind: 'cap' };
    return null;
  };
  prev.addEventListener('mousemove', e => { if (E._pdrag) return; const [cx, cy] = toCanvas(e); $('.phone').classList.toggle('grab', !!hitText(cx, cy)); });
  prev.addEventListener('mousedown', e => {
    if (!E.project) return;
    const [cx, cy] = toCanvas(e);
    const h = hitText(cx, cy);
    if (!h) { E.toggle(); return; }
    E.beginDrag(); E._pdrag = h;
    if (h.kind === 'text') E.select({ type: 'text', id: h.id });
    const move = ev => {
      const [, y] = toCanvas(ev);
      const pct = KS.clamp(Math.round(y / PH * 1000) / 10, 4, 96);
      E.dragY = y;
      if (h.kind === 'cap') E.project.style.y = pct;
      else { const tx = E.project.effects.texts.find(o => o.id === h.id); if (tx) tx.y = pct; }
      E.render();
    };
    const up = () => {
      window.removeEventListener('mousemove', move); window.removeEventListener('mouseup', up);
      E._pdrag = null; E.dragY = null; E.endDrag(); E.render();
      if (h.kind === 'cap') E.renderStyle(); else E.renderLayers();
    };
    window.addEventListener('mousemove', move); window.addEventListener('mouseup', up);
  });
  prev.addEventListener('wheel', e => {
    const [cx, cy] = toCanvas(e); const h = hitText(cx, cy); if (!h) return;
    e.preventDefault();
    E.change(() => {
      const d = e.deltaY < 0 ? 4 : -4;
      if (h.kind === 'cap') E.project.style.size = KS.clamp(E.project.style.size + d, 40, 180);
      else { const tx = E.project.effects.texts.find(o => o.id === h.id); if (tx) tx.size = KS.clamp((+tx.size || 80) + d, 30, 200); }
    }, { soft: true });
    clearTimeout(E._wheelT); E._wheelT = setTimeout(() => { E.renderStyle(); E.renderLayers(); }, 300);
  }, { passive: false });

  /* ====================================================== kadraj paneli */
  const srcC = $('#srcCanvas'), sctx = srcC.getContext('2d');
  const ASPECT = () => {
    const r = E.project.layout.split;
    return { face: 1080 / (1920 * r), game: 1080 / (1920 * (1 - r)), crop: 9 / 16 };
  };
  E.fixRects = () => {
    const p = E.project; if (!p) return;
    const L = p.layout, A = ASPECT(), W = p.width, H = p.height;
    ['face', 'game', 'crop'].forEach(k => {
      const r = L[k] = Object.assign({}, DEF_LAYOUT[k], L[k]);
      r.h = r.w * W / (A[k] * H);
      if (r.h > 1) { r.h = 1; r.w = A[k] * H / W; }
      if (r.w > 1) { r.w = 1; r.h = r.w * W / (A[k] * H); }
      r.x = KS.clamp(r.x, 0, 1 - r.w); r.y = KS.clamp(r.y, 0, 1 - r.h);
    });
  };
  E.renderLayout = () => {
    const L = E.project.layout;
    $$('#modeCards .mode-card').forEach(b => b.classList.toggle('active', b.dataset.mode === L.mode));
    $('#rectFace').hidden = $('#rectGame').hidden = L.mode !== 'split';
    $('#rectCrop').hidden = L.mode !== 'crop';
    $('#splitField').hidden = L.mode !== 'split';
    $('#layoutHint').textContent = L.mode === 'blur' ? 'Video ortada, arkası bulanık olur. Ayar gerekmez.' : 'Kutuları sürükle, köşeden büyüt.';
    $('#splitRange').value = Math.round(L.split * 100); KS.paintRange($('#splitRange'));
    $('#splitVal').textContent = Math.round(L.split * 100) + '%';
    E.placeRects();
  };
  E.placeRects = () => {
    const L = E.project.layout;
    [['#rectFace', L.face], ['#rectGame', L.game], ['#rectCrop', L.crop]].forEach(([s, r]) => {
      const el = $(s); el.style.left = r.x * 100 + '%'; el.style.top = r.y * 100 + '%'; el.style.width = r.w * 100 + '%'; el.style.height = r.h * 100 + '%';
    });
  };
  E.drawSrc = () => {
    const p = E.project; if (!p || !video.videoWidth) return;
    const w = $('#srcWrap').clientWidth || 270;
    srcC.width = w * 2; srcC.height = Math.round(w * 2 * p.height / p.width);
    sctx.drawImage(video, 0, 0, srcC.width, srcC.height);
  };
  $$('#modeCards .mode-card').forEach(b => b.onclick = () => E.change(() => { E.project.layout.mode = b.dataset.mode; E.fixRects(); }));
  $('#splitRange').oninput = e => { E.project.layout.split = e.target.value / 100; $('#splitVal').textContent = e.target.value + '%'; E.fixRects(); E.placeRects(); E.render(); };
  $('#splitRange').onpointerdown = E.beginDrag; $('#splitRange').onchange = () => E.endDrag();
  $('#layoutDefault').onclick = () => KS.api('/api/defaults', { layout: E.project.layout }).then(() => KS.toast('✓ Yeni kliplerde bu kadraj kullanılacak', 'ok'));
  $$('#srcWrap .rect').forEach(el => el.addEventListener('mousedown', e => {
    e.preventDefault(); e.stopPropagation();
    const key = el.dataset.r, r = E.project.layout[key], wrap = $('#srcWrap').getBoundingClientRect();
    const resize = e.target.classList.contains('h'), sx = e.clientX, sy = e.clientY, o = { ...r };
    const p = E.project, A = ASPECT()[key];
    E.beginDrag();
    const move = ev => {
      const dx = (ev.clientX - sx) / wrap.width, dy = (ev.clientY - sy) / wrap.height;
      if (resize) {
        let w = KS.clamp(o.w + dx, .05, 1 - o.x);
        let h = w * p.width / (A * p.height);
        if (o.y + h > 1) { h = 1 - o.y; w = h * A * p.height / p.width; }
        r.w = w; r.h = h;
      } else { r.x = KS.clamp(o.x + dx, 0, 1 - r.w); r.y = KS.clamp(o.y + dy, 0, 1 - r.h); }
      E.placeRects(); E.render();
    };
    const up = () => { window.removeEventListener('mousemove', move); window.removeEventListener('mouseup', up); E.endDrag(); };
    window.addEventListener('mousemove', move); window.addEventListener('mouseup', up);
  }));
  window.addEventListener('resize', () => { if (E.project) { E.drawSrc(); E.sizeTimeline(); E.setRtInk(); } });

  /* ====================================================== sağ sekmeler */
  E.setRtInk = () => { const a = $('#rightTabs button.active'), i = $('#rightTabs i'); if (a && a.offsetWidth) { i.style.left = a.offsetLeft + 'px'; i.style.width = a.offsetWidth + 'px'; } };
  E.rt = name => {
    $$('#rightTabs button').forEach(b => b.classList.toggle('active', b.dataset.rt === name));
    $$('#rightPanel .rt-panel').forEach(p => p.classList.toggle('active', p.id === 'rt-' + name));
    E.setRtInk();
    if (name === 'fx') E.renderFxThumbs();
  };
  $$('#rightTabs button').forEach(b => b.onclick = () => E.rt(b.dataset.rt));

  /* ====================================================== ALTYAZI */
  const subsJob = () => (KS.state.jobs || []).find(j => j.kind === 'altyazi' && (j.status === 'calisiyor' || j.status === 'bekliyor') && j.title === 'Altyazı: ' + E.project.title);
  E.renderSubs = () => {
    const p = E.project, el = $('#rt-subs');
    const job = subsJob();
    if (!p.captions.length) {
      const running = job || p.subs_status === 'calisiyor';
      el.innerHTML = `<div class="subs-empty">
        <div class="big-ico">${KS.icon.spark}</div>
        <b style="color:var(--text);font:17px var(--head)">${running ? 'Altyazı çıkarılıyor...' : 'Otomatik altyazı'}</b>
        <span>${running ? 'Konuşmalar yazıya dökülüyor. Bu sırada kadrajı ayarlayabilirsin.' : 'Konuşmaları Türkçe yazıya döküp videoya ekleyeyim.'}</span>
        ${running ? `<div class="progress"><i id="subsProg" style="width:${Math.round((job ? job.progress : 0.05) * 100)}%"></i></div><small id="subsMsg">${KS.esc(job ? job.message : '')}</small>` :
          `<button class="btn primary glow" id="subsGo">${KS.icon.spark}Altyazı Çıkar</button>`}
        ${!p.has_audio ? '<small style="color:var(--amber)">Bu videoda ses yok.</small>' : ''}
      </div>`;
      const b = $('#subsGo'); if (b) b.onclick = E.transcribe;
      return;
    }
    const flagged = p.captions.reduce((n, c) => n + c.words.filter(w => w.p < .55).length, 0);
    const mw = p.style.maxWords || 3;
    el.innerHTML = `
      <div class="subs-tools">
        ${flagged ? `<button class="chip warn" id="nextFlag" title="Sonraki şüpheli kelime (F)">⚠ ${flagged} kontrol et</button>` : '<span class="chip" style="color:var(--green)">✓ Hepsi temiz</span>'}
        <button class="chip" id="capAdd" title="Oynatma çizgisine altyazı ekle">${KS.icon.plus}Ekle</button>
        <button class="chip" id="capRedo" title="Altyazıyı baştan çıkar">↻ Yeniden</button>
        <button class="chip" id="capDict" title="Düzeltme sözlüğü">📖 Sözlük</button>
      </div>
      <div class="subs-tools"><span class="hint" style="margin-right:4px">Ekranda kelime:</span>
        ${[1, 2, 3, 4].map(n => `<button class="chip ${n === mw ? 'on' : ''}" data-mw="${n}">${n}</button>`).join('')}</div>
      <div class="hint">Yanlış kelimeye tıkla ve düzelt. <span style="color:#ffd48a">Sarı</span> kelimeler emin olunamayanlar.</div>
      <div class="cap-list" id="capList">${p.captions.map((c, i) => {
        const cut = !inSeg((c.s + c.e) / 2);
        return `<div class="cap ${cut ? 'cut' : ''}" data-ci="${i}"><span class="ct" title="${cut ? 'Bu kısım kesildi' : 'Buraya git'}">${KS.fmt(c.s, true)}</span>
          <div class="tx" contenteditable="true" spellcheck="false">${c.words.map(w => w.p < .55 ? `<span class="fl">${KS.esc(w.w)}</span>` : KS.esc(w.w)).join(' ')}</div>
          <button class="x" title="Sil">${KS.icon.x}</button></div>`;
      }).join('')}</div>`;
    $('#capAdd').onclick = E.addCaption;
    $('#capRedo').onclick = async () => { if (await KS.confirm('Altyazıyı baştan çıkar?', 'Yaptığın düzeltmeler silinecek.', 'Baştan çıkar', true)) E.transcribe(); };
    $('#capDict').onclick = () => KS.go('settings');
    const nf = $('#nextFlag'); if (nf) nf.onclick = E.nextFlag;
    $$('[data-mw]', el).forEach(b => b.onclick = async () => {
      const before = snap();
      const r = await KS.api(`/api/project/${p.id}/rechunk`, { maxWords: +b.dataset.mw });
      E.history.push(before); E.future = [];
      p.captions = r.captions; p.style.maxWords = +b.dataset.mw; E.renderSubs(); E.render(); E.drawTimeline(); E.updateUndo();
    });
    $$('.cap', el).forEach(row => {
      const i = +row.dataset.ci, tx = $('.tx', row);
      $('.ct', row).onclick = () => E.seek(p.captions[i].s + .01);
      tx.onfocus = () => { if (!video.paused) E.pause(); if (video.currentTime < p.captions[i].s || video.currentTime > p.captions[i].e) E.seek(p.captions[i].s + .01); tx.dataset.orig = tx.innerText; };
      tx.onkeydown = e => { if (e.key === 'Enter') { e.preventDefault(); tx.blur(); } if (e.key === 'Escape') { tx.innerText = tx.dataset.orig; tx.blur(); } e.stopPropagation(); };
      tx.onblur = () => { if (tx.innerText.trim() !== (tx.dataset.orig || '').trim()) E.editCaption(i, tx.innerText); };
      $('.x', row).onclick = () => E.change(() => p.captions.splice(i, 1));
    });
  };
  E.editCaption = (i, text) => {
    const p = E.project, c = p.captions[i];
    const toks = text.replace(/\s+/g, ' ').trim().split(' ').filter(Boolean);
    if (!toks.length) { E.change(() => p.captions.splice(i, 1)); return; }
    const old = c.words.map(w => w.w);
    let learn = null;
    E.change(() => {
      if (toks.length === c.words.length) {
        const diffs = [];
        c.words.forEach((w, k) => { if (w.w !== toks[k]) { diffs.push([w.w, toks[k]]); w.w = toks[k]; w.p = 1; } });
        if (diffs.length === 1) learn = diffs[0];
      } else {
        const total = toks.reduce((s, t) => s + t.length + 1, 0), span = c.e - c.s;
        let t = c.s;
        c.words = toks.map(tk => { const d = span * (tk.length + 1) / total; const w = { w: tk, s: +t.toFixed(3), e: +(t + d).toFixed(3), p: 1 }; t += d; return w; });
      }
    });
    if (learn) {
      const clean = s => s.replace(/[.,!?;:…"'()]/g, '');
      const [a, b] = [clean(learn[0]), clean(learn[1])];
      if (a && b && KS.trLower(a) !== KS.trLower(b) && !old.includes(learn[1])) {
        KS.toast(`"<b>${KS.esc(a)}</b>" → "<b>${KS.esc(b)}</b>" düzeltmesini hatırlayayım mı? Sonraki videolarda otomatik düzelir.`, '', [
          { label: 'Hatırla', primary: true, fn: async () => { const r = await KS.api('/api/fixes', { add: { [a]: b }, project: p.id }); KS.state.settings.duzeltmeler = r.duzeltmeler; if (r.captions) { p.captions = r.captions; E.renderSubs(); E.render(); } KS.toast('✓ Sözlüğe eklendi', 'ok', [], 1500); } },
        ], 6000);
      }
    }
  };
  E.addCaption = () => {
    const t = now();
    E.change(() => {
      const cs = E.project.captions;
      const c = { id: 'c' + KS.uid(), s: +t.toFixed(3), e: +(t + 1.5).toFixed(3), words: [{ w: 'Yeni', s: t, e: t + .7, p: 1 }, { w: 'yazı', s: t + .7, e: t + 1.5, p: 1 }] };
      cs.push(c); cs.sort((a, b) => a.s - b.s);
    });
    setTimeout(() => { const i = E.capAt(t + .05); const row = $(`.cap[data-ci="${i}"] .tx`); if (row) { row.focus(); document.execCommand('selectAll', false, null); } }, 50);
  };
  E.nextFlag = () => {
    const p = E.project, t = now();
    const list = []; p.captions.forEach((c, i) => c.words.forEach(w => { if (w.p < .55) list.push([i, w.s]); }));
    if (!list.length) return KS.toast('✓ Kontrol edilecek kelime kalmadı', 'ok', [], 1500);
    const n = list.find(x => x[1] > t + .05) || list[0];
    E.rt('subs'); E.seek(n[1] + .01);
    setTimeout(() => { const row = $(`.cap[data-ci="${n[0]}"]`); if (row) { row.scrollIntoView({ block: 'center', behavior: 'smooth' }); $('.tx', row).focus(); } }, 80);
  };
  E.transcribe = async () => {
    const p = E.project;
    await E.flush();
    const r = await KS.api(`/api/project/${p.id}/transcribe`, {});
    p.subs_status = 'calisiyor'; p.captions = [];
    KS.trackJob(r.job); E.renderSubs();
  };
  E.highlightCaption = () => {
    if (!E.project) return;
    const i = E.capAt(now());
    if (i === E._lastCap) return; E._lastCap = i;
    $$('#capList .cap.now').forEach(r => r.classList.remove('now'));
    const row = $(`#capList .cap[data-ci="${i}"]`);
    if (row) { row.classList.add('now'); if (!row.contains(document.activeElement)) row.scrollIntoView({ block: 'nearest', behavior: 'smooth' }); }
  };
  KS.hooks.jobTick.push(jobs => {
    if (!E.project || E.project.captions.length) return;
    const j = subsJob(), bar = $('#subsProg');
    if (j && bar) { bar.style.width = Math.round(j.progress * 100) + '%'; $('#subsMsg').textContent = j.message; }
    else if (j && !bar) E.renderSubs();
  });
  KS.hooks.jobDone.push(async j => {
    if (!E.project || !j.result || j.result.project !== E.project.id) return;
    if (j.kind === 'altyazi') {
      const fresh = await KS.api('/api/project/' + E.project.id);
      E.project.captions = fresh.captions; E.project.words = fresh.words; E.project.subs_status = fresh.subs_status;
      E.renderSubs(); E.render(); E.drawTimeline();
    }
  });
  KS.hooks.jobDone.push(j => { if (j.kind === 'altyazi' && j.status === 'hata' && E.project) { E.project.subs_status = 'hata'; E.renderSubs(); } });

  /* ====================================================== STİL */
  const swatches = (cur, key, list = SWATCH) => { cur = cur || '#FFFFFF'; return `<div class="swatches">${list.map(c => `<button class="sw ${cur.toUpperCase() === c ? 'active' : ''}" style="background:${c}" data-k="${key}" data-c="${c}"></button>`).join('')}
    <label class="sw custom" title="Özel renk"><input type="color" value="${cur}" data-k="${key}"></label></div>`; };
  const tog = (key, label, on) => `<button class="tog ${on ? 'on' : ''}" data-tog="${key}">${label}<i></i></button>`;
  E.renderStyle = () => {
    const st = E.project.style, el = $('#rt-style');
    el.innerHTML = `
      <div class="style-sec"><h4>Hazır stiller</h4><div class="preset-grid">${CAP_PRESETS.map((pr, i) => {
        const s = pr.s, act = ['font', 'color', 'hl', 'outline'].every(k => (st[k] || '').toString().toUpperCase() === (s[k] || '').toString().toUpperCase());
        const w = [s.upper ? 'BU ÇOK' : 'Bu çok', s.upper ? 'İYİ' : 'iyi'];
        return `<button class="preset ${act ? 'active' : ''}" data-cp="${i}"><div class="cap-preset" style="font-family:'${FONT_CSS[s.font]}';color:${s.color};-webkit-text-stroke:${Math.min(3, s.outlineW / 3)}px ${s.outline};paint-order:stroke fill">${w[0]}&nbsp;<span style="color:${s.karaoke ? s.hl : s.color}">${w[1]}</span></div><span>${pr.name}</span></button>`;
      }).join('')}</div></div>
      <div class="style-sec"><h4>Yazı tipi</h4><div class="font-grid">${Object.keys(FONT_CSS).map(f => `<button class="font-opt ${st.font === f ? 'active' : ''}" data-font="${f}" style="font-family:'${FONT_CSS[f]}'">${FONT_NAME[f]}</button>`).join('')}</div></div>
      <div class="field"><label>Boyut <b id="szV">${st.size}</b></label><input type="range" min="40" max="180" value="${st.size}" data-rng="size"></div>
      <div class="field"><label>Yükseklik (önizlemede sürükleyebilirsin) <b id="yV">%${Math.round(st.y)}</b></label><input type="range" min="5" max="95" value="${st.y}" data-rng="y"></div>
      <div class="style-sec"><h4>Yazı rengi</h4>${swatches(st.color, 'color')}</div>
      <div class="style-sec"><h4>Vurgu rengi (konuşulan kelime)</h4>${swatches(st.hl, 'hl')}</div>
      <div class="field"><label>Kenar kalınlığı <b id="owV">${st.outlineW}</b></label><input type="range" min="0" max="18" value="${st.outlineW}" data-rng="outlineW"></div>
      <div class="style-sec"><h4>Kenar rengi</h4>${swatches(st.outline, 'outline', ['#000000', '#FFFFFF', '#5B2BFF', '#FF3D8B', '#1A1A2E'])}</div>
      <div class="toggles">${tog('upper', 'BÜYÜK HARF', st.upper)}${tog('karaoke', 'Kelime vurgusu', st.karaoke)}${tog('anim', 'Pop animasyon', st.anim)}${tog('shadow', 'Gölge', st.shadow)}</div>
      <button class="btn ghost sm full" id="styleDefault">Bu stili varsayılan yap</button>`;
    $$('#rt-style input[type=range]').forEach(KS.paintRange);
    $$('[data-cp]', el).forEach(b => b.onclick = () => E.change(() => Object.assign(E.project.style, CAP_PRESETS[+b.dataset.cp].s)));
    $$('[data-font]', el).forEach(b => b.onclick = () => E.change(() => E.project.style.font = b.dataset.font));
    $$('.sw[data-c]', el).forEach(b => b.onclick = () => E.change(() => E.project.style[b.dataset.k] = b.dataset.c));
    $$('input[type=color]', el).forEach(i => { i.onchange = () => E.change(() => E.project.style[i.dataset.k] = i.value.toUpperCase()); });
    $$('[data-tog]', el).forEach(b => b.onclick = () => E.change(() => E.project.style[b.dataset.tog] = !E.project.style[b.dataset.tog]));
    $$('[data-rng]', el).forEach(r => {
      r.onpointerdown = E.beginDrag;
      r.oninput = () => { E.project.style[r.dataset.rng] = +r.value; const lab = { size: '#szV', y: '#yV', outlineW: '#owV' }[r.dataset.rng]; $(lab).textContent = (r.dataset.rng === 'y' ? '%' : '') + r.value; E.render(); };
      r.onchange = () => E.endDrag();
    });
    $('#styleDefault').onclick = () => KS.api('/api/defaults', { style: E.project.style }).then(() => KS.toast('✓ Yeni kliplerde bu stil kullanılacak', 'ok'));
  };

  /* ====================================================== EFEKTLER */
  E.renderFx = () => {
    const fx = E.project.effects, el = $('#rt-fx');
    const t = (k, l) => tog(k, l, fx[k]);
    el.innerHTML = `
      <div class="style-sec"><h4>Hazır görünüm</h4><div class="preset-grid" style="grid-template-columns:repeat(4,1fr)">${FX_PRESETS.map(([k, n]) => `<button class="preset ${fx.preset === k ? 'active' : ''}" data-fxp="${k}"><canvas width="90" height="90"></canvas><span>${n}</span></button>`).join('')}</div></div>
      <div class="style-sec"><h4>Zamanlı efektler <span class="hint" style="text-transform:none;letter-spacing:0">— oynatma çizgisine eklenir</span></h4>
        ${Object.entries(Object.entries(KS.fx.LIST).reduce((m, [k, v]) => ((m[v[1]] = m[v[1]] || []).push([k, v[0]]), m), {})).map(([cat, items]) => `
          <div class="fx-cat"><span class="fx-cat-n">${KS.fx.ICON[cat] || ''} ${cat}</span><div class="fx-chips">${items.map(([k, n]) => `<button class="chip fxadd" data-fxadd="${k}">${n}</button>`).join('')}</div></div>`).join('')}
        ${fx.fxLayers.length ? `<div class="hint">${fx.fxLayers.length} efekt eklendi. Ayarları Katman sekmesinde, zamanları timeline'daki "Efektler" satırında.</div>` : ''}
      </div>
      <div class="style-sec"><h4>Kesimlerde geçiş</h4>
        <div class="speed-row" style="grid-template-columns:repeat(4,1fr)">${KS.fx.TRANS.map(([k, n]) => `<button class="chip ${fx.transition.type === k ? 'on' : ''}" data-trans="${k}">${n}</button>`).join('')}</div>
        ${fx.transition.type !== 'none' ? `<div class="field"><label>Geçiş süresi <b id="trV">${(+fx.transition.d).toFixed(2)} sn</b></label><input type="range" min="15" max="120" value="${Math.round(fx.transition.d * 100)}" id="trRange"></div>` : ''}
        <div class="hint">${segs().length > 1 ? (segs().length - 1) + ' kesim noktasına uygulanır.' : 'Videoyu böldüğünde (S) kesim noktalarına uygulanır.'}</div>
      </div>
      <div class="style-sec"><h4>LUT (renk paketi)</h4>
        ${fx.lut ? `<div class="lcard sel"><div class="lhead"><i style="width:9px;height:9px;border-radius:3px;background:var(--amber)"></i><span class="nm">🎞 ${KS.esc(fx.lut.name)}</span><button class="del-btn" id="lutDel" title="Kaldır">${KS.icon.trash}</button></div>
          <div class="lbody" style="display:flex"><div class="field"><label>Etki <b id="lutV">%${fx.lut.mix ?? 100}</b></label><input type="range" min="0" max="100" value="${fx.lut.mix ?? 100}" id="lutMix"></div></div></div>`
          : `<button class="btn ghost sm full" id="lutAdd">🎞 LUT yükle (.cube)</button><div class="hint">İnternetten indirdiğin .cube dosyalarını kullanabilirsin.</div>`}
      </div>
      <div class="style-sec"><h4>Tüm videoya</h4><div class="toggles">
        ${t('vignette', 'Vinyet')}${t('grain', 'Film greni')}${t('glow', 'Parlama')}${t('rgb', 'RGB kayması')}
        ${t('sharpen', 'Keskinleştir')}${t('mirror', 'Ayna')}${t('fadeIn', 'Açılış fade')}${t('fadeOut', 'Kapanış fade')}</div></div>
      <div class="style-sec"><h4>Hız</h4><div class="speed-row">${[.5, .75, 1, 1.25, 1.5, 2].map(s => `<button class="chip ${+fx.speed === s ? 'on' : ''}" data-spd="${s}">${s}x</button>`).join('')}</div></div>
      <div class="style-sec"><h4>Zoom vurgusu</h4>
        <div class="add-row"><button class="btn ghost sm" id="fxZoom">🔍 Buraya zoom <kbd>Z</kbd></button><button class="btn ghost sm" id="fxShake">💥 Sarsıntılı zoom <kbd>X</kbd></button></div>
        <div class="hint">${fx.zooms.length ? fx.zooms.length + ' zoom var. Timeline\'daki Zoom satırından kaydırabilirsin.' : 'Komik / şok anlarda vurgu için.'}</div></div>
      <details class="fine"><summary>İnce ayar (renk)</summary>
        ${[['bright', 'Parlaklık', -50, 50], ['contrast', 'Kontrast', -50, 50], ['sat', 'Doygunluk', -100, 100], ['temp', 'Sıcaklık', -100, 100]].map(([k, l, a, b]) =>
          `<div class="field"><label>${l} <b id="fv_${k}">${fx[k]}</b></label><input type="range" min="${a}" max="${b}" value="${fx[k]}" data-frng="${k}"></div>`).join('')}
        <button class="btn ghost sm full" id="fxReset">Renkleri sıfırla</button>
      </details>`;
    $$('#rt-fx input[type=range]').forEach(KS.paintRange);
    $$('[data-fxp]', el).forEach(b => b.onclick = () => E.change(() => E.project.effects.preset = b.dataset.fxp, { soft: true }) || E.renderFx());
    $$('[data-tog]', el).forEach(b => b.onclick = () => E.change(() => E.project.effects[b.dataset.tog] = !E.project.effects[b.dataset.tog]));
    $$('[data-spd]', el).forEach(b => b.onclick = () => { E.change(() => E.project.effects.speed = +b.dataset.spd); video.playbackRate = speed(); });
    $('#fxZoom').onclick = () => E.addZoom(false); $('#fxShake').onclick = () => E.addZoom(true);
    $$('[data-frng]', el).forEach(r => {
      r.onpointerdown = E.beginDrag;
      r.oninput = () => { E.project.effects[r.dataset.frng] = +r.value; $('#fv_' + r.dataset.frng).textContent = r.value; E.render(); };
      r.onchange = () => { E.endDrag(); E.renderFxThumbs(); };
    });
    $('#fxReset').onclick = () => E.change(() => Object.assign(E.project.effects, { bright: 0, contrast: 0, sat: 0, temp: 0 }));
    $$('[data-fxadd]', el).forEach(b => b.onclick = () => E.addFx(b.dataset.fxadd));
    $$('[data-trans]', el).forEach(b => b.onclick = () => E.change(() => E.project.effects.transition.type = b.dataset.trans));
    const tr = $('#trRange');
    if (tr) { tr.onpointerdown = E.beginDrag; tr.oninput = () => { E.project.effects.transition.d = tr.value / 100; $('#trV').textContent = (tr.value / 100).toFixed(2) + ' sn'; E.render(); }; tr.onchange = () => E.endDrag(); }
    const la = $('#lutAdd'); if (la) la.onclick = KS.addFile;
    const ld = $('#lutDel'); if (ld) ld.onclick = async () => { await E.flush(); await KS.api(`/api/project/${E.project.id}/lut`, {}); E.change(() => E.project.effects.lut = null); KS.fx.lut = null; E.render(); };
    const lm = $('#lutMix'); if (lm) { lm.onpointerdown = E.beginDrag; lm.oninput = () => { E.project.effects.lut.mix = +lm.value; $('#lutV').textContent = '%' + lm.value; E.render(); }; lm.onchange = () => E.endDrag(); }
    E.renderFxThumbs();
  };
  E.renderFxThumbs = () => {
    if (!E.project || !video.videoWidth || !$('#rt-fx').classList.contains('active')) return;
    const W = video.videoWidth, H = video.videoHeight, s = Math.min(W, H);
    $$('[data-fxp]').forEach(b => {
      const c = $('canvas', b), x = c.getContext('2d');
      x.filter = (FX_PRESETS.find(p => p[0] === b.dataset.fxp) || [])[2] || 'none';
      x.drawImage(video, (W - s) / 2, (H - s) / 2, s, s, 0, 0, 90, 90);
    });
  };

  /* ====================================================== KATMANLAR */
  E.addZoom = shake => {
    const t = now();
    const z = { id: 'z' + KS.uid(), t: +t.toFixed(3), d: shake ? 0.9 : 0.8, z: shake ? 1.2 : 1.3, shake };
    E.change(() => E.project.effects.zooms.push(z));
    E.select({ type: 'zoom', id: z.id });
    KS.toast(shake ? '💥 Sarsıntılı zoom eklendi' : '🔍 Zoom eklendi', '', [], 1400);
  };
  E.addFx = kind => {
    const def = KS.fx.LIST[kind]; if (!def) return;
    const t = now();
    const f = { id: 'f' + KS.uid(), kind, s: +t.toFixed(3), e: +Math.min(E.project.duration, t + def[2]).toFixed(3), i: 70, params: {} };
    (KS.fx.PARAMS[kind] || []).forEach(([k, , v]) => f.params[k] = v);
    E.change(() => E.project.effects.fxLayers.push(f));
    E.select({ type: 'fx', id: f.id });
    KS.toast(`${KS.fx.ICON[def[1]] || '✨'} ${def[0]} eklendi (${KS.fmt(toOut(t))})`, '', [], 1500);
    if (video.paused) E.render();
  };
  E.addLut = async f => {
    await E.flush();
    try {
      const r = await KS.api(`/api/project/${E.project.id}/lut`, { path: f.path });
      E.change(() => E.project.effects.lut = r.lut);
      await KS.fx.loadLut(E.project.id);
      E.rt('fx'); E.render();
      KS.toast('🎞 LUT yüklendi: ' + KS.esc(f.name), 'ok');
    } catch (e) { KS.toast(KS.esc(e.message), 'err'); }
  };
  E.addText = () => {
    const t = now();
    const tx = { id: 't' + KS.uid(), text: 'BUNU BEKLEMİYORDU', s: +t.toFixed(3), e: +Math.min(E.project.duration, t + 3).toFixed(3), y: 16, size: 80, color: '#FFFFFF', box: true, boxColor: '#FF3D8B', anim: 'pop', upper: true, font: 'poppins-black' };
    E.change(() => E.project.effects.texts.push(tx));
    E.select({ type: 'text', id: tx.id });
    setTimeout(() => { const ta = $(`.lcard[data-lid="${tx.id}"] textarea`); if (ta) { ta.focus(); ta.select(); } }, 80);
  };
  E.addMusic = async f => {
    E.change(() => E.project.media.music = { path: f.path, name: f.name, vol: 0.25, s: +now().toFixed(3) < 1 ? 0 : +now().toFixed(3), duration: f.duration || 0 });
    await E.flush();
    E.loadMusic(); E.select({ type: 'music' });
    KS.toast('🎵 Müzik katmanı eklendi: ' + KS.esc(f.name), 'ok');
  };
  E.addImage = async f => {
    const im = { id: 'i' + KS.uid(), path: f.path, name: f.name, s: 0, e: E.project.duration, pos: 'tr', size: 22, opacity: 1 };
    E.change(() => E.project.media.images.push(im));
    await E.flush();
    E.render();
    E.select({ type: 'image', id: im.id });
    KS.toast('🖼 Resim katmanı eklendi: ' + KS.esc(f.name), 'ok');
  };
  E.select = sel => {
    E.sel = sel;
    if (sel && sel.type !== 'seg') { E.rt('layers'); E.renderLayers(); setTimeout(() => { const c = $('.lcard.sel'); if (c) c.scrollIntoView({ block: 'nearest', behavior: 'smooth' }); }, 30); }
    E.drawTimeline();
  };
  const isSel = (type, id) => E.sel && E.sel.type === type && (id === undefined || E.sel.id === id);
  const timeBtns = (kind, id) => `<div class="mini-btns"><button class="chip" data-setS="${kind}:${id}">⇤ Başlangıç = şimdi</button><button class="chip" data-setE="${kind}:${id}">Bitiş = şimdi ⇥</button></div>`;
  E.renderLayers = () => {
    const p = E.project, fx = p.effects, md = p.media, el = $('#rt-layers');
    const head = (type, id, name, time, color) => `<div class="lhead" data-pick="${type}:${id ?? ''}"><i style="width:9px;height:9px;border-radius:3px;background:${color}"></i><span class="nm">${name}</span><span class="tm">${time}</span><button class="del-btn" data-ldel="${type}:${id ?? ''}" title="Sil">${KS.icon.trash}</button></div>`;
    el.innerHTML = `
      <div class="add-row">
        <button class="add-big" id="lyAdd">${KS.icon.plus}Dosya Ekle <small>video · müzik · resim</small></button>
        <button class="btn ghost sm" id="lyText">✏️ Yazı ekle <kbd>T</kbd></button>
        <button class="btn ghost sm" id="lyZoom">🔍 Zoom ekle <kbd>Z</kbd></button>
      </div>
      <div class="hint">Dosyaları pencereye sürükleyip bırakabilirsin de. Her şey kendi katmanına gider.</div>

      <div class="layer-sec"><h4><i style="background:var(--amber)"></i>Yazılar</h4>
        ${fx.texts.length ? fx.texts.map(t => `<div class="lcard ${isSel('text', t.id) ? 'sel' : ''}" data-lid="${t.id}">
          ${head('text', t.id, KS.esc(t.text || '(boş)'), KS.fmt(t.s) + '–' + KS.fmt(t.e), 'var(--amber)')}
          <div class="lbody">
            <textarea class="inp" data-tt="${t.id}" spellcheck="false">${KS.esc(t.text)}</textarea>
            <div class="mini-btns">${[['pop', 'Pop'], ['slide', 'Kayma'], ['fade', 'Solma'], ['type', 'Daktilo']].map(([k, l]) => `<button class="chip ${t.anim === k ? 'on' : ''}" data-tanim="${t.id}:${k}">${l}</button>`).join('')}</div>
            <div class="field"><label>Boyut <b>${t.size}</b></label><input type="range" min="30" max="200" value="${t.size}" data-trng="${t.id}:size"></div>
            <div class="field"><label>Yükseklik (önizlemede sürükle) <b>%${Math.round(t.y)}</b></label><input type="range" min="4" max="96" value="${t.y}" data-trng="${t.id}:y"></div>
            <div class="style-sec"><h4>Yazı rengi</h4>${swatches(t.color, 'tcolor:' + t.id)}</div>
            <div class="toggles">${`<button class="tog ${t.box !== false ? 'on' : ''}" data-tbox="${t.id}">Arka kutu<i></i></button><button class="tog ${t.upper !== false ? 'on' : ''}" data-tup="${t.id}">BÜYÜK HARF<i></i></button>`}</div>
            ${t.box !== false ? `<div class="style-sec"><h4>Kutu rengi</h4>${swatches(t.boxColor || '#FF3D8B', 'tbox:' + t.id, ['#FF3D8B', '#7C5CFF', '#000000', '#FFE14D', '#22D3EE', '#FF3B3B', '#3DFFA2'])}</div>` : ''}
            ${timeBtns('text', t.id)}
          </div></div>`).join('') : '<div class="layer-empty">Yazı yok — oynatma çizgisine eklemek için T.</div>'}
      </div>

      <div class="layer-sec"><h4><i style="background:#b388ff"></i>Efektler</h4>
        ${fx.fxLayers.length ? fx.fxLayers.map(f => `<div class="lcard ${isSel('fx', f.id) ? 'sel' : ''}" data-lid="${f.id}">
          ${head('fx', f.id, (KS.fx.ICON[(KS.fx.LIST[f.kind] || [])[1]] || '✨') + ' ' + KS.esc((KS.fx.LIST[f.kind] || [f.kind])[0]), KS.fmt(f.s) + '–' + KS.fmt(f.e), '#b388ff')}
          <div class="lbody">
            <div class="field"><label>Şiddet <b>%${f.i}</b></label><input type="range" min="0" max="100" value="${f.i}" data-frng2="${f.id}"></div>
            ${(KS.fx.PARAMS[f.kind] || []).map(([k, l]) => `<div class="style-sec"><h4>${l}</h4>${swatches(f.params[k], 'fxp:' + f.id + ':' + k, ['#FF3D8B', '#FF8A00', '#FFE14D', '#22D3EE', '#7C5CFF', '#3DFFA2', '#2B1055', '#FFFFFF'])}</div>`).join('')}
            ${f.kind === 'dirblur' ? `<div class="field"><label>Yön <b>${f.params.angle || 0}°</b></label><input type="range" min="0" max="180" value="${f.params.angle || 0}" data-fang="${f.id}"></div>` : ''}
            ${timeBtns('fx', f.id)}
          </div></div>`).join('') : '<div class="layer-empty">Efekt sekmesinden zamanlı efekt ekleyebilirsin.</div>'}
      </div>

      <div class="layer-sec"><h4><i style="background:var(--green)"></i>Resimler</h4>
        ${md.images.length ? md.images.map(im => `<div class="lcard ${isSel('image', im.id) ? 'sel' : ''}" data-lid="${im.id}">
          ${head('image', im.id, '🖼 ' + KS.esc(im.name), KS.fmt(im.s) + '–' + KS.fmt(im.e), 'var(--green)')}
          <div class="lbody">
            <div class="pos-grid">${[['tl', '↖'], ['tr', '↗'], ['c', '●'], ['bl', '↙'], ['br', '↘']].map(([k, l]) => `<button class="chip ${im.pos === k ? 'on' : ''}" data-ipos="${im.id}:${k}">${l}</button>`).join('')}</div>
            <div class="field"><label>Boyut <b>%${im.size}</b></label><input type="range" min="5" max="100" value="${im.size}" data-irng="${im.id}:size"></div>
            <div class="field"><label>Saydamlık <b>%${Math.round(im.opacity * 100)}</b></label><input type="range" min="10" max="100" value="${Math.round(im.opacity * 100)}" data-irng="${im.id}:opacity"></div>
            ${timeBtns('image', im.id)}
          </div></div>`).join('') : '<div class="layer-empty">Logo, emoji ya da resim ekleyebilirsin.</div>'}
      </div>

      <div class="layer-sec"><h4><i style="background:var(--cyan)"></i>Müzik</h4>
        ${md.music ? `<div class="lcard ${isSel('music') ? 'sel' : ''}" data-lid="music">
          ${head('music', '', '🎵 ' + KS.esc(md.music.name), 'başlangıç ' + KS.fmt(toOut(md.music.s)), 'var(--cyan)')}
          <div class="lbody">
            <div class="field"><label>Ses seviyesi <b>%${Math.round(md.music.vol * 100)}</b></label><input type="range" min="0" max="100" value="${Math.round(md.music.vol * 100)}" id="musVol"></div>
            <div class="mini-btns"><button class="chip" id="musStart">⇤ Müzik şimdi başlasın</button></div>
            <div class="hint">Konuşma duyulsun diye %20–30 iyi olur.</div>
          </div></div>` : '<div class="layer-empty">Arka plan müziği ekleyebilirsin.</div>'}
      </div>

      <div class="layer-sec"><h4><i style="background:var(--pink)"></i>Zoomlar</h4>
        ${fx.zooms.length ? fx.zooms.slice().sort((a, b) => a.t - b.t).map(z => `<div class="lcard ${isSel('zoom', z.id) ? 'sel' : ''}" data-lid="${z.id}">
          ${head('zoom', z.id, (z.shake ? '💥 Sarsıntılı zoom' : '🔍 Zoom'), KS.fmt(z.t, true), 'var(--pink)')}
          <div class="lbody">
            <div class="field"><label>Güç <b>${Math.round((z.z - 1) * 100)}%</b></label><input type="range" min="5" max="60" value="${Math.round((z.z - 1) * 100)}" data-zrng="${z.id}:z"></div>
            <div class="field"><label>Süre <b>${(+z.d).toFixed(1)} sn</b></label><input type="range" min="3" max="40" value="${Math.round(z.d * 10)}" data-zrng="${z.id}:d"></div>
            <div class="toggles"><button class="tog ${z.shake ? 'on' : ''}" data-zshake="${z.id}">Sarsıntı<i></i></button><button class="chip" data-znow="${z.id}">Buraya taşı</button></div>
          </div></div>`).join('') : '<div class="layer-empty">Zoom yok — eklemek için Z.</div>'}
      </div>`;
    $$('#rt-layers input[type=range]').forEach(KS.paintRange);
    $('#lyAdd').onclick = KS.addFile; $('#lyText').onclick = E.addText; $('#lyZoom').onclick = () => E.addZoom(false);
    $$('[data-pick]', el).forEach(h => h.onclick = e => {
      if (e.target.closest('[data-ldel]')) return;
      const [type, id] = h.dataset.pick.split(':');
      const already = isSel(type, id || undefined);
      E.sel = already ? null : { type, id: id || undefined };
      if (!already) { const o = type === 'fx' ? fx.fxLayers.find(x => x.id === id) : type === 'text' ? fx.texts.find(x => x.id === id) : type === 'image' ? md.images.find(x => x.id === id) : type === 'zoom' ? fx.zooms.find(x => x.id === id) : md.music; if (o) E.seek((o.s ?? o.t) + .01); }
      E.renderLayers(); E.drawTimeline();
    });
    $$('[data-ldel]', el).forEach(b => b.onclick = e => { e.stopPropagation(); const [type, id] = b.dataset.ldel.split(':'); E.deleteLayer(type, id); });
    const findT = id => fx.texts.find(x => x.id === id), findI = id => md.images.find(x => x.id === id), findZ = id => fx.zooms.find(x => x.id === id), findF = id => fx.fxLayers.find(x => x.id === id);
    $$('[data-frng2]', el).forEach(rg => { const f = findF(rg.dataset.frng2); rg.onpointerdown = E.beginDrag; rg.oninput = () => { f.i = +rg.value; rg.previousElementSibling.querySelector('b').textContent = '%' + rg.value; E.render(); }; rg.onchange = () => E.endDrag(); });
    $$('[data-fang]', el).forEach(rg => { const f = findF(rg.dataset.fang); rg.onpointerdown = E.beginDrag; rg.oninput = () => { f.params.angle = +rg.value; rg.previousElementSibling.querySelector('b').textContent = rg.value + '°'; E.render(); }; rg.onchange = () => E.endDrag(); });
    $$('[data-tt]', el).forEach(ta => {
      ta.onfocus = E.beginDrag;
      ta.oninput = () => { findT(ta.dataset.tt).text = ta.value; E.render(); $('.nm', ta.closest('.lcard')).textContent = ta.value || '(boş)'; };
      ta.onblur = () => { E.endDrag(); E.drawTimeline(); };
      ta.onkeydown = e => e.stopPropagation();
    });
    $$('[data-tanim]', el).forEach(b => b.onclick = () => { const [id, k] = b.dataset.tanim.split(':'); E.change(() => findT(id).anim = k); });
    $$('[data-tbox]', el).forEach(b => b.onclick = () => E.change(() => { const t = findT(b.dataset.tbox); t.box = t.box === false; }));
    $$('[data-tup]', el).forEach(b => b.onclick = () => E.change(() => { const t = findT(b.dataset.tup); t.upper = t.upper === false; }));
    const setCol = (key, val) => { const [k, id, pk] = key.split(':'); E.change(() => { if (k === 'fxp') findF(id).params[pk] = val; else findT(id)[k === 'tcolor' ? 'color' : 'boxColor'] = val; }); };
    $$('.sw[data-c]', el).forEach(b => b.onclick = () => setCol(b.dataset.k, b.dataset.c));
    $$('input[type=color]', el).forEach(i => i.onchange = () => setCol(i.dataset.k, i.value.toUpperCase()));
    const rangeBind = (attr, find, conv, label) => $$(`[${attr}]`, el).forEach(r => {
      const [id, k] = r.getAttribute(attr).split(':');
      r.onpointerdown = E.beginDrag;
      r.oninput = () => { find(id)[k] = conv(k, +r.value); r.previousElementSibling.querySelector('b').textContent = label(k, +r.value); E.render(); E.drawTimeline(); };
      r.onchange = () => E.endDrag();
    });
    rangeBind('data-trng', findT, (k, v) => v, (k, v) => k === 'y' ? '%' + v : v);
    rangeBind('data-irng', findI, (k, v) => k === 'opacity' ? v / 100 : v, (k, v) => '%' + v);
    rangeBind('data-zrng', findZ, (k, v) => k === 'z' ? 1 + v / 100 : v / 10, (k, v) => k === 'z' ? v + '%' : (v / 10).toFixed(1) + ' sn');
    $$('[data-ipos]', el).forEach(b => b.onclick = () => { const [id, k] = b.dataset.ipos.split(':'); E.change(() => findI(id).pos = k); });
    $$('[data-zshake]', el).forEach(b => b.onclick = () => E.change(() => { const z = findZ(b.dataset.zshake); z.shake = !z.shake; }));
    $$('[data-znow]', el).forEach(b => b.onclick = () => E.change(() => findZ(b.dataset.znow).t = +now().toFixed(3)));
    const setTime = (attr, key) => $$(`[${attr}]`, el).forEach(b => b.onclick = () => {
      const [type, id] = b.getAttribute(attr).split(':'); const o = type === 'text' ? findT(id) : type === 'fx' ? findF(id) : findI(id); const t = +now().toFixed(3);
      E.change(() => { if (key === 's') { o.s = Math.min(t, o.e - .2); } else { o.e = Math.max(t, o.s + .2); } });
    });
    setTime('data-sets', 's'); setTime('data-sete', 'e');
    const mv = $('#musVol');
    if (mv) { mv.onpointerdown = E.beginDrag; mv.oninput = () => { md.music.vol = mv.value / 100; mv.previousElementSibling.querySelector('b').textContent = '%' + mv.value; music.volume = md.music.vol; }; mv.onchange = () => E.endDrag(); }
    const ms = $('#musStart'); if (ms) ms.onclick = () => E.change(() => md.music.s = +now().toFixed(3));
  };
  E.deleteLayer = (type, id) => {
    E.change(() => {
      const p = E.project;
      if (type === 'text') p.effects.texts = p.effects.texts.filter(x => x.id !== id);
      if (type === 'image') p.media.images = p.media.images.filter(x => x.id !== id);
      if (type === 'zoom') p.effects.zooms = p.effects.zooms.filter(x => x.id !== id);
      if (type === 'fx') p.effects.fxLayers = p.effects.fxLayers.filter(x => x.id !== id);
      if (type === 'music') p.media.music = null;
    });
    if (type === 'music') { music.pause(); E.loadMusic(); }
    E.sel = null; E.renderLayers();
  };

  /* ====================================================== TIMELINE */
  const tlc = $('#tlCanvas'), tl = tlc.getContext('2d'), scroll = $('#tlScroll');
  const ROWS = [
    { key: 'ruler', h: 22 }, { key: 'video', h: 40, label: 'Video', color: '#7c5cff' }, { key: 'cap', h: 22, label: 'Altyazı', color: '#c34bff' },
    { key: 'text', h: 22, label: 'Yazılar', color: '#ffb547' }, { key: 'fx', h: 22, label: 'Efektler', color: '#b388ff' }, { key: 'image', h: 22, label: 'Resimler', color: '#3dffa2' },
    { key: 'music', h: 22, label: 'Müzik', color: '#22d3ee' }, { key: 'zoom', h: 22, label: 'Zoom', color: '#ff3d8b' },
  ];
  let rowY = {}; { let y = 0; ROWS.forEach(r => { rowY[r.key] = [y, y + r.h]; y += r.h + 1; }); }
  const TLH = 205, LBL = 8;
  const hidden = k => !!((E.project.effects.hide || {})[k]);
  const EYE = '<svg viewBox="0 0 24 24"><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg>';
  const EYE_OFF = '<svg viewBox="0 0 24 24"><path d="M3 3l18 18M10.6 5.1A10 10 0 0 1 12 5c6.4 0 10 7 10 7a17 17 0 0 1-3.2 4M6.6 6.6A17 17 0 0 0 2 12s3.6 7 10 7a9.7 9.7 0 0 0 5.4-1.6"/></svg>';
  E.renderTlLayers = () => {
    const p = E.project; if (!p) return;
    const cnt = { video: segs().length + ' parça', cap: p.captions.length || '', text: p.effects.texts.length || '', fx: (p.effects.fxLayers.length + (p.effects.transition.type !== 'none' ? ' +geçiş' : '')) || '', image: p.media.images.length || '', music: p.media.music ? '1' : '', zoom: p.effects.zooms.length || '' };
    $('#tlLayers').innerHTML = ROWS.map((r, i) => r.key === 'ruler'
      ? `<div class="tl-row head" style="height:${r.h + 1}px"><span style="width:20px;text-align:center">#</span><span style="width:22px">👁</span><span style="width:12px"></span><span class="nm">Katman adı</span></div>`
      : `<div class="tl-row ${r.key !== 'video' && hidden(r.key) ? 'off' : ''}" style="height:${r.h + 1}px" data-row="${r.key}">
          <span class="num">${i}</span>
          ${r.key === 'video' ? '<span class="eye" title="Video her zaman görünür">' + EYE + '</span>' : `<button class="eye" data-eye="${r.key}" title="Göster / gizle">${hidden(r.key) ? EYE_OFF : EYE}</button>`}
          <span class="lab" style="background:${r.color}"></span><span class="nm">${r.label}</span><span class="cnt">${cnt[r.key]}</span></div>`).join('');
    $$('[data-eye]', $('#tlLayers')).forEach(b => b.onclick = () => E.change(() => {
      const h = E.project.effects.hide = Object.assign({}, E.project.effects.hide || {});
      h[b.dataset.eye] = !h[b.dataset.eye];
      if (b.dataset.eye === 'music') music.pause();
    }));
  };
  E.sizeTimeline = () => {
    if (!E.project) return;
    const vw = scroll.clientWidth || 800;
    const w = Math.max(vw, Math.round((vw - LBL - 10) * E.zoom + LBL + 10));
    tlc.style.width = w + 'px'; tlc.width = w * devicePixelRatio; tlc.height = TLH * devicePixelRatio;
    E.drawTimeline();
  };
  const pps = () => (tlc.clientWidth - LBL - 10) / E.project.duration;
  const tx2 = t => LBL + t * pps();
  const x2t = x => KS.clamp((x - LBL) / pps(), 0, E.project.duration);
  $('#zoomRange').oninput = e => {
    const t = now(), rel = tx2(t) - scroll.scrollLeft;
    E.zoom = +e.target.value; E.sizeTimeline();
    scroll.scrollLeft = tx2(t) - rel;
  };
  scroll.addEventListener('scroll', () => E.drawTimeline());
  // fare tekerleği: yakınlaş/uzaklaş (farenin olduğu yere doğru) · Shift + tekerlek: yana kaydır
  scroll.addEventListener('wheel', e => {
    if (!E.project) return;
    e.preventDefault();
    if (e.shiftKey || Math.abs(e.deltaX) > Math.abs(e.deltaY)) { scroll.scrollLeft += (e.deltaX || e.deltaY); return; }
    const r = tlc.getBoundingClientRect(), mx = e.clientX - r.left, t = x2t(mx), rel = mx - scroll.scrollLeft;
    E.zoom = KS.clamp(E.zoom * (e.deltaY < 0 ? 1.18 : 1 / 1.18), 1, 40);
    const z = $('#zoomRange'); z.value = E.zoom; KS.paintRange(z);
    E.sizeTimeline();
    scroll.scrollLeft = tx2(t) - rel;
    E.drawTimeline();
  }, { passive: false });

  const rr = (x, a, b, y0, y1, r, fill) => { x.beginPath(); x.roundRect(a, y0, Math.max(2, b - a), y1 - y0, r); x.fillStyle = fill; x.fill(); };
  E.drawTimeline = () => {
    const p = E.project; if (!p || !tlc.width) return;
    const x = tl, dpr = devicePixelRatio, W = tlc.clientWidth;
    x.setTransform(dpr, 0, 0, dpr, 0, 0);
    x.clearRect(0, 0, W, TLH);
    const D = p.duration, sl = scroll.scrollLeft, vw = scroll.clientWidth;
    // satır zeminleri (AE'deki gibi şeritli)
    ROWS.forEach((r, i) => { const [y0, y1] = rowY[r.key]; x.fillStyle = r.key === 'ruler' ? '#1f1f27' : (i % 2 ? '#1a1a21' : '#17171d'); x.fillRect(0, y0, W, y1 - y0 + 1); x.fillStyle = '#24242d'; x.fillRect(0, y1, W, 1); });
    // cetvel
    const step = [0.5, 1, 2, 5, 10, 15, 30, 60, 120, 300].find(s => s * pps() > 70) || 600;
    x.font = '10px Consolas, monospace'; x.fillStyle = 'rgba(255,255,255,.45)';
    for (let t = 0; t <= D; t += step) { const xx = tx2(t); x.fillRect(xx, 14, 1, 8); x.fillText(KS.fmt(t), xx + 3, 12); }
    for (let t = 0; t <= D; t += step / 5) { x.fillStyle = 'rgba(255,255,255,.15)'; x.fillRect(tx2(t), 18, 1, 4); }
    // çalışma alanı (kalan parçalar) cetvelde
    segs().forEach(s => { x.fillStyle = 'rgba(124,92,255,.35)'; x.fillRect(tx2(s.start), 0, tx2(s.end) - tx2(s.start), 3); });
    // video satırı
    const [vy0, vy1] = rowY.video;
    x.fillStyle = 'rgba(255,255,255,.03)'; x.fillRect(LBL, vy0, W - LBL, vy1 - vy0);
    // silinmiş kısımlar (çizgili)
    x.save(); x.beginPath(); x.rect(tx2(0), vy0, tx2(D) - tx2(0), vy1 - vy0); x.clip();
    x.strokeStyle = 'rgba(255,84,112,.18)'; x.lineWidth = 6;
    for (let k = tx2(0) - 60; k < tx2(D) + 60; k += 14) { x.beginPath(); x.moveTo(k, vy1); x.lineTo(k + 40, vy0); x.stroke(); }
    x.restore();
    segs().forEach((s, i) => {
      const a = tx2(s.start), b = tx2(s.end), sel = isSel('seg', i);
      const g = x.createLinearGradient(0, vy0, 0, vy1); g.addColorStop(0, sel ? 'rgba(255,61,139,.55)' : 'rgba(124,92,255,.5)'); g.addColorStop(1, sel ? 'rgba(195,75,255,.35)' : 'rgba(124,92,255,.22)');
      rr(x, a, b, vy0, vy1, 6, g);
      // dalga formu
      if (E.wave && E.wave.length) {
        x.save(); x.beginPath(); x.rect(a, vy0, b - a, vy1 - vy0); x.clip();
        x.fillStyle = 'rgba(255,255,255,.55)'; const n = E.wave.length, mid = (vy0 + vy1) / 2, hh = (vy1 - vy0) / 2 - 3;
        const i0 = Math.max(0, Math.floor(s.start / D * n)), i1 = Math.min(n, Math.ceil(s.end / D * n));
        const bw = Math.max(1, (b - a) / Math.max(1, i1 - i0));
        for (let k = i0; k < i1; k++) { const xx = tx2(k / n * D), h = Math.max(1, E.wave[k] * hh); x.fillRect(xx, mid - h, Math.max(1, bw - .5), h * 2); }
        x.restore();
      }
      x.strokeStyle = sel ? '#ff3d8b' : 'rgba(180,160,255,.9)'; x.lineWidth = sel ? 2 : 1.2;
      x.beginPath(); x.roundRect(a + .5, vy0 + .5, Math.max(2, b - a - 1), vy1 - vy0 - 1, 6); x.stroke();
      x.fillStyle = '#fff'; x.fillRect(a + 2, vy0 + 9, 3, vy1 - vy0 - 18); x.fillRect(b - 5, vy0 + 9, 3, vy1 - vy0 - 18);
    });
    // altyazı
    const [cy0, cy1] = rowY.cap;
    p.captions.forEach(c => { rr(x, tx2(c.s), tx2(c.e), cy0 + 2, cy1 - 2, 4, c.words.some(w => w.p < .55) ? 'rgba(255,181,71,.7)' : 'rgba(195,75,255,.65)'); });
    // yazılar
    const bar = (row, a, b, label, color, sel) => {
      const [y0, y1] = rowY[row];
      rr(x, tx2(a), tx2(b), y0 + 1, y1 - 1, 5, color);
      if (sel) { x.strokeStyle = '#fff'; x.lineWidth = 2; x.beginPath(); x.roundRect(tx2(a), y0 + 1, tx2(b) - tx2(a), y1 - y0 - 2, 5); x.stroke(); }
      x.save(); x.beginPath(); x.rect(tx2(a), y0, tx2(b) - tx2(a), y1 - y0); x.clip();
      x.fillStyle = '#0b0a12'; x.font = '700 10px Segoe UI'; x.fillText(label, tx2(a) + 6, y1 - 5); x.restore();
    };
    p.effects.texts.forEach(t => bar('text', t.s, t.e, t.text, 'rgba(255,181,71,.85)', isSel('text', t.id)));
    p.effects.fxLayers.forEach(f => bar('fx', f.s, f.e, (KS.fx.LIST[f.kind] || [f.kind])[0], 'rgba(179,136,255,.85)', isSel('fx', f.id)));
    // kesim noktalarındaki geçişler
    if (p.effects.transition.type !== 'none') {
      let acc = 0; const ss = segs();
      for (let i = 0; i < ss.length - 1; i++) {
        const xx = tx2(ss[i].end), y = (vy0 + vy1) / 2;
        x.fillStyle = '#b388ff'; x.beginPath(); x.moveTo(xx, y - 7); x.lineTo(xx + 6, y); x.lineTo(xx, y + 7); x.lineTo(xx - 6, y); x.closePath(); x.fill();
        x.strokeStyle = '#fff'; x.lineWidth = 1; x.stroke();
      }
    }
    p.media.images.forEach(im => bar('image', im.s, im.e, im.name, 'rgba(61,255,162,.8)', isSel('image', im.id)));
    if (p.media.music) { const m = p.media.music; bar('music', m.s, D, '🎵 ' + m.name, 'rgba(34,211,238,.75)', isSel('music')); }
    const [zy0, zy1] = rowY.zoom;
    p.effects.zooms.forEach(z => {
      const xx = tx2(z.t), w = Math.max(8, (+z.d || .8) * speed() * pps());
      rr(x, xx, xx + w, zy0 + 2, zy1 - 2, 4, isSel('zoom', z.id) ? '#ff3d8b' : 'rgba(255,61,139,.6)');
      x.fillStyle = '#fff'; x.font = '9px Segoe UI'; x.fillText(z.shake ? '💥' : '🔍', xx + 2, zy1 - 4);
    });
    // gizli katmanları karart
    ROWS.forEach(r => { if (r.label && r.key !== 'video' && hidden(r.key)) { const [y0, y1] = rowY[r.key]; x.fillStyle = 'rgba(23,23,29,.72)'; x.fillRect(0, y0, W, y1 - y0 + 1); } });
    // oynatma çizgisi (AE mavisi)
    const ph = tx2(now());
    x.fillStyle = '#3fa9ff'; x.fillRect(ph - .5, 0, 1.5, TLH);
    x.beginPath(); x.moveTo(ph - 7, 0); x.lineTo(ph + 7, 0); x.lineTo(ph + 7, 10); x.lineTo(ph, 17); x.lineTo(ph - 7, 10); x.closePath(); x.fill();
    // otomatik kaydır
    if (!video.paused && (ph > sl + vw - 40 || ph < sl + LBL)) scroll.scrollLeft = ph - LBL - 40;
    const kept = segs().reduce((s, g) => s + g.end - g.start, 0);
    $('#tlInfo').textContent = `Video: ${KS.fmt(outDur())}${kept < D - .05 ? ` (${KS.fmt(D - kept)} kesildi)` : ''}`;
  };

  /* --- timeline fare --- */
  const rowAt = y => (ROWS.find(r => y >= rowY[r.key][0] && y <= rowY[r.key][1] + 1) || {}).key;
  tlc.addEventListener('mousedown', e => {
    const p = E.project; if (!p) return;
    const r = tlc.getBoundingClientRect(), mx = e.clientX - r.left, my = e.clientY - r.top;
    if (mx < scroll.scrollLeft + LBL) return;
    const row = rowAt(my), t = x2t(mx), near = (tt) => Math.abs(tx2(tt) - mx) < 7;
    let drag = null;
    const S = segs();
    if (row === 'video') {
      for (let i = 0; i < S.length; i++) {
        if (near(S[i].start)) { drag = { kind: 'segS', i }; break; }
        if (near(S[i].end)) { drag = { kind: 'segE', i }; break; }
      }
      if (!drag) { const i = S.findIndex(s => t >= s.start && t <= s.end); if (i >= 0) { E.sel = { type: 'seg', id: i }; } else E.sel = null; drag = { kind: 'seek' }; }
      p.segments = S;
    } else if (row === 'text' || row === 'image' || row === 'fx') {
      const list = row === 'text' ? p.effects.texts : row === 'fx' ? p.effects.fxLayers : p.media.images;
      const o = list.slice().reverse().find(o => t >= o.s - 7 / pps() && t <= o.e + 7 / pps());
      if (o) { drag = { kind: near(o.s) ? 'oS' : near(o.e) ? 'oE' : 'oM', o, t0: t, s0: o.s, e0: o.e }; E.select({ type: row, id: o.id }); }
      else drag = { kind: 'seek' };
    } else if (row === 'music' && p.media.music && t >= p.media.music.s - 7 / pps()) {
      drag = { kind: 'mus', o: p.media.music, t0: t, s0: p.media.music.s }; E.select({ type: 'music' });
    } else if (row === 'zoom') {
      const z = p.effects.zooms.find(z => t >= z.t - 7 / pps() && t <= z.t + Math.max(8 / pps(), (+z.d || .8) * speed()));
      if (z) { drag = { kind: 'zoom', o: z, t0: t, s0: z.t }; E.select({ type: 'zoom', id: z.id }); } else drag = { kind: 'seek' };
    } else if (row === 'cap') {
      const i = E.capAt(t); if (i >= 0) { E.rt('subs'); setTimeout(() => { const rw = $(`.cap[data-ci="${i}"]`); if (rw) rw.scrollIntoView({ block: 'center', behavior: 'smooth' }); }, 30); }
      drag = { kind: 'seek' };
    } else drag = { kind: 'seek' };
    if (drag.kind === 'seek') { if (!video.paused) E.pause(); E.seek(t); }
    else E.beginDrag();
    E.drawTimeline();
    const move = ev => {
      const t2 = x2t(ev.clientX - r.left), d = drag;
      const ss = p.segments;
      if (d.kind === 'seek') { E.seek(t2); return; }
      if (d.kind === 'segS') { const lo = d.i > 0 ? ss[d.i - 1].end : 0; ss[d.i].start = +KS.clamp(t2, lo, ss[d.i].end - .1).toFixed(3); video.currentTime = ss[d.i].start; }
      if (d.kind === 'segE') { const hi = d.i < ss.length - 1 ? ss[d.i + 1].start : p.duration; ss[d.i].end = +KS.clamp(t2, ss[d.i].start + .1, hi).toFixed(3); video.currentTime = Math.max(ss[d.i].start, ss[d.i].end - .05); }
      if (d.kind === 'oM') { const len = d.e0 - d.s0, s = KS.clamp(d.s0 + t2 - d.t0, 0, p.duration - len); d.o.s = +s.toFixed(3); d.o.e = +(s + len).toFixed(3); }
      if (d.kind === 'oS') d.o.s = +KS.clamp(t2, 0, d.o.e - .2).toFixed(3);
      if (d.kind === 'oE') d.o.e = +KS.clamp(t2, d.o.s + .2, p.duration).toFixed(3);
      if (d.kind === 'mus') d.o.s = +KS.clamp(d.s0 + t2 - d.t0, 0, p.duration - .5).toFixed(3);
      if (d.kind === 'zoom') d.o.t = +KS.clamp(d.s0 + t2 - d.t0, 0, p.duration - .1).toFixed(3);
      E.render(); E.drawTimeline();
    };
    const up = () => {
      window.removeEventListener('mousemove', move); window.removeEventListener('mouseup', up);
      if (drag.kind !== 'seek') { E.endDrag(); E.renderLayers(); if (drag.kind.startsWith('seg')) E.renderSubs(); }
      E.render(); E.drawTimeline();
    };
    window.addEventListener('mousemove', move); window.addEventListener('mouseup', up);
  });
  tlc.addEventListener('mousemove', e => {
    if (!E.project || e.buttons) return;
    const r = tlc.getBoundingClientRect(), mx = e.clientX - r.left, my = e.clientY - r.top, row = rowAt(my), t = x2t(mx);
    let cur = 'pointer';
    const near = tt => Math.abs(tx2(tt) - mx) < 7;
    if (row === 'video' && segs().some(s => near(s.start) || near(s.end))) cur = 'ew-resize';
    if ((row === 'text' || row === 'image' || row === 'fx')) { const list = row === 'text' ? E.project.effects.texts : row === 'fx' ? E.project.effects.fxLayers : E.project.media.images; const o = list.find(o => t >= o.s - 7 / pps() && t <= o.e + 7 / pps()); if (o) cur = near(o.s) || near(o.e) ? 'ew-resize' : 'grab'; }
    if (row === 'music' && E.project.media.music && t >= E.project.media.music.s) cur = 'grab';
    tlc.style.cursor = cur;
  });

  /* --- kesme araçları --- */
  E.split = () => {
    const t = now(), S = segs(), i = S.findIndex(s => t > s.start + .1 && t < s.end - .1);
    if (i < 0) return KS.toast('Bölmek için oynatma çizgisini bir parçanın içine getir', '', [], 2000);
    E.change(() => { S.splice(i, 1, { start: S[i].start, end: +t.toFixed(3) }, { start: +t.toFixed(3), end: S[i].end }); E.project.segments = S; });
    E.sel = { type: 'seg', id: i + 1 }; E.drawTimeline();
  };
  E.deleteSel = () => {
    const s = E.sel; if (!s) return KS.toast('Önce timeline\'da bir parça seç', '', [], 1800);
    if (s.type === 'seg') {
      const S = segs();
      if (S.length <= 1) return KS.toast('Son parçayı silemezsin. Kenarlarından kırpabilirsin.', '', [], 2500);
      E.change(() => { S.splice(s.id, 1); E.project.segments = S; });
      E.sel = null; E.drawTimeline();
      const nx = segs().find(g => g.start >= now()) || segs()[0]; E.seek(nx.start);
    } else E.deleteLayer(s.type, s.id);
  };
  $('#splitBtn').onclick = E.split; $('#delBtn').onclick = E.deleteSel;
  $('#addFileBtn2').onclick = KS.addFile; $('#addTextBtn').onclick = E.addText; $('#addZoomBtn').onclick = () => E.addZoom(false);
  $('#resetCutBtn').onclick = () => E.change(() => E.project.segments = [{ start: 0, end: E.project.duration }]);
  $('#silenceBtn').onclick = () => {
    const p = E.project;
    const words = p.captions.flatMap(c => c.words);
    if (!words.length) return KS.toast('Boşlukları bulmak için önce altyazı çıkarılmalı', 'err');
    const pad = .18, iv = [];
    words.slice().sort((a, b) => a.s - b.s).forEach(w => {
      const a = Math.max(0, w.s - pad), b = Math.min(p.duration, w.e + pad + .07);
      if (iv.length && a - iv[iv.length - 1][1] < .45) iv[iv.length - 1][1] = Math.max(iv[iv.length - 1][1], b); else iv.push([a, b]);
    });
    const out = [];
    segs().forEach(s => iv.forEach(([a, b]) => { const x0 = Math.max(a, s.start), x1 = Math.min(b, s.end); if (x1 - x0 > .15) out.push({ start: +x0.toFixed(3), end: +x1.toFixed(3) }); }));
    if (!out.length) return KS.toast('Kırpılacak boşluk bulunamadı');
    const before = outDur();
    E.change(() => p.segments = out);
    KS.toast(`✨ Boşluklar kırpıldı: ${KS.fmt(before)} → ${KS.fmt(outDur())}`, 'ok', [{ label: 'Geri al', fn: E.undo }]);
  };

  /* ====================================================== DIŞA AKTAR */
  $('#exportBtn').onclick = () => E.exportDialog();
  E.exportDialog = () => {
    if (!E.project) return;
    const s = KS.state.settings, p = E.project;
    const o = { cozunurluk: +s.cozunurluk || 1080, fps: String(s.fps || 'kaynak'), kalite: s.kalite || 'yuksek', ses_dengele: s.ses_dengele !== false };
    const srcFps = Math.round(p.fps || 30);
    const md = KS.modal(`<h2>Dışa Aktar</h2><p class="msub">Dikey (9:16) video olarak kaydedilecek. Seçimlerin bir sonraki sefere hatırlanır.</p>
      <div class="opt-group"><label>Çözünürlük</label><div class="opts" id="oRes">
        ${[[720, '720p', 'Hızlı'], [1080, '1080p', 'Full HD'], [1440, '2K', '1440p · en net']].map(([v, a, b]) => `<button class="opt" data-v="${v}"><b>${a}</b><small>${b}</small></button>`).join('')}</div></div>
      <div class="opt-group"><label>Kare hızı (FPS)</label><div class="opts" id="oFps">
        ${[['kaynak', 'Orijinal', srcFps + ' FPS'], ['30', '30', 'FPS'], ['60', '60', 'FPS · akıcı'], ['90', '90', 'FPS · en akıcı']].map(([v, a, b]) => `<button class="opt" data-v="${v}"><b>${a}</b><small>${b}</small></button>`).join('')}</div></div>
      <div class="note" id="fpsNote" hidden></div>
      <div class="opt-group"><label>Kalite</label><div class="opts" id="oQ">
        <button class="opt" data-v="yuksek"><b>Yüksek</b><small>Önerilen</small></button><button class="opt" data-v="normal"><b>Normal</b><small>Daha küçük dosya</small></button></div></div>
      <button class="tog ${o.ses_dengele ? 'on' : ''}" id="oLoud" style="width:100%;margin-bottom:14px">Sesi dengele (çok bağırınca patlamasın, kısık yerler duyulsun)<i></i></button>
      <div class="summary"><span>Süre: <b>${KS.fmt(outDur())}</b></span><span>Altyazı: <b>${p.captions.length ? 'var' : 'yok'}</b></span><span>Katman: <b>${p.effects.texts.length + p.media.images.length + (p.media.music ? 1 : 0)}</b></span></div>
      <div class="mfoot"><button class="btn ghost" data-close>Vazgeç</button><button class="btn primary glow" id="oGo">${KS.icon.down}Dışa Aktar</button></div>`);
    const paint = () => {
      $$('#oRes .opt', md.el).forEach(b => b.classList.toggle('active', +b.dataset.v === o.cozunurluk));
      $$('#oFps .opt', md.el).forEach(b => b.classList.toggle('active', b.dataset.v === o.fps));
      $$('#oQ .opt', md.el).forEach(b => b.classList.toggle('active', b.dataset.v === o.kalite));
      const n = $('#fpsNote', md.el), f = +o.fps;
      if (o.fps !== 'kaynak' && f > srcFps + 1) { n.hidden = false; n.textContent = `Video aslında ${srcFps} FPS. ${f} FPS için ara kareler üretilecek: daha akıcı olur ama dışa aktarma birkaç kat uzun sürer.`; }
      else n.hidden = true;
    };
    $$('#oRes .opt', md.el).forEach(b => b.onclick = () => { o.cozunurluk = +b.dataset.v; paint(); });
    $$('#oFps .opt', md.el).forEach(b => b.onclick = () => { o.fps = b.dataset.v; paint(); });
    $$('#oQ .opt', md.el).forEach(b => b.onclick = () => { o.kalite = b.dataset.v; paint(); });
    $('#oLoud', md.el).onclick = e => { o.ses_dengele = !o.ses_dengele; e.currentTarget.classList.toggle('on', o.ses_dengele); };
    $('#oGo', md.el).onclick = async () => {
      md.close();
      await E.flush();
      const r = await KS.api(`/api/project/${p.id}/export`, o);
      Object.assign(KS.state.settings, o);
      KS.trackJob(r.job); KS.openJobs();
      KS.toast('🎬 Dışa aktarma başladı. Bu sırada başka klip düzenleyebilirsin.');
    };
    paint();
  };

  /* ====================================================== kısayollar */
  E.onKey = e => {
    if (!E.project) return;
    const k = e.key, c = e.ctrlKey || e.metaKey;
    const fr = 1 / (E.project.fps || 30);
    if (k === ' ') { e.preventDefault(); E.toggle(); }
    else if (c && k.toLowerCase() === 'z') { e.preventDefault(); e.shiftKey ? E.redo() : E.undo(); }
    else if (c && k.toLowerCase() === 'y') { e.preventDefault(); E.redo(); }
    else if (c && k.toLowerCase() === 's') { e.preventDefault(); $('#saveState').classList.add('dirty'); E.flush().then(() => KS.toast('✓ Kaydedildi', 'ok', [], 1200)); }
    else if (c && k.toLowerCase() === 'e') { e.preventDefault(); E.exportDialog(); }
    else if (c) return;
    else if (k.toLowerCase() === 's') E.split();
    else if (k === 'Delete' || k === 'Backspace') { e.preventDefault(); E.deleteSel(); }
    else if (k === 'ArrowLeft') { e.preventDefault(); E.seek(now() - (e.shiftKey ? fr : 1)); }
    else if (k === 'ArrowRight') { e.preventDefault(); E.seek(now() + (e.shiftKey ? fr : 1)); }
    else if (k === 'Home') E.seek(segs()[0].start);
    else if (k === 'End') E.seek(segs()[segs().length - 1].end - .05);
    else if (k.toLowerCase() === 'z') E.addZoom(false);
    else if (k.toLowerCase() === 'x') E.addZoom(true);
    else if (k.toLowerCase() === 't') { e.preventDefault(); E.addText(); }
    else if (k.toLowerCase() === 'f') E.nextFlag();
    else if (k === '+' || k === '=') { const z = $('#zoomRange'); z.value = Math.min(40, E.zoom * 1.3); z.oninput({ target: z }); KS.paintRange(z); }
    else if (k === '-') { const z = $('#zoomRange'); z.value = Math.max(1, E.zoom / 1.3); z.oninput({ target: z }); KS.paintRange(z); }
    else if (k === 'Escape') { E.sel = null; E.drawTimeline(); E.renderLayers(); }
  };
})();
