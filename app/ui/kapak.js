/* Kapak Stüdyosu — katmanlı kapak (thumbnail) editörü */
(() => {
  const U = KS.ui, host = $('#tKapak');
  const SIZES = { yt: [1280, 720, 'YouTube 16:9'], dik: [1080, 1920, 'Shorts / Reels 9:16'], kare: [1080, 1080, 'Kare 1:1'] };
  const FONTS = [['Anton', 'Anton'], ['Bebas Neue', 'Bebas'], ['Montserrat Black', 'Montserrat'], ['Archivo Black', 'Archivo'], ['Bangers', 'Bangers'], ['Luckiest Guy', 'Luckiest'], ['Bowlby One SC', 'Bowlby'], ['Rubik Mono One', 'Rubik Mono'], ['Impact', 'Impact']];
  const SW = ['#ffffff', '#000000', '#ffd400', '#ff2d2d', '#ff7a00', '#2dff6a', '#00d0ff', '#2d6bff', '#b84dff', '#ff4fd8'];
  const EMOJI = ['😱', '😂', '🤯', '😡', '😭', '💀', '🔥', '👀', '❗', '❓', '💯', '🤑', '😳', '🥶', '👑', '⚡', '💥', '✅', '❌', '🎁'];
  const SHAPES = [['ok', '➜ Ok'], ['egri', '↪ Eğri ok'], ['daire', '◯ Daire'], ['kutu', '▢ Kutu'], ['cizgi', '— Çizgi']];
  const BGS = [['#ff0844', '#ffb199'], ['#7f00ff', '#e100ff'], ['#00c6ff', '#0072ff'], ['#f7971e', '#ffd200'], ['#11998e', '#38ef7d'], ['#232526', '#414345'], ['#ff512f', '#dd2476'], ['#0f0c29', '#302b63']];

  let K = blank(), uid = 1, inited = false, hist = [], fut = [], drag = null, raf = 0, guides = null;
  const IMG = {}, OUT = {}, TRIM = {};
  function blank() {
    return { size: 'yt', W: 1280, H: 720, bg: { mode: 'gradyan', path: '', url: '', zoom: 1, ox: 0, oy: 0, blur: 0, bright: 100, sat: 115, contrast: 105, vignette: 35, tint: '#000000', tintA: 0, c1: '#ff0844', c2: '#ffb199', angle: 135, style: 'duz' }, layers: [], sel: null, src: null, frames: [], t: 0, cutJob: null, pendingKisi: null, saved: null, fmt: 'jpg' };
  }
  const L = id => K.layers.find(l => l.id === id);
  const selL = () => K.sel && K.sel !== 'bg' ? L(K.sel) : null;
  const clone = x => JSON.parse(JSON.stringify(x));
  const snap = () => JSON.stringify({ size: K.size, W: K.W, H: K.H, bg: K.bg, layers: K.layers.map(l => { const c = { ...l }; delete c._w; delete c._h; return c; }) });
  const persist = () => { try { localStorage.setItem('kapak_son', JSON.stringify({ d: snap(), src: K.src, frames: K.frames, t: K.t, fmt: K.fmt })); } catch (e) { } };
  const commit = () => { const s = snap(); if (hist[hist.length - 1] !== s) { hist.push(s); if (hist.length > 80) hist.shift(); fut = []; } persist(); updUndo(); };
  const restore = s => { Object.assign(K, JSON.parse(s)); if (K.sel && K.sel !== 'bg' && !L(K.sel)) K.sel = null; side(); draw(); persist(); };
  const undo = () => { if (hist.length < 2) return; fut.push(hist.pop()); restore(hist[hist.length - 1]); updUndo(); };
  const redo = () => { if (!fut.length) return; const s = fut.pop(); hist.push(s); restore(s); updUndo(); };
  const updUndo = () => { const a = $('#kpUndo', host), b = $('#kpRedo', host); if (a) a.disabled = hist.length < 2; if (b) b.disabled = !fut.length; };

  const img = url => {
    if (!url) return null;
    let i = IMG[url];
    if (!i) { i = IMG[url] = new Image(); i.onload = () => { draw(); }; i.onerror = () => { i._bad = 1; }; i.src = url; }
    return i.complete && i.naturalWidth ? i : null;
  };
  /* kesilmiş kişinin dolu kısmı (boş kenarları at) */
  const trimOf = url => {
    if (TRIM[url]) return TRIM[url];
    const i = IMG[url]; if (!i || !i.naturalWidth) return null;
    const w = i.naturalWidth, h = i.naturalHeight, c = document.createElement('canvas'); c.width = w; c.height = h;
    const x = c.getContext('2d', { willReadFrequently: true }); x.drawImage(i, 0, 0);
    let d; try { d = x.getImageData(0, 0, w, h).data; } catch (e) { return TRIM[url] = { x: 0, y: 0, w, h }; }
    let x0 = w, y0 = h, x1 = -1, y1 = -1;
    for (let y = 0; y < h; y += 2) for (let xx = 0; xx < w; xx += 2) if (d[(y * w + xx) * 4 + 3] > 24) { if (xx < x0) x0 = xx; if (xx > x1) x1 = xx; if (y < y0) y0 = y; if (y > y1) y1 = y; }
    if (x1 < 0) return TRIM[url] = { x: 0, y: 0, w, h };
    x0 = Math.max(0, x0 - 2); y0 = Math.max(0, y0 - 2);
    return TRIM[url] = { x: x0, y: y0, w: Math.min(w, x1 + 3) - x0, h: Math.min(h, y1 + 3) - y0 };
  };
  /* kontur + renk ayarı uygulanmış görsel (önbellekli) */
  const outlined = l => {
    const i = img(l.url), tr = i && (l.type === 'kisi' ? trimOf(l.url) : { x: 0, y: 0, w: i.naturalWidth, h: i.naturalHeight });
    if (!i || !tr) return null;
    const r = Math.round(l.stroke || 0), key = [l.url, r, l.strokeColor, l.bright, l.sat, l.contrast].join('|');
    if (OUT[l.id] && OUT[l.id].key === key) return OUT[l.id];
    const c = document.createElement('canvas'); c.width = tr.w + r * 2; c.height = tr.h + r * 2;
    const x = c.getContext('2d');
    if (r > 0) {
      const s = document.createElement('canvas'); s.width = tr.w; s.height = tr.h;
      const sx = s.getContext('2d'); sx.drawImage(i, tr.x, tr.y, tr.w, tr.h, 0, 0, tr.w, tr.h);
      sx.globalCompositeOperation = 'source-in'; sx.fillStyle = l.strokeColor || '#fff'; sx.fillRect(0, 0, tr.w, tr.h);
      for (const rr of [r, r * .7, r * .4]) for (let a = 0; a < 32; a++) x.drawImage(s, r + Math.cos(a / 32 * Math.PI * 2) * rr, r + Math.sin(a / 32 * Math.PI * 2) * rr);
    }
    x.filter = `brightness(${l.bright || 100}%) saturate(${l.sat || 100}%) contrast(${l.contrast || 100}%)`;
    x.drawImage(i, tr.x, tr.y, tr.w, tr.h, r, r, tr.w, tr.h);
    return OUT[l.id] = { key, c, w: c.width, h: c.height };
  };

  /* ---------------------------------------------------------------- çizim */
  const fontOf = l => `${l.size}px "${l.font}", Impact, sans-serif`;
  const segs = line => line.split(/(\*[^*]+\*)/).filter(Boolean).map(t => t.length > 2 && t.startsWith('*') && t.endsWith('*') ? { t: t.slice(1, -1), hi: 1 } : { t: t.replace(/\*/g, ''), hi: 0 });
  const textLines = l => (l.upper ? l.text.toLocaleUpperCase('tr-TR') : l.text).split('\n');
  /* kelimeleri satırlara böl, kapağa sığmıyorsa satır kır, yine sığmıyorsa küçült */
  const layout = (ctx, l, fs) => {
    ctx.font = `${fs}px "${l.font}", Impact, sans-serif`; ctx.letterSpacing = (l.spacing || 0) * fs / l.size + 'px';
    const maxW = K.W * (l.maxW || .9), sp = ctx.measureText(' ').width, out = [];
    textLines(l).forEach(raw => {
      const words = []; segs(raw).forEach(g => g.t.split(/\s+/).filter(Boolean).forEach(t => words.push({ t, hi: g.hi, w: ctx.measureText(t).width })));
      let cur = [], cw = 0;
      words.forEach(w => { const nw = cw + (cur.length ? sp : 0) + w.w; if (cur.length && nw > maxW) { out.push(cur); cur = [w]; cw = w.w; } else { cur.push(w); cw = nw; } });
      out.push(cur);
    });
    const lines = out.map(ws => { const sg = ws.map((w, i) => ({ t: w.t + (i < ws.length - 1 ? ' ' : ''), hi: w.hi })); sg.forEach(g => g.w = ctx.measureText(g.t).width); return { sg, w: sg.reduce((a, g) => a + g.w, 0) }; });
    return { lines, tw: Math.max(1, ...lines.map(x => x.w)), maxW };
  };
  const measureText = (ctx, l) => {
    let fs = l.size, r = layout(ctx, l, fs);
    if (r.tw > r.maxW) { fs = Math.max(8, Math.floor(fs * r.maxW / r.tw)); r = layout(ctx, l, fs); }
    const f = fs / l.size, lh = fs * (l.lh || 1.05), th = r.lines.length * lh, pad = l.box ? fs * .28 : 0, st = (l.stroke || 0) * f, st2 = (l.stroke2 || 0) * f;
    return { lines: r.lines, lh, tw: r.tw, th, pad, fs, st, st2, w: r.tw + pad * 2 + (st + st2) * 2, h: th + pad * 2 + (st + st2) * 2 };
  };
  const drawText = (ctx, l) => {
    const m = measureText(ctx, l); l._w = m.w; l._h = m.h;
    ctx.textBaseline = 'middle'; ctx.textAlign = 'left'; ctx.lineJoin = 'round'; ctx.miterLimit = 2;
    if (l.box) {
      ctx.save(); ctx.fillStyle = l.boxColor; if (l.shadow) { ctx.shadowColor = 'rgba(0,0,0,.55)'; ctx.shadowBlur = m.fs * .25; ctx.shadowOffsetY = m.fs * .08; }
      ctx.beginPath(); ctx.roundRect(-m.tw / 2 - m.pad, -m.th / 2 - m.pad, m.tw + m.pad * 2, m.th + m.pad * 2, m.fs * .18); ctx.fill(); ctx.restore();
    }
    const each = fn => m.lines.forEach((ln, i) => { let x = -ln.w / 2; const y = -m.th / 2 + m.lh * (i + .5) + m.fs * .04; ln.sg.forEach(g => { fn(g, x, y); x += g.w; }); });
    const fill = (g, y) => {
      if (g.hi) return l.hiColor;
      if (!l.grad) return l.color;
      const gr = ctx.createLinearGradient(0, y - m.fs / 2, 0, y + m.fs / 2); gr.addColorStop(0, l.color); gr.addColorStop(1, l.color2); return gr;
    };
    ctx.save();
    if (l.shadow && !l.box) { ctx.shadowColor = 'rgba(0,0,0,.7)'; ctx.shadowBlur = m.fs * .18; ctx.shadowOffsetX = m.fs * .05; ctx.shadowOffsetY = m.fs * .08; }
    if (l.glow) { ctx.shadowColor = l.glowColor; ctx.shadowBlur = m.fs * .45; ctx.shadowOffsetX = ctx.shadowOffsetY = 0; }
    if (m.st2) { ctx.lineWidth = (m.st + m.st2) * 2; ctx.strokeStyle = l.stroke2Color; each((g, x, y) => ctx.strokeText(g.t, x, y)); ctx.shadowColor = 'transparent'; }
    if (m.st) { ctx.lineWidth = m.st * 2; ctx.strokeStyle = l.strokeColor; each((g, x, y) => ctx.strokeText(g.t, x, y)); ctx.shadowColor = 'transparent'; }
    each((g, x, y) => { ctx.fillStyle = fill(g, y); ctx.fillText(g.t, x, y); });
    ctx.restore();
  };
  const shapePath = (ctx, k, w, h) => {
    ctx.beginPath();
    if (k === 'ok') { const t = h * .32; ctx.moveTo(-w / 2, -t / 2); ctx.lineTo(w / 2 - h * .55, -t / 2); ctx.lineTo(w / 2 - h * .55, -h / 2); ctx.lineTo(w / 2, 0); ctx.lineTo(w / 2 - h * .55, h / 2); ctx.lineTo(w / 2 - h * .55, t / 2); ctx.lineTo(-w / 2, t / 2); ctx.closePath(); }
    else { ctx.moveTo(-w / 2, h / 2 - h * .12); ctx.quadraticCurveTo(-w * .1, -h * .55, w / 2 - h * .5, -h * .08); ctx.lineTo(w / 2 - h * .62, -h * .36); ctx.lineTo(w / 2, -h * .02); ctx.lineTo(w / 2 - h * .7, h * .22); ctx.lineTo(w / 2 - h * .56, h * .08); ctx.quadraticCurveTo(-w * .08, -h * .25, -w / 2 + h * .1, h / 2); ctx.closePath(); }
  };
  const drawShape = (ctx, l) => {
    const w = 300 * l.s * (l.k === 'cizgi' ? 1.4 : 1), h = l.k === 'ok' || l.k === 'egri' ? 170 * l.s : l.k === 'cizgi' ? 26 * l.s : (l.k === 'daire' ? 300 : 210) * l.s;
    const lw = Math.max(4, 22 * l.s * (l.thick || 1));
    l._w = w + 20; l._h = Math.max(h, lw * 2) + 20;
    ctx.save(); ctx.lineJoin = 'round'; ctx.lineCap = 'round';
    if (l.shadow) { ctx.shadowColor = 'rgba(0,0,0,.6)'; ctx.shadowBlur = 18; ctx.shadowOffsetY = 6; }
    if (l.k === 'ok' || l.k === 'egri') {
      shapePath(ctx, l.k, w, h);
      if (l.outline) { ctx.lineWidth = lw * .9; ctx.strokeStyle = l.outlineColor; ctx.stroke(); ctx.shadowColor = 'transparent'; }
      ctx.fillStyle = l.color; ctx.fill();
    } else {
      const path = () => { ctx.beginPath(); if (l.k === 'daire') ctx.ellipse(0, 0, Math.max(1, w / 2 - lw), Math.max(1, h / 2 - lw), 0, 0, Math.PI * 2); else if (l.k === 'kutu') ctx.roundRect(-w / 2 + lw, -h / 2 + lw, w - lw * 2, h - lw * 2, lw); else { ctx.moveTo(-w / 2 + lw, 0); ctx.lineTo(w / 2 - lw, 0); } };
      if (l.outline) { path(); ctx.lineWidth = lw * 1.7; ctx.strokeStyle = l.outlineColor; ctx.stroke(); ctx.shadowColor = 'transparent'; }
      path(); ctx.lineWidth = lw; ctx.strokeStyle = l.color; ctx.stroke();
    }
    ctx.restore();
  };
  const drawLayer = (ctx, l) => {
    ctx.save(); ctx.translate(l.x, l.y); ctx.rotate((l.rot || 0) * Math.PI / 180); ctx.globalAlpha = l.alpha == null ? 1 : l.alpha;
    if (l.type === 'yazi') drawText(ctx, l);
    else if (l.type === 'emoji') { const fs = 180 * l.s; ctx.font = `${fs}px "Segoe UI Emoji","Apple Color Emoji","Noto Color Emoji",sans-serif`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; if (l.shadow) { ctx.shadowColor = 'rgba(0,0,0,.55)'; ctx.shadowBlur = fs * .12; ctx.shadowOffsetY = fs * .05; } ctx.fillText(l.ch, 0, fs * .04); l._w = fs * 1.1; l._h = fs * 1.1; }
    else if (l.type === 'sekil') drawShape(ctx, l);
    else {
      const o = outlined(l);
      if (!o) { l._w = l._w || 200; l._h = l._h || 200; }
      else {
        const w = o.w * l.s, h = o.h * l.s; l._w = w; l._h = h;
        if (l.flip) ctx.scale(-1, 1);
        if (l.shadow) { ctx.save(); ctx.shadowColor = 'rgba(0,0,0,.65)'; ctx.shadowBlur = 40 * l.s + 10; ctx.shadowOffsetX = 14 * l.s; ctx.shadowOffsetY = 18 * l.s; ctx.drawImage(o.c, -w / 2, -h / 2, w, h); ctx.restore(); }
        if (l.glow) { ctx.save(); ctx.shadowColor = l.glowColor; ctx.shadowBlur = l.glow; ctx.drawImage(o.c, -w / 2, -h / 2, w, h); ctx.restore(); }
        ctx.drawImage(o.c, -w / 2, -h / 2, w, h);
      }
    }
    ctx.restore();
  };
  const drawBg = (ctx, W, H) => {
    const b = K.bg;
    ctx.save(); ctx.fillStyle = '#111'; ctx.fillRect(0, 0, W, H);
    const i = b.mode === 'gorsel' ? img(b.url) : null;
    if (i) {
      const s = Math.max(W / i.naturalWidth, H / i.naturalHeight) * b.zoom, w = i.naturalWidth * s, h = i.naturalHeight * s, bl = b.blur ? b.blur * 2.5 * W / 1280 : 0;
      ctx.filter = `brightness(${b.bright}%) saturate(${b.sat}%) contrast(${b.contrast}%)` + (b.blur ? ` blur(${b.blur * W / 1280}px)` : '');
      ctx.drawImage(i, (W - w) / 2 + b.ox * W - bl, (H - h) / 2 + b.oy * H - bl, w + bl * 2, h + bl * 2);
      ctx.filter = 'none';
    } else if (b.mode !== 'gorsel') {
      const a = b.angle * Math.PI / 180, r = Math.hypot(W, H) / 2, g = ctx.createLinearGradient(W / 2 - Math.cos(a) * r, H / 2 - Math.sin(a) * r, W / 2 + Math.cos(a) * r, H / 2 + Math.sin(a) * r);
      g.addColorStop(0, b.c1); g.addColorStop(1, b.mode === 'renk' ? b.c1 : b.c2); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
      if (b.style === 'isin') {
        ctx.save(); ctx.translate(W / 2, H / 2); ctx.fillStyle = 'rgba(255,255,255,.13)';
        for (let q = 0; q < 24; q += 2) { ctx.beginPath(); ctx.moveTo(0, 0); ctx.arc(0, 0, r * 1.2, q / 24 * Math.PI * 2, (q + 1) / 24 * Math.PI * 2); ctx.closePath(); ctx.fill(); }
        ctx.restore();
      } else if (b.style === 'nokta') {
        ctx.fillStyle = 'rgba(255,255,255,.12)'; const st = W / 40;
        for (let y = 0, n = 0; y < H + st; y += st, n++) for (let x = n % 2 ? st / 2 : 0; x < W + st; x += st) { ctx.beginPath(); ctx.arc(x, y, st * .16, 0, Math.PI * 2); ctx.fill(); }
      }
    }
    if (b.tintA) { ctx.globalAlpha = b.tintA / 100; ctx.fillStyle = b.tint; ctx.fillRect(0, 0, W, H); ctx.globalAlpha = 1; }
    if (b.vignette) { const g = ctx.createRadialGradient(W / 2, H / 2, Math.min(W, H) * .35, W / 2, H / 2, Math.hypot(W, H) / 2); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, `rgba(0,0,0,${b.vignette / 100})`); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); }
    ctx.restore();
  };
  const render = ctx => { drawBg(ctx, K.W, K.H); K.layers.forEach(l => { if (!l.hidden) drawLayer(ctx, l); }); };
  const draw = () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(() => { const cv = $('#kpCv', host); if (!cv) { if (KS.page === 'kapak' && (K.layers.length || K.bg.url)) shell(); return; } if (cv.width !== K.W || cv.height !== K.H) { cv.width = K.W; cv.height = K.H; fit(); } render(cv.getContext('2d'));
    if (K._clamp) { K._clamp = false; let moved = false; K.layers.forEach(l => { if (l.type !== 'yazi' || !l._h) return; const m = K.H * .03, y = Math.min(Math.max(l.y, l._h / 2 + m), K.H - l._h / 2 - m), x = Math.min(Math.max(l.x, l._w / 2), K.W - l._w / 2); if (y !== l.y || x !== l.x) { l.y = y; l.x = x; moved = true; } }); if (moved) { render(cv.getContext('2d')); commit(); } }
    selBox(); }); };

  /* ---------------------------------------------------------------- yerleşim, seçim */
  let k = 1;
  const fit = () => {
    const st = $('#kpStage', host), box = $('#kpBox', host); if (!st || !box) return;
    const r = st.getBoundingClientRect();
    k = Math.max(.05, Math.min((r.width - 24) / K.W, (r.height - 24) / K.H));
    box.style.width = K.W * k + 'px'; box.style.height = K.H * k + 'px';
    selBox();
  };
  const selBox = () => {
    const s = $('#kpSel', host); if (!s) return;
    const l = selL();
    if (!l || l.hidden) s.hidden = true;
    else {
      s.hidden = false; const w = (l._w || 100) * k, h = (l._h || 100) * k;
      Object.assign(s.style, { left: (l.x * k - w / 2) + 'px', top: (l.y * k - h / 2) + 'px', width: w + 'px', height: h + 'px', transform: `rotate(${l.rot || 0}deg)` });
    }
    const g = $('#kpGuide', host);
    if (g) g.innerHTML = guides ? (guides.v != null ? `<i class="v" style="left:${guides.v * k}px"></i>` : '') + (guides.h != null ? `<i class="h" style="top:${guides.h * k}px"></i>` : '') : '';
  };
  const pt = e => { const r = $('#kpBox', host).getBoundingClientRect(); return { x: (e.clientX - r.left) / k, y: (e.clientY - r.top) / k }; };
  const hit = p => {
    for (let i = K.layers.length - 1; i >= 0; i--) {
      const l = K.layers[i]; if (l.hidden) continue;
      const a = -(l.rot || 0) * Math.PI / 180, dx = p.x - l.x, dy = p.y - l.y, x = dx * Math.cos(a) - dy * Math.sin(a), y = dx * Math.sin(a) + dy * Math.cos(a);
      if (Math.abs(x) <= (l._w || 0) / 2 && Math.abs(y) <= (l._h || 0) / 2) return l;
    }
    return null;
  };
  const scaleKey = l => l.type === 'yazi' ? 'size' : 's';
  const onDown = e => {
    if (e.button !== 0 || !$('#kpBox', host)) return;
    const p = pt(e), h = e.target.dataset && e.target.dataset.h;
    let l = selL();
    if (h && l) drag = { mode: h, l, p0: p, v0: l[scaleKey(l)], r0: l.rot || 0, d0: Math.hypot(p.x - l.x, p.y - l.y), a0: Math.atan2(p.y - l.y, p.x - l.x) };
    else {
      l = hit(p);
      if (l) { if (K.sel !== l.id) { K.sel = l.id; side(); } drag = { mode: 'move', l, p0: p, x0: l.x, y0: l.y }; }
      else if (K.sel === 'bg' && K.bg.mode === 'gorsel' && K.bg.url) drag = { mode: 'bg', p0: p, ox: K.bg.ox, oy: K.bg.oy };
      else if (K.sel) { K.sel = null; side(); }
    }
    if (drag) { e.preventDefault(); $('#kpStage', host).setPointerCapture(e.pointerId); drag.moved = false; }
    selBox();
  };
  const onMove = e => {
    if (!drag) return;
    const p = pt(e), l = drag.l; drag.moved = true;
    if (drag.mode === 'move') {
      let x = drag.x0 + p.x - drag.p0.x, y = drag.y0 + p.y - drag.p0.y; guides = {};
      if (!e.altKey) { const tol = 8 / k; if (Math.abs(x - K.W / 2) < tol) { x = K.W / 2; guides.v = x; } if (Math.abs(y - K.H / 2) < tol) { y = K.H / 2; guides.h = y; } }
      l.x = x; l.y = y;
    } else if (drag.mode === 'bg') { K.bg.ox = drag.ox + (p.x - drag.p0.x) / K.W; K.bg.oy = drag.oy + (p.y - drag.p0.y) / K.H; }
    else if (drag.mode === 'rot') {
      let r = drag.r0 + (Math.atan2(p.y - l.y, p.x - l.x) - drag.a0) * 180 / Math.PI;
      r = ((r + 540) % 360) - 180; if (!e.shiftKey) for (const s of [-180, -90, 0, 90, 180]) if (Math.abs(r - s) < 4) r = s;
      l.rot = Math.round(r * 10) / 10;
    } else {
      const f = Math.hypot(p.x - l.x, p.y - l.y) / Math.max(1, drag.d0), key = scaleKey(l);
      l[key] = key === 'size' ? Math.round(Math.max(12, Math.min(600, drag.v0 * f))) : Math.max(.03, Math.min(12, drag.v0 * f));
    }
    draw();
  };
  const onUp = () => { if (!drag) return; const d = drag; drag = null; guides = null; draw(); if (d.moved) { commit(); if (d.mode !== 'move' && d.mode !== 'bg') side(); } };

  /* ---------------------------------------------------------------- katman ekleme */
  const add = (l, select = true) => { l.id = 'k' + (uid++); K.layers.push(l); if (select) K.sel = l.id; side(); draw(); commit(); return l; };
  const S = () => Math.min(K.W, K.H) / 720;
  const newText = (text = 'YAZINI YAZ', extra = {}) => add({ type: 'yazi', text, font: 'Anton', size: Math.round(120 * S()), color: '#ffffff', color2: '#ffd400', grad: false, hiColor: '#ffd400', stroke: Math.round(10 * S()), strokeColor: '#000000', stroke2: 0, stroke2Color: '#ffffff', shadow: true, glow: false, glowColor: '#ff2d2d', box: false, boxColor: '#ff2d2d', upper: true, spacing: 0, lh: 1.02, maxW: .9, x: K.W / 2, y: K.H * .2, rot: 0, ...extra });
  const newEmoji = (ch, extra = {}) => add({ type: 'emoji', ch, s: S(), x: K.W * .78, y: K.H * .25, rot: -8, shadow: true, ...extra });
  const newShape = (kk, extra = {}) => add({ type: 'sekil', k: kk, s: S(), color: '#ff2d2d', outline: true, outlineColor: '#ffffff', shadow: true, thick: 1, x: K.W / 2, y: K.H / 2, rot: kk === 'ok' ? 20 : 0, ...extra });
  const newPic = (url, type, extra = {}) => add({ type, url, s: .5, x: K.W / 2, y: K.H / 2, rot: 0, stroke: type === 'kisi' ? Math.round(10 * S()) : 0, strokeColor: '#ffffff', glow: 0, glowColor: '#00d0ff', shadow: true, flip: false, bright: 105, sat: 112, contrast: 106, ...extra });
  /* kişiyi kadraja oturt */
  const placeKisi = (l, where = 'sag') => {
    const o = outlined(l); if (!o) return;
    const wide = K.W > K.H;
    l.s = Math.min(K.H * (wide ? .95 : .62) / o.h, K.W * (wide ? .55 : .95) / o.w);
    l.y = K.H - o.h * l.s / 2 + (wide ? K.H * .03 : 0);
    l.x = !wide || where === 'orta' ? K.W / 2 : where === 'sol' ? o.w * l.s / 2 + K.W * .02 : K.W - o.w * l.s / 2 - K.W * .02;
  };

  /* ---------------------------------------------------------------- şablonlar */
  const TEMPLATES = [
    { id: 'klasik', n: 'Klasik YouTube', d: 'Kişi sağda, büyük sarı yazı, ok', c: '#ffd400' },
    { id: 'sok', n: 'Şok anı', d: 'Bulanık arka, kişi ortada, kırmızı şerit', c: '#ff2d2d' },
    { id: 'neon', n: 'Neon', d: 'Koyu ışınlı arka, parlayan kişi', c: '#00d0ff' },
    { id: 'temiz', n: 'Temiz', d: 'Sade, beyaz yazı, gölgeli', c: '#ffffff' },
  ];
  const applyTpl = id => {
    const keepText = (K.layers.find(l => l.type === 'yazi') || {}).text || (K.src && K.src.title) || 'BUNU GÖRMELİSİN';
    const kisi = K.layers.find(l => l.type === 'kisi');
    K.layers = K.layers.filter(l => l.type === 'kisi' || l.type === 'resim');
    const wide = K.W > K.H, s = S(), b = K.bg, hasImg = !!b.url;
    if (id === 'klasik') {
      Object.assign(b, hasImg ? { mode: 'gorsel', blur: 0, bright: 92, sat: 135, contrast: 112, vignette: 45, tintA: 0 } : { mode: 'gradyan', c1: '#ff0844', c2: '#ffb199', style: 'isin', vignette: 35 });
      newText(keepText, { color: '#ffd400', hiColor: '#ffffff', size: Math.round((wide ? 130 : 150) * s), stroke: Math.round(11 * s), maxW: wide ? .55 : .9, x: wide ? K.W * .3 : K.W / 2, y: wide ? K.H * .42 : K.H * .16, rot: wide ? -3 : 0 });
      if (wide) newShape('ok', { x: K.W * .5, y: K.H * .74, rot: -12, s: .8 * s });
    } else if (id === 'sok') {
      Object.assign(b, hasImg ? { mode: 'gorsel', blur: 10, bright: 80, sat: 120, contrast: 110, vignette: 55, tint: '#ff0000', tintA: 12 } : { mode: 'gradyan', c1: '#232526', c2: '#414345', style: 'nokta', vignette: 50 });
      newText(keepText, { font: 'Montserrat Black', size: Math.round((wide ? 92 : 110) * s), stroke: 0, box: true, boxColor: '#e11d2e', x: K.W / 2, y: wide ? K.H * .17 : K.H * .14 });
      newEmoji('😱', { x: wide ? K.W * .85 : K.W * .8, y: wide ? K.H * .62 : K.H * .4 });
    } else if (id === 'neon') {
      Object.assign(b, { mode: 'gradyan', c1: '#0f0c29', c2: '#302b63', style: 'isin', vignette: 55, angle: 160, tintA: 0 });
      newText(keepText, { font: 'Bebas Neue', grad: true, color: '#ff4fd8', color2: '#ffd400', hiColor: '#00d0ff', size: Math.round((wide ? 150 : 170) * s), stroke: Math.round(6 * s), strokeColor: '#1a0033', glow: true, glowColor: '#ff4fd8', shadow: false, maxW: wide ? .55 : .9, x: wide ? K.W * .3 : K.W / 2, y: wide ? K.H * .45 : K.H * .15 });
    } else {
      Object.assign(b, hasImg ? { mode: 'gorsel', blur: 0, bright: 100, sat: 112, contrast: 105, vignette: 30, tintA: 0 } : { mode: 'gradyan', c1: '#00c6ff', c2: '#0072ff', style: 'duz', vignette: 20 });
      newText(keepText, { font: 'Archivo Black', size: Math.round((wide ? 96 : 110) * s), stroke: 0, maxW: wide ? .55 : .9, x: wide ? K.W * .3 : K.W / 2, y: wide ? K.H * .78 : K.H * .82 });
    }
    const style = { klasik: { stroke: Math.round(12 * s), strokeColor: '#ffffff', glow: 0, shadow: true }, sok: { stroke: Math.round(8 * s), strokeColor: '#ffffff', glow: 0, shadow: true }, neon: { stroke: Math.round(6 * s), strokeColor: '#00d0ff', glow: 60, glowColor: '#00d0ff', shadow: false }, temiz: { stroke: 0, glow: 0, shadow: true } }[id];
    const where = id === 'sok' ? 'orta' : 'sag';
    if (kisi) { Object.assign(kisi, style); K.layers = [kisi, ...K.layers.filter(l => l !== kisi)]; placeKisi(kisi, where); }
    else if (b.mode === 'gorsel' && b.path) { K.pendingKisi = { style, where }; cut(); }
    K.sel = (K.layers.find(l => l.type === 'yazi') || {}).id || null;
    K._clamp = true; side(); draw(); commit();
  };

  /* ---------------------------------------------------------------- kaynak, kareler, kesme */
  const loadSrc = async f => {
    K.src = f; K.frames = []; K.saved = null;
    if (f.kind === 'image') { shell(); await setBg(f.path, 0); side(); return; }
    shell();
    const lw = $('#kpLoad', host); if (lw) lw.hidden = false;
    try {
      const r = await KS.api('/api/kapak/kareler', { path: f.path, start: f.start || 0, end: f.end || 0, n: 10 });
      K.frames = r.frames; shell();
      const mid = r.frames[Math.floor(r.frames.length / 2)];
      if (mid) await setBg(f.path, mid.t);
    } catch (e) { KS.toast(KS.esc(e.message), 'err'); }
    side();
  };
  const setBg = async (path, t) => {
    const lw = $('#kpLoad', host); if (lw) lw.hidden = false;
    try {
      const r = await KS.api('/api/kapak/kare', { path, t });
      K.t = t; Object.assign(K.bg, { mode: 'gorsel', path: r.path, url: r.url, zoom: 1, ox: 0, oy: 0 });
      if (!$('#kpBox', host)) shell();
      draw(); commit();
    } catch (e) { KS.toast(KS.esc(e.message), 'err'); }
    const l2 = $('#kpLoad', host); if (l2) l2.hidden = true;
    $$('.kp-frames img', host).forEach(i => i.classList.toggle('on', Math.abs(+i.dataset.t - K.t) < .01));
    side();
  };
  const cut = async (path = K.bg.path) => {
    if (!path) return KS.toast('Önce bir video ya da fotoğraf seç', 'err');
    if (U.running(U.findJob(K.cutJob))) return;
    try { const r = await KS.api('/api/kapak/kes', { path }); K.cutJob = r.job; KS.trackJob(r.job); side(); }
    catch (e) { KS.toast(KS.esc(e.message), 'err'); }
  };
  const onCut = j => {
    const p = (j.result || {}).path; if (!p) return;
    const url = '/media/video?path=' + encodeURIComponent(p);
    const st = K.pendingKisi; K.pendingKisi = null;
    const go = () => {
      const l = newPic(url, 'kisi', st ? st.style : {});
      placeKisi(l, st ? st.where : 'sag');
      K.layers = [l, ...K.layers.filter(x => x !== l)]; K.sel = l.id; side(); draw(); commit();
    };
    img(url); const i = IMG[url];
    if (i.complete && i.naturalWidth) go(); else { i.addEventListener('load', go, { once: true }); i.addEventListener('error', () => KS.toast('Kesilen kişi yüklenemedi', 'err'), { once: true }); }
  };

  /* ---------------------------------------------------------------- kaydet */
  const fontsReady = () => document.fonts ? Promise.all([...new Set(K.layers.filter(l => l.type === 'yazi').map(l => l.font))].map(f => document.fonts.load(`80px "${f}"`, 'ĞŞİÇÖÜğşıçöüAa').catch(() => { }))) : Promise.resolve();
  const exportImg = async () => {
    const btn = $('#kpGo', host); if (btn) btn.disabled = true;
    try {
      await fontsReady();
      const c = document.createElement('canvas'); c.width = K.W; c.height = K.H; render(c.getContext('2d'));
      let data;
      if (K.fmt === 'png') data = c.toDataURL('image/png');
      else for (const q of [.95, .92, .88, .84, .8, .74, .68, .6]) { data = c.toDataURL('image/jpeg', q); if (data.length * .75 < 1.95 * 1024 * 1024) break; }
      const nm = ((K.src && (K.src.title || K.src.name.replace(/\.[^.]+$/, ''))) || 'kapak').slice(0, 50) + '_kapak';
      const s = await KS.api('/api/snapshot', { data, name: nm });
      K.saved = s; foot();
      KS.toast('🖼 Kapak kaydedildi: ' + KS.esc(s.name), 'ok', [{ label: 'Klasörde göster', primary: true, fn: () => KS.api('/api/reveal', { path: s.path }) }]);
    } catch (e) { KS.toast(KS.esc(e.message), 'err'); }
    const b2 = $('#kpGo', host); if (b2) b2.disabled = false;
  };
  const setSize = sz => {
    if (sz === K.size) return;
    const [W, H] = SIZES[sz], fx = W / K.W, fy = H / K.H, f = Math.min(fx, fy);
    K.layers.forEach(l => { l.x *= fx; l.y *= fy; if (l.type === 'yazi') { l.size = Math.round(l.size * f); l.stroke = Math.round(l.stroke * f); l.stroke2 = Math.round((l.stroke2 || 0) * f); } else l.s *= f; });
    K.size = sz; K.W = W; K.H = H;
    K.layers.filter(l => l.type === 'kisi').forEach(l => placeKisi(l, 'sag'));
    K._clamp = true; shell(); draw(); commit();
  };

  /* ---------------------------------------------------------------- arayüz */
  const sw = (key, cur) => `<div class="kp-sw" data-sw="${key}">${SW.map(c => `<button data-c="${c}" class="${String(cur).toLowerCase() === c ? 'on' : ''}" style="background:${c}"></button>`).join('')}<label title="Başka renk"><input type="color" value="${/^#[0-9a-f]{6}$/i.test(cur) ? cur : '#ffffff'}">🎨</label></div>`;
  const row = (label, inner) => `<div class="kp-row"><span>${label}</span>${inner}</div>`;
  const ICON = { yazi: '🔤', kisi: '🧍', resim: '🖼️', emoji: '😀', sekil: '➜' };
  const lname = l => l.type === 'yazi' ? (l.text || 'Yazı').replace(/\*/g, '').split('\n')[0].slice(0, 22) || 'Yazı' : l.type === 'emoji' ? 'Emoji ' + l.ch : l.type === 'sekil' ? (SHAPES.find(s => s[0] === l.k) || [0, '  Şekil'])[1].slice(2) : l.type === 'kisi' ? 'Kişi' : 'Resim';

  const shell = () => {
    const has = K.src || K.layers.length || K.bg.url;
    host.innerHTML = `${U.head('Kapak Stüdyosu', 'Kişiyi kes, arka planı seç, büyük yazı ve emoji ekle. Sürükle, büyüt, döndür.',
      `<span class="kq-name">${K.src ? KS.esc(K.src.name) : ''}</span>${has ? '<button class="btn ghost" id="kpNew" title="Baştan başla">Yeni</button>' : ''}<button class="btn ghost" id="kpPick">Video / Fotoğraf seç</button>`)}
    <div class="tk kp">
      <div class="tk-main">
        ${has ? `<div class="kp-top">
          <div class="seg kq-seg">${Object.entries(SIZES).map(([v, [, , n]]) => `<button data-size="${v}" class="${K.size === v ? 'on' : ''}">${n}</button>`).join('')}</div>
          <span class="kp-sp"></span><span class="kp-tip">Çift tık: yazıyı düzenle · Del: sil · Ctrl+D: çoğalt</span>
          <button class="btn ghost sm" id="kpUndo" title="Geri al (Ctrl+Z)">↶</button><button class="btn ghost sm" id="kpRedo" title="Yinele (Ctrl+Y)">↷</button>
        </div>` : ''}
        <div class="tk-view kp-stage" id="kpStage">
          ${!has ? `<div class="tk-empty"><div class="big">🖼️</div><b>Video ya da fotoğraf sürükle</b><span>Kişi otomatik kesilir, şablonla saniyeler içinde kapak hazır.</span><div class="kp-empty-b"><button class="btn primary" id="kpPick2">Video / Fotoğraf seç</button><button class="btn ghost" id="kpBlank">Boş kapakla başla</button></div></div>`
            : `<div class="kp-box" id="kpBox"><canvas id="kpCv"></canvas><div class="kp-guide" id="kpGuide"></div>
                <div class="kp-sel" id="kpSel" hidden><i data-h="nw"></i><i data-h="ne"></i><i data-h="sw"></i><i data-h="se"></i><i data-h="rot" class="rot" title="Döndür"></i></div></div>
               <div class="kq-load" id="kpLoad" hidden><div class="spin"></div><span>Kare alınıyor...</span></div>`}
        </div>
        ${K.frames.length ? `<div class="kp-frames">${K.frames.map(f => `<img src="${f.url}" data-t="${f.t}" class="${Math.abs(f.t - K.t) < .01 ? 'on' : ''}" title="${f.t.toFixed(1)}. saniye">`).join('')}</div>` : ''}
      </div>
      <div class="tk-side"><div class="tk-scroll" id="kpSide"></div><div class="tk-foot" id="kpFoot"></div></div>
    </div>`;
    $('#kpPick', host).onclick = pickSrc;
    const p2 = $('#kpPick2', host); if (p2) p2.onclick = pickSrc;
    const bl = $('#kpBlank', host); if (bl) bl.onclick = () => { K.layers = []; applyTpl('klasik'); shell(); };
    const nw = $('#kpNew', host); if (nw) nw.onclick = () => { if (!confirm('Kapak baştan başlasın mı?')) return; K = blank(); hist = [snap()]; fut = []; try { localStorage.removeItem('kapak_son'); } catch (e) { } shell(); };
    $$('[data-size]', host).forEach(b => b.onclick = () => setSize(b.dataset.size));
    const ub = $('#kpUndo', host); if (ub) { ub.onclick = undo; $('#kpRedo', host).onclick = redo; updUndo(); }
    $$('.kp-frames img', host).forEach(i => i.onclick = () => setBg(K.src.path, +i.dataset.t));
    const st = $('#kpStage', host);
    if ($('#kpBox', host)) {
      st.onpointerdown = onDown; st.onpointermove = onMove; st.onpointerup = st.onpointercancel = onUp;
      st.ondblclick = e => { const l = hit(pt(e)); if (l && l.type === 'yazi') { K.sel = l.id; side(); const t = $('#kpText', host); if (t) { t.focus(); t.select(); } } };
    }
    side(); fit(); draw();
  };
  const pickSrc = async () => { const f = await U.pick(['video', 'image']); if (f) loadSrc(f); };

  const side = () => {
    const el = $('#kpSide', host); if (!el) return;
    const sc = el.scrollTop;
    const l = selL(), cj = U.findJob(K.cutJob), cutting = U.running(cj);
    const layersHtml = `<div class="kp-layers">${[...K.layers].reverse().map(x => `<div class="kp-l ${K.sel === x.id ? 'on' : ''} ${x.hidden ? 'off' : ''}" data-l="${x.id}"><span class="kp-li">${ICON[x.type]}</span><b>${KS.esc(lname(x))}</b>
        <button data-la="up" title="Öne al">▲</button><button data-la="down" title="Arkaya al">▼</button><button data-la="eye" title="Gizle / göster">${x.hidden ? '◌' : '👁'}</button><button data-la="dup" title="Çoğalt">⧉</button><button data-la="del" title="Sil">✕</button></div>`).join('')}
      <div class="kp-l ${K.sel === 'bg' ? 'on' : ''}" data-l="bg"><span class="kp-li">🌄</span><b>Arka plan</b></div></div>`;
    const addBar = `<div class="kp-add">
        <button data-add="yazi">🔤<span>Yazı</span></button>
        <button data-add="kisi" ${!K.bg.path || cutting ? 'disabled' : ''} title="${K.bg.path ? 'Arka plandaki kişiyi kesip öne çıkarır' : 'Önce video ya da fotoğraf seç'}">✂️<span>${cutting ? 'Kesiliyor' : 'Kişiyi kes'}</span></button>
        <button data-add="foto" ${cutting ? 'disabled' : ''}>🧍<span>Fotoğraftan kişi</span></button>
        <button data-add="resim">🖼️<span>Resim / logo</span></button></div>
        ${cutting ? U.jobCard(cj, 'Kişi kesiliyor...') : ''}
        ${U.h('Emoji')}<div class="kp-emo">${EMOJI.map(e => `<button data-emo="${e}">${e}</button>`).join('')}</div>
        ${U.h('Ok ve şekil')}<div class="kp-shp">${SHAPES.map(([v, n]) => `<button data-shp="${v}">${n}</button>`).join('')}</div>`;
    let props = '';
    if (K.sel === 'bg') props = U.grp('Arka plan', '🌄', bgProps(), true);
    else if (l) props = U.grp(KS.esc(lname(l)), ICON[l.type], layerProps(l), true);
    el.innerHTML = `${U.grp('Şablonlar', '✨', `<div class="kp-tpl">${TEMPLATES.map(t => `<button data-tpl="${t.id}" style="--c:${t.c}"><b>${t.n}</b><small>${t.d}</small></button>`).join('')}</div>`, !K.layers.length)}
      ${props}${U.grp('Ekle', '➕', addBar, !l && K.sel !== 'bg')}${U.grp('Katmanlar', '🗂️', layersHtml, true)}`;
    bindSide(el); el.scrollTop = sc;
    foot();
  };
  const bgProps = () => {
    const b = K.bg;
    return `<div class="seg kq-seg" id="kpBgMode">${[['gorsel', 'Görsel', !b.url], ['gradyan', 'Renk geçişi'], ['renk', 'Düz renk']].map(([v, n, dis]) => `<button data-v="${v}" class="${b.mode === v ? 'on' : ''}" ${dis ? 'disabled title="Önce video ya da fotoğraf seç"' : ''}>${n}</button>`).join('')}</div>
      ${b.mode === 'gorsel' ? `${U.sl('zoom', 'Yakınlaştır', 1, 3, b.zoom, .02, 'x')}${U.sl('blur', 'Bulanıklık', 0, 30, b.blur)}${U.sl('bright', 'Parlaklık', 40, 160, b.bright, 1, '%')}${U.sl('sat', 'Canlılık', 0, 200, b.sat, 1, '%')}${U.sl('contrast', 'Kontrast', 50, 160, b.contrast, 1, '%')}
          <div class="kp-hint">Arka plan seçiliyken kapağı sürükleyerek görüntüyü kaydırabilirsin.</div>`
        : `${b.mode === 'gradyan' ? `<div class="kp-grads">${BGS.map(([a, c]) => `<button data-g="${a},${c}" style="background:linear-gradient(135deg,${a},${c})" class="${b.c1 === a && b.c2 === c ? 'on' : ''}"></button>`).join('')}</div>` : ''}
          ${row(b.mode === 'gradyan' ? 'Renk 1' : 'Renk', sw('bg.c1', b.c1))}${b.mode === 'gradyan' ? row('Renk 2', sw('bg.c2', b.c2)) + U.sl('angle', 'Açı', 0, 360, b.angle, 5, '°') : ''}
          ${U.h('Desen')}${U.seg('style', [['duz', 'Yok'], ['isin', 'Işın'], ['nokta', 'Nokta']], b.style)}`}
      ${U.sl('vignette', 'Kenar karartma', 0, 90, b.vignette, 1, '%')}
      ${row('Renk filtresi', sw('bg.tint', b.tint))}${U.sl('tintA', 'Filtre gücü', 0, 70, b.tintA, 1, '%')}`;
  };
  const layerProps = l => {
    const common = `${U.sl('rot', 'Döndür', -180, 180, Math.round(l.rot || 0), 1, '°')}${U.sl('alpha', 'Görünürlük', 10, 100, Math.round((l.alpha == null ? 1 : l.alpha) * 100), 1, '%')}`;
    if (l.type === 'yazi') return `<textarea class="inp kp-text" id="kpText" rows="2" placeholder="Yazını yaz (Enter: alt satır)">${KS.esc(l.text)}</textarea>
      <div class="kp-hint">Bir kelimeyi farklı renk yapmak için *yıldız* içine al: BU ADAM *ÇILDIRDI*</div>
      <div class="kp-ai"><button class="btn ghost sm" id="kpAi">✨ Yapay zekâ yazı önersin</button></div><div class="kp-chips" id="kpChips"></div>
      ${U.h('Yazı tipi')}<div class="kp-fonts">${FONTS.map(([f, n]) => `<button data-font="${f}" class="${l.font === f ? 'on' : ''}" style="font-family:'${f}',Impact">${n}</button>`).join('')}</div>
      ${U.sl('size', 'Boyut', 20, 400, l.size)}${U.sl('maxW', 'En fazla genişlik (sığmazsa alt satıra geçer)', .2, .98, l.maxW || .9, .01)}${U.sl('spacing', 'Harf aralığı', -5, 30, l.spacing || 0)}
      ${U.chk('upper', 'BÜYÜK HARF', l.upper)}
      ${row('Renk', sw('color', l.color))}${U.chk('grad', 'Renk geçişi (üstten alta)', l.grad)}${l.grad ? row('Alt renk', sw('color2', l.color2)) : ''}
      ${row('Vurgu rengi', sw('hiColor', l.hiColor))}
      ${U.sl('stroke', 'Kontur', 0, 40, l.stroke)}${l.stroke ? row('Kontur rengi', sw('strokeColor', l.strokeColor)) : ''}
      ${U.sl('stroke2', 'Dış kontur (çift)', 0, 30, l.stroke2 || 0)}${l.stroke2 ? row('Dış kontur rengi', sw('stroke2Color', l.stroke2Color)) : ''}
      ${U.chk('shadow', 'Gölge', l.shadow)}${U.chk('glow', 'Parlama (neon)', l.glow)}${l.glow ? row('Parlama rengi', sw('glowColor', l.glowColor)) : ''}
      ${U.chk('box', 'Arkasına kutu', l.box)}${l.box ? row('Kutu rengi', sw('boxColor', l.boxColor)) : ''}${common}`;
    if (l.type === 'emoji') return `<div class="kp-emo">${EMOJI.map(e => `<button data-swap="${e}" class="${l.ch === e ? 'on' : ''}">${e}</button>`).join('')}</div>${U.sl('s', 'Boyut', .2, 4, +l.s.toFixed(2), .05, 'x')}${U.chk('shadow', 'Gölge', l.shadow)}${common}`;
    if (l.type === 'sekil') return `<div class="kp-shp">${SHAPES.map(([v, n]) => `<button data-kk="${v}" class="${l.k === v ? 'on' : ''}">${n}</button>`).join('')}</div>${row('Renk', sw('color', l.color))}${U.sl('s', 'Boyut', .2, 4, +l.s.toFixed(2), .05, 'x')}${U.sl('thick', 'Kalınlık', .4, 3, l.thick || 1, .1, 'x')}${U.chk('outline', 'Dış çizgi', l.outline)}${l.outline ? row('Çizgi rengi', sw('outlineColor', l.outlineColor)) : ''}${U.chk('shadow', 'Gölge', l.shadow)}${common}`;
    return `${l.type === 'kisi' ? `<div class="kp-btns"><button class="btn ghost sm" data-place="sol">⇤ Sola</button><button class="btn ghost sm" data-place="orta">Ortaya</button><button class="btn ghost sm" data-place="sag">Sağa ⇥</button></div>` : `<div class="kp-btns"><button class="btn ghost sm" id="kpCutPic">✂️ Bu resimden kişiyi kes</button></div>`}
      ${U.sl('s', 'Boyut', .05, 3, +l.s.toFixed(2), .01, 'x')}${U.chk('flip', 'Aynala (sağa-sola çevir)', l.flip)}
      ${U.sl('stroke', 'Çerçeve (kontur)', 0, 40, l.stroke || 0)}${l.stroke ? row('Çerçeve rengi', sw('strokeColor', l.strokeColor)) : ''}
      ${U.sl('glow', 'Parlama', 0, 120, l.glow || 0)}${l.glow ? row('Parlama rengi', sw('glowColor', l.glowColor)) : ''}
      ${U.chk('shadow', 'Gölge', l.shadow)}
      ${U.sl('bright', 'Parlaklık', 50, 160, l.bright || 100, 1, '%')}${U.sl('sat', 'Canlılık', 0, 200, l.sat || 100, 1, '%')}${U.sl('contrast', 'Kontrast', 50, 160, l.contrast || 100, 1, '%')}${common}`;
  };
  const REDRAW_SIDE = ['grad', 'box', 'glow', 'stroke', 'stroke2', 'outline', 'style'];
  const bindSide = el => {
    const l = selL(), tgt = K.sel === 'bg' ? K.bg : l;
    const o = {};
    U.bind(el, o, (key, full) => {
      if (!tgt) return;
      let v = o[key]; if (key === 'alpha') v = v / 100;
      tgt[key] = v;
      if (full && REDRAW_SIDE.includes(key)) side();
      draw(); if (full) commit();
    });
    $$('[data-tpl]', el).forEach(b => b.onclick = () => applyTpl(b.dataset.tpl));
    $$('[data-l]', el).forEach(r => r.onclick = e => {
      const id = r.dataset.l, a = e.target.dataset.la;
      if (id === 'bg') { K.sel = 'bg'; side(); draw(); return; }
      const x = L(id), i = K.layers.indexOf(x);
      if (!a) { K.sel = id; side(); draw(); return; }
      if (a === 'del') { K.layers.splice(i, 1); if (K.sel === id) K.sel = null; }
      else if (a === 'eye') x.hidden = !x.hidden;
      else if (a === 'up' && i < K.layers.length - 1) [K.layers[i], K.layers[i + 1]] = [K.layers[i + 1], K.layers[i]];
      else if (a === 'down' && i > 0) [K.layers[i], K.layers[i - 1]] = [K.layers[i - 1], K.layers[i]];
      else if (a === 'dup') { const c = clone(x); c.x += 30; c.y += 30; add(c); return; }
      side(); draw(); commit();
    });
    $$('[data-add]', el).forEach(b => b.onclick = async () => {
      const a = b.dataset.add;
      if (a === 'yazi') return newText();
      if (a === 'kisi') return cut();
      const f = await U.pick(['image']); if (!f) return;
      if (a === 'foto') cut(f.path);
      else { const url = '/media/video?path=' + encodeURIComponent(f.path); img(url); const i = IMG[url]; const go = () => { const ll = newPic(url, 'resim', { stroke: 0, shadow: false }); ll.s = Math.min(K.W * .35 / i.naturalWidth, K.H * .35 / i.naturalHeight); draw(); commit(); }; i.complete && i.naturalWidth ? go() : i.addEventListener('load', go, { once: true }); }
    });
    $$('[data-emo]', el).forEach(b => b.onclick = () => newEmoji(b.dataset.emo));
    $$('[data-shp]', el).forEach(b => b.onclick = () => newShape(b.dataset.shp));
    $$('[data-kk]', el).forEach(b => b.onclick = () => { l.k = b.dataset.kk; side(); draw(); commit(); });
    $$('[data-swap]', el).forEach(b => b.onclick = () => { l.ch = b.dataset.swap; side(); draw(); commit(); });
    $$('[data-font]', el).forEach(b => b.onclick = async () => { l.font = b.dataset.font; $$('[data-font]', el).forEach(x => x.classList.toggle('on', x === b)); await fontsReady(); draw(); commit(); });
    $$('[data-place]', el).forEach(b => b.onclick = () => { placeKisi(l, b.dataset.place); draw(); commit(); });
    const cp = $('#kpCutPic', el); if (cp) cp.onclick = () => { const m = decodeURIComponent((l.url.split('path=')[1] || '').split('&')[0]); if (m) { K.layers = K.layers.filter(x => x !== l); K.sel = null; commit(); cut(m); } };
    $$('[data-sw]', el).forEach(g => {
      const key = g.dataset.sw, set = (v, full) => { if (key.startsWith('bg.')) K.bg[key.slice(3)] = v; else if (l) l[key] = v; $$('button', g).forEach(x => x.classList.toggle('on', x.dataset.c === v)); if (key.startsWith('bg.c')) $$('[data-g]', el).forEach(x => x.classList.remove('on')); draw(); if (full) commit(); };
      $$('button', g).forEach(b => b.onclick = () => set(b.dataset.c, true));
      const ci = $('input', g); ci.oninput = () => set(ci.value, false); ci.onchange = () => set(ci.value, true);
    });
    $$('#kpBgMode button', el).forEach(b => b.onclick = () => { K.bg.mode = b.dataset.v; side(); draw(); commit(); });
    $$('[data-g]', el).forEach(b => b.onclick = () => { const [a, c] = b.dataset.g.split(','); K.bg.c1 = a; K.bg.c2 = c; side(); draw(); commit(); });
    const tx = $('#kpText', el);
    if (tx) { tx.addEventListener('keydown', e => e.stopPropagation()); tx.oninput = () => { l.text = tx.value; draw(); const r = $(`[data-l="${l.id}"] b`, el); if (r) r.textContent = lname(l); }; tx.onchange = commit; }
    const ai = $('#kpAi', el); if (ai) ai.onclick = () => suggest(l);
  };
  const suggest = async l => {
    const konu = prompt('Video ne hakkında? (kısaca yaz)', (K.src && K.src.title) || l.text.replace(/\*/g, '') || '');
    if (!konu) return;
    const b = $('#kpAi', host); if (b) { b.disabled = true; b.textContent = '✨ Düşünüyor...'; }
    try {
      const r = await KS.api('/api/kapak/yazi', { konu });
      const ch = $('#kpChips', host);
      if (ch) {
        ch.innerHTML = r.yazilar.map(t => `<button>${KS.esc(t)}</button>`).join('');
        $$('button', ch).forEach((x, i) => x.onclick = () => { l.text = r.yazilar[i]; const tx = $('#kpText', host); if (tx) tx.value = l.text; draw(); commit(); });
      }
    } catch (e) { KS.toast(KS.esc(e.message), 'err'); }
    const b2 = $('#kpAi', host); if (b2) { b2.disabled = false; b2.textContent = '✨ Yapay zekâ yazı önersin'; }
  };
  const foot = () => {
    const f = $('#kpFoot', host); if (!f) return;
    const ok = K.layers.length || K.bg.url || K.src;
    f.innerHTML = `${K.saved ? `<div class="tk-file">✅<span>${KS.esc(K.saved.name)}</span><button class="btn ghost sm" id="kpShow">Klasörde göster</button></div>` : ''}
      ${U.seg('fmt', [['jpg', 'JPG · YouTube (2 MB altı)'], ['png', 'PNG · kayıpsız']], K.fmt)}
      <button class="btn primary glow kq-go" id="kpGo" ${ok ? '' : 'disabled'}>💾 Kapağı kaydet · ${K.W}×${K.H}</button>`;
    U.bind(f, K, () => persist());
    $('#kpGo', f).onclick = exportImg;
    const sh = $('#kpShow', f); if (sh) sh.onclick = () => KS.api('/api/reveal', { path: K.saved.path });
  };

  /* ---------------------------------------------------------------- klavye, kancalar */
  document.addEventListener('keydown', e => {
    if (KS.page !== 'kapak' || /INPUT|TEXTAREA|SELECT/.test(e.target.tagName) || document.querySelector('.modal-back')) return;
    const l = selL(), c = e.ctrlKey || e.metaKey, key = e.key.toLowerCase();
    let used = true;
    if (c && key === 'z') e.shiftKey ? redo() : undo();
    else if (c && key === 'y') redo();
    else if (c && key === 'd' && l) { const x = clone(l); x.x += 30; x.y += 30; add(x); }
    else if ((e.key === 'Delete' || e.key === 'Backspace') && l) { K.layers = K.layers.filter(x => x !== l); K.sel = null; side(); draw(); commit(); }
    else if (l && e.key.startsWith('Arrow')) { const d = e.shiftKey ? 10 : 1; if (e.key === 'ArrowLeft') l.x -= d; if (e.key === 'ArrowRight') l.x += d; if (e.key === 'ArrowUp') l.y -= d; if (e.key === 'ArrowDown') l.y += d; draw(); clearTimeout(K._kt); K._kt = setTimeout(commit, 400); }
    else if (e.key === 'Escape' && K.sel) { K.sel = null; side(); draw(); }
    else used = false;
    if (used) { e.preventDefault(); e.stopPropagation(); }
  }, true);
  window.addEventListener('resize', () => { if (KS.page === 'kapak') fit(); });
  KS.hooks.jobTick.push(() => { if (KS.page === 'kapak' && U.running(U.findJob(K.cutJob))) { const c = $('#kpSide .tk-job', host); if (c) c.outerHTML = U.jobCard(U.findJob(K.cutJob), 'Kişi kesiliyor...'); } });
  KS.hooks.jobDone.push(j => {
    if (!K.cutJob || j.id !== K.cutJob) return;
    K.cutJob = null;
    if (j.status === 'bitti') { onCut(j); if (KS.page !== 'kapak') KS.toast('✂️ Kişi kesildi, kapağa eklendi', 'ok', [{ label: 'Kapağa git', primary: true, fn: () => KS.go('kapak') }]); }
    else { K.pendingKisi = null; if (j.status === 'hata') KS.toast('Kişi kesilemedi: ' + KS.esc(j.message || ''), 'err'); side(); }
  });
  const init = () => {
    if (inited) return; inited = true;
    try {
      const s = JSON.parse(localStorage.getItem('kapak_son') || 'null');
      if (s && s.d) { Object.assign(K, JSON.parse(s.d)); K.src = s.src || null; K.frames = s.frames || []; K.t = s.t || 0; K.fmt = s.fmt || 'jpg'; K.layers.forEach(l => { const n = parseInt(String(l.id).slice(1)); if (n >= uid) uid = n + 1; }); }
    } catch (e) { }
    hist = [snap()];
    shell(); fontsReady().then(draw);
  };
  KS.hooks.page.push(p => { if (p !== 'kapak') return; if (!inited) init(); else { fit(); draw(); } });
  KS.toolDrop.kapak = f => { if (f.kind !== 'video' && f.kind !== 'image') return KS.toast('Kapak için video ya da fotoğraf bırak', 'err'); init(); loadSrc(f); };
  /* paylaşım penceresinden / asistandan: projeden kapak */
  KS.kapakFromProject = async pid => {
    KS.go('kapak'); init();
    try {
      const r = await KS.api(`/api/project/${pid}/frames`);
      K.layers = []; K.sel = null;
      await loadSrc({ path: r.source, name: r.title || 'Proje', title: r.title || '', kind: 'video', start: r.start, end: r.end });
      applyTpl('klasik');
    } catch (e) { KS.toast(KS.esc(e.message), 'err'); }
  };
})();
