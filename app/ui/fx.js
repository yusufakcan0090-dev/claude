/* Kesit Stüdyosu — zamanlı efektlerin canlı önizlemesi (dışa aktarmadaki ffmpeg efektlerinin canvas karşılığı) */
(() => {
  const FX = KS.fx = {};
  FX.LIST = {
    glitch: ['Glitch', 'Glitch', .8], rgbsplit: ['RGB Ayrışma', 'Glitch', .8], pixel: ['Piksel / Mozaik', 'Glitch', 1.5],
    glow: ['Renkli Parlama', 'Işık', 1.5], rainbow: ['Gökkuşağı Parlama', 'Işık', 1.5], softlight: ['Yumuşak Işık', 'Işık', 2],
    leak: ['Işık Sızıntısı', 'Işık', 1.6], flare: ['Lens Flare', 'Işık', 1.6], flash: ['Flaş', 'Işık', .35], strobe: ['Strobe', 'Işık', .8],
    film: ['Eski Film', 'Retro', 2.5], vhs: ['VHS', 'Retro', 2.5],
    motionblur: ['Hareket Bulanıklığı', 'Bulanıklık', .8], dirblur: ['Yön Bulanıklığı', 'Bulanıklık', .6], defocus: ['Odak Dışı', 'Bulanıklık', 1],
    shake: ['Hafif Kamera', 'Sarsıntı', 2], quake: ['Deprem', 'Sarsıntı', 1], punch: ['Yumruk', 'Sarsıntı', .6],
    posterize: ['Posterize', 'Stilize', 1.5], duotone: ['Duotone', 'Stilize', 1.5], halftone: ['Halftone', 'Stilize', 1.2],
    edges: ['Kenar Çizgisi', 'Stilize', 1.2], bwpop: ['Siyah-Beyaz Vurgu', 'Stilize', 1.5], colorkeep: ['Kırmızıyı Tut', 'Stilize', 1.5],
    invert: ['Negatif', 'Stilize', .5], symmetry: ['Ayna Simetri', 'Stilize', 1.5],
  };
  FX.ICON = { Glitch: '📺', 'Işık': '✨', Retro: '📼', 'Bulanıklık': '🌫', 'Sarsıntı': '💥', Stilize: '🎨' };
  FX.TRANS = [['none', 'Yok'], ['flash', 'Flaş'], ['zoom', 'Zoom'], ['slide', 'Kayma'], ['glitch', 'Glitch'], ['dip', 'Kararma'], ['white', 'Beyaz'], ['swirl', 'Girdap']];
  FX.PARAMS = { glow: [['color', 'Renk', '#FF3D8B']], leak: [['color', 'Renk', '#FF8A00']], duotone: [['color', 'Koyu renk', '#2B1055'], ['color2', 'Açık renk', '#FF3D8B']] };

  const tmp = document.createElement('canvas'), tx = tmp.getContext('2d');
  const tmp2 = document.createElement('canvas'), tx2 = tmp2.getContext('2d');
  const small = document.createElement('canvas'), sx = small.getContext('2d');
  const noise = document.createElement('canvas'); noise.width = noise.height = 128;
  (() => { const n = noise.getContext('2d'), d = n.createImageData(128, 128); for (let i = 0; i < d.data.length; i += 4) { const v = Math.random() * 255; d.data[i] = d.data[i + 1] = d.data[i + 2] = v; d.data[i + 3] = 255; } n.putImageData(d, 0, 0); })();
  let flareImg = null;
  const makeFlare = W => {
    const c = document.createElement('canvas'); c.width = W * 1.6; c.height = W * .9;
    const x = c.getContext('2d'), cx = c.width / 2, cy = c.height / 2;
    const rad = (r, stops) => { const g = x.createRadialGradient(cx, cy, 0, cx, cy, r); stops.forEach(([o, col]) => g.addColorStop(o, col)); x.fillStyle = g; x.fillRect(0, 0, c.width, c.height); };
    x.globalCompositeOperation = 'lighter';
    rad(W * .25, [[0, 'rgba(255,230,180,.9)'], [.15, 'rgba(255,200,140,.45)'], [1, 'rgba(0,0,0,0)']]);
    rad(W * .05, [[0, 'rgba(255,255,255,1)'], [1, 'rgba(255,220,160,0)']]);
    const g = x.createLinearGradient(0, 0, c.width, 0); g.addColorStop(0, 'rgba(100,170,255,0)'); g.addColorStop(.5, 'rgba(140,200,255,.8)'); g.addColorStop(1, 'rgba(100,170,255,0)');
    x.fillStyle = g; x.fillRect(0, cy - W * .006, c.width, W * .012);
    x.strokeStyle = 'rgba(150,255,200,.25)'; x.lineWidth = W * .01; x.beginPath(); x.arc(cx, cy, W * .28, 0, 7); x.stroke();
    [[-.25, .03, 'rgba(100,220,255,.35)'], [-.42, .05, 'rgba(255,120,230,.3)'], [.3, .02, 'rgba(255,255,150,.35)']].forEach(([gx, r, col]) => { x.fillStyle = col; x.beginPath(); x.arc(cx + gx * c.width, cy, W * r, 0, 7); x.fill(); });
    return c;
  };
  const hex = (h, d) => { h = (h || d).replace('#', ''); return [0, 2, 4].map(i => parseInt(h.substr(i, 2), 16) || 0); };

  /* x: önizleme bağlamı (PW x PH), lt: efektin başından itibaren saniye, D: süre, I: 0..1 */
  FX.apply = (x, kind, lt, D, I, p, PW, PH) => {
    tmp.width = PW; tmp.height = PH; tx.drawImage(x.canvas, 0, 0);
    const W = PW;
    x.save();
    const shiftCopies = (sh, a) => {
      x.globalCompositeOperation = 'screen'; x.globalAlpha = a;
      x.filter = 'sepia(1) saturate(6) hue-rotate(-50deg)'; x.drawImage(tmp, -sh, 0);
      x.filter = 'sepia(1) saturate(6) hue-rotate(170deg)'; x.drawImage(tmp, sh, 0);
      x.filter = 'none'; x.globalAlpha = 1; x.globalCompositeOperation = 'source-over';
    };
    const noiseOver = a => { x.globalAlpha = a; x.globalCompositeOperation = 'overlay'; x.translate(-Math.random() * 128, -Math.random() * 128); x.fillStyle = x.createPattern(noise, 'repeat'); x.fillRect(0, 0, PW + 128, PH + 128); x.setTransform(1, 0, 0, 1, 0, 0); x.globalAlpha = 1; x.globalCompositeOperation = 'source-over'; };
    const vign = a => { const g = x.createRadialGradient(PW / 2, PH / 2, PH * .25, PW / 2, PH / 2, PH * .62); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, `rgba(0,0,0,${a})`); x.fillStyle = g; x.fillRect(0, 0, PW, PH); };
    const filt = f => { x.clearRect(0, 0, PW, PH); x.filter = f; x.drawImage(tmp, 0, 0); x.filter = 'none'; };
    const pixels = fn => { const d = x.getImageData(0, 0, PW, PH), a = d.data; fn(a); x.putImageData(d, 0, 0); };
    const shakeDraw = (z, ox, oy) => { x.clearRect(0, 0, PW, PH); x.translate(PW / 2, PH / 2); x.scale(z, z); x.translate(-PW / 2 + ox / z, -PH / 2 + oy / z); x.drawImage(tmp, 0, 0); x.setTransform(1, 0, 0, 1, 0, 0); };
    switch (kind) {
      case 'glitch': case 'tr_glitch': {
        if (kind === 'tr_glitch') I = 1;
        const sh = Math.max(1, W * .012 * (.5 + I));
        x.filter = `hue-rotate(${40 * I * Math.sin(lt * 83)}deg) brightness(${1 + .1 * I * Math.sin(lt * 97)}) contrast(${1 + .25 * I})`; x.drawImage(tmp, 0, 0); x.filter = 'none';
        shiftCopies(sh, .45);
        const h = Math.floor(PH / 10), f1 = Math.floor(lt * 15), f2 = Math.floor(lt * 12);
        const y1 = (f1 * 397 * (PH / 1920)) % (PH - h), y2 = ((f2 * 911 + 200) * (PH / 1920)) % (PH - h);
        x.drawImage(tmp, 0, y1, PW, h, W * .05 * I * Math.sin(f1 * 13), y1, PW, h);
        x.drawImage(tmp, 0, y2, PW, h / 2, -W * .07 * I * Math.sin(f2 * 7), y2, PW, h / 2);
        noiseOver(.12 + .25 * I); break;
      }
      case 'rgbsplit': shiftCopies(W * .018 * (.4 + I), .55); break;
      case 'pixel': { const b = 6 + 40 * I; small.width = Math.max(4, PW * 2 / b); small.height = Math.max(4, PH * 2 / b); sx.drawImage(tmp, 0, 0, small.width, small.height); x.imageSmoothingEnabled = false; x.drawImage(small, 0, 0, PW, PH); x.imageSmoothingEnabled = true; break; }
      case 'glow': case 'rainbow': case 'softlight': {
        tmp2.width = PW; tmp2.height = PH;
        tx2.filter = `blur(${PW / (kind === 'softlight' ? 30 : 45)}px)` + (kind === 'rainbow' ? ` hue-rotate(${lt * 300}deg) saturate(2.5)` : '');
        tx2.drawImage(tmp, 0, 0); tx2.filter = 'none';
        if (kind === 'glow') { tx2.globalCompositeOperation = 'multiply'; tx2.fillStyle = (p && p.color) || '#FF3D8B'; tx2.fillRect(0, 0, PW, PH); tx2.globalCompositeOperation = 'source-over'; }
        x.globalCompositeOperation = kind === 'softlight' ? 'soft-light' : 'screen'; x.globalAlpha = kind === 'softlight' ? .3 + .6 * I : .35 + .6 * I;
        x.drawImage(tmp2, 0, 0); break;
      }
      case 'leak': {
        const a = Math.min(1, lt / .2, (D - lt) / .25) * (.4 + .6 * I), [r, g, b] = hex(p && p.color, '#FF8A00');
        const cx = PW * (.1 + .8 * lt / D), cy = PH * (.15 + .5 * lt / D);
        const gr = x.createRadialGradient(cx, cy, 0, cx, cy, PH * .75); gr.addColorStop(0, `rgba(${r},${g},${b},${a})`); gr.addColorStop(.35, `rgba(255,210,122,${a * .6})`); gr.addColorStop(1, 'rgba(0,0,0,0)');
        x.globalCompositeOperation = 'screen'; x.fillStyle = gr; x.fillRect(0, 0, PW, PH); break;
      }
      case 'flare': {
        if (!flareImg || flareImg.width !== Math.round(PW * 1.6)) flareImg = makeFlare(PW);
        const a = Math.min(1, lt / .25, (D - lt) / .3) * (.55 + .45 * I);
        x.globalCompositeOperation = 'screen'; x.globalAlpha = Math.max(0, a);
        x.drawImage(flareImg, -flareImg.width * .75 + lt / D * PW * .9, PH * .22 - flareImg.height / 2); break;
      }
      case 'flash': x.fillStyle = `rgba(255,255,255,${(.55 + .4 * I) * Math.max(0, 1 - lt / Math.min(D, .35))})`; x.fillRect(0, 0, PW, PH); break;
      case 'strobe': if ((lt * (8 + 8 * I)) % 1 < .5) { x.fillStyle = `rgba(255,255,255,${.4 + .5 * I})`; x.fillRect(0, 0, PW, PH); } break;
      case 'film': {
        filt(`sepia(1) contrast(1.1) brightness(${1 + .04 * Math.sin(lt * 31)})`); noiseOver(.15 + .2 * I); vign(.55);
        const f = Math.floor(lt * 24);
        if (f % 7 < 2) { x.fillStyle = 'rgba(255,255,255,.35)'; x.fillRect((f * 173 * PW / 1080) % PW, 0, 1.5, PH); }
        if (f % 5 < 1) { x.fillStyle = 'rgba(0,0,0,.45)'; x.fillRect(((f * 389 + 60) * PW / 1080) % PW, 0, 1, PH); }
        break;
      }
      case 'vhs': {
        filt(`saturate(${1.2 + .3 * I}) contrast(1.08) blur(.4px)`); shiftCopies(Math.max(1, PW / 260), .3); noiseOver(.1 + .12 * I);
        x.fillStyle = `rgba(0,0,0,${.15 + .2 * I})`; for (let y = 0; y < PH; y += 2) x.fillRect(0, y, PW, 1);
        x.fillStyle = `rgba(255,255,255,${.08 + .1 * I})`; x.fillRect(0, (lt * PH * .3) % PH, PW, PH / 22); break;
      }
      case 'motionblur': x.globalAlpha = .35; x.drawImage(tmp, -3 - 6 * I, 0); x.drawImage(tmp, 3 + 6 * I, 0); break;
      case 'dirblur': case 'tr_slide': {
        if (kind === 'tr_slide') { x.clearRect(0, 0, PW, PH); const z = 1.35, off = (lt - D / 2) / D * PW * .22; x.translate(PW / 2, PH / 2); x.scale(z, z); x.translate(-PW / 2 - off, -PH / 2); x.drawImage(tmp, 0, 0); x.setTransform(1, 0, 0, 1, 0, 0); tmp.getContext('2d').drawImage(x.canvas, 0, 0); }
        const r = kind === 'tr_slide' ? PW / 18 : (10 + 50 * I) * PW / 1080, ang = ((p && +p.angle) || 0) * Math.PI / 180;
        x.globalAlpha = .18; for (let k = -3; k <= 3; k++) if (k) x.drawImage(tmp, Math.cos(ang) * r * k / 3, Math.sin(ang) * r * k / 3);
        break;
      }
      case 'defocus': filt(`blur(${(3 + 14 * I) * PW / 1080 * 1.4}px)`); break;
      case 'shake': { const A = W * .012 * (.5 + I); shakeDraw(1.06, Math.sin(lt * 7) * A + Math.sin(lt * 13) * A / 2, Math.cos(lt * 9) * A + Math.sin(lt * 5) * A / 3); break; }
      case 'quake': { const A = W * .03 * (.4 + I); shakeDraw(1.12, (Math.sin(lt * 47) + .6 * Math.sin(lt * 83) + .3 * Math.sin(lt * 131)) * A * .55, (Math.cos(lt * 53) + .5 * Math.sin(lt * 97)) * A * .55); break; }
      case 'punch': { const A = W * .045 * (.4 + I), e = Math.exp(-lt * 7); shakeDraw(1.12, e * Math.sin(lt * 55) * A, e * Math.cos(lt * 48) * A * .7); break; }
      case 'posterize': { const lv = Math.max(2, Math.round(6 - 4 * I)), q = Math.floor(256 / lv); pixels(a => { for (let i = 0; i < a.length; i += 4) { a[i] = Math.floor(a[i] / q) * q + q / 2; a[i + 1] = Math.floor(a[i + 1] / q) * q + q / 2; a[i + 2] = Math.floor(a[i + 2] / q) * q + q / 2; } }); break; }
      case 'duotone': { const c0 = hex(p && p.color, '#2B1055'), c1 = hex(p && p.color2, '#FF3D8B'), k = 1 + .3 * I; pixels(a => { for (let i = 0; i < a.length; i += 4) { let v = (a[i] * .3 + a[i + 1] * .59 + a[i + 2] * .11); v = Math.min(255, Math.max(0, (v - 128) * k + 128)) / 255; a[i] = c0[0] + (c1[0] - c0[0]) * v; a[i + 1] = c0[1] + (c1[1] - c0[1]) * v; a[i + 2] = c0[2] + (c1[2] - c0[2]) * v; } }); break; }
      case 'halftone': { const k = (.75 - .45 * I) * 1080 / PW; pixels(a => { for (let y = 0, i = 0; y < PH; y++) for (let xx = 0; xx < PW; xx++, i += 4) { const v = a[i] * .3 + a[i + 1] * .59 + a[i + 2] * .11, o = v > 128 + 115 * Math.sin(xx * k) * Math.sin(y * k) ? 245 : 15; a[i] = a[i + 1] = a[i + 2] = o; } }); break; }
      case 'edges': { pixels(a => { const g = new Float32Array(PW * PH); for (let i = 0, j = 0; i < a.length; i += 4, j++) g[j] = a[i] * .3 + a[i + 1] * .59 + a[i + 2] * .11; const th = 40 - 25 * I; for (let y = 1; y < PH - 1; y++) for (let xx = 1; xx < PW - 1; xx++) { const j = y * PW + xx, gx = g[j + 1] - g[j - 1], gy = g[j + PW] - g[j - PW], m = Math.hypot(gx, gy), i = j * 4; if (m < th) { a[i] *= .15; a[i + 1] *= .15; a[i + 2] *= .15; } } }); break; }
      case 'bwpop': filt(`grayscale(1) contrast(${1.2 + .3 * I}) brightness(.97)`); vign(.5); break;
      case 'colorkeep': { const sim = .15 + .25 * I; pixels(a => { for (let i = 0; i < a.length; i += 4) { const r = a[i], g = a[i + 1], b = a[i + 2]; const red = r > 90 && r > g * (1.6 - sim) && r > b * (1.6 - sim); if (!red) { const v = r * .3 + g * .59 + b * .11; a[i] = a[i + 1] = a[i + 2] = v; } } }); break; }
      case 'invert': filt('invert(1)'); break;
      case 'symmetry': x.save(); x.translate(PW, 0); x.scale(-1, 1); x.drawImage(tmp, 0, 0, PW / 2, PH, 0, 0, PW / 2, PH); x.restore(); break;
      case 'tr_flash': x.fillStyle = `rgba(255,255,255,${.95 * Math.max(0, 1 - Math.abs(lt - D / 2) / (D / 2))})`; x.fillRect(0, 0, PW, PH); break;
      case 'tr_white': x.fillStyle = `rgba(255,255,255,${Math.max(0, 1 - Math.abs(lt - D / 2) / (D / 2))})`; x.fillRect(0, 0, PW, PH); break;
      case 'tr_dip': x.fillStyle = `rgba(0,0,0,${Math.max(0, 1 - Math.abs(lt - D / 2) / (D / 2))})`; x.fillRect(0, 0, PW, PH); break;
      case 'tr_zoom': shakeDraw(1 + .45 * Math.sin(Math.PI * Math.min(1, lt / D)), 0, 0); break;
      case 'tr_swirl': { const z = 1 + .5 * Math.sin(Math.PI * Math.min(1, lt / D)), a = 1.2 * Math.sin(Math.PI * Math.min(1, lt / D)); x.clearRect(0, 0, PW, PH); x.fillStyle = '#000'; x.fillRect(0, 0, PW, PH); x.translate(PW / 2, PH / 2); x.rotate(a); x.scale(z, z); x.translate(-PW / 2, -PH / 2); x.filter = `blur(${PW / 240}px)`; x.drawImage(tmp, 0, 0); x.setTransform(1, 0, 0, 1, 0, 0); x.filter = 'none'; break; }
    }
    x.restore();
  };

  /* LUT önizleme */
  FX.lut = null;
  FX.loadLut = async pid => { try { const r = await KS.api(`/api/project/${pid}/lutdata`); FX.lut = r.size ? r : null; } catch (e) { FX.lut = null; } };
  FX.applyLut = (x, PW, PH, mix) => {
    const L = FX.lut; if (!L) return;
    const n = L.size, t = L.data, s = (n - 1) / 255, m = Math.max(0, Math.min(1, mix));
    const d = x.getImageData(0, 0, PW, PH), a = d.data;
    for (let i = 0; i < a.length; i += 4) {
      const r = Math.round(a[i] * s), g = Math.round(a[i + 1] * s), b = Math.round(a[i + 2] * s);
      const j = ((b * n + g) * n + r) * 3;
      a[i] += (t[j] * 255 - a[i]) * m; a[i + 1] += (t[j + 1] * 255 - a[i + 1]) * m; a[i + 2] += (t[j + 2] * 255 - a[i + 2]) * m;
    }
    x.putImageData(d, 0, 0);
  };
})();
