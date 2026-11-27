/* Kesit Stüdyosu — Yapay zekâ: asistan, otomatik edit, paylaşım, kapak */
(() => {
  const A = KS.ai = { busy: false, chat: [] };
  const hasKey = () => !!(KS.state.settings && KS.state.settings.gemini_anahtar);
  KS.openUrl = url => KS.api('/api/open_url', { url }).catch(() => window.open(url, '_blank'));
  KS.copy = async text => {
    try { await navigator.clipboard.writeText(text); return true; } catch (e) { }
    const t = document.createElement('textarea'); t.value = text; t.style.position = 'fixed'; t.style.opacity = '0';
    document.body.appendChild(t); t.select(); let ok = false; try { ok = document.execCommand('copy'); } catch (e) { } t.remove(); return ok;
  };

  /* ================================================================ ASİSTAN */
  const fab = $('#aiNav');
  const dr = document.createElement('aside');
  dr.className = 'ai-drawer'; dr.id = 'aiDrawer';
  dr.innerHTML = `<div class="ai-head"><div><b>✨ Asistan</b><small>Yaz, ben yapayım</small></div>
      <button class="btn ghost sm" id="aiNew" title="Yeni sohbet">Yeni</button><button class="icon-btn" id="aiClose">${KS.icon.x}</button></div>
    <div class="ai-msgs" id="aiMsgs"></div>
    <div class="ai-sugg" id="aiSugg"></div>
    <form class="ai-in" id="aiForm"><textarea id="aiText" rows="1" placeholder="Örn: rraenee'nin son yayınından 3 komik Reels yap"></textarea><button class="btn primary" id="aiSend" title="Gönder">➤</button></form>`;
  document.body.appendChild(dr);
  const msgs = $('#aiMsgs', dr), txt = $('#aiText', dr);
  const SUGG = ['Son yayından en komik 3 anı Reels yap', 'Açık projenin altyazısını çıkar', 'Bu video için başlık ve açıklama yaz', 'Açık projeyi 1080p dışa aktar', 'Projelerimi göster'];
  const md = s => KS.esc(s).replace(/\*\*(.+?)\*\*/g, '<b>$1</b>').replace(/\n/g, '<br>');
  A.render = () => {
    if (!hasKey()) {
      msgs.innerHTML = `<div class="ai-setup"><b>Asistanı açmak için ücretsiz bir Gemini anahtarı gerekiyor</b>
        <ol><li><a href="#" id="aiGetKey">Google AI Studio</a>'yu aç, Google hesabınla gir</li><li><b>Create API key</b>'e bas, anahtarı kopyala</li><li>Aşağıya yapıştır, <b>Kaydet</b>'e bas</li></ol>
        <div class="ai-keyrow"><input class="inp" id="aiKey" type="password" placeholder="AIza..."><button class="btn primary sm" id="aiKeySave">Kaydet</button></div>
        <small>Ücretsiz sürümde gönderdiğin yazılar Google'ın modellerini geliştirmek için kullanılabilir. Anahtar sadece bu bilgisayarda saklanır.</small></div>`;
      $('#aiGetKey', msgs).onclick = e => { e.preventDefault(); KS.openUrl('https://aistudio.google.com/apikey'); };
      $('#aiKeySave', msgs).onclick = () => A.saveKey($('#aiKey', msgs).value, $('#aiKeySave', msgs));
      $('#aiSugg', dr).innerHTML = ''; return;
    }
    msgs.innerHTML = A.chat.length ? A.chat.map(m => m.rol === 'is' ? A.jobCard(m.id) : `<div class="ai-m ${m.rol === 'sen' ? 'me' : 'bot'}${m.err ? ' err' : ''}">${md(m.metin)}</div>`).join('')
      : `<div class="ai-hello"><b>Merhaba! 👋</b><span>Klip bulma, otomatik edit, altyazı, dışa aktarma, kalite artırma, başlık-açıklama yazma ve paylaşıma hazırlama işlerini benden isteyebilirsin.</span></div>`;
    if (A.busy) msgs.insertAdjacentHTML('beforeend', '<div class="ai-m bot typing"><i></i><i></i><i></i></div>');
    A.paintJobs();
    $('#aiSugg', dr).innerHTML = A.chat.length ? '' : SUGG.map(s => `<button class="chip">${s}</button>`).join('');
    $$('#aiSugg .chip', dr).forEach(b => b.onclick = () => { txt.value = b.textContent; A.send(); });
    msgs.scrollTop = msgs.scrollHeight;
  };
  A.saveKey = async (k, btn) => {
    k = (k || '').trim(); if (!k) return;
    if (btn) { btn.disabled = true; btn.textContent = 'Deneniyor...'; }
    try {
      const r = await KS.api('/api/ai/test', { key: k });
      KS.state.settings.gemini_anahtar = k;
      KS.toast('✨ Yapay zekâ bağlandı' + (r.model ? ` (${KS.esc(r.model)})` : ''), 'ok');
      A.render(); if (KS.page === 'settings') KS.renderSettings();
    } catch (e) { KS.toast(KS.esc(e.message), 'err'); }
    finally { if (btn) { btn.disabled = false; btn.textContent = 'Kaydet'; } }
  };
  A.open = async () => {
    dr.classList.add('show'); fab.classList.add('on');
    try { const r = await KS.api('/api/ai/chat'); A.chat = r.chat || []; } catch (e) { }
    A.render(); setTimeout(() => txt.focus(), 200);
  };
  A.close = () => { dr.classList.remove('show'); fab.classList.remove('on'); };
  fab.onclick = () => dr.classList.contains('show') ? A.close() : A.open(); $('#aiClose', dr).onclick = A.close;
  $('#aiNew', dr).onclick = async () => { await KS.api('/api/ai/reset', {}); A.chat = []; A.render(); };
  txt.addEventListener('keydown', e => { e.stopPropagation(); if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); A.send(); } });
  txt.addEventListener('input', () => { txt.style.height = 'auto'; txt.style.height = Math.min(120, txt.scrollHeight) + 'px'; });
  $('#aiForm', dr).onsubmit = e => { e.preventDefault(); A.send(); };
  A.ctx = () => ({ page: KS.page, project: KS.editor && KS.editor.project ? KS.editor.project.id : null, kalite: KS.kalite && KS.kalite.src ? KS.kalite.src.path : null });
  A.send = async () => {
    const m = txt.value.trim(); if (!m || A.busy) return;
    txt.value = ''; txt.style.height = 'auto';
    A.chat.push({ rol: 'sen', metin: m }); A.busy = true; A.render();
    const bot = { rol: 'ai', metin: '' }; let bubble = null, status = '';
    const paint = () => {
      if (!bubble) { const t = msgs.querySelector('.typing'); if (t) t.remove(); bubble = document.createElement('div'); bubble.className = 'ai-m bot'; msgs.appendChild(bubble); }
      bubble.innerHTML = md(bot.metin) + (status ? `<div class="ai-st">${KS.esc(status)}…</div>` : '');
      msgs.scrollTop = msgs.scrollHeight;
    };
    const acts = [];
    try {
      const res = await fetch('/api/ai/stream', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: m, ctx: A.ctx() }) });
      if (!res.ok || !res.body) throw new Error('Sunucu hatası ' + res.status);
      const rd = res.body.getReader(), dec = new TextDecoder(); let buf = '';
      for (;;) {
        const { value, done } = await rd.read(); if (done) break;
        buf += dec.decode(value, { stream: true });
        let i;
        while ((i = buf.indexOf('\n\n')) >= 0) {
          const line = buf.slice(0, i).trim(); buf = buf.slice(i + 2);
          if (!line.startsWith('data:')) continue;
          const ev = JSON.parse(line.slice(5));
          if (ev.type === 'text') { bot.metin += ev.text; status = ''; paint(); }
          else if (ev.type === 'tool') { status = ev.label; paint(); }
          else if (ev.type === 'actions') { for (const a of ev.actions || []) { acts.push(a); if (a.type === 'job') { if (bot.metin.trim()) { A.chat.push({ ...bot }); bot.metin = ''; } bubble = null; } await A.act(a); } }
          else if (ev.type === 'error') { bot.metin = ev.message; bot.err = true; }
          else if (ev.type === 'done') { if (ev.reply && !bot.metin.trim()) bot.metin = ev.reply; for (const a of ev.actions || []) await A.act(a); }
        }
      }
      KS.kickJobs && KS.kickJobs();
    } catch (e) { bot.metin = e.message; bot.err = true; }
    finally { if (bot.metin.trim() || bot.err) A.chat.push(bot); A.busy = false; A.render(); }
  };
  /* sohbet içi iş kartı: yüzde, kalan süre, bitince düğme */
  const dur = s => { s = Math.max(0, Math.round(s || 0)); return s < 60 ? `${s} sn` : s < 3600 ? `${Math.floor(s / 60)} dk ${s % 60} sn` : `${Math.floor(s / 3600)} sa ${Math.floor(s % 3600 / 60)} dk`; };
  A.jobCard = id => {
    const j = (KS.state.jobs || []).find(x => x.id === id);
    if (!j) return `<div class="ai-job" data-job="${id}"><b>İş</b><span>bekleniyor…</span></div>`;
    const p = Math.round((j.progress || 0) * 100), ex = j.extra || {}, ok = j.status === 'bitti', bad = j.status === 'hata';
    const eta = ex.eta != null ? ` · kalan ~${dur(ex.eta)}` : (j.status === 'calisiyor' && p > 3 && ex.elapsed ? ` · kalan ~${dur(ex.elapsed * (100 - p) / p)}` : '');
    const r = j.result || {};
    const btn = ok && r.projects ? `<button class="btn primary sm" data-open="${r.projects[0]}">Editörde aç</button>` : ok && r.project && !r.reload ? `<button class="btn primary sm" data-open="${r.project}">Aç</button>` : ok && r.path ? `<button class="btn ghost sm" data-reveal="${KS.esc(r.path)}">Klasörde göster</button>` : '';
    return `<div class="ai-job ${ok ? 'ok' : bad ? 'bad' : ''}" data-job="${id}"><div class="ai-job-t"><b>${ok ? '✓ ' : bad ? '✕ ' : ''}${KS.esc(j.title)}</b><span>${ok ? 'Bitti' : bad ? 'Hata' : '%' + p + eta}</span></div>
      ${ok || bad ? '' : `<div class="kq-pbar"><i style="width:${p}%"></i></div>`}<small>${KS.esc(bad ? j.message : ok ? j.message : (ex.asama || j.message || ''))}</small>${btn ? `<div class="ai-job-b">${btn}</div>` : ''}</div>`;
  };
  A.paintJobs = () => {
    $$('.ai-job[data-job]', msgs).forEach(el => { const h = A.jobCard(el.dataset.job); if (el.outerHTML !== h) { const t = document.createElement('div'); t.innerHTML = h; el.replaceWith(t.firstElementChild); } });
    $$('[data-open]', msgs).forEach(b => b.onclick = () => KS.openProject(b.dataset.open));
    $$('[data-reveal]', msgs).forEach(b => b.onclick = () => KS.api('/api/reveal', { path: b.dataset.reveal }));
  };
  KS.hooks.jobTick.push(() => { if (dr.classList.contains('show')) A.paintJobs(); });
  A.act = async a => {
    try {
      if (a.type === 'job') { A.chat.push({ rol: 'is', id: a.id }); KS.trackJob(a.id); A.render(); return; }
      if (a.type === 'reload') { if (KS.editor && KS.editor.project && KS.editor.project.id === a.id) await KS.editor.reload(a.id); else await KS.openProject(a.id); return; }
      if (a.type === 'open_project') await KS.openProject(a.id);
      else if (a.type === 'go') KS.go(a.page);
      else if (a.type === 'search') { KS.go('finder'); $('#channelInput').value = a.q; KS.finder.search(); }
      else if (a.type === 'share') KS.share(a.id, a.platform);
      else if (a.type === 'thumb') KS.thumb(a.id);
      else if (a.type === 'meta' && KS.editor && KS.editor.project && KS.editor.project.id === a.id) { const p = await KS.api('/api/project/' + a.id); KS.editor.project.paylasim = p.paylasim; }
    } catch (e) { }
  };

  /* ================================================================ OTOMATİK EDİT */
  KS.autoEdit = src => {
    const s = KS.state.settings;
    const o = { count: s.oto_adet || 3, format: (s.son_bicim || 'dikey').startsWith('kaynak') ? 'kaynak' : (s.son_bicim || 'dikey'), subs: s.oto_altyazi_ekle !== false };
    const m = KS.modal(`<h2>🤖 Otomatik Edit</h2><p class="msub">${KS.esc(src.title || '')}</p>
      <p class="ae-note">${hasKey() ? 'Yayını dinler, yapay zekâ en iyi anları seçer, her biri için <b>altyazılı, hazır bir kısa video</b> projesi yapar; başlık ve açıklamayı da yazar.'
        : 'En heyecanlı anları sesten bulur ve her biri için hazır bir proje yapar. <b>Yapay zekâ anahtarı eklersen</b> konuşmaları da dinleyip çok daha iyi seçer, başlık da yazar (Ayarlar → Yapay Zekâ).'}</p>
      <div class="opt-group"><label>Kaç video</label><div class="opts" id="aeN">${[1, 3, 5, 10].map(n => `<button class="opt" data-v="${n}"><b>${n}</b></button>`).join('')}</div></div>
      <div class="opt-group"><label>Biçim</label><div class="opts" id="aeF">
        <button class="opt" data-v="dikey"><b>Reels / Shorts</b><small>9:16 dikey</small></button>
        <button class="opt" data-v="kaynak"><b>Orijinal</b><small>videonun kendi boyutu</small></button>
        <button class="opt" data-v="yatay"><b>Yatay</b><small>16:9</small></button></div></div>
      <label class="ae-chk" style="margin:4px 0 10px"><input type="checkbox" id="aeS" ${o.subs ? 'checked' : ''}> Altyazı ekle</label>
      <div class="mfoot"><button class="btn ghost" data-close>Vazgeç</button><button class="btn primary glow" id="aeGo">🤖 Başlat</button></div>`);
    const paint = () => { $$('#aeN .opt', m.el).forEach(b => b.classList.toggle('active', +b.dataset.v === +o.count)); $$('#aeF .opt', m.el).forEach(b => b.classList.toggle('active', b.dataset.v === o.format)); };
    $$('#aeN .opt', m.el).forEach(b => b.onclick = () => { o.count = +b.dataset.v; paint(); });
    $$('#aeF .opt', m.el).forEach(b => b.onclick = () => { o.format = b.dataset.v; paint(); });
    paint();
    $('#aeGo', m.el).onclick = async () => {
      m.close();
      try {
        const r = await KS.api('/api/autoedit', { ...src, count: o.count, format: o.format, subs: $('#aeS', m.el).checked });
        Object.assign(KS.state.settings, { oto_adet: o.count });
        KS.trackJob(r.job); KS.openJobs();
        KS.toast('🤖 Otomatik edit başladı. Bitince videolar editörde açılacak.');
      } catch (e) { KS.toast(KS.esc(e.message), 'err'); }
    };
  };

  /* ================================================================ PAYLAŞ (hazırla ve aç) */
  const PL = { youtube: ['YouTube Shorts', '▶️', 180], tiktok: ['TikTok', '🎵', 600], instagram: ['Instagram Reels', '📸', 90] };
  KS.share = async (pid, platform) => {
    pid = pid || (KS.editor && KS.editor.project && KS.editor.project.id);
    if (!pid) return KS.toast('Önce bir proje aç', 'err');
    let p;
    try { p = await KS.api('/api/project/' + pid); } catch (e) { return KS.toast(KS.esc(e.message), 'err'); }
    let tab = platform || 'youtube', meta = p.paylasim || {}, saveT = null;
    const ex = (p.exports || []).filter(e => e.path).slice(-1)[0];
    const fmtInfo = KS.fmtInfo ? KS.fmtInfo(p.format) : [1080, 1920];
    const dur = (p.clips || []).reduce((a, c) => a + ((c.out - c.in) / (c.speed || 1)), 0);
    const m = KS.modal(`<h2>📤 Paylaş</h2><p class="msub">${KS.esc(p.title)}</p><div id="shBody"></div>`, { wide: true });
    const body = $('#shBody', m.el);
    const val = (k, f) => ((meta[k] || {})[f]) || '';
    const save = () => { clearTimeout(saveT); saveT = setTimeout(() => KS.api(`/api/project/${pid}/paylasim`, meta).catch(() => { }), 500); };
    const warn = () => {
      const w = [], [W, H] = fmtInfo, lim = PL[tab][2];
      if (W > H) w.push('Video yatay; Reels/Shorts/TikTok için dikey (9:16) daha iyi görünür.');
      if (dur > lim) w.push(`${PL[tab][0]} için ${KS.fmt(lim)}'dan uzun (video ${KS.fmt(dur)}).`);
      return w.map(x => `<div class="sh-warn">⚠ ${KS.esc(x)}</div>`).join('');
    };
    const draw = () => {
      const fields = tab === 'youtube'
        ? `<label class="sh-l">Başlık <button class="lnk" data-cp="baslik">Kopyala</button></label><input class="inp" id="shTitle" maxlength="100" value="${KS.esc(val('youtube', 'baslik'))}" placeholder="Başlık">
           <label class="sh-l">Açıklama <button class="lnk" data-cp="aciklama">Kopyala</button></label><textarea class="inp" id="shDesc" rows="4">${KS.esc(val('youtube', 'aciklama'))}</textarea>
           <label class="sh-l">Etiketler <button class="lnk" data-cp="etiket">Kopyala</button></label><input class="inp" id="shTags" value="${KS.esc((val('youtube', 'etiketler') || []).join(', '))}" placeholder="virgülle ayır">`
        : `<label class="sh-l">Açıklama <button class="lnk" data-cp="aciklama">Kopyala</button></label><textarea class="inp" id="shDesc" rows="5">${KS.esc(val(tab, 'aciklama'))}</textarea>`;
      body.innerHTML = `<div class="seg sh-tabs">${Object.entries(PL).map(([k, v]) => `<button data-t="${k}" class="${k === tab ? 'on' : ''}">${v[1]} ${v[0]}</button>`).join('')}</div>
        <div class="sh-file">${ex ? `🎬 <b>${KS.esc(ex.name || ex.path.split(/[\\/]/).pop())}</b><span>dışa aktarılan son video</span><button class="btn ghost sm" id="shReExp">Yeniden aktar</button>`
          : `🎬 <span>Bu proje henüz dışa aktarılmadı.</span><button class="btn primary sm" id="shExp">Dışa aktar (1080p)</button>`}</div>
        ${warn()}
        <div class="sh-fields">${fields}</div>
        <div class="sh-ai">${hasKey() ? '<button class="btn ghost sm" id="shGen">✨ Yapay zekâ ile yaz</button><input class="inp" id="shNote" placeholder="İstersen not: daha komik olsun, soru sorsun...">' : '<small>Başlık ve açıklamayı yapay zekâya yazdırmak için Ayarlar → Yapay Zekâ\'dan anahtar ekle.</small>'}</div>
        <ol class="sh-steps"><li>Aşağıdaki tuş açıklamayı kopyalar, ${PL[tab][0]} yükleme sayfasını açar ve videoyu klasörde seçili gösterir.</li>
          <li>Videoyu sayfaya sürükle, açıklama kısmına <b>Ctrl+V</b> ile yapıştır.</li><li>Son olarak orada <b>Paylaş</b>'a bas.</li></ol>
        <div class="mfoot"><button class="btn ghost" data-close>Kapat</button><button class="btn ghost" id="shThumb">🖼 Kapak yap</button><button class="btn primary glow" id="shGo" ${ex ? '' : 'disabled'}>📋 Kopyala ve ${PL[tab][0]}'u aç</button></div>`;
      $$('[data-close]', body).forEach(b => b.onclick = m.close);
      $$('.sh-tabs button', body).forEach(b => b.onclick = () => { tab = b.dataset.t; draw(); });
      const bind = (id, k, f, map = x => x) => { const el = $(id, body); if (el) { el.addEventListener('keydown', e => e.stopPropagation()); el.oninput = () => { meta[k] = meta[k] || {}; meta[k][f] = map(el.value); save(); }; } };
      bind('#shTitle', 'youtube', 'baslik'); bind('#shDesc', tab, 'aciklama'); bind('#shTags', 'youtube', 'etiketler', v => v.split(',').map(x => x.trim()).filter(Boolean));
      if ($('#shNote', body)) $('#shNote', body).addEventListener('keydown', e => e.stopPropagation());
      $$('[data-cp]', body).forEach(b => b.onclick = async () => {
        const k = b.dataset.cp, t = k === 'baslik' ? val('youtube', 'baslik') : k === 'etiket' ? (val('youtube', 'etiketler') || []).join(', ') : val(tab, 'aciklama');
        if (await KS.copy(t)) KS.toast('Kopyalandı', 'ok', [], 1500);
      });
      const exp = async () => {
        try { const r = await KS.api(`/api/project/${pid}/export`, { cozunurluk: 1080, fps: 'kaynak' }); KS.trackJob(r.job); KS.openJobs(); m.close(); KS._shareAfter = { job: r.job, pid, tab }; KS.toast('Dışa aktarılıyor. Bitince paylaşım penceresi tekrar açılacak.'); }
        catch (e) { KS.toast(KS.esc(e.message), 'err'); }
      };
      if ($('#shExp', body)) $('#shExp', body).onclick = exp;
      if ($('#shReExp', body)) $('#shReExp', body).onclick = exp;
      if ($('#shGen', body)) $('#shGen', body).onclick = async () => {
        const b = $('#shGen', body); b.disabled = true; b.textContent = '✨ Yazıyor...';
        try { meta = await KS.api('/api/ai/meta/' + pid, { not: $('#shNote', body).value }); draw(); }
        catch (e) { KS.toast(KS.esc(e.message), 'err'); b.disabled = false; b.textContent = '✨ Yapay zekâ ile yaz'; }
      };
      $('#shThumb', body).onclick = () => { m.close(); setTimeout(() => KS.thumb(pid), 260); };
      $('#shGo', body).onclick = async () => {
        if (!ex) return;
        const desc = val(tab, 'aciklama');
        if (desc) await KS.copy(desc);
        try { await KS.api('/api/share/open', { platform: tab, path: ex.path }); } catch (e) { KS.toast(KS.esc(e.message), 'err'); }
        KS.toast(tab === 'youtube' && val('youtube', 'baslik') ? 'Açıklama kopyalandı. Başlığı da pencereden kopyalayabilirsin.' : (desc ? 'Açıklama kopyalandı, yükleme sayfası açılıyor.' : 'Yükleme sayfası açılıyor.'), 'ok');
      };
    };
    draw();
  };

  /* ================================================================ KAPAK (thumbnail) */
  KS.thumb = async pid => {
    pid = pid || (KS.editor && KS.editor.project && KS.editor.project.id);
    if (!pid) return KS.toast('Önce bir proje aç', 'err');
    const m = KS.modal(`<h2>🖼 Kapak Yap</h2><p class="msub">Bir kare seç, yazını yaz, kaydet.</p><div id="thBody"><div class="th-load">Kareler hazırlanıyor...</div></div>`, { wide: true });
    let r;
    try { r = await KS.api(`/api/project/${pid}/frames`); } catch (e) { m.close(); return KS.toast(KS.esc(e.message), 'err'); }
    const o = { frame: 0, text: r.title || '', ratio: '16:9', pos: 'alt', color: '#ffd400', size: 100, dark: true };
    const body = $('#thBody', m.el);
    body.innerHTML = `<div class="th-wrap"><div class="th-prev"><canvas id="thC"></canvas></div>
      <div class="th-side">
        <div class="th-frames">${r.frames.map((f, i) => `<img src="${f.url}" data-i="${i}" class="${i === 0 ? 'on' : ''}">`).join('')}</div>
        <label class="sh-l">Yazı</label><textarea class="inp" id="thText" rows="2">${KS.esc(o.text)}</textarea>
        <div class="seg" id="thRatio"><button data-v="16:9" class="on">YouTube 16:9</button><button data-v="9:16">Shorts/Reels 9:16</button></div>
        <div class="seg" id="thPos"><button data-v="ust">Üst</button><button data-v="orta">Orta</button><button data-v="alt" class="on">Alt</button></div>
        <div class="th-colors">${['#ffd400', '#ffffff', '#ff3b3b', '#3bff6e', '#38bdf8'].map(c => `<button data-c="${c}" style="background:${c}" class="${c === o.color ? 'on' : ''}"></button>`).join('')}</div>
        <label class="sh-l">Yazı boyutu</label><input type="range" id="thSize" min="50" max="160" value="100">
        <label class="ae-chk"><input type="checkbox" id="thDark" checked> Alt/üst kısmı karart (yazı okunsun)</label>
      </div></div>
      <div class="mfoot"><button class="btn ghost" data-close>Kapat</button><button class="btn primary glow" id="thSave">💾 Kapağı kaydet</button></div>`;
    $$('[data-close]', body).forEach(b => b.onclick = m.close);
    const cv = $('#thC', body), ctx = cv.getContext('2d'), imgs = r.frames.map(f => { const im = new Image(); im.src = f.url; im.onload = () => draw(); return im; });
    const wrap = (text, maxW) => {
      const out = [];
      text.split('\n').forEach(par => { let line = ''; par.split(' ').forEach(w => { const t = line ? line + ' ' + w : w; if (ctx.measureText(t).width > maxW && line) { out.push(line); line = w; } else line = t; }); if (line) out.push(line); });
      return out;
    };
    const draw = () => {
      const [W, H] = o.ratio === '16:9' ? [1280, 720] : [1080, 1920];
      cv.width = W; cv.height = H;
      ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
      const im = imgs[o.frame];
      if (im && im.naturalWidth) { const s = Math.max(W / im.naturalWidth, H / im.naturalHeight), w = im.naturalWidth * s, h = im.naturalHeight * s; ctx.drawImage(im, (W - w) / 2, (H - h) / 2, w, h); }
      const fs = Math.round((o.ratio === '16:9' ? 92 : 110) * o.size / 100);
      ctx.font = `${fs}px Anton, PoppinsBlk, Impact, sans-serif`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      const lines = wrap(o.text.toLocaleUpperCase('tr-TR'), W * .9).slice(0, 4), lh = fs * 1.08, th = lines.length * lh;
      let y0 = o.pos === 'ust' ? H * .06 + lh / 2 : o.pos === 'orta' ? H / 2 - th / 2 + lh / 2 : H - H * .06 - th + lh / 2;
      if (o.dark && lines.length) {
        const g = o.pos === 'ust' ? ctx.createLinearGradient(0, 0, 0, th + H * .2) : o.pos === 'alt' ? ctx.createLinearGradient(0, H, 0, H - th - H * .2) : null;
        if (g) { g.addColorStop(0, 'rgba(0,0,0,.75)'); g.addColorStop(1, 'rgba(0,0,0,0)'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); }
      }
      lines.forEach((l, i) => {
        const y = y0 + i * lh;
        ctx.lineJoin = 'round'; ctx.lineWidth = fs * .16; ctx.strokeStyle = '#000'; ctx.strokeText(l, W / 2, y);
        ctx.fillStyle = o.color; ctx.fillText(l, W / 2, y);
      });
    };
    document.fonts && document.fonts.load('80px Anton').then(draw).catch(() => { });
    $$('.th-frames img', body).forEach(im => im.onclick = () => { o.frame = +im.dataset.i; $$('.th-frames img', body).forEach(x => x.classList.toggle('on', x === im)); draw(); });
    const t = $('#thText', body); t.addEventListener('keydown', e => e.stopPropagation()); t.oninput = () => { o.text = t.value; draw(); };
    const seg = (id, k) => $$(`#${id} button`, body).forEach(b => b.onclick = () => { o[k] = b.dataset.v; $$(`#${id} button`, body).forEach(x => x.classList.toggle('on', x === b)); draw(); });
    seg('thRatio', 'ratio'); seg('thPos', 'pos');
    $$('.th-colors button', body).forEach(b => b.onclick = () => { o.color = b.dataset.c; $$('.th-colors button', body).forEach(x => x.classList.toggle('on', x === b)); draw(); });
    const sz = $('#thSize', body); KS.paintRange && KS.paintRange(sz); sz.oninput = () => { o.size = +sz.value; KS.paintRange && KS.paintRange(sz); draw(); };
    $('#thDark', body).onchange = e => { o.dark = e.target.checked; draw(); };
    $('#thSave', body).onclick = async () => {
      try {
        const s = await KS.api('/api/snapshot', { data: cv.toDataURL('image/png'), name: (r.title || 'kapak').slice(0, 50) + '_kapak' });
        KS.toast('🖼 Kapak kaydedildi: ' + KS.esc(s.name), 'ok', [{ label: 'Klasörde göster', primary: true, fn: () => KS.api('/api/reveal', { path: s.path }) }]);
      } catch (e) { KS.toast(KS.esc(e.message), 'err'); }
    };
    draw();
  };

  /* ================================================================ iş bitince */
  KS.hooks.jobDone.push(j => {
    const r = j.result || {};
    if (j.status !== 'bitti') return;
    if (j.kind === 'otoedit' && r.projects && r.projects.length) {
      KS.refresh && KS.refresh();
      KS.toast(`🤖 <b>${r.projects.length} video hazır!</b> Hepsi Projeler'de. İlki editörde açılıyor.`, 'ok', [{ label: 'Paylaş', primary: true, fn: () => KS.share(r.projects[0]) }], 9000);
      KS.openProject(r.projects[0]);
    }
    if (j.kind === 'yuz' && r.project) {
      if (KS.editor && KS.editor.project && KS.editor.project.id === r.project) KS.editor.reload(r.project);
      KS.toast(r.found ? '🎯 Yüz bulundu, YÜZ kutusu yerleştirildi' : 'Videoda yüz bulunamadı', r.found ? 'ok' : '');
    }
    if (j.kind === 'aktar' && KS._shareAfter && KS._shareAfter.job === j.id) {
      const s = KS._shareAfter; KS._shareAfter = null; setTimeout(() => KS.share(s.pid, s.tab), 400);
    }
    if (j.kind === 'gorsel' && r.path) {
      if (KS.page === 'kalite' && KS.kalite) { KS.kalite.load(r.path); KS.toast('✓ ' + KS.esc(r.name), 'ok', [{ label: 'Klasörde göster', fn: () => KS.api('/api/reveal', { path: r.path }) }]); }
      else KS.toast('✓ Görsel hazır: ' + KS.esc(r.name), 'ok', [{ label: 'Klasörde göster', primary: true, fn: () => KS.api('/api/reveal', { path: r.path }) }]);
    }
  });

  /* editör araç çubuğu: Paylaş */
  const eb = $('#exportBtn');
  if (eb && !$('#shareBtn')) {
    const b = document.createElement('button'); b.id = 'shareBtn'; b.title = 'YouTube / TikTok / Instagram için hazırla'; b.textContent = '📤 Paylaş';
    b.onclick = () => KS.share(); eb.after(b);
  }
})();
