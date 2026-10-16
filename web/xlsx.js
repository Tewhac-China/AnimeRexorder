/* 零依赖 xlsx 写入器：手写 ZIP(store) + OOXML，离线 file:// 可用。
   XLSX.download(name, sheets)  sheets=[{name,widths,rows:[{c:[..],s:'h'|'b'}],freeze,filter}] */
(function (global) {
  'use strict';
  const CRC_T = (() => { const t = new Uint32Array(256);
    for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0 }
    return t })();
  const crc32 = u => { let c = 0xFFFFFFFF;
    for (let i = 0; i < u.length; i++) c = CRC_T[(c ^ u[i]) & 255] ^ (c >>> 8);
    return (c ^ 0xFFFFFFFF) >>> 0 };

  function zipStore(files) {
    const enc = new TextEncoder(), body = [], cd = []; let off = 0;
    for (const f of files) {
      const nm = enc.encode(f.name), d = f.b, crc = crc32(d);
      const lh = new Uint8Array(30 + nm.length), v = new DataView(lh.buffer);
      v.setUint32(0, 0x04034b50, 1); v.setUint16(4, 20, 1); v.setUint16(6, 0x0800, 1); v.setUint16(8, 0, 1);
      v.setUint16(10, 0, 1); v.setUint16(12, 0x3039, 1); v.setUint32(14, crc, 1);
      v.setUint32(18, d.length, 1); v.setUint32(22, d.length, 1); v.setUint16(26, nm.length, 1); lh.set(nm, 30);
      body.push(lh, d);
      const ch = new Uint8Array(46 + nm.length), w = new DataView(ch.buffer);
      w.setUint32(0, 0x02014b50, 1); w.setUint16(4, 20, 1); w.setUint16(6, 20, 1); w.setUint16(8, 0x0800, 1);
      w.setUint16(10, 0, 1); w.setUint16(12, 0, 1); w.setUint16(14, 0x3039, 1);
      w.setUint32(16, crc, 1); w.setUint32(20, d.length, 1); w.setUint32(24, d.length, 1);
      w.setUint16(28, nm.length, 1); w.setUint32(42, off, 1); ch.set(nm, 46);
      cd.push(ch); off += lh.length + d.length;
    }
    const cds = cd.reduce((s, a) => s + a.length, 0), eo = new Uint8Array(22), x = new DataView(eo.buffer);
    x.setUint32(0, 0x06054b50, 1); x.setUint16(8, files.length, 1); x.setUint16(10, files.length, 1);
    x.setUint32(12, cds, 1); x.setUint32(16, off, 1);
    const out = new Uint8Array(off + cds + 22); let p = 0;
    for (const a of body) { out.set(a, p); p += a.length }
    for (const a of cd) { out.set(a, p); p += a.length }
    out.set(eo, p); return out;
  }
  const colName = n => { let s = ''; for (n++; n; n = Math.floor((n - 1) / 26)) s = String.fromCharCode(65 + (n - 1) % 26) + s; return s };
  const xs = s => String(s == null ? '' : s)
    .replace(/[\x00-\x08\x0B\x0C\x0E-\x1F]/g, '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

  function cell(ref, v, st) {
    const s = st ? ` s="${st}"` : '';
    if (v === null || v === undefined || v === '') return `<c r="${ref}"${s}/>`;
    if (typeof v === 'number' && isFinite(v)) return `<c r="${ref}"${s}><v>${v}</v></c>`;
    return `<c r="${ref}"${s} t="inlineStr"><is><t xml:space="preserve">${xs(v)}</t></is></c>`;
  }

  function sheetXml(sh) {
    const rows = sh.rows || [], widths = sh.widths || rows.map(_ => 14);
    const fr = sh.freeze ? `<pane ySplit="${sh.freeze}" topLeftCell="A${sh.freeze + 1}" activePane="bottomLeft" state="frozen"/>` : '';
    const last = colName(Math.max(widths.length, ...rows.map(r => r.c.length)) - 1);
    const body = rows.map((r, i) => `<row r="${i + 1}"${r.s ? ' ht="19" customHeight="1"' : ''}>` +
      r.c.map((v, j) => cell(colName(j) + (i + 1), v, r.s === 'h' ? 1 : r.s === 'b' ? 2 : 0)).join('') +
      `</row>`).join('');
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
      `<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">` +
      `<dimension ref="A1:${last}${Math.max(1, rows.length)}"/>` +
      `<sheetViews><sheetView showGridLines="0" workbookViewId="0">${fr}</sheetView></sheetViews>` +
      `<sheetFormatPr defaultRowHeight="15"/>` +
      `<cols>${widths.map((w, i) => `<col min="${i + 1}" max="${i + 1}" width="${w}" customWidth="1"/>`).join('')}</cols>` +
      `<sheetData>${body}</sheetData>` +
      (sh.filter ? `<autoFilter ref="A1:${last}${rows.length}"/>` : '') +
      `<pageMargins left="0.4" right="0.4" top="0.5" bottom="0.5" header="0.2" footer="0.2"/></worksheet>`;
  }

  const STYLES = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
    '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">' +
    '<numFmts count="0"/>' +
    '<fonts count="3"><font><sz val="11"/><color rgb="FF1B2430"/><name val="微软雅黑"/></font>' +
    '<font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="微软雅黑"/></font>' +
    '<font><b/><sz val="11"/><color rgb="FF0A5A84"/><name val="微软雅黑"/></font></fonts>' +
    '<fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill>' +
    '<fill><patternFill patternType="solid"><fgColor rgb="FF2A6B8F"/><bgColor indexed="64"/></patternFill></fill></fills>' +
    '<borders count="2"><border><left/><right/><top/><bottom/><diagonal/></border>' +
    '<border><left style="thin"><color rgb="FFD5DCE5"/></left><right style="thin"><color rgb="FFD5DCE5"/></right>' +
    '<top style="thin"><color rgb="FFD5DCE5"/></top><bottom style="thin"><color rgb="FFD5DCE5"/></bottom><diagonal/></border></borders>' +
    '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>' +
    '<cellXfs count="3">' +
    '<xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1"/>' +
    '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1" applyAlignment="1"><alignment vertical="center"/></xf>' +
    '<xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0" applyFont="1"/></cellXfs>' +
    '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>';

  function makeXlsx(sheets, title) {
    const enc = new TextEncoder(), B = s => enc.encode(s);
    const REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships';
    const PKG = 'http://schemas.openxmlformats.org/package/2006/relationships';
    const CT = 'application/vnd.openxmlformats-officedocument.spreadsheetml';
    const files = [
      { name: '[Content_Types].xml', b: B('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
        `<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>` +
        `<Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="${CT}.sheet.main+xml"/>` +
        `<Override PartName="/xl/styles.xml" ContentType="${CT}.styles+xml"/>` +
        sheets.map((s, i) => `<Override PartName="/xl/worksheets/sheet${i + 1}.xml" ContentType="${CT}.worksheet+xml"/>`).join('') + '</Types>') },
      { name: '_rels/.rels', b: B(`<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="${PKG}">` +
        `<Relationship Id="rId1" Type="${REL}/officeDocument" Target="xl/workbook.xml"/></Relationships>`) },
      { name: 'xl/workbook.xml', b: B('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
        `<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="${REL}"><bookViews><workbookView/></bookViews><sheets>` +
        sheets.map((s, i) => `<sheet name="${xs(s.name)}" sheetId="${i + 1}" r:id="rId${i + 1}"/>`).join('') +
        `</sheets><definedNames/><calcPr calcId="0"/></workbook>`) },
      { name: 'xl/_rels/workbook.xml.rels', b: B(`<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="${PKG}">` +
        sheets.map((s, i) => `<Relationship Id="rId${i + 1}" Type="${REL}/worksheet" Target="worksheets/sheet${i + 1}.xml"/>`).join('') +
        `<Relationship Id="rId${sheets.length + 1}" Type="${REL}/styles" Target="styles.xml"/></Relationships>`) },
      { name: 'xl/styles.xml', b: B(STYLES) },
      ...sheets.map((s, i) => ({ name: `xl/worksheets/sheet${i + 1}.xml`, b: B(sheetXml(s)) })),
    ];
    void title;
    return zipStore(files);
  }

  function download(filename, sheets) {
    const u8 = makeXlsx(sheets);
    const blob = new Blob([u8], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = filename; a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 5000);
    return blob.size;
  }

  global.XLSX = { zipStore, crc32, makeXlsx, download, sheetXml, colName };
})(window);
