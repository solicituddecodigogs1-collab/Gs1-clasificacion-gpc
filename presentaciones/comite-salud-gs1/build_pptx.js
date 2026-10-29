const pptxgen=require('pptxgenjs'),sharp=require('sharp'),React=require('react'),RDS=require('react-dom/server'),LU=require('react-icons/lu');
const SK='/root/.claude/skills/synced/e17759f6-d5fa-40c2-941f-c3e91756f2fa_cf038d14-8b9f-4054-925d-160651d6e840/pptx/scripts/apply_theme.js';
const {applyTheme}=require(SK);
const OUT=process.argv[2];
process.env.LOGO_PNG=process.env.LOGO_PNG||'/tmp/claude-0/vendor/logo_poster.png';
const fs=require('fs');const b64=f=>'image/png;base64,'+fs.readFileSync(f).toString('base64');
const THEME={name:'GS1 Healthcare',headFontFace:'Arial',bodyFontFace:'Calibri',colors:{dk1:'0B132B',lt1:'FFFFFF',dk2:'002C6C',lt2:'F8FAFC',accent1:'1CA9C9',accent2:'F26334',accent3:'00A79D',accent4:'10B981',accent5:'EF4444',accent6:'0097B2',hlink:'0097B2',folHlink:'002C6C'}};
const H={navy:'002C6C',cyan:'1CA9C9',cyan2:'0097B2',orange:'F26334',teal:'00A79D',dark:'0B132B',ok:'10B981',bad:'EF4444',white:'FFFFFF'};
const pres=new pptxgen();pres.layout='LAYOUT_WIDE';pres.theme={headFontFace:THEME.headFontFace,bodyFontFace:THEME.bodyFontFace};
pres.title='COMITÉ Salud GS1';pres.author='GS1 Venezuela';pres.company='GS1 Venezuela';
const C=pres.SchemeColor;const col={navy:C.text2,cyan:C.accent1,orange:C.accent2,teal:C.accent3,ok:C.accent4,bad:C.accent5,cyan2:C.accent6,white:C.background1,dark:C.text1,bg:C.background2};
const p=v=>v/96;
/* ---------- SVG generators ---------- */
function rng(s){return function(){s|=0;s=s+0x6D2B79F5|0;let t=Math.imul(s^s>>>15,1|s);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296}}
function qrInner(seed,fg='#0B132B'){const n=29,r=rng(seed);let o='';const fin=(x,y)=>`<rect x="${x}" y="${y}" width="7" height="7" fill="${fg}"/><rect x="${x+1}" y="${y+1}" width="5" height="5" fill="#fff"/><rect x="${x+2}" y="${y+2}" width="3" height="3" fill="${fg}"/>`;
 for(let y=0;y<n;y++)for(let x=0;x<n;x++){if((x<9&&y<9)||(x>n-10&&y<9)||(x<9&&y>n-10))continue;if(r()>.52)o+=`<rect x="${x}" y="${y}" width="1.02" height="1.02" fill="${fg}"/>`}
 return{n,inner:o+fin(0,0)+fin(n-7,0)+fin(0,n-7)}}
function dmInner(seed){const n=22,r=rng(seed);let o='';for(let y=0;y<n;y++)for(let x=0;x<n;x++){let on;if(x===0||y===n-1)on=true;else if(y===0)on=x%2===0;else if(x===n-1)on=y%2===1;else on=r()>.5;if(on)o+=`<rect x="${x}" y="${y}" width="1.02" height="1.02" fill="#0B132B"/>`}return{n,inner:o}}
function eanInner(){let o='',x=0;const r=rng(7);while(x<92){const w=1+Math.floor(r()*3);if(r()>.4)o+=`<rect x="${x}" y="0" width="${w}" height="${(x<4||x>86||(x>44&&x<48))?58:50}" fill="#0B132B"/>`;x+=w+(r()>.5?1:0)}return{inner:o+`<text x="0" y="68" font-family="Courier New" font-size="9" font-weight="700" fill="#0B132B">7 591196 014853</text>`}}
const F='font-family="Arial, Helvetica, sans-serif"';
function boxSvg(kind,seed){let code;
 if(kind==='qr'){const q=qrInner(seed||5);code=`<svg x="116" y="112" width="48" height="48" viewBox="-1 -1 ${q.n+2} ${q.n+2}"><rect x="-1" y="-1" width="${q.n+2}" height="${q.n+2}" fill="#fff"/>${q.inner}</svg>`}
 else if(kind==='dm'){const q=dmInner(seed||9);code=`<svg x="116" y="112" width="48" height="48" viewBox="-1 -1 ${q.n+2} ${q.n+2}"><rect x="-1" y="-1" width="${q.n+2}" height="${q.n+2}" fill="#fff"/>${q.inner}</svg>`}
 else{const e=eanInner();code=`<rect x="100" y="116" width="66" height="46" rx="3" fill="#fff"/><svg x="104" y="119" width="58" height="40" viewBox="-2 -2 99 74">${e.inner}</svg>`}
 return`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 250 200" width="1000" height="800">
 <ellipse cx="125" cy="190" rx="105" ry="7" fill="#002C6C" opacity=".12"/>
 <polygon points="30,34 76,12 228,12 182,34" fill="#E8F7FB"/><polygon points="182,34 228,12 228,162 182,184" fill="#0097B2"/>
 <rect x="30" y="34" width="152" height="150" fill="#fff" stroke="#cbd5e1"/><rect x="30" y="34" width="152" height="22" fill="#002C6C"/>
 <text x="40" y="49" ${F} font-weight="800" font-size="10" fill="#fff">Rx · USO ORAL</text>
 <text x="40" y="78" ${F} font-weight="800" font-size="16" fill="#002C6C">Acetaminofén</text>
 <text x="40" y="102" ${F} font-weight="900" font-size="22" fill="#1CA9C9">500 mg</text>
 <text x="40" y="118" ${F} font-weight="600" font-size="9" fill="#475569">10 Tabletas</text>
 <rect x="30" y="170" width="152" height="5" fill="#F26334"/><rect x="40" y="130" width="46" height="20" rx="10" fill="#00A79D"/><text x="63" y="143" text-anchor="middle" ${F} font-weight="800" font-size="8" fill="#fff">GS1 VE</text>
 ${code}<text x="205" y="105" transform="rotate(-90 205 105)" ${F} font-weight="800" font-size="11" fill="#fff" text-anchor="middle">Acetaminofén 500 mg</text></svg>`}
function codeSvg(kind,seed,fg){let q,vb;if(kind==='qr'){q=qrInner(seed,fg);vb=`-2 -2 ${q.n+4} ${q.n+4}`}else{q=dmInner(seed);vb=`-1 -1 ${q.n+2} ${q.n+2}`}
 return`<svg xmlns="http://www.w3.org/2000/svg" viewBox="${vb}" width="800" height="800"><rect x="-2" y="-2" width="40" height="40" fill="#fff"/>${q.inner}</svg>`}
function logoSvg(dark,w=200,h=56){const t=dark?'#fff':'#002C6C';return`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 56" width="${w*4}" height="${h*4}"><circle cx="28" cy="28" r="27" fill="${dark?'#1CA9C9':'#002C6C'}"/><g fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round"><path d="M11 34C19 22 37 22 45 34"/><path d="M17 40C23 31 33 31 39 40"/><path d="M22 46C26 41 30 41 34 46"/></g><circle cx="28" cy="18" r="3.6" fill="#F26334"/><text x="64" y="30" ${F} font-weight="900" font-size="29" fill="${t}">GS1</text><text x="65" y="46" ${F} font-weight="800" font-size="14" fill="#F26334">Venezuela</text></svg>`}
const wavesCover=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="2560" height="1440"><path d="M760 0H1280V330C1160 290 1020 230 950 130C905 66 850 20 760 0Z" fill="#1CA9C9"/><path d="M900 0H1280V250C1180 225 1070 170 1015 100C985 62 945 20 900 0Z" fill="#002C6C"/><path d="M1280 720H760C880 650 1040 610 1280 585Z" fill="#1CA9C9"/><path d="M1280 720H900C990 680 1120 650 1280 640Z" fill="#002C6C"/></svg>`;
const wavesClose=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="2560" height="1440"><path d="M0 0H420C330 40 250 100 200 170C150 240 80 270 0 280Z" fill="#1CA9C9"/><path d="M0 0H300C230 30 160 80 120 130C80 180 40 200 0 205Z" fill="#002C6C"/><path d="M1280 720H760C880 650 1040 610 1280 585Z" fill="#1CA9C9"/><path d="M1280 720H900C990 680 1120 650 1280 640Z" fill="#002C6C"/></svg>`;
const wavesBottom=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 64" width="1200" height="256"><path d="M300 64H0C80 24 190 6 300 0Z" fill="#1CA9C9"/><path d="M300 64H110C170 38 230 24 300 20Z" fill="#002C6C"/></svg>`;
const wavesCorner=d=>`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 190 86" width="760" height="344"><path d="M190 0V86C140 70 100 40 80 0Z" fill="#1CA9C9" ${d?'fill-opacity=".55"':''}/><path d="M190 0V56C160 46 130 26 118 0Z" fill="${d?'#0097B2':'#002C6C'}"/></svg>`;
const bgDark=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1920" height="1080"><defs><radialGradient id="a" cx="12%" cy="8%" r="45%"><stop offset="0" stop-color="#1CA9C9" stop-opacity=".25"/><stop offset="1" stop-color="#1CA9C9" stop-opacity="0"/></radialGradient><radialGradient id="b" cx="92%" cy="95%" r="45%"><stop offset="0" stop-color="#F26334" stop-opacity=".18"/><stop offset="1" stop-color="#F26334" stop-opacity="0"/></radialGradient></defs><rect width="1280" height="720" fill="#0B132B"/><rect width="1280" height="720" fill="url(#a)"/><rect width="1280" height="720" fill="url(#b)"/></svg>`;
const png=async svg=>'image/png;base64,'+(await sharp(Buffer.from(svg),{density:96}).png().toBuffer()).toString('base64');
const iconCache={};
async function icon(name,color){const k=name+color;if(iconCache[k])return iconCache[k];const C_=LU['Lu'+name];if(!C_)throw new Error('icon '+name);
 const svg=RDS.renderToStaticMarkup(React.createElement(C_,{color:'#'+color,size:256}));return iconCache[k]='image/png;base64,'+(await sharp(Buffer.from(svg)).resize(256,256).png().toBuffer()).toString('base64')}

async function clampAdj(f){const JSZip=require('jszip');const z=await JSZip.loadAsync(fs.readFileSync(f));
 for(const n of Object.keys(z.files)){if(!/ppt\/(slides|slideLayouts|slideMasters)\/[^/]+\.xml$/.test(n))continue;let x=await z.file(n).async('string');
  const y=x.replace(/(prst="roundRect"><a:avLst><a:gd name="adj" fmla="val )(\d+)"/g,(m,a,v)=>a+Math.min(+v,50000)+'"');if(y!==x)z.file(n,y)}
 fs.writeFileSync(f,await z.generateAsync({type:'nodebuffer',compression:'DEFLATE'}))}
(async()=>{
const IMG={};
IMG.logoL=await png(logoSvg(false));IMG.logoD=await png(logoSvg(true));IMG.logoMiniL=await png(logoSvg(false));IMG.logoMiniD=await png(logoSvg(true));
if(process.env.LOGO_PNG){ // logo oficial: LOGO_PNG=/ruta/Logo-GS1.png
 const src=await sharp(process.env.LOGO_PNG).trim({threshold:45}).toBuffer();
 const fit=async(bg,pad,W=800,Hh=224)=>{const inner=await sharp(src).resize(W-pad*2,Hh-pad*2,{fit:'contain',background:{r:0,g:0,b:0,alpha:0}}).png().toBuffer();
  let img=sharp({create:{width:W,height:Hh,channels:4,background:bg}}).composite([{input:inner,gravity:'center'}]);
  if(pad){const m=Buffer.from(`<svg width="${W}" height="${Hh}"><rect width="${W}" height="${Hh}" rx="40" fill="#fff"/></svg>`);img=sharp(await img.png().toBuffer()).composite([{input:m,blend:'dest-in'}])}
  return 'image/png;base64,'+(await img.png().toBuffer()).toString('base64')};
 IMG.logoL=await fit({r:255,g:255,b:255,alpha:1},0,600,300);IMG.logoMiniL=await fit({r:248,g:250,b:252,alpha:1},0);
 IMG.logoD=IMG.logoMiniD=await fit({r:255,g:255,b:255,alpha:1},16);}
IMG.wCover=await png(wavesCover);IMG.wClose=await png(wavesClose);IMG.wCL=await png(wavesCorner(false));IMG.wCD=await png(wavesCorner(true));IMG.bgDark=await png(bgDark);IMG.wBot=await png(wavesBottom);
IMG.box={};for(const [k,s] of [['ean'],['qr',5],['dm',9]])IMG.box[k]=await png(boxSvg(k,s));
IMG.qrGray=await png(codeSvg('qr',5,'#6b7280'));IMG.qr=await png(codeSvg('qr',5));IMG.qr12=await png(codeSvg('qr',12));IMG.qrDm=await png(codeSvg('dm',9));

/* ---------- layouts ---------- */
const footer=(dark)=>[
 {image:{x:p(48),y:p(680),w:p(100),h:p(28),data:dark?IMG.logoMiniD:IMG.logoMiniL,altText:'Logo GS1 Venezuela'}},
 {text:{text:'Comité Salud GS1 · 5 Nov 2026 · www.gs1ve.org',options:{x:p(340),y:p(686),w:p(600),h:p(20),fontSize:9,color:dark?'94A3B8':'64748B',align:'center',margin:0}}},
 {image:{x:p(1090),y:0,w:p(190),h:p(86),data:dark?IMG.wCD:IMG.wCL,altText:'Onda decorativa'}},{image:{x:p(980),y:p(656),w:p(300),h:p(64),data:IMG.wBot,altText:'Onda decorativa'}}];
pres.defineSlideMaster({title:'GS1_CLARO',background:{color:'F8FAFC'},objects:[...footer(false),
 {placeholder:{options:{name:'title',type:'title',x:p(48),y:p(52),w:p(960),h:p(76),fontSize:26,align:'left',bold:true,color:C.text2,fontFace:'Arial',margin:0,valign:'top'},text:''}}],slideNumber:{x:p(1170),y:p(684),w:p(60),h:p(24),fontSize:10,bold:true,color:'FFFFFF',align:'right'}});
pres.defineSlideMaster({title:'GS1_OSCURO',background:{data:IMG.bgDark},objects:[...footer(true),
 {placeholder:{options:{name:'title',type:'title',x:p(48),y:p(52),w:p(1000),h:p(76),fontSize:26,align:'left',bold:true,color:C.background1,fontFace:'Arial',margin:0,valign:'top'},text:''}}],slideNumber:{x:p(1170),y:p(684),w:p(60),h:p(24),fontSize:10,bold:true,color:H.orange,align:'right'}});
pres.defineSlideMaster({title:'GS1_LIBRE',background:{color:'FFFFFF'},objects:[]});

/* ---------- helpers ---------- */
const shadow=()=>({type:'outer',color:'1E3A8A',opacity:.14,blur:14,offset:3,angle:90});
function T(s,t,x,y,w,h,o={}){s.addText(t,{x:p(x),y:p(y),w:p(w),h:p(h),fontSize:o.sz||11,bold:o.b,italic:o.i,color:o.c||col.dark,align:o.al||'left',valign:o.va||'top',margin:0,isTextBox:true,fontFace:o.mono?'Courier New':(o.h?'Arial':'Calibri'),charSpacing:o.cs,paraSpaceAfter:o.psa,lineSpacingMultiple:o.ls,objectName:o.name,rotate:o.rot,fit:'none'})}
function card(s,x,y,w,h,o={}){s.addShape(pres.ShapeType.roundRect,{x:p(x),y:p(y),w:p(w),h:p(h),rectRadius:o.r??.2,fill:{color:o.fill||col.white,transparency:o.tr},line:{color:o.line||'E2E8F0',width:o.lw||.75},shadow:o.noShadow?undefined:shadow(),objectName:o.name||'Tarjeta',rotate:o.rot})}
function dcard(s,x,y,w,h){s.addShape(pres.ShapeType.roundRect,{x:p(x),y:p(y),w:p(w),h:p(h),rectRadius:.18,fill:{color:'FFFFFF',transparency:92},line:{color:'FFFFFF',transparency:85,width:.75},objectName:'Tarjeta oscura'})}
function circle(s,x,y,d,fill,o={}){s.addShape(pres.ShapeType.ellipse,{x:p(x),y:p(y),w:p(d),h:p(d),fill:{color:fill,transparency:o.tr},line:o.line?{color:o.line,width:o.lw||1}:{type:'none'},shadow:o.sh?shadow():undefined,objectName:o.name||'Círculo'})}
function badge(s,x,y,d,fill,txt,sz,tc){circle(s,x,y,d,fill,{name:'Insignia '+txt});T(s,txt,x,y,d,d,{sz:sz||12,b:true,c:tc||col.white,al:'center',va:'middle',h:true})}
async function ic(s,name,color,x,y,sz){s.addImage({data:await icon(name,color),x:p(x),y:p(y),w:p(sz),h:p(sz),altText:'Icono '+name})}
async function ibadge(s,x,y,d,fill,name,ci='FFFFFF'){circle(s,x,y,d,fill,{name:'Icono '+name});await ic(s,name,ci,x+d*.24,y+d*.24,d*.52)}
function kicker(s,t,x=48,y=28,c){T(s,t.toUpperCase(),x,y,700,18,{sz:9,b:true,c:c||col.orange,cs:2})}
function title(s,runs){s.addText(runs,{placeholder:'title'})}
const R=(t,c,extra)=>({text:t,options:{color:c,...extra}});
async function photo(s,x,y,w,h,o={}){ // marcador de foto editable (clic derecho > Cambiar imagen no aplica; reemplazar por foto)
 s.addShape(o.circ?pres.ShapeType.ellipse:pres.ShapeType.roundRect,{x:p(x),y:p(y),w:p(w),h:p(h),rectRadius:o.circ?undefined:.35,fill:{color:o.fill||col.cyan2},line:{color:col.white,width:o.circ?5:3},shadow:shadow(),rotate:o.rot,objectName:'FOTO (reemplazar): '+(o.label||'imagen temática')});
 const sz=Math.min(w,h)*.38;await ic(s,o.icon||'HeartPulse','FFFFFF',x+w/2-sz/2,y+h/2-sz/2,sz);
 if(o.rot){/* el icono no rota */}
 T(s,'Insertar foto: '+(o.label||''),x+8,y+h-26,w-16,16,{sz:8,c:col.white,al:'center',name:'Etiqueta foto'})}
function pimg(s,f,x,y,w,h,rot,name){s.addImage({data:b64(f),x:p(x),y:p(y),w:p(w),h:p(h),rotate:rot,altText:name})}
function line(s,x1,y1,x2,y2,color,w=1,o={}){const dx=x2-x1,dy=y2-y1;s.addShape(pres.ShapeType.line,{x:p(Math.min(x1,x2)),y:p(Math.min(y1,y2)),w:p(Math.abs(dx)),h:p(Math.abs(dy)),flipV:dx*dy<0,line:{color,width:w,transparency:o.tr,dashType:o.dash}})}

function topRound(s,o){s.addShape(pres.ShapeType.roundRect,{...o,rectRadius:Math.min(o.rectRadius||.2,.5)});s.addShape(pres.ShapeType.rect,{x:o.x,y:o.y+o.h/2,w:o.w,h:o.h/2,fill:o.fill,line:{type:'none'},objectName:(o.objectName||'Forma')+' (base)'})}
function strip(s,x,y,w,c,h=8){topRound(s,{x:p(x),y:p(y),w:p(w),h:p(h),rectRadius:.5,fill:{color:c},line:{type:'none'},objectName:'Barra de color'})}
/* ===== 1 PORTADA ===== */
let s=pres.addSlide({masterName:'GS1_LIBRE'});
s.addImage({data:IMG.wCover,x:0,y:0,w:p(1280),h:p(720),altText:'Ondas corporativas'});
s.addImage({data:IMG.logoL,x:p(48),y:p(20),w:p(168),h:p(84),altText:'Logo GS1 Venezuela'});
T(s,'COMITÉ',56,108,620,100,{sz:69,b:true,c:col.navy,h:true,name:'Título'});
T(s,'Salud GS1',56,206,620,90,{sz:58,b:true,c:col.cyan,h:true});
const ag=[['BrainCircuit',H.navy,'Rastreo Inteligente: IA Aplicada a la Trazabilidad Médica.'],['ShieldPlus',H.cyan,'Seguridad del paciente, eficiencia de la cadena de suministro y trazabilidad de medicamentos.'],['Globe',H.navy,'Casos de Éxito Internacionales y Contexto Venezolano.'],['MessagesSquare',H.cyan,'GS1 News & Ronda Abierta.']];
for(let i=0;i<4;i++){const y=318+i*52;await ibadge(s,56,y,36,ag[i][1],ag[i][0]);T(s,[R(`${i+1}. `,col.orange,{bold:true}),R(ag[i][2],col.navy,{bold:true})],104,y-2,620,42,{sz:12,va:'middle'})}
card(s,56,574,670,112,{fill:col.cyan,line:H.cyan,r:.3});
await ic(s,'CalendarDays','FFFFFF',80,590,22);T(s,'5 Noviembre, 2026',110,588,200,26,{sz:16,b:true,c:col.white,h:true});
await ic(s,'Clock','FFFFFF',80,628,18);T(s,'8:30 am – 10:00 am',110,626,200,22,{sz:12,b:true,c:col.white});
line(s,330,592,330,668,'FFFFFF',1,{tr:50});
await ic(s,'MapPin','FFFFFF',350,594,22);T(s,[R('Oficina GS1 Venezuela. ',col.white,{bold:true}),R('Los Ruices, Calle Los Laboratorios, Edf. Quorum, Piso 1, Oficina K (Caracas).',col.white)],380,590,330,78,{sz:11,va:'middle'});
pimg(s,'/tmp/claude-0/vendor/photo_capsula.png',835,150,276,446,6,'Médico y paciente');
pimg(s,'/tmp/claude-0/vendor/photo_circulo.png',730,318,250,250,0,'Médico con iconos de salud y protección');
circle(s,935,285,58,col.white,{line:H.cyan,lw:3,sh:true});T(s,'+',935,285,58,58,{sz:34,b:true,c:col.cyan,al:'center',va:'middle'});
await ibadge(s,1090,130,48,col.ok,'ShieldCheck');
await ic(s,'Phone','FFFFFF',1010,664,16);T(s,'+58 414 2771877',1032,662,200,20,{sz:11,b:true,c:col.white});
await ic(s,'Globe','FFFFFF',1010,688,16);T(s,'www.gs1ve.org',1032,686,200,20,{sz:11,b:true,c:col.white});
s.addNotes('Portada. Reemplazar los marcadores de foto (cápsula y círculo) por fotos de atención médica.');

/* ===== A AGENDA ===== */
s=pres.addSlide({masterName:'GS1_CLARO'});
kicker(s,'Comité Salud GS1 · 5 Noviembre 2026');title(s,[R('Agenda ',col.navy),R('de hoy',col.cyan)]);
const agn=[['BrainCircuit',col.navy,H.navy,'Rastreo Inteligente','IA aplicada a la trazabilidad médica',['Datos estándar + IA','Predicción, visión artificial y anomalías']],['ShieldPlus',col.cyan,H.cyan,'Seguridad, cadena y trazabilidad','Pacientes, suministro y medicamentos',['Los 5 Correctos (BCMA)','Eficiencia de la cadena','De EAN-13 a 2D: DataMatrix y QR GS1','Casos de éxito']],['Newspaper',col.teal,H.teal,'GS1 News','Novedades y hoja de ruta',['Sunrise 2027','GS1 Digital Link Latam','EPCIS 2.0']],['MessagesSquare',col.orange,H.orange,'Ronda Abierta','Mesa de trabajo del Comité',['Retos de implementación','Integración y educación','Próximos pilotos']]];
for(let i=0;i<4;i++){const x=48+i*301.33,a=agn[i];card(s,x,135,280,370);strip(s,x+14,135,252,a[1]);badge(s,x+20,160,40,a[1],String(i+1),14);await ibadge(s,x+210,158,48,a[1],a[0]);
 T(s,a[3],x+20,222,244,50,{sz:15,b:true,c:col.navy,h:true});T(s,a[4],x+20,276,244,34,{sz:11,i:true,c:'64748B'});
 a[5].forEach((b,j)=>{circle(s,x+22,326+j*44+5,8,a[1],{name:'Viñeta'});T(s,b,x+40,322+j*44,224,40,{sz:11.5,c:'334155'})})}
s.addShape(pres.ShapeType.roundRect,{x:p(48),y:p(525),w:p(1184),h:p(84),rectRadius:.3,fill:{color:col.navy},line:{type:'none'},objectName:'Barra informativa'});
await ic(s,'CalendarDays',H.cyan,76,553,26);T(s,'5 Noviembre, 2026 · 8:30 am – 10:00 am',112,550,380,32,{sz:13,b:true,c:col.white,va:'middle',h:true});
line(s,512,552,512,584,'FFFFFF',1,{tr:60});await ic(s,'MapPin',H.orange,536,553,26);T(s,'Oficina GS1 Venezuela · Los Ruices, Calle Los Laboratorios, Edf. Quorum, Piso 1, Oficina K (Caracas)',572,545,640,44,{sz:11.5,b:true,c:col.white,va:'middle'});

/* ===== B CONTEXTO ===== */
s=pres.addSlide({masterName:'GS1_CLARO'});
kicker(s,'Contexto venezolano · El nuevo paciente');title(s,[R('Información, confianza y ',col.navy),R('verificación en cada empaque',col.cyan)]);
for(const [i,v,clr,hex,txt] of [[0,41,H.orange,H.orange,'No escanea códigos estáticos que no aportan información útil.'],[1,80,H.cyan,H.cyan,'Está dispuesto a escanear para conocer origen, registro sanitario y autenticidad.']]){
 const y=140+i*245;card(s,48,y,300,225,{line:hex,lw:1.5});
 s.addChart(pres.charts.DOUGHNUT,[{name:'%',labels:['Sí','No'],values:[v,100-v]}],{x:p(148),y:p(y+8),w:p(100),h:p(100),holeSize:68,chartColors:[clr,'E2E8F0'],showLegend:false,showTitle:false,showValue:false,showPercent:false,showLabel:false,dataBorder:{pt:0,color:'FFFFFF'}});
 T(s,v+'%',48,y+106,300,60,{sz:42,b:true,c:i?col.cyan:col.orange,al:'center',h:true});T(s,txt,68,y+168,260,52,{sz:11,c:'475569',al:'center'})}
const vc=[['FileText',H.navy,'Información','Acceso al prospecto digital actualizado (e-PIL), posología y alertas sanitarias desde el móvil.'],['ShieldCheck',H.orange,'Confianza','Protección frente a medicamentos ilícitos, contrabando o sin registro sanitario (SACS / INHRR) en el mercado nacional.'],['Network',H.cyan,'Experiencia','Transparencia total entre laboratorio, droguería, farmacia, médico y paciente.']];
for(let i=0;i<3;i++){const y=140+i*160;card(s,376,y,560,145);await ibadge(s,396,y+22,56,vc[i][1],vc[i][0]);T(s,vc[i][2],472,y+22,440,26,{sz:15,b:true,c:col.navy,h:true});T(s,vc[i][3],472,y+54,440,84,{sz:12,c:'475569'})}
await photo(s,970,150,240,420,{rot:4,icon:'Smartphone',label:'farmacéutica / paciente escaneando',fill:col.navy});
await ibadge(s,940,140,56,col.orange,'ScanLine');

/* ===== C IA DATO ===== */
s=pres.addSlide({masterName:'GS1_CLARO'});
kicker(s,'Agenda · Punto 1');title(s,[R('Rastreo Inteligente: ',col.navy),R('la IA parte del dato estándar',col.cyan)]);
T(s,'Los algoritmos de IA son tan buenos como la calidad de los datos estándar que los alimentan.',48,114,1000,24,{sz:12.5,i:true,c:'475569'});
const c3=[['Database',col.navy,H.navy,'1 · Datos estándar GS1','Identificadores únicos y universales',[['GTIN','qué producto'],['GLN','dónde / ubicación'],['Lote/Serie','qué unidad'],['SSCC','qué envío']]],['Radar',col.cyan,H.cyan2,'2 · Eventos EPCIS 2.0','Cada movimiento queda registrado',[['QUÉ','producto y cantidad'],['DÓNDE','ubicación GLN'],['CUÁNDO','fecha y hora'],['POR QUÉ','recepción, despacho, dispensación']]],['Cpu',col.teal,H.teal,'3 · Inteligencia Artificial','Modelos sobre datos confiables',[['Predicción','demanda y escasez'],['Visión','verificación de códigos 2D'],['Anomalías','desvíos y cadena de frío']]]];
for(let i=0;i<3;i++){const x=48+i*420,c=c3[i];card(s,x,160,344,350);topRound(s,{x:p(x),y:p(160),w:p(344),h:p(76),rectRadius:.18,fill:{color:c[1]},line:{type:'none'},objectName:'Cabecero'});
 await ic(s,c[0],'FFFFFF',x+18,176,26);T(s,c[3],x+52,174,280,28,{sz:13.5,b:true,c:col.white,h:true,va:'middle'});T(s,c[4],x+18,206,310,22,{sz:10.5,c:col.white});
 c[5].forEach((r,j)=>{const y=252+j*60;s.addShape(pres.ShapeType.roundRect,{x:p(x+16),y:p(y),w:p(312),h:p(50),rectRadius:.12,fill:{color:'F4F8FB'},line:{type:'none'},objectName:'Dato '+r[0]});T(s,r[0],x+26,y,100,50,{sz:10.5,b:true,c:c[2]==='0097B2'?col.cyan2:(i?col.teal:col.navy),mono:true,va:'middle'});T(s,r[1],x+128,y,196,50,{sz:11,c:'334155',va:'middle'})});
 if(i<2)s.addShape(pres.ShapeType.rightArrow,{x:p(x+354),y:p(320),w:p(56),h:p(32),fill:{color:col.cyan},line:{type:'none'},objectName:'Flecha'})}
s.addShape(pres.ShapeType.roundRect,{x:p(48),y:p(534),w:p(1184),h:p(84),rectRadius:.2,fill:{color:'FFF7ED'},line:{color:col.orange,width:1.5},objectName:'Alerta'});
await ic(s,'TriangleAlert',H.orange,74,562,30);T(s,[R('Sin estándar, no hay IA confiable: ',col.orange,{bold:true}),R('códigos genéricos, datos incompletos o duplicados producen predicciones y alertas poco fiables.',col.dark)],120,538,1090,76,{sz:13,va:'middle'});

/* ===== D TRES USOS ===== */
s=pres.addSlide({masterName:'GS1_CLARO'});
kicker(s,'Agenda · Punto 1');title(s,[R('Tres usos de la ',col.navy),R('IA + GS1 en salud',col.cyan)]);
const us=[['ChartLine',col.cyan,H.cyan,'Modelos predictivos de demanda','Anticipan la escasez de insumos críticos y reactivos en clínicas y hospitales venezolanos.'],['ScanEye',col.teal,H.teal,'Visión artificial en líneas de empaque','Verificación a alta velocidad de GS1 DataMatrix y QR GS1 Digital Link en plantas farmacéuticas.'],['Snowflake',col.orange,H.orange,'Detección de anomalías con Machine Learning','Alerta temprana de desvíos a canales irregulares y rupturas de cadena de frío (insulinas, vacunas, biológicos).']];
for(let i=0;i<3;i++){const y=140+i*156;card(s,48,y,600,142,{line:us[i][2],lw:1.5});await ibadge(s,68,y+24,56,us[i][2],us[i][0]);T(s,us[i][3],144,y+22,480,26,{sz:13.5,b:true,c:col.navy,h:true});T(s,us[i][4],144,y+54,480,84,{sz:12,c:'475569'})}
await photo(s,680,140,552,222,{icon:'Warehouse',label:'cadena de suministro farmacéutica',fill:col.cyan2});
[['GTIN',H.orange,704],['GLN',H.cyan,790],['EPCIS',H.teal,864]].forEach(([t,c,x],i)=>{s.addShape(pres.ShapeType.roundRect,{x:p(x),y:p(312),w:p(i==2?76:64),h:p(28),rectRadius:.5,fill:{color:c},line:{type:'none'},objectName:'Badge '+t});T(s,t,x,312,i==2?76:64,28,{sz:10.5,b:true,c:col.white,al:'center',va:'middle',mono:true})});
s.addShape(pres.ShapeType.rightArrow,{x:p(770),y:p(318),w:p(16),h:p(16),fill:{color:col.white},line:{type:'none'}});s.addShape(pres.ShapeType.rightArrow,{x:p(848),y:p(318),w:p(14),h:p(16),fill:{color:col.white},line:{type:'none'}});
card(s,680,384,552,172,{line:H.navy,lw:1.5});T(s,'IMPACTO DIRECTO EN VENEZUELA',702,398,400,16,{sz:9,b:true,c:col.orange,cs:2});
await ic(s,'Route',H.cyan,702,430,22);T(s,'Optimización de rutas logísticas entre laboratorios nacionales, droguerías y farmacias en todo el país.',736,428,478,48,{sz:11.5,c:col.dark});
await ic(s,'Hourglass',H.cyan,702,494,22);T(s,[R('Gestión de vencimientos ',col.dark),R('FEFO',col.orange,{bold:true}),R(' (First Expired, First Out): menos mermas financieras por caducidad.',col.dark)],736,492,478,50,{sz:11.5});

/* ===== E BCMA ===== */
s=pres.addSlide({masterName:'GS1_CLARO'});
kicker(s,'Agenda · Punto 2');title(s,[R('Seguridad del paciente: los ',col.navy),R('5 Correctos',col.cyan),R(' (BCMA)',col.navy)]);
T(s,'Escaneo a pie de cama — Bedside Barcode Medication Administration',48,112,800,20,{sz:11,i:true,c:'64748B'});
pimg(s,'/tmp/claude-0/vendor/photo_capsula.png',60,160,250,404,-5,'Médico sosteniendo la mano del paciente');
pimg(s,'/tmp/claude-0/vendor/photo_circulo.png',170,430,200,200,0,'Médico con iconos de salud');
await ibadge(s,76,140,56,col.ok,'ShieldCheck');
const fc=[['1',col.navy,H.navy,'Paciente correcto','Escaneo del código GS1 del brazalete de identificación hospitalaria.','GSRN'],['2',col.cyan,H.cyan,'Medicamento correcto','Validación instantánea del GTIN contra la prescripción médica electrónica.','GTIN'],['3',col.teal,H.teal,'Dosis correcta','Confirma la concentración (500 mg vs 1000 mg) y evita errores LASA (Look-Alike, Sound-Alike).','LASA'],['4',col.navy,H.navy,'Vía y hora correctas','Registro automático en la Historia Clínica Electrónica.','HCE'],['5',col.orange,H.orange,'Vigencia garantizada','El sistema bloquea la dosis si (17) indica vencido o si el lote (10) tiene alerta de retiro.','BLOQUEO ACTIVO']];
for(let i=0;i<5;i++){const y=160+i*92,f=fc[i];card(s,400,y,832,80,{line:i===4?H.orange:'E2E8F0',lw:i===4?1.5:.75});badge(s,420,y+17,46,f[1],f[0],14);T(s,f[3],486,y+10,560,22,{sz:13.5,b:true,c:col.navy,h:true});T(s,f[4],486,y+36,600,40,{sz:11,c:'475569'});
 const w=i===4?140:88;s.addShape(pres.ShapeType.roundRect,{x:p(1212-w),y:p(y+26),w:p(w),h:p(28),rectRadius:.5,fill:{color:f[1]},line:{type:'none'},objectName:'Etiqueta '+f[5]});T(s,f[5],1212-w,y+26,w,28,{sz:9.5,b:true,c:col.white,al:'center',va:'middle',mono:true})}

/* ===== F CADENA ===== */
s=pres.addSlide({masterName:'GS1_CLARO'});
kicker(s,'Agenda · Punto 2');title(s,[R('Eficiencia de la ',col.navy),R('cadena de suministro',col.cyan)]);
T(s,'Un mismo lenguaje GS1 desde el laboratorio hasta el paciente en Venezuela',48,112,800,20,{sz:11,i:true,c:'64748B'});
const nd2=[['Factory',col.navy,H.navy,'Laboratorio','GTIN · Lote · Serie'],['Truck',col.cyan,H.cyan,'Droguería / Distribuidor','SSCC · GLN'],['Store',col.teal,H.teal,'Farmacia / Clínica','GTIN · GLN'],['User',col.orange,H.orange,'Paciente','GSRN · e-PIL']];
for(let i=0;i<4;i++){const cx=48+i*301.33,mid=cx+140;circle(s,mid-46,150,92,nd2[i][1],{line:'FFFFFF',lw:4,sh:true,name:'Nodo '+nd2[i][3]});await ic(s,nd2[i][0],'FFFFFF',mid-22,172,44);
 T(s,nd2[i][3],cx,254,280,24,{sz:13,b:true,c:col.navy,al:'center',h:true});s.addShape(pres.ShapeType.roundRect,{x:p(mid-100),y:p(284),w:p(200),h:p(30),rectRadius:.5,fill:{color:'E0F4F9'},line:{type:'none'},objectName:'Claves GS1'});T(s,nd2[i][4],mid-100,284,200,30,{sz:10.5,b:true,c:col.cyan2,al:'center',va:'middle',mono:true});
 if(i<3)s.addShape(pres.ShapeType.chevron,{x:p(mid+70),y:p(176),w:p(36),h:p(40),fill:{color:col.cyan},line:{type:'none'},objectName:'Flecha flujo'})}
const bn=[['Eye',col.cyan,H.cyan,'Visibilidad en tiempo real','Cada movimiento se registra con EPCIS 2.0 y es consultable por los socios autorizados.'],['Hourglass',col.orange,H.orange,'Vencimientos FEFO','Se despacha primero lo que vence primero, con lote y fecha leídos del código.'],['Undo2',col.teal,H.teal,'Retiro de lotes ágil','Un recall se ubica por lote y GLN en minutos, sin revisar inventario caja por caja.'],['Snowflake',col.navy,H.navy,'Cadena de frío','Alertas ante desvíos de temperatura en insulinas, vacunas y biológicos.']];
for(let i=0;i<4;i++){const x=48+i*301.33;card(s,x,350,280,250);strip(s,x+14,350,252,bn[i][1]);await ibadge(s,x+20,376,48,bn[i][2],bn[i][0]);T(s,bn[i][3],x+20,438,244,44,{sz:13,b:true,c:col.navy,h:true});T(s,bn[i][4],x+20,486,244,104,{sz:11,c:'475569'})}
/* ===== 5 ANATOMÍA ===== */
s=pres.addSlide({masterName:'GS1_CLARO'});
kicker(s,'Agenda · Punto 2 · Trazabilidad de medicamentos');title(s,[R('De la barra tradicional al ',col.navy),R('estándar 2D en salud',col.cyan)]);
const ev=[['1973 – 2022 · Hasta ahora','F1F5F9','475569',['ean'],'EAN-13 · código 1D','Solo identifica el GTIN, de forma estática.'],['2023 – 2026 · Transición dual','FDE9E2',H.orange,['ean','qr'],'Coexisten 1D + 2D','Se preparan lectores ópticos en farmacias y centros de salud.'],['2027+ · Ambición global y Healthcare',H.cyan,'FFFFFF',['dm','qr'],'GS1 DataMatrix + QR Digital Link','Trazabilidad clínica/regulatoria + interacción con el paciente.']];
for(let i=0;i<3;i++){const x=48+i*404,e=ev[i];card(s,x,130,372,262,{line:i===2?H.cyan:'E2E8F0',lw:i===2?1.5:.75});
 s.addShape(pres.ShapeType.roundRect,{x:p(x+36),y:p(144),w:p(300),h:p(26),rectRadius:.5,fill:{color:e[1]},line:{type:'none'},objectName:'Etapa'});T(s,e[0],x+36,144,300,26,{sz:10,b:true,c:e[2]===H.orange?col.orange:(e[2]==='FFFFFF'?col.white:e[2]),al:'center',va:'middle'});
 if(e[3].length===1)s.addImage({data:IMG.box[e[3][0]],x:p(x+86),y:p(176),w:p(200),h:p(160),altText:'Caja Acetaminofén 500 mg'});
 else e[3].forEach((k,j)=>s.addImage({data:IMG.box[k],x:p(x+16+j*172),y:p(188),w:p(172),h:p(138),altText:'Caja Acetaminofén 500 mg'}));
 T(s,e[4],x+10,338,352,20,{sz:12,b:true,c:col.navy,al:'center',h:true});T(s,e[5],x+16,360,340,28,{sz:10,c:'475569',al:'center'})}
for(const x of [424,828])s.addShape(pres.ShapeType.rightArrow,{x:p(x),y:p(248),w:p(26),h:p(26),fill:{color:col.orange},line:{type:'none'},objectName:'Flecha'});
const ai=[['(01)','07591196014853','GTIN','ID único del medicamento (prefijo 759 GS1 Venezuela)'],['(17)','281231','Vencimiento','31 Dic 2028'],['(10)','LOTE-VE26','Lote','trazabilidad de producción'],['(21)','SN998877','Serie','autenticación unitaria anti-falsificación']];
for(let i=0;i<4;i++){const x=48+i*301.33;card(s,x,412,280,92);T(s,[R(ai[i][0]+' ',col.orange,{bold:true}),R(ai[i][1],col.navy,{bold:true})],x+14,422,256,24,{sz:13,mono:true});T(s,[R(ai[i][2]+' · ',col.navy,{bold:true}),R(ai[i][3],'475569')],x+14,450,254,50,{sz:10.5})}
T(s,'ESTRUCTURA GS1 DIGITAL LINK',48,520,400,16,{sz:9,b:true,c:'64748B',cs:2});
card(s,48,542,1184,60);
T(s,[R('https://','94A3B8'),R('dl.gs1ve.org',col.teal),R('/01/',col.orange),R('07591196014853',col.navy),R('/10/',col.orange),R('LOTE-VE26',col.navy),R('?17=',col.orange),R('281231',col.navy)],72,542,1136,60,{sz:15.5,b:true,mono:true,va:'middle'});
T(s,[R('● Dominio web     ',col.teal,{bold:true}),R('● Identificador de aplicación (AI)     ',col.orange,{bold:true}),R('● GTIN / Lote / Vencimiento',col.navy,{bold:true})],48,612,900,18,{sz:10});

/* ===== G CASOS ===== */
s=pres.addSlide({masterName:'GS1_CLARO'});
kicker(s,'Evidencia internacional · GS1 Healthcare');title(s,[R('Casos de éxito: ',col.navy),R('impacto real en hospitales y regulación',col.cyan)]);
const cs=[['Hospital',H.navy,'Reino Unido · NHS','Proyecto Scan4Safety','GTIN · GLN · GSRN','Adopción en hospitales públicos británicos.'],['Pill',H.cyan2,'Argentina (ANMAT) y Brasil','ANVISA · Sírio-Libanês · Einstein','GS1 DataMatrix','Trazabilidad unitaria de medicamentos oncológicos y de alto costo.'],['ScanLine',H.teal,'Unión Europea (FMD) y Colombia','Sincronización GDSN','DataMatrix · e-PIL · Digital Link','Verificación serializada punto a punto y prospecto electrónico (e-PIL) mediante GS1 Digital Link.']];
for(let i=0;i<3;i++){const x=48+i*402,c=cs[i];card(s,x,125,378,500);
 topRound(s,{x:p(x),y:p(125),w:p(378),h:p(130),rectRadius:.18,fill:{color:c[1]},line:{type:'none'},objectName:'FOTO (reemplazar): '+c[2]});await ic(s,c[0],'FFFFFF',x+169,163,40);T(s,'Insertar foto',x+10,232,358,16,{sz:8,c:col.white,al:'center'});
 T(s,c[2],x+20,268,340,24,{sz:14,b:true,c:col.navy,h:true});T(s,c[3],x+20,294,340,20,{sz:11.5,b:true,c:col.cyan});T(s,c[4],x+20,322,340,18,{sz:10,b:true,c:col.orange,mono:true});T(s,c[5],x+20,346,340,46,{sz:11,c:'475569'});}
// metricas
{const x=48;for(let j=0;j<3;j++){const m=[['76%','menos errores de medicación'],['+140,000','horas clínicas liberadas'],['<30 min','para ubicar lotes (recall)']][j];const bx=x+20+j*114;card(s,bx,404,106,120,{fill:col.bg,noShadow:true,r:.15});T(s,m[0],bx,416,106,40,{sz:j?15:24,b:true,c:col.orange,al:'center',va:'middle',h:true});T(s,m[1],bx+6,462,94,56,{sz:9.5,c:'475569',al:'center'})}}
T(s,'99.9%',450+20,404,340,64,{sz:44,b:true,c:col.orange,h:true});T(s,'de precisión en dispensación intrahospitalaria',470,470,340,36,{sz:11,b:true,c:'475569'});
card(s,470,520,338,82,{fill:'E6F8F1',line:'E6F8F1',noShadow:true,r:.15});await ic(s,'ShieldCheck',H.ok,484,546,24);T(s,'Erradicación de fármacos falsificados en el canal formal.',518,524,280,74,{sz:10.5,b:true,c:'047857',va:'middle'});
T(s,'−40%',852+20,404,340,64,{sz:44,b:true,c:col.orange,h:true});T(s,'de errores de catalogación entre laboratorios y clínicas',872,470,340,40,{sz:11,b:true,c:'475569'});

/* ===== H NEWS ===== */
s=pres.addSlide({masterName:'GS1_CLARO'});
kicker(s,'Agenda · Punto 3 · GS1 News');title(s,[R('Novedades globales y ',col.navy),R('hoja de ruta 2026–2027',col.cyan)]);
s.addImage({data:IMG.logoD,x:p(1080),y:p(14),w:p(160),h:p(45),altText:'Logo GS1 Venezuela'});
const nw=[['Sunrise',H.orange,'Rumbo a GS1 Sunrise 2027','Puntos de venta y farmacias avanzan hacia la lectura nativa de códigos 2D.'],['QrCode',H.cyan,'Plataforma GS1 Digital Link Latam',''],['Share2',H.teal,'EPCIS 2.0 e interoperabilidad con IA','Nuevo estándar global para compartir eventos de visibilidad en cadenas de suministro de salud con máxima ciberseguridad.'],['GraduationCap',H.navy,'Formación y acompañamiento técnico','Consultoría del Departamento de Estándares de GS1 Venezuela para adecuar líneas de empaque, asignación de GLN/GTIN y catalogación.']];
for(let i=0;i<4;i++){const x=48+(i%2)*604,y=135+Math.floor(i/2)*250,n=nw[i];card(s,x,y,580,232);await ibadge(s,x+24,y+24,64,n[1],n[0]);T(s,n[2],x+108,y+24,450,28,{sz:15,b:true,c:col.navy,h:true});
 if(i===0){T(s,'2027',x+108,y+58,130,50,{sz:36,b:true,c:col.cyan,h:true});T(s,'año meta de GS1 Sunrise (pilotos en 48 países / 88% del PIB mundial)',x+240,y+62,320,44,{sz:11,c:'475569',va:'middle'});T(s,n[3],x+108,y+118,450,90,{sz:12.5,c:'475569'})}
 else if(i===1){T(s,[R('Disponible para afiliados de GS1 Venezuela en ',col.dark),R('app.gs1digitallink.lat',col.cyan2,{bold:true}),R('. Exportación de arte tanto para QR Digital Link como GS1 DataMatrix:',col.dark)],x+108,y+58,450,70,{sz:12.5});
  ['SVG','PNG','PDF','EPS'].forEach((f,j)=>{s.addShape(pres.ShapeType.roundRect,{x:p(x+108+j*70),y:p(y+150),w:p(60),h:p(30),rectRadius:.12,fill:{color:'E0F4F9'},line:{type:'none'},objectName:'Formato '+f});T(s,f,x+108+j*70,y+150,60,30,{sz:10.5,b:true,c:col.cyan2,al:'center',va:'middle',mono:true})})}
 else T(s,n[3],x+108,y+62,450,150,{sz:12.5,c:'475569'})}

/* ===== I RONDA ===== */
s=pres.addSlide({masterName:'GS1_CLARO'});
kicker(s,'Agenda · Punto 4 · Mesa de trabajo del Comité');title(s,[R('Ronda ',col.navy),R('Abierta',col.cyan)]);
await photo(s,60,140,360,440,{rot:-3,icon:'Users',label:'mesa de trabajo del comité',fill:col.cyan2});
s.addShape(pres.ShapeType.roundRect,{x:p(86),y:p(548),w:p(250),h:p(34),rectRadius:.5,fill:{color:col.navy},line:{type:'none'},objectName:'Etiqueta comité'});T(s,'Comité Salud GS1 · 5 Nov 2026',86,548,250,34,{sz:10.5,b:true,c:col.white,al:'center',va:'middle'});
const dq=[[col.navy,'Retos en empaque primario y secundario','Líneas de impresión para códigos 2D variables (lote / vencimiento).'],[col.cyan,'Integración con farmacias y clínicas','Homologación de lectores ópticos 2D y sistemas ERP / HIS en Venezuela.'],[col.orange,'Educación al médico y al paciente','Estrategias conjuntas para impulsar el escaneo de autenticidad y prospecto digital.'],[col.teal,'Próximos pilotos 2026–2027','Definición de las mesas técnicas de trabajo del Comité Salud.']];
for(let i=0;i<4;i++){const y=140+i*120;card(s,470,y,762,104);badge(s,492,y+26,52,dq[i][0],String(i+1),18);T(s,dq[i][1],566,y+18,640,26,{sz:14,b:true,c:col.navy,h:true});T(s,dq[i][2],566,y+50,640,48,{sz:12,c:'475569'})}
/* ===== 12 CIERRE ===== */
s=pres.addSlide({masterName:'GS1_LIBRE'});
s.addImage({data:IMG.wClose,x:0,y:0,w:p(1280),h:p(720),altText:'Ondas corporativas'});
s.addImage({data:IMG.logoL,x:p(512),y:p(20),w:p(168),h:p(84),altText:'Logo GS1 Venezuela'});
T(s,[R('Únete al ',col.navy),R('Comité Salud GS1',col.cyan)],520,104,720,56,{sz:33,b:true,h:true,name:'Título'});
T(s,'Solicita tu acceso a la plataforma Digital Link.',520,164,700,22,{sz:12.5,c:'475569'});
card(s,130,250,300,300,{r:.25});s.addImage({data:IMG.qr12,x:p(154),y:p(274),w:p(252),h:p(252),altText:'Código QR ilustrativo'});
for(const [cx,cy,sx,sy,c] of [[118,238,1,1,H.navy],[442,238,-1,1,H.cyan],[118,562,1,-1,H.cyan],[442,562,-1,-1,H.navy]]){line(s,cx,cy,cx+sx*44,cy,c,5);line(s,cx,cy,cx,cy+sy*44,c,5)}
T(s,'ESCANEA · SOLICITA ACCESO',130,584,300,16,{sz:9,b:true,c:col.orange,al:'center',cs:2});
const ct=[['MapPin',[R('Oficina GS1 Venezuela. ',col.dark,{bold:true}),R('Los Ruices, Calle Los Laboratorios, Edf. Quorum, Piso 1, Oficina K, Caracas, Venezuela.',col.dark)],58,false],['Phone','+58 414-2771877  /  +58 412-628-3276',44,true],['Mail','Solicituddecodigo@gs1ve.org\nGlabrador@gs1ve.org · Acastro@gs1ve.org',66,true],['Globe','www.gs1ve.org  ·  Instagram @GS1Venezuela  ·  RIF J-00336360-0',44,false]];
let cy=214;for(const [ico,txt,h,mono] of ct){card(s,520,cy,712,h,{r:.3});await ic(s,ico,H.orange,540,cy+h/2-11,22);T(s,txt,576,cy,640,h,{sz:mono?11:11.5,b:ico!=='MapPin',va:'middle',mono,c:col.dark});cy+=h+14}
T(s,[R('Datos estándar, ',col.navy),R('decisiones seguras.',col.orange)],520,540,500,34,{sz:17,b:true,h:true});
await pres.writeFile({fileName:OUT});await applyTheme(OUT,THEME);await clampAdj(OUT);console.log('ok');
})().catch(e=>{console.error(e);process.exit(1)});
