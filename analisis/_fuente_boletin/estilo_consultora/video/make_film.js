// Genera "treinta_anos_en_codigos.mp4": animación de datos (carrera de sectores 1993–2025) con Playwright + ffmpeg.
// Uso: node make_film.js [salida.mp4]
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), { execFileSync } = require('child_process');
const D = path.join(__dirname, '..', 'datos'), R = path.join(__dirname, '..', '..');
const data = JSON.parse(fs.readFileSync(path.join(D, 'sector_year.json'), 'utf8'));
const serie = fs.readFileSync(path.join(D, 'captacion_afiliados_por_ano.csv'), 'utf8').replace(/^﻿/, '').trim().split('\n').slice(1).map((l) => l.split(',').map(Number));
data.emp = serie.map((r) => r[2]);
const b64 = (f) => fs.readFileSync(path.join(R, f)).toString('base64');
const FPS = 24, DUR = 75, OUT = path.resolve(process.argv[2] || path.join(__dirname, 'treinta_anos_en_codigos.mp4'));
const fontCss = [['Barlow', 400, 'Barlow-400-latin'], ['Barlow', 700, 'Barlow-700-latin'], ['Barlow Condensed', 700, 'BarlowCondensed-700-latin']]
  .map(([n, w, f]) => `@font-face{font-family:'${n}';font-weight:${w};src:url(data:font/woff2;base64,${b64('fonts/' + f + '.woff2')}) format('woff2')}`).join('');
const html = `<!doctype html><html><head><meta charset="utf-8"><style>${fontCss}body{margin:0;background:#002C6C}canvas{display:block}</style></head><body><canvas id="c" width="1280" height="720"></canvas><img id="lg" style="display:none" src="data:image/png;base64,${b64('logo/logo.png')}"><script>
const DATA=${JSON.stringify(data)};
const c=document.getElementById('c'),x=c.getContext('2d'),lg=document.getElementById('lg');
const NAVY='#002C6C',OR='#F26334',MID='#5A78AD';
const names=Object.keys(DATA.sectors),COL={};const pal=['#F26334','#5A78AD','#9FB0CF','#1E8E3E','#F9C0A5','#7D93BD','#C9D4EA','#E07A55','#3B5FA0','#B5C3DD'];names.forEach((n,i)=>COL[n]=pal[i]);
const ease=(t)=>t<0?0:t>1?1:t*t*(3-2*t);
const fmt=(n)=>Math.round(n).toLocaleString('de-DE');
const CAP=[[1993,'1993 · Arranca el registro: 8.720 códigos'],[1999,'1999 · 36.467 códigos: la primera gran expansión'],[2011,'2011 · Máximo histórico: 99.774 códigos'],[2021,'2021 · El piso reciente: 40.940 códigos'],[2025,'2025 · El rebote: 68.339 códigos']];
function txt(s,px,py,f,col,al,a){x.globalAlpha=a==null?1:a;x.font=f;x.fillStyle=col;x.textAlign=al||'left';x.fillText(s,px,py);x.globalAlpha=1}
function intro(t){ // 0–4 s
  const a=ease(t/1);x.fillStyle=NAVY;x.fillRect(0,0,1280,720);
  for(let i=0;i<60;i++){const w=[3,6,4,8,3,5][i%6],px=140+i*17,h=ease((t-0.2-i*0.012)/0.8)*120;x.fillStyle=OR;x.fillRect(px,330-h,w,h)}
  txt('Más de 30 años en códigos',140,430,'bold 84px Barlow Condensed','#fff','left',ease((t-0.6)/0.8));
  txt('El registro de GS1 Venezuela, 1993–2025',140,480,'400 28px Barlow','#C6D2EE','left',ease((t-1.2)/0.8));
}
function race(t,T){ // T = progreso 0..1 sobre los 33 años
  x.fillStyle='#fff';x.fillRect(0,0,1280,720);x.fillStyle=NAVY;x.fillRect(0,0,1280,92);
  const fy=T*(DATA.years.length-1),i0=Math.floor(fy),i1=Math.min(DATA.years.length-1,i0+1),f=fy-i0;
  const lerp=(arr)=>arr[i0]+(arr[i1]-arr[i0])*f;
  const year=1993+fy;txt('Códigos por sector y año',48,58,'bold 34px Barlow','#fff');
  txt(String(Math.round(year)),1232,720-40,'bold 150px Barlow Condensed','#E7ECF6','right');
  const vals=names.map((n)=>({n,v:lerp(DATA.sectors[n])})).sort((a,b)=>b.v-a.v);
  const max=vals[0].v*1.08, bx=330, bw=800, rh=38, y0=120;
  vals.forEach((r,k)=>{const y=y0+k*(rh+7);const w=Math.max(2,r.v/Math.max(max,1)*bw);
    x.fillStyle=COL[r.n];x.fillRect(bx,y,Math.min(w,bw),rh);
    txt(r.n,bx-14,y+26,'400 20px Barlow',NAVY,'right');txt(fmt(r.v),bx+Math.min(w,bw)+10,y+27,'bold 20px Barlow',NAVY,'left');});
  const tot=lerp(DATA.total),emp=lerp(DATA.emp);
  txt('Códigos del año: '+fmt(tot),48,690,'bold 30px Barlow',OR);txt('Empresas que codificaron: '+fmt(emp),48,660,'400 22px Barlow',NAVY);
  // subtítulo de eventos
  let cap='';CAP.forEach(([y,s])=>{if(Math.abs(year-y)<1.6)cap=s});
  if(cap){const k=Math.max(0,1-Math.abs(year-parseInt(cap))/1.6);txt(cap,48,118+10*(rh+7)+36,'bold 26px Barlow',OR,'left',ease(k*2))}
}
function outro(t){x.fillStyle=NAVY;x.fillRect(0,0,1280,720);
  const items=[['+1,6 M','códigos registrados'],['+3.500','empresas registradas'],['+30','años de historia'],['68.339','códigos en 2025']];
  items.forEach(([n,s],i)=>{const al=ease((t-0.3-i*0.5)/0.7);txt(n,140+i*260,165,'bold 78px Barlow Condensed','#fff','left',al);txt(s,140+i*260,205,'400 24px Barlow','#C6D2EE','left',al)});
  x.fillStyle=OR;x.fillRect(140,70,1000,4);
  const q=ease((t-3.5)/1.2);
  txt('«Lo que no se codifica, no se mide;',140,340,'italic 54px Georgia','#fff','left',q);
  txt('lo que no se mide no se controla.»',140,410,'italic 54px Georgia','#fff','left',ease((t-4.6)/1.2));
  txt('Adaptación de Lord Kelvin',140,462,'400 26px Barlow','#FFB59A','left',ease((t-6)/1));
  const fa=ease((t-7.5)/1);x.globalAlpha=fa;x.fillStyle='#fff';x.fillRect(140,540,210,92);x.drawImage(lg,150,548,190,76);x.globalAlpha=1;
  txt('gs1ve.org',380,592,'700 30px Barlow','#fff','left',fa);
}
window.draw=function(t){if(t<5)intro(t);else if(t<62){race(t,Math.min(1,(t-5)/57))}else outro(t-62)};
</script></body></html>`;
(async () => {
  const dir = fs.mkdtempSync(path.join(require('os').tmpdir(), 'film-'));
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
  await p.setContent(html); await p.waitForTimeout(600);
  const N = FPS * DUR;
  for (let i = 0; i < N; i++) {
    const d = await p.evaluate((t) => { window.draw(t); return document.getElementById('c').toDataURL('image/jpeg', 0.92); }, i / FPS);
    fs.writeFileSync(path.join(dir, 'f' + String(i).padStart(4, '0') + '.jpg'), Buffer.from(d.split(',')[1], 'base64'));
  }
  await b.close();
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(FPS), '-i', path.join(dir, 'f%04d.jpg'), '-c:v', 'libx264', '-preset', 'slow', '-crf', '27', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', OUT]);
  console.log('video:', OUT, (fs.statSync(OUT).size / 1e6).toFixed(2) + ' MB');
})();
