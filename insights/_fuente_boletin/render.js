// Genera el PDF del boletín desde boletin.html (Playwright + Chromium).
// Uso: node render.js [salida.pdf]   (por defecto ../Boletin_insights_GS1_edicion_revista.pdf)
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const out = path.resolve(process.argv[2] || path.join(__dirname, '..', 'Boletin_insights_GS1_edicion_revista.pdf'));
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 794, height: 1123 } });
  await p.goto('file://' + path.join(__dirname, 'boletin.html'));
  await p.waitForTimeout(800);
  const ov = await p.evaluate(() => [...document.querySelectorAll('.page')].map((pg, i) => {
    const top = pg.getBoundingClientRect().top;
    const pl = pg.querySelector('.plain');
    const lim = (pl ? pl.getBoundingClientRect().top : pg.querySelector('.foot').getBoundingClientRect().top) - top;
    let max = 0;
    pg.querySelectorAll(':scope > *:not(.foot):not(.plain)').forEach((e) => { max = Math.max(max, e.getBoundingClientRect().bottom - top); });
    return [i + 1, Math.round(max), Math.round(lim)];
  }));
  console.log('páginas:', ov.length);
  await p.pdf({ path: out, width: '794px', height: '1123px', printBackground: true });
  await b.close();
  console.log('PDF:', out);
})();
