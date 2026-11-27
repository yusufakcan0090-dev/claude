/* Kesit Stüdyosu — Araçlar sayfası + araçların ortak parçaları */
(() => {
  KS.hooks.page = KS.hooks.page || [];
  KS.toolDrop = KS.toolDrop || {};
  const TOOLS = [
    { id: 'vbg', icon: '🟩', t: 'Video Arka Plan Sil', d: 'Yeşil perde olmadan kişiyi videodan ayır; arkasına renk, bulanık, resim ya da video koy.', c: '#22c55e' },
    { id: 'kapak', icon: '🖼️', t: 'Kapak Stüdyosu', d: 'Kişiyi kes, renkli arka plan, büyük yazı, ok ve emoji: tıklanan YouTube / Reels kapakları.', c: '#f59e0b' },
    { id: 'kanal', icon: '📊', t: 'Kanal Analizi', d: 'YouTube kanalında hangi videolar tuttu, hangi gün ve saat daha çok izleniyor, ne yapmalı?', c: '#38bdf8' },
    { id: 'donustur', icon: '⇄', t: 'Dönüştür', d: 'Video, ses ve fotoğrafları istediğin biçime çevir.', c: '#94a3b8' },
    { id: 'kalite', icon: '💎', t: 'Kalite Artır', d: 'Video ve fotoğrafı yapay zekâ ile netleştir, büyüt, FPS artır.', c: '#2d8ceb' },
  ];
  const grid = $('#arGrid');
  grid.innerHTML = TOOLS.map(x => `<button class="ar-card" data-goto="${x.id}" style="--c:${x.c}"><span class="ar-ic">${x.icon}</span><b>${x.t}</b><small>${x.d}</small><span class="ar-go">Aç →</span></button>`).join('');

  /* ---- ortak parçalar ---- */
  const U = KS.ui = {};
  U.esc = KS.esc;
  U.seg = (key, list, cur, cls = '') => `<div class="seg kq-seg ${cls}" data-k="${key}">${list.map(([v, n, tip]) => `<button data-v="${v}" class="${String(cur) === String(v) ? 'on' : ''}" ${tip ? `title="${U.esc(tip)}"` : ''}>${n}</button>`).join('')}</div>`;
  U.sl = (key, label, min, max, cur, step = 1, unit = '') => `<div class="kq-sl"><div><span>${label}</span><b id="v_${key}">${cur}${unit}</b></div><input type="range" min="${min}" max="${max}" step="${step}" value="${cur}" data-r="${key}" data-unit="${unit}"></div>`;
  U.chk = (key, label, on) => `<label class="ae-chk kq-chk"><input type="checkbox" data-c="${key}" ${on ? 'checked' : ''}>${label}</label>`;
  U.h = t => `<div class="kq-h">${t}</div>`;
  U.grp = (title, icon, body, open = true) => `<details class="kq-g" ${open ? 'open' : ''}><summary><span class="kq-gi">${icon}</span>${title}<span class="kq-chev"></span></summary><div class="kq-gb">${body}</div></details>`;
  U.head = (title, sub, right = '') => `<header class="page-head tool-head"><div><button class="tool-back" data-goto="araclar">← Araçlar</button><h1>${title}</h1><p class="sub">${sub}</p></div><div class="tool-right">${right}</div></header>`;
  /** o nesnesine bağla: seg/slider/checkbox değişince o[key] güncellenir, cb(key) çağrılır */
  U.bind = (root, o, cb) => {
    $$('.kq-seg', root).forEach(g => $$('button', g).forEach(b => b.onclick = () => { o[g.dataset.k] = isNaN(+b.dataset.v) || b.dataset.v === '' ? b.dataset.v : +b.dataset.v; $$('button', g).forEach(x => x.classList.toggle('on', x === b)); cb && cb(g.dataset.k, true); }));
    $$('[data-r]', root).forEach(r => { KS.paintRange(r); r.oninput = () => { o[r.dataset.r] = +r.value; const v = $('#v_' + r.dataset.r, root); if (v) v.textContent = r.value + (r.dataset.unit || ''); KS.paintRange(r); cb && cb(r.dataset.r, false); }; r.onchange = () => cb && cb(r.dataset.r, true); });
    $$('[data-c]', root).forEach(c => c.onchange = () => { o[c.dataset.c] = c.checked; cb && cb(c.dataset.c, true); });
    $$('input.inp, textarea.inp', root).forEach(i => i.addEventListener('keydown', e => e.stopPropagation()));
  };
  U.pick = async kinds => {
    const f = await KS.api('/api/pick_any', {});
    if (!f || !f.path) return null;
    if (f.error) { KS.toast(U.esc(f.error), 'err'); return null; }
    if (kinds && !kinds.includes(f.kind)) { KS.toast('Bu araç için ' + kinds.map(k => ({ video: 'video', image: 'fotoğraf', audio: 'ses' }[k])).join(' ya da ') + ' seç', 'err'); return null; }
    return f;
  };
  U.media = p => '/media/kalite_src?path=' + encodeURIComponent(p);
  U.jobCard = (j, label) => {
    if (!j) return '';
    const p = Math.round((j.progress || 0) * 100), run = j.status === 'calisiyor' || j.status === 'bekliyor', ex = j.extra || {};
    const left = ex.eta != null ? ex.eta : (run && p >= 3 && ex.elapsed ? ex.elapsed * (100 - p) / p : null);
    const eta = left != null ? ` · kalan ~${left < 60 ? Math.max(1, Math.round(left)) + ' sn' : Math.round(left / 60) + ' dk'}` : '';
    return `<div class="tk-job ${j.status === 'hata' ? 'bad' : j.status === 'bitti' ? 'ok' : ''}"><div><b>${run ? U.esc(ex.asama || j.message || label || 'Hazırlanıyor...') : j.status === 'bitti' ? '✓ ' + U.esc(j.message) : '✕ ' + U.esc(j.message)}</b><span>${run ? '%' + p + eta : ''}</span></div>${run ? `<div class="kq-pbar big"><i style="width:${p}%"></i></div>` : ''}</div>`;
  };
  U.findJob = id => id && (KS.state.jobs || []).find(x => x.id === id);
  U.running = j => j && (j.status === 'calisiyor' || j.status === 'bekliyor');
})();
