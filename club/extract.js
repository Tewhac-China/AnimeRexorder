/* 在 thwiki 页面上下文里执行的抽取器。由 sink /file 下发，注入后调用 __RUN(cfg)
   cfg = {slug:'01-莲台野夜行', mode:'album'|'story'}  */
window.__RUN = async function (cfg) {
  const SINK = 'http://127.0.0.1:8788/save?path=';
  const post = async (path, body) => {
    const r = await fetch(SINK + encodeURIComponent(path), { method: 'POST', body });
    return r.text();
  };
  const postBin = async (path, blob) => {
    const r = await fetch(SINK + encodeURIComponent(path), { method: 'POST', body: blob });
    return r.text();
  };
  const C = document.querySelector('#mw-content-text');
  const clean = t => (t || '').replace(/[\u200b\u200e\u200f]/g, '')
    .replace(/\[\d+\]/g, '').replace(/\s*\n\s*/g, '\n').trim();
  const toFull = s => {
    if (!/\/thumb\//.test(s)) return s;
    const u = new URL(s), seg = u.pathname.split('/').filter(Boolean);
    seg.shift(); seg.pop();                   // 去 'thumb' 段与 NNNpx- 文件名
    return u.origin + '/' + seg.join('/');    // 原始大图
  };
  const stripEdit = el => { el.querySelectorAll('.mw-editsection,sup.reference,.noprint').forEach(x => x.remove()); };

  /* ---- 节点 → Markdown（按节点自身分派，未知容器兜底，绝不静默丢内容） ---- */
  const textBR = el => {
    let t = '';
    const walk = n => {
      for (const c of n.childNodes) {
        if (c.nodeType === 3) t += c.nodeValue;
        else if (c.tagName === 'BR') t += '\n';
        else if (c.tagName === 'P' || c.tagName === 'DIV') walk(c), t += '\n';
        else if (!/^(SCRIPT|STYLE)$/.test(c.tagName || '')) walk(c);
      }
    };
    walk(el);
    return t.replace(/[ \t]+/g, ' ').replace(/\n{3,}/g, '\n\n').trim();
  };
  function blockMd(ch) {
    const tag = ch.tagName, cls = ch.className || '';
    if (/STYLE|SCRIPT|LINK/.test(tag) || ch.id === 'toc') return '';
    if (/mw-heading/.test(cls) || /^H[2-4]$/.test(tag)) {
      const h = ch.matches('h2,h3,h4') ? ch : ch.querySelector('h2,h3,h4');
      return h ? '\n### ' + clean(h.textContent) + '\n\n' : '';
    }
    if (tag === 'TABLE') {
      if (ch.classList.contains('navbox') || /导航|目录/.test(ch.innerText.slice(0, 12))) return '';
      const rows = [...ch.querySelectorAll('tr')].map(tr =>
        [...tr.children].map(td => clean(textBR(td)).replace(/\|/g, '\\|').replace(/\n+/g, ' ')));
      if (!rows.length) return '';
      return '| ' + rows[0].join(' | ') + ' |\n|' + rows[0].map(() => '---|').join('') + '\n'
        + rows.slice(1).map(r => '| ' + r.join(' | ') + ' |').join('\n') + '\n\n';
    }
    if (tag === 'UL' || tag === 'OL')
      return [...ch.children].filter(li => li.tagName === 'LI')
        .map(li => '- ' + clean(textBR(li)).replace(/\n+/g, ' ')).join('\n') + '\n\n';
    if (tag === 'DL')
      return [...ch.children].map(d => (d.tagName === 'DT' ? '**' + clean(textBR(d)) + '**' : '> ' + clean(textBR(d))))
        .filter(x => x.replace(/[*\s>|]/g, '')).join('\n') + '\n\n';
    if (tag === 'BLOCKQUOTE') return '> ' + clean(textBR(ch)) + '\n\n';
    if (tag === 'P') { const t = clean(textBR(ch)); return t ? t + '\n\n' : ''; }
    if (tag === 'DIV') {
      const im = ch.querySelector('img');
      if (/thumb|image/.test(cls) && im) {
        const cap = clean((ch.querySelector('.thumbcaption,figcaption') || {}).textContent || '');
        return '![图](' + toSize(im.getAttribute('src') || '', cfg.px || 800) + ')' + (cap ? ' *（' + cap + '）*' : '') + '\n\n';
      }
      const kids = [...ch.children].filter(c => !/STYLE|SCRIPT/.test(c.tagName));
      const t = kids.length ? kids.map(blockMd).join('') : '';
      return t.trim() ? t : (clean(textBR(ch)) ? clean(textBR(ch)) + '\n\n' : '');
    }
    const t = clean(textBR(ch));
    return t ? t + '\n\n' : '';
  }
  const nodeMd = el => [...el.children].map(blockMd).join('');

  const res = { slug: cfg.slug, url: location.href, page: document.querySelector('#firstHeading').textContent.trim() };

  const toSize = (s, px) => s.replace(/(\/thumb\/.+\/)\d+px-/, (m, a) => a + px + 'px-');
  function collectImgs() {
    const seen = new Set(), list = [];
    for (const im of C.querySelectorAll('img')) {
      let s = im.getAttribute('src') || im.getAttribute('data-src') || '';
      if (!/^https?:/.test(s) || /\/template\/|icon/.test(s)) continue;
      s = s.split('?')[0];
      const u = toSize(s, cfg.px || 800);
      if (seen.has(u)) continue;
      seen.add(u); list.push({ sized: u, raw: s, orig: toFull(s) });
    }
    return list;
  }
  async function grab(i, it, pre) {
    let blob = null, used = null;
    for (const cand of [it.sized, it.orig, it.raw]) {          // 降级：请求尺寸 → 原图 → 页面尺寸
      try { const r = await fetch(cand); if (r.ok) { blob = await r.blob(); used = cand; break } } catch (e) { }
    }
    if (!blob) throw new Error('all sizes failed');
    const nm = decodeURIComponent(used.split('/').pop()).replace(/^(\d+px-)?/, '').replace(/[\/"\\]/g, '_').slice(-48);
    const pfx = (pre || '') + (i === 0 && !pre ? 'cover' : String(i).padStart(2, '0'));
    await postBin('albums/' + cfg.slug + '/images/' + pfx + '-' + nm, blob);
    return [nm, blob.size, /\/thumb\//.test(used) ? used.match(/\/(\d+)px-/)[1] + 'px' : 'original'];
  }

  const out = C.querySelector('.mw-parser-output') || C;
  const headOf = n => {
    if (/^H[2-4]$/.test(n.tagName)) return n;
    if (n.classList && n.classList.contains('mw-heading')) return n.querySelector('h2,h3,h4');
    return null;
  };
  function sectionsOf(stop) {
    const parts = {}; let cur = '概述'; parts[cur] = '';
    for (const n of out.children) {
      const h = headOf(n);
      if (h) { const t = clean(h.textContent); if ((stop || []).concat(['导航', '目录']).includes(t)) { cur = null; continue } cur = t; parts[cur] = parts[cur] || ''; continue }
      if (!cur) continue;
      if (n.id === 'toc' || n.classList.contains('catlinks') || /STYLE|SCRIPT/.test(n.tagName)) continue;
      if (n.classList.contains('navbox') || n.classList.contains('page-content-header')) continue;
      parts[cur] += blockMd(n);
    }
    for (const k of Object.keys(parts)) if (!parts[k].trim()) delete parts[k];
    return parts;
  }

  if (cfg.mode === 'story') {
    const parts = sectionsOf();
    const SP = cfg.sp > 1 ? String(cfg.sp) : '';
    await post('albums/' + cfg.slug + '/story' + SP + '.html', document.documentElement.outerHTML);
    const md = '# ' + res.page + '（' + cfg.slug + ' · 附带故事）\n\n> 来源: ' + location.href + '  ·  THBWiki\n\n'
      + Object.entries(parts).map(([k, v]) => '## ' + k + '\n\n' + v).join('\n');
    await post('albums/' + cfg.slug + '/story' + SP + '.md', md);
    res.storyChars = md.length; res.sections = Object.keys(parts);
    res.sectionChars = Object.fromEntries(Object.entries(parts).map(([k, v]) => [k, v.length]));
    const list = collectImgs();
    res.storyImgs = list.length;
    const got = [];
    for (let i = 0; cfg.to && i < Math.min(list.length, cfg.to); i++) {
      try { got.push(await grab(i, list[i], 'story' + SP)) } catch (e) { got.push([list[i].sized.slice(-24), 'FAIL']) }
    }
    res.storyImages = got;
    if (cfg.next) setTimeout(() => { location.href = cfg.next }, 60);
    return res;
  }

  if (cfg.mode === 'imgs') {
    const list = collectImgs();
    const a = cfg.from | 0, b = Math.min(list.length, (cfg.to | 0) || (a + 5));
    const got = [];
    for (let i = a; i < b; i++) {
      try { got.push(await grab(i, list[i], cfg.pre || '')) } catch (e) { got.push([list[i].sized.slice(-24), 'FAIL ' + (e.message || '').slice(0, 30)]) }
    }
    return { slug: cfg.slug, total: list.length, range: [a, b], saved: got, urls: list.slice(a, b).map(u => u.orig.slice(-44)) };
  }

  /* ---- 专辑页 ---- */
  await post('albums/' + cfg.slug + '/page.html', document.documentElement.outerHTML);

  // 基本信息 infobox
  const info = [];
  const ib = C.querySelector('table.wikitable');
  if (ib) for (const tr of ib.querySelectorAll('tr')) {
    const td = [...tr.children].map(x => clean(x.textContent));
    if (td.length >= 2 && td[0]) info.push([td[0], td.slice(1).join(' ')]);
    else if (td[0]) info.push(['# ' + td[0], '']);
  }
  res.fields = info.map(r => r[0]);

  // 曲目表
  const tracks = [];
  const mt = C.querySelector('table.musicTable');
  if (mt) {
    stripEdit(mt);
    let cur = null;
    for (const tr of mt.querySelectorAll('tr')) {
      const td = [...tr.children].map(x => clean(x.textContent));
      if (/^\d{1,2}$/.test(td[0]) && td.length >= 3) { cur = { no: td[0], cn: td[1], dur: td[2], orig: '', src: '' }; tracks.push(cur); }
      else if (td[1] === '原曲' && cur) cur.orig = td[2] || '';
      else if (td[1] === '来源' && cur) cur.src = td[2] || '';
      else if (td[1] && cur && td.length === 2 && !cur.jp) cur.jp = td[1];
    }
    await post('albums/' + cfg.slug + '/tracks.raw.html', mt.outerHTML);
  }
  res.tracks = tracks.length;

  const parts = sectionsOf();
  res.sections = Object.keys(parts);
  res.sectionChars = Object.fromEntries(Object.entries(parts).map(([k, v]) => [k, v.length]));

  // 链接到故事子页
  const storyLinks = [...new Set([...C.querySelectorAll('a')].map(a => a.getAttribute('href') || '')
    .filter(h => /\/(附带故事|后记|故事|Booklet|booklet)$/.test(decodeURIComponent(h))))];
  res.storyLinks = storyLinks; res.storyLink = storyLinks[0] || null;
  const LF = String.fromCharCode(10);
  await post('albums/' + cfg.slug + '/links.txt',
    [res.page + ' | ' + location.href].concat(storyLinks.map(h => 'https://thwiki.cc' + h)).join(LF) + LF);

  // 图片（缩略图 → 原图；兼容懒加载 data-src）
  let saved = [];
  const list = collectImgs();
  res.imgCount = list.length;
  if (!cfg.skipImgs) {
    for (let i = 0; i < Math.min(list.length, (cfg.max || 4)); i++) {
      try { saved.push(await grab(i, list[i])) } catch (e) { saved.push([list[i].sized.slice(-24), 'FAIL ' + e.message.slice(0, 28)]) }
    }
    res.images = saved;
  }
  res.imgFirst = list.slice(0, 2).map(u => u.orig.slice(-46));

  const md = '# ' + res.page + '\n\n> 来源: ' + location.href + '  ·  THBWiki\n\n'
    + '## 基本信息\n\n| 项 | 值 |\n|---|---|\n' + info.map(r => '| ' + r[0] + ' | ' + r[1] + ' |').join('\n') + '\n\n'
    + (tracks.length ? '## 曲目\n\n| # | 曲名 | 原名 | 时长 | 原曲 | 来源 |\n|---|---|---|---|---|---|\n'
      + tracks.map(t => '| ' + t.no + ' | ' + t.cn + ' | ' + (t.jp || '') + ' | ' + t.dur + ' | ' + t.orig + ' | ' + t.src + ' |').join('\n') + '\n\n' : '')
    + Object.entries(parts).filter(([k]) => k !== '曲目').map(([k, v]) => '## ' + k + '\n\n' + v).join('\n')
    + '\n## 本地文件\n\n'
    + saved.map((s, i) => '- `images/' + (i === 0 ? 'cover-' : String(i).padStart(2, '0') + '-') + s[0] + '` — '
      + (typeof s[1] === 'number' ? (s[1] / 1024).toFixed(0) + ' KB' : s[1])).join('\n') + '\n'
    + (res.storyLink ? '\n\n附带故事全文见子页：[' + decodeURIComponent(res.storyLink) + '](https://thwiki.cc' + res.storyLink + ')\n' : '');
  await post('albums/' + cfg.slug + '/album.md', md);
  res.mdChars = md.length;
  if (cfg.autoNext && res.storyLinks && res.storyLinks.length)
    setTimeout(() => { location.href = 'https://thwiki.cc' + res.storyLinks[0] }, 120);
  else if (cfg.next) setTimeout(() => { location.href = cfg.next }, 60);
  return res;
};
