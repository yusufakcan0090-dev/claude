/* Kanal Analizi — YouTube kanalında ne tutuyor, ne yapmalı? */
(() => {
  const U = KS.ui, host = $('#tKanal');
  const C = { uzun: '#3f8ef0', shorts: '#d98a0b' };
  const S = { input: '', n: 50, job: null, key: null, a: null, ai: null, aiBusy: false, sort: 'tarih', dir: -1, tab: 'hepsi' };
  let inited = false;
  const esc = KS.esc;
  const num = n => { n = +n || 0; if (n >= 1e6) return (n / 1e6).toFixed(1).replace(/\.0$/, '').replace('.', ',') + ' Mn'; if (n >= 1e3) return (n / 1e3).toFixed(1).replace(/\.0$/, '').replace('.', ',') + ' B'; return String(Math.round(n)); };
  const full = n => (Math.round(+n || 0)).toLocaleString('tr-TR');
  const pct = x => x == null ? '—' : '%' + x.toFixed(1).replace('.', ',');
  const durS = s => { s = Math.round(s || 0); return s >= 3600 ? `${Math.floor(s / 3600)}:${String(Math.floor(s % 3600 / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}` : `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`; };

  /* ---------------------------------------------------------------- grafikler (SVG) */
  const barPath = (x, y, w, h, r = 4) => { if (h <= 0) return ''; r = Math.min(r, w / 2, h); return `M${x},${y + h}V${y + r}Q${x},${y} ${x + r},${y}H${x + w - r}Q${x + w},${y} ${x + w},${y + r}V${y + h}Z`; };
  const bars = (data, o) => {
    const W = o.w || 600, H = o.h || 180, padL = 6, padB = o.labels ? 22 : 6, padT = 18, n = data.length, gap = o.gap != null ? o.gap : 2;
    const max = Math.max(1e-9, o.ref || 0, ...data.map(o.v)) * 1.08, bw = Math.max(1, (W - padL * 2 - gap * (n - 1)) / n);
    let s = `<svg viewBox="0 0 ${W} ${H}" class="kn-svg">`;
    if (o.ref != null) { const y = padT + (H - padT - padB) * (1 - o.ref / max); s += `<line x1="0" x2="${W}" y1="${y}" y2="${y}" class="kn-ref"/><text x="${W - 4}" y="${y - 4}" text-anchor="end" class="kn-reft">${o.refLabel || ''}</text>`; }
    data.forEach((d, i) => {
      const v = o.v(d), h = (H - padT - padB) * v / max, x = padL + i * (bw + gap), y = H - padB - h;
      s += `<g class="kn-bar" data-tip="${esc(o.tip(d))}"><rect x="${x - gap / 2}" y="0" width="${bw + gap}" height="${H}" fill="transparent"/><path d="${barPath(x, y, bw, h)}" fill="${o.color(d)}" opacity="${o.dim && o.dim(d) ? .38 : 1}"/>`;
      if (o.top && o.top(d)) s += `<text x="${x + bw / 2}" y="${y - 5}" text-anchor="middle" class="kn-val">${o.top(d)}</text>`;
      if (o.labels) s += `<text x="${x + bw / 2}" y="${H - 6}" text-anchor="middle" class="kn-lab">${o.labels(d, i)}</text>`;
      s += '</g>';
    });
    return s + `<line x1="0" x2="${W}" y1="${H - padB}" y2="${H - padB}" class="kn-base"/></svg>`;
  };
  const tipOn = root => {
    let tip = $('#knTip'); if (!tip) { tip = document.createElement('div'); tip.id = 'knTip'; tip.className = 'kn-tip'; tip.hidden = true; document.body.appendChild(tip); }
    root.addEventListener('mousemove', e => { const g = e.target.closest('[data-tip]'); if (!g || !root.contains(g)) { tip.hidden = true; return; } tip.innerHTML = g.dataset.tip; tip.hidden = false; const r = tip.getBoundingClientRect(); tip.style.left = Math.min(innerWidth - r.width - 8, e.clientX + 14) + 'px'; tip.style.top = Math.max(8, e.clientY - r.height - 10) + 'px'; });
    root.addEventListener('mouseleave', () => { tip.hidden = true; });
    const sc = $('#knScroll', host); if (sc) sc.addEventListener('scroll', () => { tip.hidden = true; }, { passive: true });
  };

  /* ---------------------------------------------------------------- görünüm */
  const render = () => {
    const j = U.findJob(S.job), run = U.running(j), recent = (KS.state.settings && KS.state.settings.kanal_son) || [];
    host.innerHTML = `${U.head('Kanal Analizi', 'YouTube kanalının son videolarını inceler: ne tuttu, hangi gün ve saat daha iyi, ne yapmalısın.', '')}
      <div class="kn-scroll" id="knScroll">
      <div class="kn-bar-in">
        <input class="inp kn-in" id="knIn" placeholder="@kanaladi ya da YouTube kanal linki" value="${esc(S.input)}">
        <div class="seg kq-seg" data-k="n">${[[20, 'Son 20'], [50, 'Son 50'], [100, 'Son 100']].map(([v, t]) => `<button data-v="${v}" class="${S.n === v ? 'on' : ''}">${t}</button>`).join('')}</div>
        <button class="btn primary glow" id="knGo" ${run ? 'disabled' : ''}>${run ? 'İnceleniyor...' : '📊 Analiz et'}</button>
      </div>
      ${recent.length ? `<div class="kn-recent"><span>Son bakılanlar:</span>${recent.map(r => `<button data-r="${esc(r.girdi)}">${esc(r.ad || r.girdi)}</button>`).join('')}</div>` : ''}
      ${run || (j && j.status === 'hata') ? `<div class="kn-job">${U.jobCard(j, 'Kanal inceleniyor...')}${run ? '<small>Her video tek tek açılıp izlenme, beğeni, yorum ve yüklenme saati okunuyor. 50 video yaklaşık 1 dakika sürer.</small>' : ''}</div>` : ''}
      <div class="kn-body" id="knBody">${S.a ? dash(S.a) : run ? '' : empty()}</div></div>`;
    bind();
  };
  const empty = () => `<div class="tk-empty kn-empty"><div class="big">📊</div><b>Bir YouTube kanalı yaz ve "Analiz et"e bas</b>
    <span>Kendi kanalına ya da örnek aldığın kanallara bakabilirsin. Kanalın herkese açık olması yeterli, giriş yapmana gerek yok.</span>
    <div class="kn-what"><div>📅 En iyi gün ve saat</div><div>📱 Shorts mı uzun video mu?</div><div>🏆 En çok tutan videolar</div><div>✍️ Tutan başlık kelimeleri</div><div>💬 Etkileşim oranı</div><div>✨ Yapay zekâ önerileri</div></div></div>`;
  const dash = a => {
    const o = a.ozet, k = a.kanal, L = a.uzun, Sh = a.shorts_g;
    const when = new Date(a.zaman * 1000).toLocaleString('tr-TR', { day: '2-digit', month: 'long', hour: '2-digit', minute: '2-digit' });
    const tiles = [['Toplam izlenme', num(o.toplam), `${o.adet} videoda`], ['Ortanca izlenme', num(o.medyan), 'bir video genelde bu kadar izleniyor'], ['Etkileşim', pct(o.etkilesim), 'beğeni + yorum / izlenme'], ['Yükleme sıklığı', o.haftalik != null ? String(o.haftalik).replace('.', ',') + ' / hafta' : '—', `son 30 günde ${o.son30} video`]];
    const trend = a.trend;
    let bestG = -1; a.gun.forEach((g, i) => { if (g.adet >= 2 && (bestG < 0 || g.rel > a.gun[bestG].rel)) bestG = i; });
    const sa = a.saat.filter(x => x.adet >= 2), bestH = sa.length ? sa.reduce((b, x) => x.rel > b.rel ? x : b).saat : -1;
    const cmp = (lbl, l, s, f, isPct) => { const mx = Math.max(f(l) || 0, f(s) || 0, 1e-9); return `<div class="kn-cmp"><span>${lbl}</span>${[['Uzun', l, C.uzun], ['Shorts', s, C.shorts]].map(([n, g, c]) => `<div class="kn-cmpr"><em>${n}</em><i><b style="width:${g.adet ? Math.max(2, (f(g) || 0) / mx * 100) : 0}%;background:${c}"></b></i><strong>${g.adet ? (isPct ? pct(f(g)) : num(f(g))) : '—'}</strong></div>`).join('')}</div>`; };
    const card = v => `<a class="kn-vid" data-url="${esc(v.url)}" title="YouTube'da aç"><span class="kn-th"><img src="${esc(v.kapak)}" loading="lazy" onerror="this.style.visibility='hidden'"><em class="${v.short ? 's' : ''}">${v.short ? 'Shorts' : durS(v.sure)}</em></span><b>${esc(v.baslik)}</b><small>${num(v.izlenme)} izlenme · ${v.tarih || ''}${v.gunluk ? ` · günde ${num(v.gunluk)}` : ''}</small></a>`;
    const KEY = { tarih: 'ts', izlenme: 'izlenme', begeni: 'begeni', yorum: 'yorum', etkilesim: 'etkilesim', gunluk: 'gunluk', sure: 'sure' }[S.sort];
    const rows = a.videolar.filter(v => S.tab === 'hepsi' || (S.tab === 'shorts') === v.short).slice().sort((x, y) => { const p = x[KEY] ?? -1, q = y[KEY] ?? -1; return S.dir * ((p > q) - (p < q)); });
    const th = (k2, t) => `<th data-s="${k2}" class="${S.sort === k2 ? 'on' : ''}">${t}${S.sort === k2 ? (S.dir < 0 ? ' ▾' : ' ▴') : ''}</th>`;
    const legend = `<div class="kn-legend"><i style="background:${C.uzun}"></i>Uzun video <i style="background:${C.shorts}"></i>Shorts</div>`;
    return `
    <div class="kn-ch">
      <div class="kn-av"><span>${esc((k.ad || '?')[0].toUpperCase())}</span>${k.avatar ? `<img src="${esc(k.avatar)}" onerror="this.remove()">` : ''}</div>
      <div class="kn-chi"><b>${esc(k.ad)}</b><span>${k.abone ? num(k.abone) + ' abone · ' : ''}${o.adet} video incelendi (${o.uzun} uzun, ${o.shorts} Shorts) · ${o.ilk} - ${o.son}</span><small>Son güncelleme: ${when}</small></div>
      <button class="btn ghost sm" id="knOpen">Kanala git ↗</button><button class="btn ghost sm" id="knRe">↻ Yenile</button>
    </div>
    <div class="kn-tiles">${tiles.map(([t, v, s]) => `<div class="kn-tile"><span>${t}</span><b>${v}</b><small>${s}</small></div>`).join('')}</div>
    <div class="kn-2">
      <section class="kn-card kn-adv"><h3>🎯 Ne yapmalısın?</h3>
        <ul>${a.oneriler.map(x => `<li><span>${x.ikon}</span><p>${esc(x.metin)}</p></li>`).join('')}</ul>
        <div class="kn-ai">${S.ai ? aiHtml(S.ai) : `<button class="btn ghost" id="knAi" ${S.aiBusy ? 'disabled' : ''}>${S.aiBusy ? '✨ Yapay zekâ inceliyor...' : '✨ Yapay zekâ da yorumlasın (başlık fikirleri dahil)'}</button>`}</div>
      </section>
      <section class="kn-card"><h3>📱 Shorts mı, uzun video mu?</h3>
        ${cmp('Ortanca izlenme', L, Sh, g => g.medyan)}${cmp('Günde ortalama izlenme', L, Sh, g => g.gunluk)}${cmp('Etkileşim', L, Sh, g => g.etkilesim, true)}
        ${legend}
      </section>
    </div>
    <section class="kn-card"><h3>📈 Videoların izlenmeleri (eskiden yeniye)</h3>
      <div class="kn-chart">${bars(trend, { w: 1000, h: 200, gap: trend.length > 80 ? 1 : 2, v: t => t.i, color: t => t.s ? C.shorts : C.uzun, tip: t => `<b>${esc(t.b)}</b><br>${full(t.i)} izlenme · ${t.t} · ${t.s ? 'Shorts' : 'Uzun'}`, ref: a.ozet.medyan, refLabel: 'ortanca ' + num(a.ozet.medyan) })}</div>
      <div class="kn-axis"><span>${trend[0] ? trend[0].t : ''}</span>${legend}<span>${trend.length ? trend[trend.length - 1].t : ''}</span></div>
    </section>
    <div class="kn-2">
      <section class="kn-card"><h3>📅 Hangi gün yüklemeli?</h3><p class="kn-note">Çubuk: o gün yüklenen videoların, kendi türünün ortancasına göre izlenmesi. Çizgi = normal.</p>
        <div class="kn-chart">${bars(a.gun, { w: 520, h: 190, gap: 10, labels: g => g.gun.slice(0, 3), v: g => g.adet ? g.rel : 0, color: () => C.uzun, dim: g => a.gun.indexOf(g) !== bestG, tip: g => `<b>${g.gun}</b><br>${g.adet} video · ${g.adet ? (g.rel >= 1 ? '%' + Math.round((g.rel - 1) * 100) + ' daha fazla' : '%' + Math.round((1 - g.rel) * 100) + ' daha az') + ' izlenme' : 'video yok'}`, top: g => g.adet ? g.adet + ' video' : '', ref: 1, refLabel: 'normal' })}</div></section>
      <section class="kn-card"><h3>⏰ Hangi saatte yüklemeli? (Türkiye saati)</h3><p class="kn-note">Sadece yüklenme saati bilinen videolar. Az videolu saatlere güvenme (üzerine gel).</p>
        <div class="kn-chart">${bars(a.saat, { w: 520, h: 190, gap: 3, labels: (x, i) => i % 3 === 0 ? String(i).padStart(2, '0') : '', v: x => x.adet ? x.rel : 0, color: () => C.uzun, dim: x => x.saat !== bestH, tip: x => `<b>${String(x.saat).padStart(2, '0')}:00 - ${String((x.saat + 1) % 24).padStart(2, '0')}:00</b><br>${x.adet} video${x.adet ? ' · normalin ' + x.rel.toFixed(1).replace('.', ',') + ' katı' : ''}`, ref: 1, refLabel: 'normal' })}</div></section>
    </div>
    <section class="kn-card"><h3>🏆 En çok tutanlar</h3><div class="kn-vids">${a.en_iyi.map(card).join('')}</div>
      ${a.yukselen.length ? `<h3 class="kn-h2">🚀 Son 30 günün yükselenleri <small>(günlük izlenmeye göre)</small></h3><div class="kn-vids">${a.yukselen.map(card).join('')}</div>` : ''}</section>
    <div class="kn-2">
      <section class="kn-card"><h3>⏱ En iyi süre</h3>${[['uzun', 'Uzun video', C.uzun], ['shorts', 'Shorts', C.shorts]].map(([t, n, c]) => { const d = a.sure[t]; const mx = Math.max(1, ...d.map(x => x.medyan)); return d.some(x => x.adet) ? `<div class="kn-dur"><span>${n}</span>${d.map(x => `<div class="kn-cmpr" data-tip="${x.adet} video · ortanca ${full(x.medyan)} izlenme"><em>${x.ad}</em><i><b style="width:${x.adet ? Math.max(2, x.medyan / mx * 100) : 0}%;background:${c}"></b></i><strong>${x.adet ? num(x.medyan) : '—'}</strong></div>`).join('')}</div>` : ''; }).join('')}
        <p class="kn-note">Ortanca izlenme. Üzerine gelince kaç videodan hesaplandığını görürsün; az videoya güvenme.</p></section>
      <section class="kn-card"><h3>✍️ Tutan başlıklar</h3>
        <p class="kn-note">En iyi videoların başlıklarında sık geçen kelimeler:</p>
        <div class="kn-words">${a.baslik.kelimeler.length ? a.baslik.kelimeler.map(w => `<span>${esc(w.k)} <b>${w.n}</b></span>`).join('') : '<em>Yeterli veri yok</em>'}</div>
        <p class="kn-note">Başlık uzunluğu (ortanca): en iyi videolarda <b>${a.baslik.top_uzunluk}</b> harf, diğerlerinde <b>${a.baslik.diger_uzunluk}</b> harf.</p></section>
    </div>
    <section class="kn-card"><h3>📋 Tüm videolar</h3>
      <div class="seg kn-tabs">${[['hepsi', 'Hepsi'], ['uzun', 'Uzun'], ['shorts', 'Shorts']].map(([v, t]) => `<button data-tab="${v}" class="${S.tab === v ? 'on' : ''}">${t}</button>`).join('')}</div>
      <div class="kn-tw"><table class="kn-table"><thead><tr><th>Video</th>${th('tarih', 'Tarih')}${th('sure', 'Süre')}${th('izlenme', 'İzlenme')}${th('gunluk', 'Günlük')}${th('begeni', 'Beğeni')}${th('yorum', 'Yorum')}${th('etkilesim', 'Etkileşim')}</tr></thead>
      <tbody>${rows.map(v => `<tr data-url="${esc(v.url)}"><td><i style="background:${v.short ? C.shorts : C.uzun}"></i>${esc(v.baslik)}</td><td>${v.tarih}</td><td>${durS(v.sure)}</td><td>${full(v.izlenme)}</td><td>${v.gunluk ? num(v.gunluk) : '—'}</td><td>${v.begeni != null ? full(v.begeni) : '—'}</td><td>${v.yorum != null ? full(v.yorum) : '—'}</td><td>${pct(v.etkilesim)}</td></tr>`).join('')}</tbody></table></div>
    </section>`;
  };
  const aiHtml = r => `<div class="kn-aires"><h4>✨ Yapay zekâ yorumu</h4>${r.ozet ? `<p>${esc(r.ozet)}</p>` : ''}
    ${(r.oneriler || []).length ? `<ol>${r.oneriler.map(x => `<li>${esc(x)}</li>`).join('')}</ol>` : ''}
    ${(r.basliklar || []).length ? `<h4>💡 Video başlığı fikirleri <small>(tıkla, kopyala)</small></h4><div class="kn-ideas">${r.basliklar.map(x => `<button>${esc(x)}</button>`).join('')}</div>` : ''}
    ${r.dikkat ? `<p class="kn-warn">⚠️ ${esc(r.dikkat)}</p>` : ''}</div>`;

  const bind = () => {
    const inp = $('#knIn', host);
    inp.addEventListener('keydown', e => { e.stopPropagation(); if (e.key === 'Enter') go(); });
    inp.oninput = () => { S.input = inp.value; };
    $$('[data-k="n"] button', host).forEach(b => b.onclick = () => { S.n = +b.dataset.v; $$('[data-k="n"] button', host).forEach(x => x.classList.toggle('on', x === b)); });
    $('#knGo', host).onclick = go;
    $$('[data-r]', host).forEach(b => b.onclick = () => { S.input = b.dataset.r; go(); });
    const body = $('#knBody', host); tipOn(body);
    $$('[data-url]', body).forEach(x => x.onclick = () => KS.openUrl(x.dataset.url));
    $$('[data-s]', body).forEach(x => x.onclick = () => { S.dir = S.sort === x.dataset.s ? -S.dir : -1; S.sort = x.dataset.s; keepScroll(render); });
    $$('[data-tab]', body).forEach(x => x.onclick = () => { S.tab = x.dataset.tab; keepScroll(render); });
    const op = $('#knOpen', body); if (op) op.onclick = () => KS.openUrl(S.a.kanal.url);
    const re = $('#knRe', body); if (re) re.onclick = () => { S.input = S.a.girdi || S.input; go(); };
    const ai = $('#knAi', body); if (ai) ai.onclick = askAi;
    $$('.kn-ideas button', body).forEach(b => b.onclick = async () => { if (await KS.copy(b.textContent)) KS.toast('Başlık kopyalandı', 'ok'); });
  };
  const keepScroll = fn => { const y = ($('#knScroll', host) || {}).scrollTop || 0; fn(); const el = $('#knScroll', host); if (el) el.scrollTop = y; };
  const go = async () => {
    const t = (S.input || '').trim(); if (!t) return KS.toast('Kanal adını ya da linkini yaz', 'err');
    if (U.running(U.findJob(S.job))) return;
    try { const r = await KS.api('/api/kanal/start', { kanal: t, n: S.n }); S.job = r.job; KS.trackJob(r.job); render(); }
    catch (e) { KS.toast(esc(e.message), 'err'); }
  };
  const askAi = async () => {
    S.aiBusy = true; keepScroll(render);
    try { S.ai = await KS.api('/api/kanal/ai', { key: S.key }); } catch (e) { KS.toast(esc(e.message), 'err'); }
    S.aiBusy = false; keepScroll(render);
  };

  KS.hooks.jobTick.push(() => { if (KS.page === 'kanal' && U.running(U.findJob(S.job))) { const c = $('.kn-job .tk-job', host); if (c) c.outerHTML = U.jobCard(U.findJob(S.job), 'Kanal inceleniyor...'); } });
  KS.hooks.jobDone.push(j => {
    if (!S.job || j.id !== S.job) return;
    if (j.status === 'bitti' && j.result) {
      S.a = j.result.analiz; S.key = j.result.key; S.ai = null; S.job = null; S.tab = 'hepsi';
      try { localStorage.setItem('kanal_son_key', S.key); } catch (e) { }
      KS.api('/api/settings', {}).then(r => { KS.state.settings = r; if (KS.page === 'kanal') keepScroll(render); }).catch(() => { });
      if (KS.page !== 'kanal') KS.toast('📊 Kanal analizi hazır', 'ok', [{ label: 'Göster', primary: true, fn: () => KS.go('kanal') }]);
    }
    if (KS.page === 'kanal') render();
  });
  KS.hooks.page.push(async p => {
    const tp = $('#knTip'); if (tp) tp.hidden = true;
    if (p !== 'kanal' || inited) return;
    inited = true; render();
    let key = null; try { key = localStorage.getItem('kanal_son_key'); } catch (e) { }
    if (key) { try { const r = await KS.api('/api/kanal/sonuc?key=' + encodeURIComponent(key)); S.a = r.analiz; S.key = r.key; S.input = S.a.girdi || ''; render(); } catch (e) { } }
  });
  KS.toolDrop.kanal = () => KS.toast('Kanal Analizi için kanal adını yaz', 'err');
})();
