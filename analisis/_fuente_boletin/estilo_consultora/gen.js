// Boletín GS1 Venezuela Insights · versión "estilo consultora" (una idea por lámina, títulos que dicen la conclusión).
// Genera un HTML autocontenido (tipografías y logo en base64).  Uso: node gen.js [salida.html]
const fs = require('fs'), path = require('path');
const R = path.join(__dirname, '..');             // analisis/_fuente_boletin
const D = path.join(__dirname, 'datos');          // datos ya calculados (sin nombres de empresa)
const J = (f) => JSON.parse(fs.readFileSync(path.join(D, f), 'utf8'));
const FU = J('full.json'), F2 = J('full2.json'), RC = J('recap.json'), FID = J('fid.json'), G14 = J('g14_1825.json');
const SERIE = fs.readFileSync(path.join(D, 'captacion_afiliados_por_ano.csv'), 'utf8').replace(/^﻿/, '').trim().split('\n').slice(1).map((l) => l.split(',')).map((r) => [+r[0], +r[1], +r[2], +r[3]]);
const NAVY = '#002C6C', OR = '#F26334', GR = '#1E8E3E', MID = '#5A78AD', LT = '#C9D4EA', INK = '#1A2742', MUTE = '#6B7690', RULE = '#D9DEE8', BG = '#F4F6FA';
const fN = (n) => Math.round(n).toLocaleString('de-DE');
const pc = (v, d = 1) => (Math.round(v * 10 ** d) / 10 ** d).toString().replace('.', ',') + '%';
const dec = (v) => String(v).replace('.', ',');
const b64 = (f, mime) => `data:${mime};base64,` + fs.readFileSync(path.join(R, f)).toString('base64');
const LOGO = b64('logo/logo.png', 'image/png');
const fonts = [['Barlow', 400, 'Barlow-400-latin'], ['Barlow', 500, 'Barlow-500-latin'], ['Barlow', 600, 'Barlow-600-latin'], ['Barlow', 700, 'Barlow-700-latin'], ['Barlow Condensed', 600, 'BarlowCondensed-600-latin'], ['Barlow Condensed', 700, 'BarlowCondensed-700-latin']]
  .map(([n, w, f]) => `@font-face{font-family:'${n}';font-weight:${w};src:url(${b64('fonts/' + f + '.woff2', 'font/woff2')}) format('woff2')}`).join('');
const SRC = 'Fuente: GS1 Venezuela, registros anuales de codificación 1993–2025 clasificados con GPC. Un código es un GTIN único por año. Análisis GS1 Venezuela Insights.';

// ---------- gráficos ----------
const T = (x, y, s, o = {}) => `<text x="${x}" y="${y}" font-size="${o.size || 10}" fill="${o.fill || INK}" font-weight="${o.w || 400}" text-anchor="${o.anchor || 'start'}" font-family="Barlow,sans-serif">${s}</text>`;
function lineChart(opt) {
  const W = 700, H = opt.h || 300, L = 46, Rr = 14, Tp = 30, B = 26, iw = W - L - Rr, ih = H - Tp - B;
  const ys = opt.data.map((d) => d[0]), vs = opt.data.map((d) => d[1]), max = opt.max || 100000;
  const x = (y) => L + (y - ys[0]) / (ys[ys.length - 1] - ys[0]) * iw, yy = (v) => Tp + ih - v / max * ih;
  let s = `<svg viewBox="0 0 ${W} ${H}" width="100%" style="display:block">`;
  (opt.bands || []).forEach(([a, b, c, lab]) => { s += `<rect x="${x(a) - 4}" y="${Tp - 22}" width="${x(b) - x(a) + 8}" height="${ih + 22}" fill="${c}" opacity=".5"/>` + T((x(a) + x(b)) / 2, Tp - 10, lab, { anchor: 'middle', size: 11, fill: MUTE, w: 600 }); });
  for (let g = 0; g <= max; g += opt.step || 25000) { s += `<line x1="${L}" x2="${W - Rr}" y1="${yy(g)}" y2="${yy(g)}" stroke="${RULE}" stroke-width="${g === 0 ? 1.4 : .6}"/>` + T(L - 6, yy(g) + 3, fN(g), { anchor: 'end', size: 9, fill: MUTE }); }
  s += `<path d="M${x(ys[0])},${yy(0)} ` + opt.data.map(([y, v]) => `L${x(y)},${yy(v)}`).join(' ') + ` L${x(ys[ys.length - 1])},${yy(0)} Z" fill="${NAVY}" opacity=".08"/>`;
  s += `<polyline fill="none" stroke="${NAVY}" stroke-width="2.4" stroke-linejoin="round" points="${opt.data.map(([y, v]) => x(y) + ',' + yy(v)).join(' ')}"/>`;
  for (let y = ys[0]; y <= ys[ys.length - 1]; y += 4) s += T(x(y), H - 8, y, { anchor: 'middle', size: 9, fill: MUTE });
  (opt.notes || []).forEach(({ y, v, label, dy, dx, color, anchor }) => { const c = color || NAVY; s += `<circle cx="${x(y)}" cy="${yy(v)}" r="4" fill="${c}" stroke="#fff" stroke-width="1.5"/>` + T(x(y) + (dx || 0), yy(v) + dy, label, { anchor: anchor || 'middle', size: 11.5, w: 700, fill: c }); });
  return s + '</svg>';
}
function hbars(rows, o = {}) {
  const lw = o.lw || 150, W = 100, max = o.max || Math.max(...rows.map((r) => r.v));
  return `<div class="hb">` + rows.map((r) => `<div class="hbr" style="grid-template-columns:${lw}px 1fr ${o.vw || 56}px"><div class="hl${r.bold ? ' b' : ''}">${r.l}</div><div class="ht"><i style="width:${Math.max(1.5, r.v / max * 100)}%;background:${r.c || NAVY}"></i></div><div class="hv" style="color:${r.c && r.c !== NAVY ? r.c : INK}">${r.d}</div></div>`).join('') + `</div>`;
}
function dumbbell(rows, o = {}) {  // a = antes (gris) → b = después (naranja)
  const W = 330, lw = 132, iw = W - lw - 14, max = o.max || Math.max(...rows.flatMap((r) => [r.a, r.b])) * 1.1, rh = 28, H = rows.length * rh + 30;
  const x = (v) => lw + v / max * iw;
  let s = `<svg viewBox="0 0 ${W} ${H}" width="100%" style="display:block">`;
  s += `<circle cx="${lw + 4}" cy="8" r="4" fill="${LT}"/>` + T(lw + 12, 11, o.la || '2010–2019', { size: 9, fill: MUTE }) + `<circle cx="${lw + 78}" cy="8" r="4" fill="${OR}"/>` + T(lw + 86, 11, o.lb || '2025', { size: 9, fill: MUTE });
  rows.forEach((r, i) => { const y = 30 + i * rh + 8; s += `<line x1="${lw}" x2="${W - 10}" y1="${y}" y2="${y}" stroke="${RULE}" stroke-width=".6"/>` + T(lw - 8, y + 3.5, r.l, { anchor: 'end', size: 11 }) + `<line x1="${x(r.a)}" x2="${x(r.b)}" y1="${y}" y2="${y}" stroke="${r.b >= r.a ? OR : MID}" stroke-width="2.4" opacity=".55"/><circle cx="${x(r.a)}" cy="${y}" r="4.2" fill="${LT}" stroke="${MID}" stroke-width=".8"/><circle cx="${x(r.b)}" cy="${y}" r="4.6" fill="${r.b >= r.a ? OR : MID}"/>` + T(x(Math.max(r.a, r.b)) + 8, y + 3.5, dec(r.b) + '%', { size: 9.5, w: 700, fill: r.b >= r.a ? OR : MID }); });
  return s + '</svg>';
}
function columns(rows, o = {}) {
  const W = 360, H = o.h || 190, L = 8, B = 22, Tp = 22, n = rows.length, bw = (W - L * 2) / n, max = o.max || Math.max(...rows.map((r) => r.v)) * 1.12;
  let s = `<svg viewBox="0 0 ${W} ${H}" width="100%" style="display:block"><line x1="${L}" x2="${W - L}" y1="${H - B}" y2="${H - B}" stroke="${INK}" stroke-width="1"/>`;
  rows.forEach((r, i) => { const h = r.v / max * (H - B - Tp), x = L + i * bw + bw * .16; s += `<rect x="${x}" y="${H - B - h}" width="${bw * .68}" height="${h}" fill="${r.c || NAVY}"/>` + T(x + bw * .34, H - B - h - 5, r.d, { anchor: 'middle', size: 10, w: 700, fill: r.c || NAVY }) + T(x + bw * .34, H - 7, r.l, { anchor: 'middle', size: 9.5, fill: MUTE }); });
  return s + '</svg>';
}
// ---------- estructura de página ----------
let PN = 0;
const ex = (n, title, sub, body, cls = '') => `<div class="ex ${cls}"><div class="exl">Gráfico ${n}</div><div class="ext">${title}</div>${sub ? `<div class="exs">${sub}</div>` : ''}${body}</div>`;
const rail = (title, items) => `<aside class="rail"><div class="rt">${title}</div><div class="ris">${items.map((i) => `<div class="ri">${i}</div>`).join('')}</div></aside>`;
const railSide = (title, items) => `<aside class="rail side"><div class="rt">${title}</div>${items.map((i) => `<div class="ri">${i}</div>`).join('')}</aside>`;
const page = (kick, title, deck, body, o = {}) => { PN++; return `<section class="page pg"><header class="hd"><span><b>GS1</b> Venezuela Insights</span><span>${kick}</span></header><h1>${title}</h1>${deck ? `<p class="deck">${deck}</p>` : ''}<div class="bd">${body}</div><footer class="ft"><div class="src">${o.src || SRC}</div><div class="fr"><img src="${LOGO}" alt="GS1 Venezuela"><span>${PN} / 14</span></div></footer></section>`; };
const big = (n, t, c) => `<div class="big"><b style="color:${c || NAVY}">${n}</b><span>${t}</span></div>`;

// ---------- 1 portada ----------
const bars = Array.from({ length: 46 }, (_, i) => { const w = [2, 4, 3, 5, 2, 6, 3, 2, 4, 3][i % 10]; return `<i style="width:${w}px"></i>`; }).join('');
PN++;
const cover = `<section class="page cover"><div class="cv-top"><div class="cv-logo"><img src="${LOGO}" alt="GS1 Venezuela"></div><div class="cv-kick">BOLETÍN DE INSIGHTS · 1993–2025</div></div>
<div class="cv-main"><h1>El mercado<br>en códigos</h1><p>Más de 30 años de productos, empresas y cadena de suministro en Venezuela, leídos a través de lo que se codifica.</p><div class="cv-bars">${bars}</div></div>
<div class="cv-stats"><div><b>+1,6 M</b><span>códigos registrados</span></div><div><b>+3.500</b><span>empresas registradas</span></div><div><b>+30</b><span>años de historia</span></div><div><b>68.339</b><span>códigos en 2025</span></div></div>
<div class="cv-q">«Lo que no se codifica, no se mide; lo que no se mide no se controla.»<small>Adaptación de Lord Kelvin</small></div>
<div class="cv-f">Fuente: archivos anuales de codificación de GS1 Venezuela 1993–2025 y catálogo oficial GPC. Por confidencialidad no se mencionan empresas ni marcas.</div></section>`;

// ---------- 2 carta ----------
PN++;
const letter = `<section class="page"><header class="hd"><span><b>GS1</b> Venezuela Insights</span><span>CARTA DEL EDITOR</span></header><h1>Cada código de barras es una decisión</h1>
<p class="deck">Detrás de los más de 1,6 millones de códigos que GS1 Venezuela ha registrado entre 1993 y 2025 hay una empresa que decidió poner un producto en el mercado, clasificarlo y hacerlo viajar: del fabricante al pallet, del almacén a la góndola.</p>
<div class="bd" style="grid-template-columns:1fr 210px"><div class="lt">
<div class="li"><b>1</b><div><h4>El volumen se recupera</h4><p>En 2025 se registraron 68.339 códigos, la cifra más alta desde 2015. Venían de un piso de unos 41.000 al año entre 2020 y 2022.</p></div></div>
<div class="li"><b>2</b><div><h4>Pocas empresas sostienen el año</h4><p>Tres empresas generaron el 30,1% de los códigos de 2025 y 46 empresas con 200 códigos o más, el 63,9%.</p></div></div>
<div class="li"><b>3</b><div><h4>Una de cada tres vuelve a codificar</h4><p>De las empresas que codifican por primera vez en un año, una de cada tres vuelve a codificar al año siguiente.</p></div></div>
<div class="li"><b>4</b><div><h4>El surtido tiene dos formas</h4><p>Alimentos y Bebidas es el sector más variado (822 tipos de producto); Calzado, el más profundo (14 tipos, unas 2.300 versiones cada uno).</p></div></div>
<div class="li"><b>5</b><div><h4>El bulto también tiene código</h4><p>Entre 2018 y 2025, casi 3 de cada 10 códigos identifican un bulto o empaque.</p></div></div>
<p class="sg">Este boletín no promete adivinar el futuro: muestra con datos qué está pasando hoy y dónde hay oportunidad con base sólida.<br><b>Equipo editorial · GS1 Venezuela Insights</b></p></div>
${railSide('En este número', ['<div class="ix"><span>La historia en una gráfica</span><b>3</b></div><div class="ix"><span>Quién sostiene el registro</span><b>4</b></div><div class="ix"><span>Continuidad de las empresas</span><b>5</b></div><div class="ix"><span>Cuatro capítulos</span><b>6</b></div><div class="ix"><span>Novedad y variedad</span><b>7</b></div><div class="ix"><span>Productos y dependencia</span><b>8</b></div><div class="ix"><span>El viaje del producto</span><b>9</b></div><div class="ix"><span>Bultos, packs y tamaños</span><b>10</b></div><div class="ix"><span>Qué se consume</span><b>11</b></div><div class="ix"><span>Oportunidades</span><b>12–13</b></div><div class="ix"><span>Cinco ideas</span><b>14</b></div>'])}</div>
<footer class="ft"><div class="src">${SRC}</div><div class="fr"><img src="${LOGO}" alt="GS1 Venezuela"><span>2 / 14</span></div></footer></section>`;

// ---------- 3 historia ----------
const p3 = page('HISTORIA', 'El registro tocó fondo en 2021 y desde entonces se recupera: 2025 cerró con 68.339 códigos',
  'Los códigos únicos por año pasaron de unos 17.000 en los años noventa a 63.000 entre 2010 y 2019. Tras el piso de 2020–2022, el registro sube cada año. Aun así, 2025 es el quinto año más alto de la serie.',
  `<div class="main">${ex(1, 'Cuatro capítulos y un rebote: 2011 marcó el máximo y 2021 el mínimo reciente', 'Códigos únicos por año, 1993–2025', lineChart({ data: SERIE.map((r) => [r[0], r[1]]), bands: [[1993, 1999, '#EEF2F9', 'El arranque'], [2000, 2009, '#fff', 'La consolidación'], [2010, 2019, '#EEF2F9', 'La expansión'], [2020, 2025, '#fff', 'El piso y el rebote']], h: 440,
    notes: [{ y: 1993, v: 8720, label: '8.720', dy: -9, dx: 6, anchor: 'start' }, { y: 1999, v: 36467, label: '36.467', dy: -9 }, { y: 2003, v: 22647, label: '22.647', dy: 17 }, { y: 2009, v: 73129, label: '73.129', dy: -9, dx: -8 }, { y: 2011, v: 99774, label: '99.774', dy: -9, color: OR }, { y: 2015, v: 72348, label: '72.348', dy: -9 }, { y: 2017, v: 41771, label: '41.771', dy: 17 }, { y: 2021, v: 40940, label: '40.940', dy: 17, color: OR }, { y: 2025, v: 68339, label: '68.339', dy: -10, dx: -4, color: GR }] })
    + `<div class="leg"><span><i style="background:${OR}"></i>Máximo y mínimo recientes</span><span><i style="background:${GR}"></i>2025</span></div>`)}
  ${rail('Ideas clave', [big('+64%', 'creció el registro de 2025 frente a 2022'), big('41.000', 'códigos al año en el piso de 2020–2022'), big('5.º', 'año más alto de la serie, tras 2011, 2012, 2009 y 2015'), '<p class="n">Los picos de 2011 y 2015 se explican por cargas de pocas empresas.</p>'])}</div>`);

// ---------- 4 concentración ----------
const p4 = page('QUIÉN SOSTIENE EL REGISTRO', 'Tres empresas aportaron el 30,1% de los códigos de 2025, y 46 empresas, el 63,9%',
  'El registro funciona como dos mundos: muchas empresas con pocos códigos y unas pocas con catálogos enormes. La mediana de una empresa es 9 códigos en 2025; el promedio, 54,9.',
  `<div class="main"><div>${ex(2, 'Las empresas con 200 códigos o más pasaron de 23 a 46 y de explicar el 40,6% al 63,9% del año', 'Parte de los códigos del año generada por empresas con 200 códigos o más', `<div class="stk"><div class="sk"><span>2021</span><div><i style="width:40.6%;background:${MID}"></i><em>40,6% · 23 empresas</em></div></div><div class="sk"><span>2025</span><div><i style="width:30.1%;background:${OR}"></i><i style="width:33.8%;background:${NAVY}"></i><em style="left:64.5%;color:${NAVY}">63,9% · 46 empresas</em></div></div></div><div class="leg"><span><i style="background:${OR}"></i>Tres empresas: 30,1%</span><span><i style="background:${NAVY}"></i>Otras 43 empresas con 200 o más: 33,8%</span><span><i style="background:${MID}"></i>2021</span></div>`)}
  ${ex(3, 'El 54% de las empresas registró 10 productos o menos y, juntas, aportaron el 4,3% de los códigos', 'Códigos promedio por empresa en el acumulado 1993–2025, según sector', hbars([{ l: 'Prendas de vestir', v: 234, d: '234', c: OR }, { l: 'Calzado', v: 136, d: '136', c: OR }, { l: 'Construcción', v: 70, d: '70' }, { l: 'Alimentos y Bebidas', v: 41, d: '41' }], { lw: 140 }))}</div>
  ${rail('Ideas clave', [big('9', 'códigos registró en 2025 la empresa típica (mediana del año)'), big('129', 'empresas (1,5% de las que han codificado) generan la mitad de todos los códigos desde 1993'), big('38,8%', 'del año 2011 vino de un solo afiliado (38.748 códigos)', OR), '<p class="n">Una sola carga de catálogo puede mover el total de un mes.</p>'])}</div>`);

// ---------- 5 continuidad ----------
const ch = FID.ch;
const p5 = page('CONTINUIDAD', 'Una de cada tres empresas que codifica por primera vez vuelve a codificar al año siguiente',
  'Que una empresa no codifique en un año no significa que se haya ido: puede retomar más adelante. En 2025, el 35,4% de los códigos vino de empresas que codificaban por primera vez en el registro.',
  `<div class="main"><div>${ex(4, 'La continuidad fue mayor en los años noventa (55%) y se mantiene cerca de 30% desde 2010', 'Empresas que codifican por primera vez en el período: porcentaje que vuelve a codificar al año siguiente', hbars(ch.map((c) => ({ l: c[0] + ' · ' + fN(c[1]) + ' empresas', v: c[2], d: pc(c[2]), c: c[0] === '2020–2024' ? OR : NAVY })), { lw: 200, max: 60 }))}
  ${ex(5, 'Una de cada cinco empresas que entró entre 2020 y 2024 sigue codificando en 2025', 'Empresas del período que codifican en 2025', hbars(ch.map((c) => ({ l: c[0], v: c[3], d: pc(c[3]), c: c[0] === '2020–2024' ? OR : MID })), { lw: 200, max: 60 }))}</div>
  ${rail('Ideas clave', [big('34%', 'de las empresas que entran en un año vuelve a codificar al siguiente (promedio 1993–2024)'), big('35,4%', 'de los códigos de 2025 vino de empresas en su primer año', OR), big('17,7%', 'aportan las 261 empresas con más de diez años en el registro'), '<p class="n">Solo 586 empresas han codificado en diez años distintos o más.</p>'])}</div>`);

// ---------- 6 recap ----------
const CHc = [LT, MID, OR, NAVY];
const recBars = `<svg viewBox="0 0 700 260" width="100%" style="display:block">` + SERIE.map(([y, v], i) => { const c = y <= 1999 ? CHc[0] : y <= 2009 ? CHc[1] : y <= 2019 ? CHc[2] : CHc[3]; const h = v / 100000 * 220, x = 14 + i * 20.3; return `<rect x="${x}" y="${236 - h}" width="15" height="${h}" fill="${c}"/>` + (y % 4 === 1 ? T(x + 7.5, 253, String(y).slice(2), { anchor: 'middle', size: 8.5, fill: MUTE }) : ''); }).join('') + `</svg>`;
const p6 = page('CUATRO CAPÍTULOS', 'En 33 años, cada capítulo trajo más empresas codificando y una clasificación cada vez más fina',
  'Una empresa «codifica» en un año cuando registra al menos un producto. Desde 1993 el registro pasó por el arranque, la consolidación, la expansión y el piso con rebote.',
  `<div class="main1">${ex(6, 'Del arranque a hoy, el promedio de empresas que codifican por año pasó de 246 a 1.291', 'Códigos únicos por año, coloreados por capítulo', recBars + `<div class="leg"><span><i style="background:${CHc[0]}"></i>1993–1999</span><span><i style="background:${CHc[1]}"></i>2000–2009</span><span><i style="background:${CHc[2]}"></i>2010–2019</span><span><i style="background:${CHc[3]}"></i>2020–2025</span></div>`)}
  <table class="tbl"><tr><th></th>${RC.map((r, i) => `<th style="border-top:3px solid ${CHc[i]}">${r.n}</th>`).join('')}</tr>
  <tr><td>Códigos por año (promedio)</td>${RC.map((r) => `<td><b>${fN(r.avg)}</b></td>`).join('')}</tr>
  <tr><td>Empresas que codifican por año (promedio)</td>${RC.map((r) => `<td><b>${fN(r.emp)}</b></td>`).join('')}</tr>
  <tr><td>Empresas que codifican por primera vez, por año</td>${RC.map((r) => `<td><b>${fN(r.nuevas)}</b></td>`).join('')}</tr>
  <tr><td>Año con más códigos</td>${RC.map((r) => `<td>${r.peak[0]} · ${fN(r.peak[1])}</td>`).join('')}</tr>
  <tr><td>Sector con más códigos</td>${RC.map((r) => `<td>${r.top[0][0]}<br><b>${pc(r.top[0][1])}</b></td>`).join('')}</tr>
  <tr><td>Códigos que llegan al nivel más fino (Brick)</td>${RC.map((r) => `<td><b>${pc(r.brick)}</b></td>`).join('')}</tr>
  <tr><td>Aporte de las 10 empresas con más códigos</td>${RC.map((r) => `<td>${pc(r.top10share)}</td>`).join('')}</tr></table></div>`);

// ---------- 7 novedad y variedad ----------
const nov = FU.novedad.filter((r) => r[1] >= 300 && r[0] !== 'Plantas de horticultura').sort((a, b) => b[2] - a[2]);
const novRows = nov.slice(0, 7).concat(nov.filter((r) => ['Alimentos y Bebidas', 'Calzado', 'Hogar y mobiliario'].includes(r[0].replace('Fontanería', 'Plomería'))).filter((r) => !nov.slice(0, 7).includes(r)))
  .map((r) => ({ l: r[0].replace('Fontanería', 'Plomería').replace('Alimentación/cuidados de', 'Cuidado de mascotas').replace('Materias primas (no alim', 'Materias primas'), v: r[2], d: '×' + dec(r[2]), c: r[2] >= 1.5 ? GR : r[2] < 1 ? OR : NAVY }));
const sc = (() => { const rows = FU.profundidad.filter((r) => r[1] >= 12), W = 340, H = 330, L = 36, B = 28, Tp = 10, Rr = 12, lx = (v) => L + (Math.log10(v) - 1) / (Math.log10(1000) - 1) * (W - L - Rr), ly = (v) => Tp + (1 - v / 2500) * (H - Tp - B);
  const names = { 'Calzado': 'Calzado', 'Prendas de vestir': 'Prendas de vestir', 'Alimentos y Bebidas': 'Alimentos y Bebidas', 'Construcción': 'Construcción', 'Automotriz': 'Automotriz', 'Limpieza del hogar': 'Limpieza del hogar' };
  let s = `<svg viewBox="0 0 ${W} ${H}" width="100%" style="display:block">`;
  [0, 500, 1000, 1500, 2000, 2500].forEach((g) => { s += `<line x1="${L}" x2="${W - Rr}" y1="${ly(g)}" y2="${ly(g)}" stroke="${RULE}" stroke-width=".6"/>` + T(L - 5, ly(g) + 3, fN(g), { anchor: 'end', size: 8.5, fill: MUTE }); });
  [10, 30, 100, 300, 1000].forEach((g) => { s += T(lx(g), H - 14, fN(g), { anchor: 'middle', size: 8.5, fill: MUTE }); });
  s += T((L + W - Rr) / 2, H - 2, 'Tipos de producto distintos (escala logarítmica) →', { anchor: 'middle', size: 9, fill: MUTE }) + `<text transform="translate(9,${H / 2}) rotate(-90)" font-size="9" fill="${MUTE}" text-anchor="middle" font-family="Barlow,sans-serif">Versiones por tipo ↑</text>`;
  rows.forEach((r) => { const n = r[0].replace('Fontanería', 'Plomería'), hi = names[n]; s += `<circle cx="${lx(r[1])}" cy="${ly(r[2])}" r="${hi ? 5.5 : 3.6}" fill="${n === 'Alimentos y Bebidas' ? NAVY : hi ? OR : LT}" stroke="#fff" stroke-width="1"/>` + (hi ? T(lx(r[1]) + (n === 'Alimentos y Bebidas' ? -8 : 8), ly(r[2]) + (n === 'Alimentos y Bebidas' ? -10 : n === 'Construcción' ? 17 : n === 'Automotriz' ? 15 : 3.5), n, { size: 9.5, w: 700, anchor: n === 'Alimentos y Bebidas' ? 'end' : 'start', fill: n === 'Alimentos y Bebidas' ? NAVY : OR }) : ''); });
  return s + '</svg>'; })();
const p7 = page('RETAIL · NOVEDAD Y VARIEDAD', 'Plomería y climatización lanzó tres veces más productos en 2025 que su promedio reciente; Alimentos y Bebidas es el sector más variado',
  'Para entender un sector conviene mirar si le llega producto nuevo y si su oferta es variada (muchos tipos distintos) o profunda (muchas versiones del mismo tipo).',
  `<div class="main2"><div>${ex(7, 'Novedad: ocho sectores lanzaron al menos 1,9 veces su promedio anual de 2021–2024', 'Veces que los códigos de 2025 superan el promedio anual de 2021–2024 · sectores con 300 códigos o más en 2025', hbars(novRows, { lw: 150, max: 3.2, vw: 40 }))}</div>
  <div>${ex(8, 'Variedad y profundidad: Alimentos y Bebidas abre muchos tipos; Calzado y Prendas repiten pocos tipos en muchas versiones', 'Cada punto es un sector · 1993–2025', sc)}</div></div>
  <div class="call"><b>Cómo leerlo</b> Alimentos pide variedad: 822 tipos de producto con unas 237 versiones cada uno. Calzado y Prendas piden profundidad: 14 y 72 tipos con más de 2.000 versiones por tipo (tallas, colores, modelos).</div>`);

// ---------- 8 productos y dependencia ----------
const dep = [['Alimentos y Bebidas', 809, 6], ['Asistencia sanitaria', 178, 16], ['Belleza y cuidado personal', 170, 15], ['Limpieza e higiene del hogar', 124, 20], ['Automotriz', 81, 23], ['Papelería y celebraciones', 51, 31], ['Arte, artesanía y costura', 27, 40], ['Prendas de vestir', 50, 67], ['Construcción', 106, 65], ['Plomería y climatización', 47, 72], ['Calzado', 13, 73]];
const p8 = page('PRODUCTOS Y MARCAS', 'En Alimentos y Bebidas la mayor empresa aporta el 6% del sector; en Calzado, el 73%',
  'Entre 1993 y 2025 las prendas y el calzado ocupan tres de los cuatro tipos de producto con más códigos. Pero lo que separa a un mercado diversificado de uno dependiente es cuánto pesa su mayor empresa.',
  `<div class="main2"><div>${ex(9, 'Camisas, blusas, polos y camisetas lideran con mucha ventaja', 'Tipos de producto con más códigos · 1993–2025', hbars(FU.bricks.map((b, i) => ({ l: b[0].replace(' – Confitería', '').replace('Chocolate y combinaciones de chocolate/caramelo', 'Chocolate y confitería').replace('Camisas/blusas/polos/camisetas', 'Camisas, blusas, polos y camisetas'), v: b[1], d: fN(b[1]), c: i === 0 ? OR : NAVY })), { lw: 150, vw: 52 }))}</div>
  <div>${ex(10, 'Seis sectores dependen de una o dos empresas por encima del 40%', 'Parte del sector que aporta la mayor empresa · 2025 · sectores con 1.000 códigos o más', hbars(dep.map(([n, e, p]) => ({ l: n + ' <small>(' + e + ' empr.)</small>', v: p, d: p + '%', c: p >= 50 ? OR : p > 25 ? MID : NAVY })), { lw: 150, max: 80, vw: 36 }) + `<div class="leg"><span><i style="background:${NAVY}"></i>Diversificado (hasta 25%)</span><span><i style="background:${MID}"></i>Intermedio (26–49%)</span><span><i style="background:${OR}"></i>Dependiente (50% o más)</span></div>`)}</div></div>`);

// ---------- 9 viaje ----------
const steps = [['1', 'Fabricante', 'El prefijo de empresa y el GTIN-13 identifican la unidad de venta.', 'Más de 1,6 millones de códigos de más de 3.500 empresas, 1993–2025.', 1], ['2', 'Clasificación', 'El GPC ubica cada producto en segmento, familia, clase y brick.', 'El 86,5% de los códigos de 2025 llega a Brick.', 1], ['3', 'Bulto', 'El GTIN-14 identifica la caja o empaque que contiene la unidad.', '29,2% de los códigos de 2018–2025 son GTIN-14.', 1], ['4', 'Pallet y transporte', 'El SSCC identifica la unidad logística; el GS1-128 lleva lote y vencimiento; el GLN, ubicaciones.', 'No se mide: el registro no contiene SSCC, GLN ni lotes.', 0], ['5', 'Retail', 'El GTIN-13 se lee en el punto de venta y con él se arma el surtido.', 'Alimentos y Bebidas: 397 tipos de producto en 2025.', 1], ['6', 'Consumidor', 'GS1 Digital Link y los códigos 2D conectan el producto con información en línea.', 'No se mide: el registro no indica el tipo de símbolo.', 0]];
const p9 = page('LOGÍSTICA · EL VIAJE DEL PRODUCTO', 'El código viaja con el producto: el registro mide bien los primeros eslabones y no ve los últimos',
  'Un producto cambia de identidad a medida que avanza: unidad de venta, bulto, pallet, ubicación. GS1 tiene un estándar para cada paso.',
  `<div class="steps">${steps.map(([n, t, s, r, m]) => `<div class="stp"><div class="sn" style="background:${m ? NAVY : LT};color:${m ? '#fff' : NAVY}">${n}</div><div class="sb"><h4>${t}</h4><div class="sl">ESTÁNDAR GS1</div><p>${s}</p><div class="sl" style="color:${m ? OR : MUTE}">EN EL REGISTRO</div><p><b>${r}</b></p></div></div>`).join('')}</div>
  <div class="call"><b>Un dato que viene de la industria</b> GS1 impulsa a nivel global el paso a códigos 2D en el punto de venta con la campaña «Sunrise 2027». El registro de codificación no permite medir esa transición hoy: es un dato que habría que sumar a la carga.</div>`);

// ---------- 10 bultos, packs y tamaños ----------
const yrs = Object.entries(G14.year).map(([y, v]) => ({ l: y, v, d: pc(v), c: y === '2025' ? OR : NAVY }));
const pk = F2.pack_top.slice(0, 8).map(([k, v]) => ({ l: k + ' unidades', v, d: fN(v), c: (k === 12 || k === 24) ? OR : NAVY }));
const p10 = page('LOGÍSTICA · BULTOS, PACKS Y TAMAÑOS', 'Casi tres de cada diez códigos son de bulto, y en bebidas y alimentos mandan los packs de 12 y 24 unidades',
  'Entre 2018 y 2025, el 29,2% de los códigos identifica un bulto o empaque (GTIN-14), y el 99,3% de esos bultos tiene su unidad registrada.',
  `<div class="main2"><div>${ex(11, 'En 2025 el peso del bulto bajó a 20,9% porque el año lo dominaron unidades de venta', 'Parte de los códigos de cada año que son GTIN-14', columns(yrs.map((r) => ({ ...r, l: r.l.slice(2) })), { h: 260, max: 42 }))}</div>
  <div>${ex(12, 'Plomería, limpieza y cultivos tienen el mayor peso de bultos', 'Bultos (GTIN-14) por cada 100 unidades · 2018–2025', hbars(G14.caj.slice(0, 8).map((r) => ({ l: r[0], v: r[3], d: dec(r[3]), c: r[3] >= 55 ? OR : NAVY })), { lw: 150, max: 75, vw: 36 }))}</div></div>
  <div class="main2"><div>${ex(13, 'Los múltiplos de 6 mandan: 12 y 24 unidades son los packs más frecuentes', 'Códigos con pack indicado en la descripción · Alimentos y Bebidas · 1993–2025', hbars(pk, { lw: 110, vw: 44 }))}</div>
  <div>${ex(14, 'En 2025 la mediana de líquidos baja a 500 ml y la de sólidos a 300 g', 'Tamaño mediano en Alimentos y Bebidas', `<table class="tbl s"><tr><th></th><th>1993–99</th><th>2000–09</th><th>2010–19</th><th>2020–25</th><th>2025</th></tr><tr><td>Sólidos (g)</td><td>${F2.gr_med['1993–1999']}</td><td>${F2.gr_med['2000–2009']}</td><td>${F2.gr_med['2010–2019']}</td><td>${F2.gr_med['2020–2025']}</td><td><b style="color:${OR}">${F2.gr_med['2025']}</b></td></tr><tr><td>Líquidos (ml)</td><td>${F2.ml_med['1993–1999']}</td><td>${F2.ml_med['2000–2009']}</td><td>${F2.ml_med['2010–2019']}</td><td>${F2.ml_med['2020–2025']}</td><td><b style="color:${OR}">${F2.ml_med['2025']}</b></td></tr></table><p class="n" style="margin-top:8px">Más unidades pequeñas por bulto: una pista para planear picking, almacenaje y armado de pallets.</p>`)}</div></div>`);

// ---------- 11 qué se consume ----------
const g = (arr, names, a, b) => names.map((n) => { const r = arr.find((x) => x[0] === n); return { l: n.replace(' (peso en lácteos)', '').replace('Vino, espumante y sangría', 'Vino y espumante').replace('Mora y frutos rojos', 'Mora y frutos rojos'), a: r[a], b: r[b] }; });
const p11 = page('BENCHMARK · QUÉ SE CONSUME', 'En bebidas ganan el refresco, la lata y el envase individual; en alimentos, el yogurt',
  'Cada código es un producto que una empresa decide poner en el mercado, así que la descripción permite ver hacia dónde se mueve la oferta. Son registros de productos, no ventas ni consumo.',
  `<div class="grid2">${ex(15, 'Bebidas: el refresco pasa de 1,4% a 13,2% de los códigos', 'Parte de los códigos de bebidas · tipo de bebida', dumbbell(g(F2.tip, ['Refresco y gaseosa', 'Vino, espumante y sangría', 'Ron', 'Whisky', 'Agua', 'Jugo y néctar', 'Té e infusión', 'Cerveza', 'Café'], 3, 5)))}
  ${ex(16, 'Sabores: manzana, durazno y piña suben; chocolate baja', 'Parte de los códigos de bebidas que mencionan el sabor', dumbbell(g(F2.sab, ['Manzana', 'Durazno', 'Pera', 'Piña', 'Mora y frutos rojos', 'Limón', 'Naranja', 'Fresa', 'Chocolate'], 3, 5)))}
  ${ex(17, 'Lácteos: el yogurt pasa de 10,4% a 19,7% de los códigos de lácteos', 'Parte de los códigos de lácteos que mencionan el atributo', dumbbell(g(F2.lac, ['Yogurt (peso en lácteos)', 'Yogurt natural', 'Yogurt griego', 'Light o descremado', 'Fresa', 'Durazno'], 3, 5)))}
  ${ex(18, 'Salsas: BBQ y aderezos crecen; ketchup retrocede', 'Parte de los códigos de salsas y condimentos que mencionan el atributo', dumbbell(g(F2.sal, ['BBQ y barbacoa', 'Aderezos', 'Ajo', 'Mayonesa', 'Ketchup', 'Picante y ají'], 3, 5)))}</div>
  <div class="call"><b>Cómo leerlo</b> Porcentaje de códigos del grupo cuya descripción menciona el atributo; son mínimos observables, no participación de mercado. En bebidas, además, el envase individual de 500 ml o menos pasa del 11,9% al 37,5% y la lata, del 0,5% al 10,0%.</div>`);

// ---------- 12 oportunidades con respaldo amplio ----------
const opp = [['Muebles para el hogar y oficina', 127, 416, 228, 19, 30], ['Nata y sustitutos', 89, 200, 125, 45, 25], ['Equipos de aire acondicionado', 90, 192, 113, 10, 26], ['Vasos no desechables', 152, 320, 111, 22, 18], ['Leche y sustitutos', 174, 322, 85, 60, 16], ['Bocadillos', 194, 344, 77, 37, 13], ['Salchichas procesadas', 205, 317, 55, 45, 10], ['Bebidas alcohólicas', 409, 619, 51, 71, 8]];
const cai = [['Cuadros, espejos y marcos', 574, 113, -80], ['Suministro de agua y gas', 1086, 375, -65], ['Ferretería de fijaciones y cierres', 3412, 1251, -63], ['Pintura', 1232, 577, -53]];
const p12 = page('OPORTUNIDADES', 'Los productos que más crecen con respaldo amplio están en lácteos, bocadillos y bebidas',
  'Son clases GPC que crecieron al menos 50% entre 2024 y 2025, con 8 o más empresas detrás y donde la mayor empresa aporta 40% o menos: tendencias de mercado y no cargas de una sola empresa.',
  `<div class="main2" style="grid-template-columns:1.25fr 1fr"><div>${ex(19, 'Ocho clases crecieron entre 51% y 228% con muchas empresas detrás', 'Crecimiento de códigos 2024 → 2025', hbars(opp.map((o) => ({ l: o[0] + ` <small>(${o[4]} empr.)</small>`, v: o[3], d: '+' + o[3] + '%', c: GR })), { lw: 190, max: 240, vw: 44 }))}</div>
  <div>${ex(20, 'Las mayores caídas están en ferretería, pintura y agua y gas', 'Variación de códigos 2024 → 2025 · clases con 100 códigos o más', hbars(cai.map((o) => ({ l: o[0], v: -o[3], d: o[3] + '%', c: OR })), { lw: 150, max: 90, vw: 40 }))}
  <div class="call" style="margin-top:12px"><b>Mirar ambos lados</b> evita apostar a una moda de una sola empresa.</div></div></div>
  <div class="main2"><div>${ex(21, 'Alimentos y Bebidas es la primera carga del 57% de las empresas desde 1993', 'Sector de la primera carga de cada empresa · parte del total de empresas', hbars([['Alimentos y Bebidas', 57], ['Limpieza del hogar', 8.1], ['Belleza y cuidado personal', 7.4], ['Asistencia sanitaria', 4.6], ['Construcción', 2.6], ['Artículos de cocina', 2.5], ['Cultivos', 2.3], ['Hogar y mobiliario', 1.7]].map(([l, v], i) => ({ l, v, d: pc(v), c: i === 0 ? OR : NAVY })), { lw: 150, vw: 44 }))}</div>
  <div>${ex(22, 'Los cinco sectores más grandes crecieron en 2025; Prendas y Plomería, más del doble', 'Cambio de códigos únicos 2025 frente a 2024', hbars([['Plomería y climatización', 114, '1.958 → 4.199'], ['Prendas de vestir', 113, '5.331 → 11.330'], ['Construcción', 47, '6.068 → 8.905'], ['Asistencia sanitaria', 12, '4.273 → 4.778'], ['Alimentos y Bebidas', 5, '12.128 → 12.785']].map(([l, v, n]) => ({ l: l + ' <small>' + n + '</small>', v, d: '+' + v + '%', c: v > 100 ? OR : NAVY })), { lw: 180, max: 120, vw: 44 }))}</div></div>`);

// ---------- 13 por eslabón ----------
const col = (t, sub, c, items, todo) => `<div class="eslab"><div class="eh" style="background:${c}"><b>${t}</b><span>${sub}</span></div>${items.map(([n, tx]) => `<div class="en"><b style="color:${c}">${n}</b><span>${tx}</span></div>`).join('')}<div class="ea"><b>QUÉ HACER</b>${todo}</div></div>`;
const p13 = page('OPORTUNIDADES · A CADA ESLABÓN', 'Las mismas cifras se leen distinto según quién las use: tres señales para tres eslabones de la cadena',
  'Estas son las señales más claras para quien fabrica, quien vende y quien mueve la mercancía.',
  `<div class="cols3">${col('Fabricar y lanzar', 'Quieren lanzar o ampliar su oferta', NAVY, [['46,1%', 'de los códigos de bebidas de 2025 son bebidas listas para beber'], ['37,5%', 'de las bebidas de 2025 se codifica en envase individual de 500 ml o menos'], ['809', 'empresas codificaron alimentos y bebidas en 2025; la mayor aporta solo el 6,3%']], 'Pensar el lanzamiento en formatos para llevar y apostar por un sector con muchas empresas.')}
  ${col('Vender y surtir', 'Arman surtido y compran a proveedores', MID, [['397', 'tipos de producto distintos en Alimentos y Bebidas en 2025'], ['42,9%', 'de los códigos clasificados a nivel Brick se concentra en 100 tipos de producto'], ['65–73%', 'aporta la mayor empresa en construcción, prendas, plomería y calzado']], 'Variedad en alimentos, núcleo estable y proveedores alternativos donde una empresa pesa demasiado.')}
  ${col('Mover y almacenar', 'Almacenan, despachan y rastrean', OR, [['29,2%', 'de los códigos de 2018–2025 identifica bultos o empaques'], ['41,2%', 'en plomería, 38,9% en limpieza y 38,6% en cultivos: los sectores con más peso de bultos'], ['37,8%', 'de las empresas no registra ningún GTIN-14']], 'Llevar la identificación hasta el bulto y el pallet en los sectores con más embalaje.')}</div>`);

// ---------- 14 cierre ----------
const ideas = [['Codificar cada producto y cada presentación.', 'Lo que no se codifica no se mide: cada código es una referencia que se puede comparar, reponer y vender en toda la cadena.'], ['Pensar el lanzamiento desde el formato.', 'En bebidas, el envase individual (37,5%), el refresco y la lata ganan terreno en lo que se registra.'], ['Armar el surtido con variedad y con proveedores alternativos.', 'Alimentos y Bebidas es el sector más variado; en construcción, prendas, plomería y calzado, una sola empresa aporta más del 60% de los códigos.'], ['Llevar la identificación hasta el bulto y el pallet.', 'El 37,8% de las empresas no registra ningún GTIN-14.'], ['Seguir la novedad sector por sector.', 'Plomería y climatización lanzó tres veces más productos en 2025 que su promedio de 2021–2024: ahí hay movimiento.']];
const p14 = page('CIERRE', 'Cinco ideas para llevar', 'Codificar completo, lanzar con foco en el formato y llevar la identificación desde la unidad hasta el bulto.',
  `<div class="idea5">${ideas.map(([a, b], i) => `<div class="id"><b>${i + 1}</b><div><h4>${a}</h4><p>${b}</p></div></div>`).join('')}</div>
  <div class="kp5">${[['68.339', 'códigos en 2025'], ['30,1%', 'de los códigos de 2025 los registraron solo tres empresas'], ['63,9%', 'de los códigos de 2025 los registraron 46 empresas'], ['9', 'códigos registró en 2025 la empresa típica (mediana)'], ['397', 'tipos de producto en Alimentos y Bebidas en 2025'], ['29,2%', 'son bultos (GTIN-14, 2018–2025)']].map(([n, t], i) => `<div><b style="color:${i % 2 ? OR : NAVY}">${n}</b><span>${t}</span></div>`).join('')}</div>
  <div class="cta"><div><div class="ck">DATOS PARA DECIDIR</div><div class="ct">Más información sobre el estándar y la codificación en gs1ve.org</div></div></div>`);

const CSS = `${fonts}
*{box-sizing:border-box;margin:0;padding:0}body{background:#E6E9EF;font-family:'Barlow',sans-serif;color:${INK};-webkit-print-color-adjust:exact;print-color-adjust:exact}
.page{width:794px;height:1123px;margin:18px auto;background:#fff;position:relative;padding:0 50px;overflow:hidden;box-shadow:0 2px 14px rgba(0,0,0,.14);break-after:page}
@media print{body{background:#fff}.page{margin:0;box-shadow:none}}@page{size:794px 1123px;margin:0}
.hd{display:flex;justify-content:space-between;padding:26px 0 8px;border-bottom:2px solid ${NAVY};font-size:9.5px;letter-spacing:1.6px;color:${MUTE};font-weight:600;text-transform:uppercase}.hd b{color:${OR}}
h1{font-family:Georgia,'Times New Roman',serif;font-weight:700;font-size:25px;line-height:1.18;color:${NAVY};margin:22px 0 10px;letter-spacing:-.2px}
.deck{font-size:12.5px;line-height:1.5;color:#3C4963;margin-bottom:16px;max-width:660px}
.page.pg{display:flex;flex-direction:column}.page.pg .bd{flex:1;display:flex;flex-direction:column;justify-content:space-between;padding-bottom:84px}.page.pg .bd>*{margin-bottom:0}.main{display:block}.main2{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:6px}.main1{display:block}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px 22px}
.ex{margin-bottom:22px}.exl{font-size:9px;letter-spacing:1.4px;font-weight:700;color:${OR};text-transform:uppercase}.ext{font-size:14px;font-weight:700;line-height:1.3;color:${INK};margin:3px 0 2px}.exs{font-size:10.5px;color:${MUTE};margin-bottom:8px;line-height:1.3}
.rail{background:${BG};border-top:3px solid ${NAVY};padding:14px 18px 16px;margin-top:6px}.ris{display:grid;grid-template-columns:repeat(4,1fr);gap:22px}.rail.side .ris{display:block}.rt{font-size:9.5px;letter-spacing:1.4px;font-weight:700;color:${NAVY};text-transform:uppercase;margin-bottom:8px}.ri{padding:2px 0 2px 14px;border-left:3px solid ${OR}}.rail.side .ri{padding:9px 0;border-left:none;border-top:1px solid ${RULE}}
.big b{display:block;font-family:'Barlow Condensed',sans-serif;font-size:38px;line-height:1;font-weight:700}.big span{display:block;font-size:11.5px;line-height:1.35;color:#3C4963;margin-top:3px}.n{font-size:11.5px;line-height:1.4;color:#3C4963}
.hbr{display:grid;gap:10px;align-items:center;margin:11px 0;font-size:12px}.hl{line-height:1.2}.hl small{color:${MUTE}}.hl.b{font-weight:700}.ht{height:17px;background:#EEF1F6;position:relative}.ht i{position:absolute;left:0;top:0;bottom:0;display:block}.hv{font-weight:700;text-align:right;font-size:12px}
.leg{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:10.5px;color:${MUTE};margin-top:8px}.leg i{display:inline-block;width:9px;height:9px;margin-right:5px;vertical-align:-1px}
.stk{margin-top:6px}.sk{display:grid;grid-template-columns:44px 1fr;align-items:center;margin:16px 0;font-size:11px;font-weight:700}.sk>div{position:relative;height:40px;background:#EEF1F6;display:flex}.sk i{display:block;height:100%}.sk em{position:absolute;left:42%;top:6px;font-style:normal;font-size:11px;color:#fff;font-weight:700}.sk:first-child em{color:#fff;left:3%}.sk:last-child em{left:8%;color:#fff}
.tbl{width:100%;border-collapse:collapse;font-size:12px;margin-top:10px}.tbl th{font-size:12px;text-align:left;padding:9px 8px;color:${NAVY};font-weight:700}.tbl td{padding:11px 8px;border-top:1px solid ${RULE};vertical-align:top;line-height:1.3}.tbl td:first-child{color:#3C4963;width:36%}.tbl.s td,.tbl.s th{padding:5px 6px;text-align:center}.tbl.s td:first-child,.tbl.s th:first-child{text-align:left}
.call{background:${BG};border-left:4px solid ${OR};padding:14px 18px;font-size:12.5px;line-height:1.5;margin-top:10px}.call b{display:block;font-size:9.5px;letter-spacing:1.4px;color:${OR};text-transform:uppercase;margin-bottom:3px}
.ft{position:absolute;left:50px;right:50px;bottom:20px;border-top:1px solid ${RULE};padding-top:8px;display:flex;justify-content:space-between;align-items:flex-end;gap:20px}.src{font-size:8.5px;line-height:1.4;color:${MUTE};max-width:560px}.fr{display:flex;align-items:center;gap:12px;font-size:9.5px;color:${MUTE}}.fr img{height:26px}
.cover{background:${NAVY};color:#fff;padding:0 56px}.cv-top{display:flex;justify-content:space-between;align-items:center;padding-top:44px}.cv-logo{background:#fff;padding:10px 16px}.cv-logo img{height:44px;display:block}.cv-kick{font-size:11px;letter-spacing:3px;font-weight:600;color:#FFB59A}
.cv-main{margin-top:150px}.cover h1{font-size:66px;line-height:1.02;color:#fff;margin:0 0 22px;letter-spacing:-1px}.cv-main p{font-size:16px;line-height:1.5;max-width:470px;color:#C6D2EE}.cv-bars{display:flex;gap:3px;height:56px;align-items:flex-end;margin-top:40px}.cv-bars i{display:block;height:100%;background:${OR}}
.cv-stats{position:absolute;left:56px;right:56px;bottom:170px;display:grid;grid-template-columns:repeat(4,1fr);gap:16px;border-top:2px solid ${OR};padding-top:18px}.cv-stats b{display:block;font-family:'Barlow Condensed',sans-serif;font-size:42px;line-height:1;font-weight:700}.cv-stats span{font-size:12px;color:#C6D2EE}
.cv-q{position:absolute;left:56px;right:56px;bottom:64px;font-family:Georgia,serif;font-size:17px;font-style:italic;color:#fff}.cv-q small{display:block;font-family:'Barlow',sans-serif;font-style:normal;font-size:10px;letter-spacing:1px;color:#9FB0CF;margin-top:6px}.cv-f{position:absolute;left:56px;right:56px;bottom:22px;font-size:8.5px;color:#8FA3C8}
.lt{padding-right:6px}.li{display:flex;gap:14px;padding:15px 0;border-top:1px solid ${RULE}}.li b{font-family:Georgia,serif;font-size:24px;color:${OR};width:22px}.li h4{font-size:13px;color:${NAVY};margin-bottom:2px}.li p{font-size:12.5px;line-height:1.45;color:#3C4963}.sg{margin-top:14px;font-size:11.5px;line-height:1.5;color:#3C4963;font-style:italic}.sg b{font-style:normal;color:${NAVY}}
.ix{display:flex;justify-content:space-between;font-size:11px;padding:1px 0}.ix b{color:${OR}}
.steps{display:grid;grid-template-columns:1fr 1fr;gap:26px 24px;margin-bottom:20px}.stp{display:flex;gap:12px;border-top:3px solid ${NAVY};padding-top:12px}.sn{flex:0 0 32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:15px}.sb h4{font-family:Georgia,serif;font-size:19px;color:${NAVY};margin-bottom:6px}.sl{font-size:8.5px;letter-spacing:1.4px;font-weight:700;color:${MUTE};margin-top:6px}.sb p{font-size:12.5px;line-height:1.45;margin-top:2px}
.cols3{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.eslab{background:${BG}}.eh{color:#fff;padding:12px 14px}.eh b{display:block;font-family:Georgia,serif;font-size:17px}.eh span{font-size:10px;color:#DCE4F3}.en{padding:20px 16px;border-bottom:1px solid ${RULE}}.en b{display:block;font-family:'Barlow Condensed',sans-serif;font-size:38px;line-height:1;font-weight:700}.en span{display:block;font-size:12.5px;line-height:1.4;margin-top:4px;color:#3C4963}.ea{padding:16px;font-size:12.5px;line-height:1.45}.ea b{display:block;font-size:9px;letter-spacing:1.4px;color:${OR};margin-bottom:3px}
.idea5{margin-bottom:12px}.id{display:flex;gap:16px;padding:16px 0;border-top:1px solid ${RULE}}.id b{font-family:Georgia,serif;font-size:30px;color:${OR};width:28px;line-height:1}.id h4{font-size:16px;color:${NAVY};margin-bottom:2px}.id p{font-size:12.5px;line-height:1.45;color:#3C4963}
.kp5{display:grid;grid-template-columns:repeat(3,1fr);gap:0;border-top:3px solid ${NAVY};margin-top:6px}.kp5>div{padding:16px 10px 16px 0;border-bottom:1px solid ${RULE}}.kp5 b{display:block;font-family:'Barlow Condensed',sans-serif;font-size:40px;line-height:1;font-weight:700}.kp5 span{font-size:11.5px;line-height:1.35;color:#3C4963;display:block;margin-top:3px}
.cta{background:${NAVY};color:#fff;padding:18px 24px;margin-top:16px}.ck{font-size:9px;letter-spacing:3px;font-weight:700;color:#FFB59A}.ct{font-family:Georgia,serif;font-size:21px;line-height:1.2;margin-top:6px}`;
const html = `<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=820"><title>El mercado en códigos · GS1 Venezuela Insights</title><style>${CSS}</style></head><body>${cover}${letter}${p3}${p4}${p5}${p6}${p7}${p8}${p9}${p10}${p11}${p12}${p13}${p14}</body></html>`;
fs.writeFileSync(process.argv[2] || path.join(__dirname, 'boletin_estilo_consultora.html'), html);
console.log('páginas', PN);
