const pptxgen=require('pptxgenjs'),sharp=require('sharp'),React=require('react'),RDS=require('react-dom/server'),LU=require('react-icons/lu');
const SK='/root/.claude/skills/synced/e17759f6-d5fa-40c2-941f-c3e91756f2fa_cf038d14-8b9f-4054-925d-160651d6e840/pptx/scripts/apply_theme.js';
const {applyTheme}=require(SK);
const OUT=process.argv[2];
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
const wavesCorner=d=>`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 190 86" width="760" height="344"><path d="M190 0V86C140 70 100 40 80 0Z" fill="#1CA9C9" ${d?'fill-opacity=".55"':''}/><path d="M190 0V56C160 46 130 26 118 0Z" fill="${d?'#0097B2':'#002C6C'}"/></svg>`;
const bgDark=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1920" height="1080"><defs><radialGradient id="a" cx="12%" cy="8%" r="45%"><stop offset="0" stop-color="#1CA9C9" stop-opacity=".25"/><stop offset="1" stop-color="#1CA9C9" stop-opacity="0"/></radialGradient><radialGradient id="b" cx="92%" cy="95%" r="45%"><stop offset="0" stop-color="#F26334" stop-opacity=".18"/><stop offset="1" stop-color="#F26334" stop-opacity="0"/></radialGradient></defs><rect width="1280" height="720" fill="#0B132B"/><rect width="1280" height="720" fill="url(#a)"/><rect width="1280" height="720" fill="url(#b)"/></svg>`;
const png=async svg=>'image/png;base64,'+(await sharp(Buffer.from(svg),{density:96}).png().toBuffer()).toString('base64');
const iconCache={};
async function icon(name,color){const k=name+color;if(iconCache[k])return iconCache[k];const C_=LU['Lu'+name];if(!C_)throw new Error('icon '+name);
 const svg=RDS.renderToStaticMarkup(React.createElement(C_,{color:'#'+color,size:256}));return iconCache[k]='image/png;base64,'+(await sharp(Buffer.from(svg)).resize(256,256).png().toBuffer()).toString('base64')}

(async()=>{
const IMG={};
IMG.logoL=await png(logoSvg(false));IMG.logoD=await png(logoSvg(true));IMG.logoMiniL=await png(logoSvg(false));IMG.logoMiniD=await png(logoSvg(true));
if(process.env.LOGO_PNG){ // logo oficial: LOGO_PNG=/ruta/Logo-GS1.png
 const src=await sharp(process.env.LOGO_PNG).trim().toBuffer();
 const fit=async(bg,pad)=>{const W=800,Hh=224;const inner=await sharp(src).resize(W-pad*2,Hh-pad*2,{fit:'contain',background:{r:0,g:0,b:0,alpha:0}}).png().toBuffer();
  let img=sharp({create:{width:W,height:Hh,channels:4,background:bg}}).composite([{input:inner,gravity:'center'}]);
  if(pad){const m=Buffer.from(`<svg width="${W}" height="${Hh}"><rect width="${W}" height="${Hh}" rx="40" fill="#fff"/></svg>`);img=sharp(await img.png().toBuffer()).composite([{input:m,blend:'dest-in'}])}
  return 'image/png;base64,'+(await img.png().toBuffer()).toString('base64')};
 IMG.logoL=IMG.logoMiniL=await fit({r:0,g:0,b:0,alpha:0},0);
 IMG.logoD=IMG.logoMiniD=await fit({r:255,g:255,b:255,alpha:1},16);}
IMG.wCover=await png(wavesCover);IMG.wClose=await png(wavesClose);IMG.wCL=await png(wavesCorner(false));IMG.wCD=await png(wavesCorner(true));IMG.bgDark=await png(bgDark);
IMG.box={};for(const [k,s] of [['ean'],['qr',5],['dm',9]])IMG.box[k]=await png(boxSvg(k,s));
IMG.qrGray=await png(codeSvg('qr',5,'#6b7280'));IMG.qr=await png(codeSvg('qr',5));IMG.qr12=await png(codeSvg('qr',12));IMG.qrDm=await png(codeSvg('dm',9));

/* ---------- layouts ---------- */
const footer=(dark)=>[
 {image:{x:p(48),y:p(680),w:p(100),h:p(28),data:dark?IMG.logoMiniD:IMG.logoMiniL,altText:'Logo GS1 Venezuela'}},
 {text:{text:'Comité Salud GS1 · 5 Nov 2026 · www.gs1ve.org',options:{x:p(340),y:p(686),w:p(600),h:p(20),fontSize:9,color:dark?'94A3B8':'64748B',align:'center',margin:0}}},
 {image:{x:p(1090),y:0,w:p(190),h:p(86),data:dark?IMG.wCD:IMG.wCL,altText:'Onda decorativa'}}];
pres.defineSlideMaster({title:'GS1_CLARO',background:{color:'F8FAFC'},objects:[...footer(false),
 {placeholder:{options:{name:'title',type:'title',x:p(48),y:p(52),w:p(960),h:p(76),fontSize:26,align:'left',bold:true,color:C.text2,fontFace:'+mj-lt',margin:0,valign:'top'},text:''}}],slideNumber:{x:p(1170),y:p(684),w:p(60),h:p(24),fontSize:10,bold:true,color:H.orange,align:'right'}});
pres.defineSlideMaster({title:'GS1_OSCURO',background:{data:IMG.bgDark},objects:[...footer(true),
 {placeholder:{options:{name:'title',type:'title',x:p(48),y:p(52),w:p(1000),h:p(76),fontSize:26,align:'left',bold:true,color:C.background1,fontFace:'+mj-lt',margin:0,valign:'top'},text:''}}],slideNumber:{x:p(1170),y:p(684),w:p(60),h:p(24),fontSize:10,bold:true,color:H.orange,align:'right'}});
pres.defineSlideMaster({title:'GS1_LIBRE',background:{color:'FFFFFF'},objects:[]});

/* ---------- helpers ---------- */
const shadow=()=>({type:'outer',color:'1E3A8A',opacity:.14,blur:14,offset:3,angle:90});
function T(s,t,x,y,w,h,o={}){s.addText(t,{x:p(x),y:p(y),w:p(w),h:p(h),fontSize:o.sz||11,bold:o.b,italic:o.i,color:o.c||col.dark,align:o.al||'left',valign:o.va||'top',margin:0,isTextBox:true,fontFace:o.mono?'Courier New':(o.h?'+mj-lt':undefined),charSpacing:o.cs,paraSpaceAfter:o.psa,lineSpacingMultiple:o.ls,objectName:o.name,rotate:o.rot,fit:'none'})}
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
function line(s,x1,y1,x2,y2,color,w=1,o={}){const dx=x2-x1,dy=y2-y1;s.addShape(pres.ShapeType.line,{x:p(Math.min(x1,x2)),y:p(Math.min(y1,y2)),w:p(Math.abs(dx)),h:p(Math.abs(dy)),flipV:dx*dy<0,line:{color,width:w,transparency:o.tr,dashType:o.dash}})}

/* ===== 1 PORTADA ===== */
let s=pres.addSlide({masterName:'GS1_LIBRE'});
s.addImage({data:IMG.wCover,x:0,y:0,w:p(1280),h:p(720),altText:'Ondas corporativas'});
s.addImage({data:IMG.logoL,x:p(56),y:p(34),w:p(200),h:p(56),altText:'Logo GS1 Venezuela'});
T(s,'COMITÉ',56,108,620,100,{sz:69,b:true,c:col.navy,h:true,name:'Título'});
T(s,'Salud GS1',56,206,620,90,{sz:58,b:true,c:col.cyan,h:true});
const ag=[['BrainCircuit',H.navy,'Rastreo Inteligente: IA Aplicada a la Trazabilidad Médica.'],['ShieldPlus',H.cyan,'Seguridad del paciente, eficiencia de la cadena de suministro y trazabilidad de medicamentos.'],['Newspaper',H.navy,'GS1 News.'],['MessagesSquare',H.cyan,'Ronda Abierta.']];
for(let i=0;i<4;i++){const y=318+i*52;await ibadge(s,56,y,36,ag[i][1],ag[i][0]);T(s,[R(`${i+1}. `,col.orange,{bold:true}),R(ag[i][2],col.navy,{bold:true})],104,y-2,620,42,{sz:12,va:'middle'})}
card(s,56,574,670,112,{fill:col.cyan,line:H.cyan,r:.3});
await ic(s,'CalendarDays','FFFFFF',80,590,22);T(s,'5 Noviembre, 2026',110,588,200,26,{sz:16,b:true,c:col.white,h:true});
await ic(s,'Clock','FFFFFF',80,628,18);T(s,'8:30 am – 10:00 am',110,626,200,22,{sz:12,b:true,c:col.white});
line(s,330,592,330,668,'FFFFFF',1,{tr:50});
await ic(s,'MapPin','FFFFFF',350,594,22);T(s,[R('Oficina GS1 Venezuela. ',col.white,{bold:true}),R('Los Ruices, Calle Los Laboratorios, Edf. Quorum, Piso 1, Oficina K (Caracas).',col.white)],380,590,330,78,{sz:11,va:'middle'});
await photo(s,850,150,260,420,{rot:6,fill:col.cyan2,icon:'Stethoscope',label:'atención médica'});
await photo(s,740,318,230,230,{circ:true,fill:col.navy,icon:'User',label:'médico'});
circle(s,935,285,58,col.white,{line:H.cyan,lw:3,sh:true});T(s,'+',935,285,58,58,{sz:34,b:true,c:col.cyan,al:'center',va:'middle'});
await ibadge(s,1090,130,48,col.orange,'ShieldCheck');
await ic(s,'Phone','FFFFFF',1010,664,16);T(s,'+58 414 2771877',1032,662,200,20,{sz:11,b:true,c:col.white});
await ic(s,'Globe','FFFFFF',1010,688,16);T(s,'www.gs1ve.org',1032,686,200,20,{sz:11,b:true,c:col.white});
s.addNotes('Portada. Reemplazar los marcadores de foto (cápsula y círculo) por fotos de atención médica.');

/* ===== AGENDA ===== */
s=pres.addSlide({masterName:'GS1_CLARO'});
kicker(s,'Comité Salud GS1 · 5 Noviembre 2026');title(s,[R('Agenda ',col.navy),R('de hoy',col.cyan)]);
const agn=[['BrainCircuit',H.navy,'Rastreo Inteligente','IA aplicada a la trazabilidad médica',['Datos estándar + IA','Predicción, visión artificial y anomalías']],['ShieldPlus',H.cyan,'Seguridad, cadena y trazabilidad','Pacientes, suministro y medicamentos',['Los 5 Correctos (BCMA)','Eficiencia de la cadena','De EAN-13 a 2D: DataMatrix y QR GS1']],['Newspaper',H.orange,'GS1 News','Novedades y hoja de ruta',['Sunrise 2027','GS1 Digital Link Latam','EPCIS 2.0']],['MessagesSquare',H.teal,'Ronda Abierta','Mesa de trabajo del Comité',['Retos de implementación','Integración y educación','Próximos pilotos']]];
for(let i=0;i<4;i++){const x=48+i*301.33,a=agn[i];card(s,x,150,280,380);badge(s,x+20,168,40,a[1],String(i+1),14);await ibadge(s,x+210,168,50,a[1],a[0]);
 T(s,a[2],x+20,230,240,50,{sz:15,b:true,c:col.navy,h:true});T(s,a[3],x+20,284,240,34,{sz:11,i:true,c:'64748B'});
 a[4].forEach((b,j)=>{circle(s,x+22,340+j*52+6,8,a[1],{name:'Viñeta'});T(s,b,x+40,336+j*52,224,44,{sz:11.5,c:'334155'})})}
card(s,48,552,1184,70,{fill:col.cyan,line:H.cyan,r:.3});
await ic(s,'CalendarDays','FFFFFF',72,576,22);T(s,'5 Noviembre, 2026 · 8:30 am – 10:00 am',102,573,380,28,{sz:13,b:true,c:col.white,va:'middle'});
await ic(s,'MapPin','FFFFFF',500,576,22);T(s,'Oficina GS1 Venezuela · Los Ruices, Calle Los Laboratorios, Edf. Quorum, Piso 1, Oficina K (Caracas)',530,566,680,40,{sz:11.5,b:true,c:col.white,va:'middle'});

/* ===== IA DATOS ===== */
s=pres.addSlide({masterName:'GS1_OSCURO'});
kicker(s,'Agenda · Punto 1');title(s,[R('Rastreo Inteligente: ',col.white),R('la IA parte del dato estándar',col.cyan)]);
T(s,'Los algoritmos de IA son tan buenos como la calidad de los datos estándar que los alimentan.',48,128,1000,24,{sz:13,i:true,c:'CBD5E1'});
const cols3=[['Database',H.cyan,'1 · Datos estándar GS1','Identificadores únicos y universales',[['GTIN','qué producto'],['GLN','dónde (ubicación)'],['Lote / Serie','qué unidad'],['SSCC','qué envío']]],['Radar',H.orange,'2 · Eventos EPCIS 2.0','Cada movimiento queda registrado',[['QUÉ','producto y cantidad'],['DÓNDE','ubicación GLN'],['CUÁNDO','fecha y hora'],['POR QUÉ','recepción, despacho, dispensación']]],['Cpu',H.teal,'3 · Inteligencia artificial','Modelos sobre datos confiables',[['Predicción','demanda y escasez'],['Visión','verificación de códigos 2D'],['Anomalías','desvíos y cadena de frío']]]];
for(let i=0;i<3;i++){const x=48+i*410,c=cols3[i];dcard(s,x,180,364,360);await ibadge(s,x+20,198,52,c[1],c[0]);T(s,c[2],x+86,200,260,24,{sz:14,b:true,c:col.white,h:true});T(s,c[3],x+86,226,260,34,{sz:10.5,c:'CBD5E1'});
 c[4].forEach((r,j)=>{const y=282+j*58;s.addShape(pres.ShapeType.roundRect,{x:p(x+20),y:p(y),w:p(324),h:p(48),rectRadius:.12,fill:{color:'FFFFFF',transparency:90},line:{type:'none'},objectName:'Dato '+r[0]});T(s,r[0],x+32,y,110,48,{sz:11,b:true,c:col.cyan,mono:true,va:'middle'});T(s,r[1],x+144,y,196,48,{sz:11,c:col.white,va:'middle'})})
 if(i<2)s.addShape(pres.ShapeType.rightArrow,{x:p(x+372),y:p(344),w:p(30),h:p(30),fill:{color:col.orange},line:{type:'none'},objectName:'Flecha'})}
dcard(s,48,562,1184,84);await ic(s,'TriangleAlert',H.orange,72,586,30);
T(s,[R('Sin estándar, no hay IA confiable: ',col.orange,{bold:true}),R('códigos genéricos, datos incompletos o duplicados producen predicciones y alertas poco fiables.',col.white)],116,566,1090,76,{sz:13,va:'middle'});

/* ===== 3 IA ===== */
s=pres.addSlide({masterName:'GS1_OSCURO'});
kicker(s,'Agenda · Punto 1');title(s,[R('Tres usos de la IA ',col.white),R('+ GS1 en salud',col.cyan)]);
T(s,'Los algoritmos de IA son tan buenos como la calidad de los datos estándar que los alimentan.',48,128,1000,24,{sz:13,i:true,c:'CBD5E1'});
T(s,'IA + GS1 · GTIN + GLN + EPCIS 2.0',48,176,600,18,{sz:9,b:true,c:col.cyan,cs:2});
const ia=[['ChartLine',H.cyan,'Modelos predictivos de demanda','Anticipan la escasez de insumos críticos y reactivos en clínicas y hospitales venezolanos.'],['ScanEye',H.orange,'Visión artificial en líneas de empaque','Verificación a alta velocidad de GS1 DataMatrix y QR GS1 Digital Link.'],['Snowflake',H.teal,'Detección de anomalías con Machine Learning','Alerta temprana de desvíos a canales irregulares y rupturas de cadena de frío (insulinas, vacunas, biológicos).']];
for(let i=0;i<3;i++){const y=202+i*130;dcard(s,48,y,600,114);await ibadge(s,66,y+20,48,ia[i][1],ia[i][0]);T(s,ia[i][2],130,y+16,500,24,{sz:13,b:true,c:col.white,h:true});T(s,ia[i][3],130,y+44,500,64,{sz:11,c:'CBD5E1'})}
await photo(s,700,195,215,215,{icon:'Warehouse',label:'cadena de suministro',fill:col.cyan2});
const nd=[[30,40],[30,110],[30,180],[110,20],[110,80],[110,140],[200,50],[200,110],[200,175]],ox=935,oy=195,ed=[[0,3],[0,4],[1,3],[1,4],[1,5],[2,4],[2,5],[3,6],[4,6],[4,7],[5,7],[5,8]];
for(const [a,b] of ed)line(s,ox+nd[a][0],oy+nd[a][1],ox+nd[b][0],oy+nd[b][1],H.cyan,1,{tr:40});
for(const a of [6,7,8]){}
for(const [a,b] of [[6,[275,85]],[7,[275,85]],[7,[275,150]],[8,[275,150]]])line(s,ox+nd[a][0],oy+nd[a][1],ox+b[0],oy+b[1],H.cyan,1,{tr:40});
for(const [x,y] of nd)s.addShape(pres.ShapeType.ellipse,{x:p(ox+x-9),y:p(oy+y-9),w:p(18),h:p(18),fill:{color:H.dark},line:{color:H.cyan,width:1.5},objectName:'Nodo'});
for(const [x,y] of [[275,85],[275,150]])circle(s,ox+x-13,oy+y-13,26,col.orange,{name:'Nodo salida'});
T(s,'GTIN',ox,oy-4,60,14,{sz:8,b:true,c:col.white,mono:true});T(s,'GLN',ox,oy+196,60,14,{sz:8,b:true,c:col.white,mono:true});T(s,'EPCIS',ox+118,oy+196,60,14,{sz:8,b:true,c:col.white,mono:true});
dcard(s,700,435,532,190);
T(s,'IMPACTO DIRECTO EN VENEZUELA',722,452,400,16,{sz:9,b:true,c:col.orange,cs:2});
await ic(s,'Route',H.cyan,722,486,22);T(s,'Optimización de rutas logísticas entre laboratorios nacionales, droguerías y farmacias en todo el país.',756,484,450,48,{sz:11.5,c:col.white});
await ic(s,'Hourglass',H.cyan,722,548,22);T(s,[R('Gestión de vencimientos ',col.white),R('FEFO',col.orange,{bold:true}),R(' (First Expired, First Out): menos mermas financieras por caducidad.',col.white)],756,546,450,56,{sz:11.5});

/* ===== 4 BCMA ===== */
s=pres.addSlide({masterName:'GS1_CLARO'});
kicker(s,'Agenda · Punto 2');title(s,[R('Seguridad del paciente: los ',col.navy),R('5 Correctos',col.cyan),R(' (BCMA)',col.navy)]);
T(s,'Escaneo a pie de cama — Bedside Barcode Medication Administration',48,112,800,20,{sz:11,i:true,c:'64748B'});
await photo(s,60,160,250,400,{rot:-4,icon:'HeartPulse',label:'enfermera escaneando brazalete',fill:col.navy});
await photo(s,190,450,180,180,{circ:true,icon:'ScanLine',label:'brazalete',fill:col.cyan2});
const fc=[['1',H.navy,'Paciente correcto','Escaneo del código GS1 del brazalete de identificación hospitalaria.','GSRN',H.cyan2],['2',H.cyan,'Medicamento correcto','Validación instantánea del GTIN contra la prescripción médica electrónica.','GTIN',H.orange],['3',H.navy,'Dosis correcta','Confirma la concentración (500 mg vs 1000 mg) y evita errores LASA (Look-Alike, Sound-Alike).','LASA','64748B'],['4',H.cyan,'Vía y hora correctas','Registro automático en la Historia Clínica Electrónica.','HCE',H.teal],['5',H.ok,'Vigencia garantizada','El sistema bloquea la dosis si (17) indica vencido o si el lote (10) tiene alerta de retiro.','',H.bad]];
for(let i=0;i<5;i++){const y=160+i*92,f=fc[i];card(s,410,y,822,80,{line:i===4?H.ok:'E2E8F0'});badge(s,430,y+17,46,f[1],f[0],14);T(s,f[2],496,y+10,560,22,{sz:13.5,b:true,c:col.navy,h:true});T(s,f[3],496,y+36,600,40,{sz:11,c:'475569'});
 if(f[4]){s.addShape(pres.ShapeType.roundRect,{x:p(1120),y:p(y+26),w:p(88),h:p(28),rectRadius:.5,fill:{color:'F1F5F9'},line:{type:'none'},objectName:'Etiqueta '+f[4]});T(s,f[4],1120,y+26,88,28,{sz:10,b:true,c:f[5],al:'center',va:'middle',mono:true})}
 else await ic(s,'Ban',H.bad,1168,y+26,30)}

/* ===== CADENA ===== */
s=pres.addSlide({masterName:'GS1_CLARO'});
kicker(s,'Agenda · Punto 2');title(s,[R('Eficiencia de la ',col.navy),R('cadena de suministro',col.cyan)]);
T(s,'Un mismo lenguaje GS1 desde el laboratorio hasta el paciente',48,112,800,20,{sz:11,i:true,c:'64748B'});
const nd2=[['Factory',H.navy,'Laboratorio','GTIN · Lote · Serie'],['Truck',H.cyan,'Droguería / Distribuidor','SSCC · GLN'],['Store',H.orange,'Farmacia / Clínica','GTIN · GLN'],['User',H.teal,'Paciente','GSRN · e-PIL']];
for(let i=0;i<4;i++){const cx=48+i*301.33,mid=cx+140;circle(s,mid-40,160,80,nd2[i][1],{sh:true,name:'Nodo '+nd2[i][2]});await ic(s,nd2[i][0],'FFFFFF',mid-20,180,40);
 T(s,nd2[i][2],cx,252,280,22,{sz:13,b:true,c:col.navy,al:'center',h:true});s.addShape(pres.ShapeType.roundRect,{x:p(mid-100),y:p(280),w:p(200),h:p(28),rectRadius:.5,fill:{color:'E0F4F9'},line:{type:'none'},objectName:'Claves GS1'});T(s,nd2[i][3],mid-100,280,200,28,{sz:10.5,b:true,c:col.cyan2,al:'center',va:'middle',mono:true});
 if(i<3)s.addShape(pres.ShapeType.rightArrow,{x:p(mid+62),y:p(186),w:p(150),h:p(28),fill:{color:'CBD5E1'},line:{type:'none'},objectName:'Flecha flujo'})}
const bn=[['Eye','Visibilidad en tiempo real','Cada movimiento se registra con EPCIS 2.0 y es consultable por los socios autorizados.',H.cyan],['Hourglass','Vencimientos FEFO','Se despacha primero lo que vence primero, con lote y fecha leídos del código.',H.orange],['Undo2','Retiro de lotes ágil','Un recall se ubica por lote y GLN, sin revisar inventario caja por caja.',H.teal],['Snowflake','Cadena de frío','Alertas ante desvíos de temperatura en insulinas, vacunas y biológicos.',H.navy]];
for(let i=0;i<4;i++){const x=48+i*301.33;card(s,x,350,280,240);await ibadge(s,x+20,368,48,bn[i][3],bn[i][0]);T(s,bn[i][1],x+20,430,244,44,{sz:13.5,b:true,c:col.navy,h:true});T(s,bn[i][2],x+20,478,244,104,{sz:11,c:'475569'})}
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

/* ===== 6 LIBRO VS TELEVISOR ===== */
s=pres.addSlide({masterName:'GS1_LIBRE'});
s.addShape(pres.ShapeType.rect,{x:0,y:0,w:p(640),h:p(720),fill:{color:'EEF0F3'},line:{type:'none'},objectName:'Fondo izquierdo'});
s.addShape(pres.ShapeType.rect,{x:p(640),y:0,w:p(640),h:p(720),fill:{color:col.navy},line:{type:'none'},objectName:'Fondo derecho'});
T(s,'ANALOGÍA CONCEPTUAL',340,20,600,16,{sz:9,b:true,c:col.orange,al:'center',cs:2});
card(s,330,42,620,58,{r:.5});T(s,[R('El Libro ',col.navy),R('vs. ','94A3B8'),R('El Televisor Clínico',col.cyan)],330,42,620,58,{sz:22,b:true,al:'center',va:'middle',h:true});
await ibadge(s,48,130,44,col.bad,'TriangleAlert');T(s,'QR genérico / estático',104,128,440,26,{sz:16.5,b:true,c:'334155',h:true});T(s,'Como un libro impreso',104,156,400,18,{sz:10.5,b:true,c:col.bad});
card(s,48,196,190,190,{noShadow:false});s.addImage({data:IMG.qrGray,x:p(60),y:p(208),w:p(166),h:p(166),altText:'QR genérico'});
card(s,262,230,300,96,{r:.1});T(s,[R('http://mi-laboratorio.com/prospecto.pdf',col.dark)],276,240,272,40,{sz:9.5,mono:true,c:'64748B'});T(s,'URL fija · no editable',276,292,272,20,{sz:9.5,b:true,c:col.bad,mono:true});
const bl=['La URL queda fija una vez impreso el empaque.','No sirve para pasar por caja ni sistemas hospitalarios.','Si cambia la normativa sanitaria, se desecha el material de empaque.'];
for(let i=0;i<3;i++){await ic(s,'CircleX',H.bad,48,418+i*52,22);T(s,bl[i],82,416+i*52,480,44,{sz:12,b:true,c:'334155'})}
await ibadge(s,690,130,44,col.ok,'BadgeCheck');T(s,'QR GS1 Digital Link',746,128,480,26,{sz:16.5,b:true,c:col.white,h:true});T(s,'Como un televisor inteligente · Sello GS1 Venezuela',746,156,480,18,{sz:10.5,b:true,c:col.ok});
card(s,690,196,190,190,{line:H.ok,lw:3});s.addImage({data:IMG.qr,x:p(702),y:p(208),w:p(166),h:p(166),altText:'QR GS1 Digital Link'});
s.addShape(pres.ShapeType.roundRect,{x:p(904),y:p(224),w:p(300),h:p(110),rectRadius:.12,fill:{color:'000000',transparency:70},line:{color:'FFFFFF',transparency:60,width:1.5},objectName:'Control remoto'});
T(s,'CAMBIAR EL CANAL',920,236,260,16,{sz:9,b:true,c:col.cyan,cs:2});T(s,'dl.gs1ve.org/01/0759…',920,258,260,18,{sz:10,mono:true,c:'E2E8F0'});
badge(s,920,288,30,col.orange,'1',11);badge(s,958,288,30,col.cyan,'2',11);badge(s,996,288,30,col.bad,'3',11);
const ch=[[col.orange,'1','Farmacia / Hospital: ','lectura de GTIN, lote y vencimiento en el punto de dispensación.'],[col.cyan,'2','Paciente: ','prospecto digital (e-PIL), video de aplicación y validación de originalidad.'],[col.bad,'3','Emergencia sanitaria: ','alerta de farmacovigilancia o retiro de lote (Recall) inmediata.']];
for(let i=0;i<3;i++){const y=412+i*76;s.addShape(pres.ShapeType.roundRect,{x:p(690),y:p(y),w:p(540),h:p(66),rectRadius:.12,fill:{color:'FFFFFF',transparency:88},line:{type:'none'},objectName:'Canal '+(i+1)});badge(s,704,y+17,32,ch[i][0],ch[i][1],12);T(s,[R(ch[i][2],col.white,{bold:true}),R(ch[i][3],col.white)],750,y+6,470,54,{sz:11,va:'middle'})}
circle(s,613,330,54,col.orange,{line:'FFFFFF',lw:3,sh:true,name:'VS'});T(s,'VS',613,330,54,54,{sz:15,b:true,c:col.white,al:'center',va:'middle',h:true});
T(s,'Comité Salud GS1 · 5 Nov 2026',48,690,400,18,{sz:9,b:true,c:'64748B'});s.addImage({data:IMG.logoD,x:p(1130),y:p(682),w:p(100),h:p(28),altText:'Logo GS1 Venezuela'});

/* ===== 10 GS1 NEWS ===== */
s=pres.addSlide({masterName:'GS1_OSCURO'});
kicker(s,'Agenda · Punto 3 · GS1 News');title(s,[R('Novedades globales y ',col.white),R('hoja de ruta 2026–2027',col.cyan)]);
line(s,60,238,1220,238,H.cyan,3);
const nw=[['Sunrise',H.orange,'Rumbo a GS1 Sunrise 2027','2027','año meta de GS1 Sunrise: códigos 2D en el punto de venta','Puntos de venta y farmacias avanzan hacia la lectura nativa de códigos 2D.'],['QrCode',H.cyan,'Plataforma GS1 Digital Link Latam','','Disponible para afiliados de GS1 Venezuela.','Arte para QR Digital Link y GS1 DataMatrix.'],['Share2',H.teal,'EPCIS 2.0 e interoperabilidad con IA','','','Nuevo estándar global para compartir eventos de visibilidad en cadenas de suministro de salud con máxima ciberseguridad.'],['GraduationCap',H.orange,'Formación y acompañamiento técnico','','','Consultoría del Departamento de Estándares de GS1 Venezuela para adecuar líneas de empaque y catalogación.']];
for(let i=0;i<4;i++){const x=48+i*301.33,n=nw[i];dcard(s,x,274,280,340);badge(s,x+120,218,40,[H.orange,H.cyan,H.teal,H.orange][i],String(i+1),14);
 await ic(s,n[0],n[1],x+20,292,32);T(s,n[2],x+20,334,244,48,{sz:13,b:true,c:col.white,h:true});let y=388;
 if(n[3]){T(s,n[3],x+20,y,240,44,{sz:32,b:true,c:col.cyan,h:true});T(s,n[4],x+20,y+44,240,34,{sz:10.5,c:'CBD5E1'});y+=84}
 if(i===1){T(s,n[4],x+20,y,240,20,{sz:11,c:'CBD5E1'});T(s,'app.gs1digitallink.lat',x+20,y+42,244,16,{sz:9.5,c:col.cyan,mono:true});
  ['SVG','PNG','PDF','EPS'].forEach((f,j)=>{s.addShape(pres.ShapeType.roundRect,{x:p(x+20+j*54),y:p(y+68),w:p(46),h:p(24),rectRadius:.1,fill:{color:'FFFFFF',transparency:88},line:{type:'none'},objectName:'Formato '+f});T(s,f,x+20+j*54,y+68,46,24,{sz:9.5,b:true,c:col.white,al:'center',va:'middle',mono:true})});y+=104}
 T(s,n[5],x+20,y,244,100,{sz:11,c:'CBD5E1'})}

/* ===== 11 RONDA ABIERTA ===== */
s=pres.addSlide({masterName:'GS1_CLARO'});
kicker(s,'Agenda · Punto 4 · Mesa de trabajo del Comité');title(s,[R('Ronda ',col.navy),R('Abierta',col.cyan)]);
await photo(s,1020,34,124,124,{circ:true,icon:'Users',label:'comité',fill:col.cyan2});
const dq=[[H.navy,'Retos en empaque primario y secundario','¿Cómo preparan los laboratorios nacionales sus líneas de impresión para códigos 2D variables (lote / vencimiento)?'],[H.cyan,'Integración con farmacias y clínicas','Homologación de lectores ópticos 2D y de sistemas ERP / HIS en Venezuela.'],[H.orange,'Educación al médico y al paciente','Estrategias conjuntas para impulsar el escaneo de verificación de autenticidad y la lectura del prospecto digital.'],[H.teal,'Próximos pilotos 2026–2027','Definición de las mesas técnicas de trabajo del Comité Salud.']];
for(let i=0;i<4;i++){const x=48+(i%2)*606,y=176+Math.floor(i/2)*226;card(s,x,y,578,206);badge(s,x+22,y+22,50,dq[i][0],String(i+1),18);T(s,dq[i][1],x+90,y+22,460,50,{sz:15,b:true,c:col.navy,h:true,va:'middle'});T(s,dq[i][2],x+90,y+84,460,110,{sz:12.5,c:'475569'})}

/* ===== 12 CIERRE ===== */
s=pres.addSlide({masterName:'GS1_LIBRE'});
s.addImage({data:IMG.wClose,x:0,y:0,w:p(1280),h:p(720),altText:'Ondas corporativas'});
s.addImage({data:IMG.logoL,x:p(520),y:p(34),w:p(200),h:p(56),altText:'Logo GS1 Venezuela'});
T(s,[R('Únete al ',col.navy),R('Comité Salud GS1',col.cyan)],520,104,720,56,{sz:33,b:true,h:true,name:'Título'});
T(s,'Solicita tu acceso a la plataforma Digital Link.',520,164,700,22,{sz:12.5,c:'475569'});
card(s,130,250,300,300,{r:.25});s.addImage({data:IMG.qr12,x:p(154),y:p(274),w:p(252),h:p(252),altText:'Código QR ilustrativo'});
for(const [cx,cy,sx,sy,c] of [[118,238,1,1,H.navy],[442,238,-1,1,H.cyan],[118,562,1,-1,H.cyan],[442,562,-1,-1,H.navy]]){line(s,cx,cy,cx+sx*44,cy,c,5);line(s,cx,cy,cx,cy+sy*44,c,5)}
T(s,'ESCANEA · SOLICITA ACCESO',130,584,300,16,{sz:9,b:true,c:col.orange,al:'center',cs:2});
const ct=[['MapPin',[R('Oficina GS1 Venezuela. ',col.dark,{bold:true}),R('Los Ruices, Calle Los Laboratorios, Edf. Quorum, Piso 1, Oficina K, Caracas, Venezuela.',col.dark)],58,false],['Phone','+58 414-2771877  /  +58 412-628-3276',44,true],['Mail','Solicituddecodigo@gs1ve.org\nGlabrador@gs1ve.org · Acastro@gs1ve.org',66,true],['Globe','www.gs1ve.org  ·  Instagram @GS1Venezuela  ·  RIF J-00336360-0',44,false]];
let cy=214;for(const [ico,txt,h,mono] of ct){card(s,520,cy,712,h,{r:.3});await ic(s,ico,H.orange,540,cy+h/2-11,22);T(s,txt,576,cy,640,h,{sz:mono?11:11.5,b:ico!=='MapPin',va:'middle',mono,c:col.dark});cy+=h+14}
T(s,[R('Datos estándar, ',col.navy),R('decisiones seguras.',col.orange)],520,540,500,34,{sz:17,b:true,h:true});
await pres.writeFile({fileName:OUT});await applyTheme(OUT,THEME);console.log('ok');
})().catch(e=>{console.error(e);process.exit(1)});
