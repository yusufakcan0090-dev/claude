/* Kesit Stüdyosu — Dönüştür: video / ses / fotoğraf biçim çevirici */
(() => {
  const D = KS.donustur = { files: [], job: null };
  const FMTS = {
    video: [['mp4', 'MP4', 'Her yerde açılır'], ['mp4_h265', 'MP4 H.265', 'Aynı kalite, yarı boyut'], ['mov', 'MOV', 'iPhone, Mac, montaj'], ['mkv', 'MKV', 'Kayıpsız taşıyıcı'], ['webm', 'WEBM', 'Web siteleri'], ['avi', 'AVI', 'Eski cihazlar'], ['gif', 'GIF', 'Hareketli resim']],
    audio: [['mp3', 'MP3', 'Sadece ses'], ['m4a', 'M4A', 'Sadece ses (AAC)'], ['wav', 'WAV', 'Kayıpsız ses'], ['flac', 'FLAC', 'Kayıpsız, küçük'], ['ogg', 'OGG', 'Sadece ses (Opus)']],
    image: [['jpg', 'JPG', 'Küçük, her yerde açılır'], ['png', 'PNG', 'Kayıpsız, şeffaflık korunur'], ['webp', 'WEBP', 'Çok küçük, web için'], ['bmp', 'BMP', 'Sıkıştırmasız'], ['tiff', 'TIFF', 'Baskı / arşiv'], ['ico', 'ICO', 'Simge']],
  };
  const ICON = { video: '🎬', audio: '🎵', image: '🖼️' };
  const st = () => KS.state.settings || {};
  D.o = null;
  const opts = () => {
    if (!D.o) { const s = st().donustur_ayar || {}; D.o = { format: s.format || 'mp4', kalite: s.kalite || 'kaynak', cozunurluk: s.cozunurluk || 'kaynak', fps: s.fps || 'kaynak', sessiz: !!s.sessiz, klasor: s.klasor || 'kaynak' }; }
    return D.o;
  };
  const size = b => b > 1e9 ? (b / 1e9).toFixed(2) + ' GB' : b > 1e6 ? (b / 1e6).toFixed(1) + ' MB' : Math.max(1, Math.round(b / 1e3)) + ' KB';
  const fmtT = s => { s = Math.round(s || 0); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`; };
  const kinds = () => new Set(D.files.map(f => f.kind === 'image' ? 'image' : 'media'));
  const allowed = () => {
    const k = kinds();
    if (!k.size) return ['video', 'audio', 'image'];
    if (k.has('image') && k.has('media')) return [];
    return k.has('image') ? ['image'] : (D.files.every(f => f.kind === 'audio') ? ['audio'] : ['video', 'audio']);
  };

  D.add = async paths => {
    const jj = D.job && (KS.state.jobs || []).find(x => x.id === D.job);
    if (!jj || (jj.status !== 'calisiyor' && jj.status !== 'bekliyor')) { D.job = null; D.files.forEach(f => { f.done = null; f.err = null; }); }
    paths = paths.filter(p => !D.files.some(f => f.path === p));
    if (!paths.length) return;
    try {
      const r = await KS.api('/api/donustur/info', { paths });
      r.files.forEach(f => { if (f.error) KS.toast(KS.esc(f.name + ': ' + f.error), 'err'); else D.files.push(f); });
    } catch (e) { KS.toast(KS.esc(e.message), 'err'); }
    const al = allowed(), o = opts();
    if (al.length && !al.some(g => FMTS[g].some(x => x[0] === o.format))) o.format = FMTS[al[0]][0][0];
    D.render();
  };
  D.pick = async () => { try { const r = await KS.api('/api/donustur/pick', {}); if (r.files && r.files.length) { const ok = r.files.filter(f => !f.error); if (ok.length) await D.add(ok.map(f => f.path)); } } catch (e) { KS.toast(KS.esc(e.message), 'err'); } };

  D.render = () => {
    const box = $('#dnFiles'), side = $('#dnSide'); if (!box) return;
    const o = opts(), al = allowed(), j = D.job && (KS.state.jobs || []).find(x => x.id === D.job), run = j && (j.status === 'calisiyor' || j.status === 'bekliyor');
    box.innerHTML = D.files.length ? `<div class="dn-list">${D.files.map((f, i) => `<div class="dn-row ${f.done ? 'ok' : ''}">
        <span class="dn-ic">${ICON[f.kind] || '📄'}</span>
        <div class="dn-meta"><b title="${KS.esc(f.path)}">${KS.esc(f.name)}</b><small>${[f.w ? `${f.w}×${f.h}` : '', f.dur && f.kind !== 'image' ? fmtT(f.dur) : '', (f.v || f.a || '').toUpperCase(), size(f.size)].filter(Boolean).join(' · ')}</small></div>
        ${f.done ? `<button class="btn ghost sm" data-show="${i}">✓ Klasörde göster</button>` : f.err ? `<span class="dn-err" title="${KS.esc(f.err)}">✕ Hata</span>` : ''}
        ${run ? '' : `<button class="icon-btn dn-x" data-rm="${i}" title="Listeden çıkar">✕</button>`}</div>`).join('')}</div>
        <div class="dn-add"><button class="btn ghost" id="dnAdd">+ Dosya ekle</button>${run ? '' : '<button class="btn ghost" id="dnClr">Listeyi temizle</button>'}<span>${D.files.length} dosya</span></div>`
      : `<div class="dn-empty" id="dnDrop"><div class="dn-big">⇄</div><b>Dosyaları buraya sürükle</b><span>Video, ses ya da fotoğraf. Birden fazla dosya da olur.</span><button class="btn primary" id="dnAdd">Dosya seç</button></div>`;
    const grp = g => `<div class="dn-g ${al.includes(g) ? '' : 'off'}"><div class="kq-h">${{ video: 'Video', audio: 'Sadece ses', image: 'Fotoğraf' }[g]}</div><div class="dn-fmts">${FMTS[g].map(([v, n, d]) => `<button data-f="${v}" class="${o.format === v ? 'on' : ''}" ${al.includes(g) ? '' : 'disabled'}><b>${n}</b><small>${d}</small></button>`).join('')}</div></div>`;
    const isImg = (FMTS.image.some(x => x[0] === o.format)), isAud = FMTS.audio.some(x => x[0] === o.format), isGif = o.format === 'gif';
    const seg = (k, list) => `<div class="seg kq-seg" data-k="${k}">${list.map(([v, n]) => `<button data-v="${v}" class="${String(o[k]) === String(v) ? 'on' : ''}">${n}</button>`).join('')}</div>`;
    side.innerHTML = `<div class="dn-scroll">
        <div class="kq-ph"><b>Neye dönüştürülsün?</b></div>
        ${al.length ? '' : '<div class="dn-warn">Listede hem fotoğraf hem video var. Bunlar aynı biçime çevrilemez; birini listeden çıkar.</div>'}
        ${['video', 'audio', 'image'].filter(g => al.includes(g) || !D.files.length).map(grp).join('')}
        <div class="kq-h">Kalite</div>${seg('kalite', isImg ? [['kaynak', 'En yüksek'], ['yuksek', 'Yüksek'], ['normal', 'Normal'], ['kucuk', 'Küçük dosya']] : [['kaynak', 'Aynı kalite'], ['yuksek', 'Yüksek'], ['normal', 'Normal'], ['kucuk', 'Küçük dosya']])}
        <small class="kq-note">${isImg ? 'En yüksek: hiç kalite kaybı olmaz.' : isAud ? 'Aynı kalite / Yüksek: 320 kbps ya da kayıpsız.' : '"Aynı kalite" mümkünse videoyu yeniden kodlamadan çevirir: hiç kalite kaybı olmaz ve saniyeler sürer.'}</small>
        ${isAud ? '' : `<div class="kq-h">${isGif ? 'GIF genişliği' : 'Çözünürlük'}</div>${seg('cozunurluk', isGif ? [['kaynak', '640 px'], ['480', '480 px'], ['720', '720 px'], ['1080', '1080 px']] : [['kaynak', 'Aynı'], ['1080', '1080p'], ['720', '720p'], ['480', '480p']])}`}
        ${!isImg && !isAud ? `<div class="kq-h">Kare hızı (FPS)</div>${seg('fps', isGif ? [['kaynak', '15'], ['10', '10'], ['20', '20'], ['30', '30']] : [['kaynak', 'Aynı'], ['60', '60'], ['30', '30'], ['24', '24']])}` : ''}
        ${!isImg && !isAud && !isGif ? `<label class="ae-chk kq-chk"><input type="checkbox" id="dnMute" ${o.sessiz ? 'checked' : ''}> Sesi kaldır</label>` : ''}
        <div class="kq-h">Nereye kaydedilsin?</div>${seg('klasor', [['kaynak', 'Dosyanın yanına'], ['cikti', 'Çıktı klasörüne']])}
      </div>
      <div class="kq-foot">${j ? `<div class="dn-prog ${j.status === 'hata' ? 'bad' : ''}"><div><b>${run ? KS.esc(j.message || 'Hazırlanıyor...') : j.status === 'bitti' ? '✓ ' + KS.esc(j.message) : j.status === 'hata' ? '✕ ' + KS.esc(j.message) : ''}</b><span>${run ? '%' + Math.round(j.progress * 100) : ''}</span></div>${run ? `<div class="kq-pbar"><i style="width:${Math.round(j.progress * 100)}%"></i></div>` : ''}</div>` : ''}
        ${run ? '<button class="btn ghost" id="dnStop">✕ Durdur</button>' : `<button class="btn primary glow kq-go" id="dnGo" ${D.files.length && al.length ? '' : 'disabled'}>⇄ Dönüştür${D.files.length > 1 ? ` (${D.files.length} dosya)` : ''}</button>`}</div>`;
    $$('#dnAdd', box).forEach(b => b.onclick = D.pick);
    if ($('#dnClr', box)) $('#dnClr', box).onclick = () => { D.files = []; D.job = null; D.render(); };
    $$('[data-rm]', box).forEach(b => b.onclick = () => { D.files.splice(+b.dataset.rm, 1); D.render(); });
    $$('[data-show]', box).forEach(b => b.onclick = () => KS.api('/api/reveal', { path: D.files[+b.dataset.show].done }));
    $$('[data-f]', side).forEach(b => b.onclick = () => { o.format = b.dataset.f; if (o.format === 'gif' || FMTS.image.some(x => x[0] === o.format)) { o.cozunurluk = 'kaynak'; o.fps = 'kaynak'; } D.render(); });
    $$('.kq-seg', side).forEach(g => $$('button', g).forEach(b => b.onclick = () => { o[g.dataset.k] = b.dataset.v; D.render(); }));
    if ($('#dnMute', side)) $('#dnMute', side).onchange = e => { o.sessiz = e.target.checked; };
    if ($('#dnGo', side)) $('#dnGo', side).onclick = D.start;
    if ($('#dnStop', side)) $('#dnStop', side).onclick = () => KS.api(`/api/jobs/${D.job}/cancel`, {});
  };

  D.start = async () => {
    const o = opts();
    D.files.forEach(f => { f.done = null; f.err = null; });
    try {
      const r = await KS.api('/api/donustur', { files: D.files.map(f => f.path), format: o.format, opts: { kalite: o.kalite, cozunurluk: o.cozunurluk, fps: o.fps, sessiz: o.sessiz, klasor: o.klasor } });
      D.job = r.job; KS.trackJob(r.job); D.render();
    } catch (e) { KS.toast(KS.esc(e.message), 'err'); }
  };
  KS.hooks.jobTick.push(() => { if (KS.page === 'donustur' && D.job) D.render(); });
  KS.hooks.jobDone.push(j => {
    if (j.kind !== 'donustur') return;
    const r = j.result || {};
    (r.files || []).forEach(x => { const f = D.files.find(y => y.name === x.src); if (f) f.done = x.path; });
    (r.fails || []).forEach(x => { const f = D.files.find(y => y.name === x.src); if (f) f.err = x.hata; });
    if (j.status === 'bitti') KS.toast(`⇄ ${KS.esc(j.message)}`, 'ok', r.path ? [{ label: 'Klasörde göster', primary: true, fn: () => KS.api('/api/reveal', { path: r.path }) }] : []);
    D.render();
  });
  const go = KS.go;
  KS.go = page => { go(page); if (page === 'donustur') D.render(); };
  D.render();
})();
