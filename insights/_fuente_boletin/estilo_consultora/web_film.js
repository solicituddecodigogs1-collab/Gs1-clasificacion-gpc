  // ---------- película de datos dibujada en vivo (no depende de que el teléfono reproduzca video) ----------
  (function () {
    const cv = $('#film'); if (!cv) return;
    const x = cv.getContext('2d'), lg = $('#flogo'), SY = DATA.sy, EMP = DATA.serie.map((r) => r[2]), DUR = 75;
    const NAVY = '#002C6C', OR = '#F26334';
    const names = Object.keys(SY.sectors), COL = {};
    const pal = ['#F26334', '#5A78AD', '#9FB0CF', '#1E8E3E', '#F9C0A5', '#7D93BD', '#C9D4EA', '#E07A55', '#3B5FA0', '#B5C3DD'];
    names.forEach((n, i) => { COL[n] = pal[i]; });
    const ease = (t) => (t < 0 ? 0 : t > 1 ? 1 : t * t * (3 - 2 * t));
    const fmt = (n) => Math.round(n).toLocaleString('de-DE');
    const CAP = [[1993, '1993 · Arranca el registro: 8.720 códigos'], [1999, '1999 · 36.467 códigos: la primera gran expansión'], [2011, '2011 · Máximo histórico: 99.774 códigos'], [2021, '2021 · El piso reciente: 40.940 códigos'], [2025, '2025 · El rebote: 68.339 códigos']];
    const txt = (s, px, py, f, col, al, a) => { x.globalAlpha = a == null ? 1 : a; x.font = f; x.fillStyle = col; x.textAlign = al || 'left'; x.fillText(s, px, py); x.globalAlpha = 1; };
    function intro(t) {
      x.fillStyle = NAVY; x.fillRect(0, 0, 1280, 720);
      for (let i = 0; i < 60; i++) { const w = [3, 6, 4, 8, 3, 5][i % 6], px = 140 + i * 17, h = ease((t - 0.2 - i * 0.012) / 0.8) * 120; x.fillStyle = OR; x.fillRect(px, 330 - h, w, h); }
      txt('Más de 30 años en códigos', 140, 430, 'bold 84px Barlow Condensed', '#fff', 'left', ease((t - 0.6) / 0.8));
      txt('El registro de GS1 Venezuela, 1993–2025', 140, 480, '400 28px Barlow', '#C6D2EE', 'left', ease((t - 1.2) / 0.8));
    }
    function race(T) {
      x.fillStyle = '#fff'; x.fillRect(0, 0, 1280, 720); x.fillStyle = NAVY; x.fillRect(0, 0, 1280, 92);
      const fy = T * (SY.years.length - 1), i0 = Math.floor(fy), i1 = Math.min(SY.years.length - 1, i0 + 1), f = fy - i0;
      const lerp = (arr) => arr[i0] + (arr[i1] - arr[i0]) * f;
      const year = 1993 + fy; txt('Códigos por sector y año', 48, 58, 'bold 34px Barlow', '#fff');
      txt(String(Math.round(year)), 1232, 680, 'bold 150px Barlow Condensed', '#E7ECF6', 'right');
      const vals = names.map((n) => ({ n, v: lerp(SY.sectors[n]) })).sort((a, b) => b.v - a.v);
      const max = vals[0].v * 1.08, bx = 330, bw = 800, rh = 38, y0 = 120;
      vals.forEach((r, k) => { const y = y0 + k * (rh + 7), w = Math.max(2, r.v / Math.max(max, 1) * bw); x.fillStyle = COL[r.n]; x.fillRect(bx, y, Math.min(w, bw), rh); txt(r.n, bx - 14, y + 26, '400 20px Barlow', NAVY, 'right'); txt(fmt(r.v), bx + Math.min(w, bw) + 10, y + 27, 'bold 20px Barlow', NAVY, 'left'); });
      txt('Códigos del año: ' + fmt(lerp(SY.total)), 48, 690, 'bold 30px Barlow', OR); txt('Empresas que codificaron: ' + fmt(lerp(EMP)), 48, 660, '400 22px Barlow', NAVY);
      let cap = ''; CAP.forEach(([y, s]) => { if (Math.abs(year - y) < 1.6) cap = s; });
      if (cap) { const k = Math.max(0, 1 - Math.abs(year - parseInt(cap)) / 1.6); txt(cap, 48, 118 + 10 * (rh + 7) + 36, 'bold 26px Barlow', OR, 'left', ease(k * 2)); }
    }
    function outro(t) {
      x.fillStyle = NAVY; x.fillRect(0, 0, 1280, 720);
      [['+1,6 M', 'códigos registrados'], ['+3.500', 'empresas registradas'], ['+30', 'años de historia'], ['68.339', 'códigos en 2025']].forEach(([n, s], i) => { const al = ease((t - 0.3 - i * 0.5) / 0.7); txt(n, 140 + i * 260, 165, 'bold 78px Barlow Condensed', '#fff', 'left', al); txt(s, 140 + i * 260, 205, '400 24px Barlow', '#C6D2EE', 'left', al); });
      x.fillStyle = OR; x.fillRect(140, 70, 1000, 4);
      txt('«Lo que no se codifica, no se mide;', 140, 340, 'italic 54px Georgia, serif', '#fff', 'left', ease((t - 3.5) / 1.2));
      txt('lo que no se mide no se controla.»', 140, 410, 'italic 54px Georgia, serif', '#fff', 'left', ease((t - 4.6) / 1.2));
      txt('Adaptación de Lord Kelvin', 140, 462, '400 26px Barlow', '#FFB59A', 'left', ease((t - 6) / 1));
      const fa = ease((t - 7.5) / 1); x.globalAlpha = fa; x.fillStyle = '#fff'; x.fillRect(140, 540, 210, 92); if (lg && lg.complete) x.drawImage(lg, 150, 548, 190, 76); x.globalAlpha = 1;
      txt('gs1ve.org', 380, 592, '700 30px Barlow', '#fff', 'left', fa);
    }
    const mm = (s) => Math.floor(s / 60) + ':' + String(Math.floor(s % 60)).padStart(2, '0');
    let t = 2.5, playing = false, last = 0;
    const btn = $('#fplay'), seek = $('#fseek'), lab = $('#ftime');
    const render = () => { if (t < 5) intro(t); else if (t < 62) race(Math.min(1, (t - 5) / 57)); else outro(t - 62); seek.value = t; lab.textContent = mm(t) + ' / 1:15'; };
    const stopF = () => { playing = false; btn.textContent = t >= DUR ? '↺ Ver de nuevo' : '▶ Reproducir'; };
    const tick = (ts) => { if (!playing) return; t += (ts - last) / 1000; last = ts; if (t >= DUR) { t = DUR; render(); stopF(); return; } render(); requestAnimationFrame(tick); };
    const toggle = () => { if (playing) { stopF(); return; } if (t >= DUR) t = 0; playing = true; btn.textContent = '❚❚ Pausa'; last = performance.now(); requestAnimationFrame(tick); };
    btn.onclick = toggle; cv.onclick = toggle;
    seek.oninput = () => { t = parseFloat(seek.value); render(); };
    render();
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(render);
    if (lg) lg.onload = render;
  })();
