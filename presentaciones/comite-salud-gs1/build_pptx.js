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
const ag=[['BrainCircuit',H.navy,'Rastreo Inteligente: IA Aplicada a la Trazabilidad Médica.'],['ShieldPlus',H.cyan,'Seguridad del paciente, eficiencia de la cadena de suministro y trazabilidad de medicamentos.'],['Globe',H.navy,'Casos de Éxito Internacionales y Contexto Venezolano.'],['MessagesSquare',H.cyan,'GS1 News & Ronda Abierta.']];
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

/* ===== 2 NUEVO PACIENTE ===== */
s=pres.addSlide({masterName:'GS1_CLARO'});
kicker(s,'El ecosistema de salud en Venezuela');title(s,[R('El ',col.navy),R('Nuevo Paciente',col.cyan),R(' venezolano',col.navy)]);
for(const [i,v,clr,ico,txt] of [[0,41,H.bad,'QrCode','No escanea códigos QR estáticos sin valor agregado.'],[1,80,H.ok,'BadgeCheck','Escanearía para verificar origen, registro sanitario y autenticidad.']]){
 const x=48+i*324;card(s,x,150,300,245);
 s.addChart(pres.charts.DOUGHNUT,[{name:'%',labels:['Sí','No'],values:[v,100-v]}],{x:p(x+16),y:p(166),w:p(96),h:p(96),holeSize:68,chartColors:[clr,'E2E8F0'],showLegend:false,showTitle:false,showValue:false,showPercent:false,showLabel:false,dataBorder:{pt:0,color:'FFFFFF'}});
 await ic(s,ico,clr,x+130,x?190:190,40);
 T(s,v+'%',x+24,272,250,70,{sz:48,b:true,c:col.orange,h:true});T(s,txt,x+24,342,252,44,{sz:11,c:'475569'})}
await photo(s,720,140,230,270,{rot:-5,icon:'Pill',label:'farmacia',fill:col.navy});
await photo(s,900,215,200,200,{circ:true,icon:'Smartphone',label:'escaneo',fill:col.cyan2});
await ibadge(s,1075,170,56,col.orange,'ScanLine');
const tri=[['FileText',H.navy,'1 · Información','Posología, alertas de farmacovigilancia y prospecto digital (e-PIL) al instante.'],['ShieldCheck',H.orange,'2 · Confianza','Validación frente a medicamentos ilícitos, contrabando o sin registro sanitario (SACS / INHRR).'],['Network',H.cyan,'3 · Experiencia','Conexión directa: laboratorio, droguería, farmacia, clínica y paciente.']];
for(let i=0;i<3;i++){const x=48+i*402;card(s,x,440,378,150);await ibadge(s,x+18,458,52,tri[i][1],tri[i][0]);T(s,tri[i][2],x+84,458,280,24,{sz:14,b:true,c:col.navy,h:true});T(s,tri[i][3],x+84,486,280,96,{sz:11,c:'475569'})}

/* ===== 3 IA ===== */
s=pres.addSlide({masterName:'GS1_OSCURO'});
kicker(s,'Agenda · Punto 1');title(s,[R('Rastreo Inteligente: ',col.white),R('IA aplicada a la trazabilidad médica',col.cyan)]);
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

/* ===== 5 ANATOMÍA ===== */
s=pres.addSlide({masterName:'GS1_CLARO'});
kicker(s,'Anatomía técnica del estándar');title(s,[R('De la barra tradicional al ',col.navy),R('estándar 2D en salud',col.cyan)]);
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

/* ===== 7 CASOS 1 ===== */
s=pres.addSlide({masterName:'GS1_CLARO'});
kicker(s,'Casos de éxito internacionales · Parte 1');title(s,[R('Estándares GS1 que salvan vidas: ',col.navy),R('NHS, UE y EE. UU.',col.cyan)]);
card(s,48,125,740,500);badge(s,72,146,42,col.navy,'UK',11);T(s,'NHS Inglaterra · Scan4Safety',126,146,500,22,{sz:15,b:true,c:col.navy,h:true});T(s,'Adopción integral de estándares GS1 en hospitales',126,170,500,16,{sz:10,c:'64748B'});
for(const [x,w,t,f,c] of [[72,150,'GTIN · productos','FDE9E2',col.orange],[232,150,'GLN · ubicaciones','E0F4F9',col.cyan2],[392,210,'GSRN · pacientes/personal','E2E8F0',col.navy]]){s.addShape(pres.ShapeType.roundRect,{x:p(x),y:p(206),w:p(w),h:p(26),rectRadius:.5,fill:{color:f},line:{type:'none'},objectName:'Etiqueta '+t});T(s,t,x,206,w,26,{sz:9.5,b:true,c,al:'center',va:'middle',mono:true})}
const mt=[['76%','menos errores de medicación y de selección de implantes quirúrgicos'],['+140.000','horas de enfermería liberadas de conteos manuales para cuidado directo'],['<30 min','para retirar lotes defectuosos (recalls); antes tomaba días']];
for(let i=0;i<3;i++){const x=72+i*232;card(s,x,252,216,160,{fill:col.bg,noShadow:true,r:.15});T(s,mt[i][0],x,266,216,56,{sz:i===0?40:30,b:true,c:col.orange,al:'center',va:'middle',h:true});T(s,mt[i][1],x+12,328,192,78,{sz:11,c:'475569',al:'center'})}
await photo(s,72,432,692,170,{icon:'Hospital',label:'hospital moderno',fill:col.navy});
card(s,812,125,420,500);badge(s,836,146,48,col.cyan,'UE·US',9);T(s,'Directiva FMD (UE) y DSCSA (EE. UU.)',896,146,310,44,{sz:14,b:true,c:col.navy,h:true,va:'middle'});
s.addImage({data:IMG.box.dm,x:p(902),y:p(215),w:p(200),h:p(160),altText:'Caja con GS1 DataMatrix'});
await ic(s,'ScanBarcode',H.orange,836,410,24);T(s,[R('Verificación ',col.dark),R('unitaria',col.dark,{bold:true}),R(' de cajas con ',col.dark),R('GS1 DataMatrix',col.dark,{bold:true}),R(' serializado antes de dispensar.',col.dark)],872,408,336,56,{sz:11.5});
await ic(s,'FileText',H.orange,836,488,24);T(s,[R('e-PIL',col.dark,{bold:true}),R(' (prospecto electrónico) mediante ',col.dark),R('GS1 Digital Link',col.dark,{bold:true}),R('.',col.dark)],872,486,336,56,{sz:11.5});

/* ===== 8 CASOS 2 ===== */
s=pres.addSlide({masterName:'GS1_CLARO'});
kicker(s,'Casos de éxito internacionales · Parte 2');title(s,[R('Referentes en ',col.navy),R('América Latina',col.cyan)]);
const flags={AR:[['74ACDF',0,1/3],['FFFFFF',1/3,1/3],['74ACDF',2/3,1/3]],CO:[['FCD116',0,.5],['003893',.5,.25],['CE1126',.75,.25]]};
const cc=[['Argentina','Sistema Nacional de Trazabilidad · ANMAT','FlaskConical','AR','GTIN + Serie + GLN','Cada movimiento se reporta en tiempo real, del laboratorio a la administración al paciente.',null,'Erradicó medicamentos robados o falsificados en el canal hospitalario y obras sociales.'],['Brasil','ANVISA · Sírio-Libanês / Albert Einstein','Hospital','BR',null,'Farmacias hospitalarias automatizadas: dosis unitarias con GS1 DataMatrix e IA para control de dispensación robótica.',['99.9%','trazabilidad en oncológicos y alto costo']],['Colombia','Pilotos GS1 Healthcare · Unidosis','Microscope','CO',null,'Catálogos electrónicos sincronizados (GDSN) entre laboratorios y clínicas privadas.',['−40%','discrepancias en órdenes de compra y facturación']]];
for(let i=0;i<3;i++){const x=48+i*402,c=cc[i];card(s,x,125,378,500);
 s.addShape(pres.ShapeType.round2SameRect,{x:p(x),y:p(125),w:p(378),h:p(130),rectRadius:.18,fill:{color:i%2?col.navy:col.cyan2},line:{type:'none'},objectName:'FOTO (reemplazar): '+c[0]});await ic(s,c[2],'FFFFFF',x+169,163,40);T(s,'Insertar foto',x+10,230,358,16,{sz:8,c:col.white,al:'center'});
 const fx=x+20,fy=276;if(c[3]==='BR'){s.addShape(pres.ShapeType.rect,{x:p(fx),y:p(fy),w:p(36),h:p(24),fill:{color:'009C3B'},line:{type:'none'},objectName:'Bandera Brasil'});s.addShape(pres.ShapeType.diamond,{x:p(fx+6),y:p(fy+4),w:p(24),h:p(16),fill:{color:'FFDF00'},line:{type:'none'},objectName:'Rombo'})}
 else for(const [fc2,off,hh] of flags[c[3]])s.addShape(pres.ShapeType.rect,{x:p(fx),y:p(fy+off*24),w:p(36),h:p(hh*24),fill:{color:fc2},line:{color:'E2E8F0',width:.5},objectName:'Bandera '+c[0]});
 T(s,c[0],x+66,272,290,28,{sz:15,b:true,c:col.navy,h:true});T(s,c[1],x+20,306,340,18,{sz:10,b:true,c:col.cyan2});
 let y=332;if(c[4]){T(s,c[4],x+20,y,340,18,{sz:10,b:true,c:col.orange,mono:true});y+=26}
 if(c[6]){T(s,c[6][0],x+20,y,340,58,{sz:40,b:true,c:col.orange,h:true});T(s,c[6][1],x+20,y+58,340,18,{sz:10,b:true,c:'64748B'});y+=88}
 T(s,c[5],x+20,y,340,76,{sz:11,c:'475569'});
 if(c[7]){card(s,x+20,y+82,338,82,{fill:'E6F8F1',line:'E6F8F1',noShadow:true,r:.15});await ic(s,'ShieldCheck',H.ok,x+32,y+104,24);T(s,c[7],x+66,y+88,282,70,{sz:10.5,b:true,c:'047857',va:'middle'})}}

/* ===== 9 CONTROL REMOTO ===== */
s=pres.addSlide({masterName:'GS1_CLARO'});
kicker(s,'Aplicación práctica en Venezuela');title(s,[R('“Control Remoto QR” para el ',col.navy),R('sector salud',col.cyan)]);
const st=[['Registra el GTIN 0759…','Vinculación automática con el catálogo de GS1 Venezuela.'],['Configura la experiencia sanitaria','Redirección inteligente, landing page aprobada por dirección médica o Pasaporte Digital del Producto (DPP).'],['Analítica en tiempo real','Escaneos por estado, tasa de verificación de autenticidad y grupos terapéuticos.']];
for(let i=0;i<3;i++){const y=130+i*152;card(s,48,y,400,138);badge(s,66,y+18,44,col.orange,String(i+1),14);T(s,st[i][0],124,y+16,310,40,{sz:13,b:true,c:col.navy,h:true,va:'middle'});T(s,st[i][1],124,y+60,310,72,{sz:11,c:'475569'})}
card(s,480,125,752,500,{r:.1});s.addShape(pres.ShapeType.round2SameRect,{x:p(480),y:p(125),w:p(752),h:p(36),rectRadius:.1,fill:{color:'F1F5F9'},line:{type:'none'},objectName:'Barra navegador'});
for(const [dx,c] of [[498,H.bad],[516,'FBBF24'],[534,H.ok]])circle(s,dx,137,12,c,{name:'Botón ventana'});
s.addShape(pres.ShapeType.roundRect,{x:p(560),y:p(134),w:p(200),h:p(18),rectRadius:.5,fill:{color:'FFFFFF'},line:{type:'none'},objectName:'URL'});T(s,'app.gs1digitallink.lat',560,134,200,18,{sz:8.5,c:'64748B',al:'center',va:'middle',mono:true});
const kp=[['Escaneos totales','48.213',col.white,col.navy,true],['Verificados','100%',col.ok,col.bg],['GTIN activos','126',col.cyan,col.bg],['Alertas de lote','0',col.orange,col.bg]];
for(let i=0;i<4;i++){const x=496+i*181,k=kp[i];card(s,x,176,169,76,{fill:i?col.bg:col.navy,line:'E2E8F0',noShadow:true,r:.12});T(s,k[0],x+12,184,150,14,{sz:9,c:i?'64748B':'CBD5E1'});T(s,k[1],x+12,200,150,44,{sz:22,b:true,c:k[2],h:true,va:'middle'})}
card(s,496,262,430,184,{noShadow:true,r:.1,fill:col.white});T(s,'Tendencia de escaneos (30 días)',510,270,360,16,{sz:10,b:true,c:col.navy});
s.addChart(pres.charts.AREA,[{name:'Escaneos',labels:['1','4','7','10','13','16','19','22','25','28','30'],values:[820,1100,980,1500,1380,1900,1760,2300,2150,2700,2600]}],{x:p(504),y:p(288),w:p(414),h:p(152),chartColors:[H.cyan],chartColorsOpacity:35,showLegend:false,showTitle:false,catAxisLabelFontSize:8,valAxisLabelFontSize:8,catAxisLabelColor:'64748B',valAxisLabelColor:'64748B',catAxisLabelFontFace:'+mn-lt',valAxisLabelFontFace:'+mn-lt',valGridLine:{color:'E2E8F0',size:.5},catGridLine:{style:'none'}});
card(s,938,262,278,184,{noShadow:true,r:.1,fill:col.white});T(s,'Escaneos por estado',952,270,240,16,{sz:10,b:true,c:col.navy});
s.addChart(pres.charts.BAR,[{name:'Escaneos',labels:['Zulia','Carabobo','Miranda','Caracas'],values:[18,22,31,45]}],{x:p(946),y:p(288),w:p(264),h:p(152),barDir:'bar',chartColors:[H.navy],showLegend:false,showTitle:false,showValue:true,dataLabelPosition:'outEnd',dataLabelFontSize:8,dataLabelColor:'334155',dataLabelFontFace:'+mn-lt',catAxisLabelFontSize:8,valAxisHidden:true,catAxisLabelColor:'334155',catAxisLabelFontFace:'+mn-lt',valGridLine:{style:'none'},catGridLine:{style:'none'},barGapWidthPct:60});
card(s,496,458,720,100,{noShadow:true,r:.1,fill:col.white});T(s,'Grupos terapéuticos',510,466,300,16,{sz:10,b:true,c:col.navy});
const gt=[['Pill','Analgésicos','E0F4F9',H.cyan2],['Bug','Antibióticos','FDE9E2',H.orange],['Snowflake','Cadena de frío','E2E8F0',H.navy],['Syringe','Disp. médicos','D9F2F0',H.teal]];
for(let i=0;i<4;i++){const x=510+i*176;s.addShape(pres.ShapeType.roundRect,{x:p(x),y:p(494),w:p(164),h:p(48),rectRadius:.15,fill:{color:gt[i][2]},line:{type:'none'},objectName:'Grupo '+gt[i][1]});await ic(s,gt[i][0],gt[i][3],x+12,508,20);T(s,gt[i][1],x+40,494,120,48,{sz:11,b:true,c:gt[i][3],va:'middle'})}
T(s,'* Datos ilustrativos de maqueta.',496,566,400,14,{sz:8,c:'94A3B8'});

/* ===== 10 GS1 NEWS ===== */
s=pres.addSlide({masterName:'GS1_OSCURO'});
kicker(s,'GS1 News');title(s,[R('Novedades globales y ',col.white),R('hoja de ruta 2026–2027',col.cyan)]);
line(s,60,238,1220,238,H.cyan,3);
const nw=[['Sunrise',H.orange,'Rumbo a GS1 Sunrise 2027','48','países en pilotos activos (88% del PIB mundial)','Puntos de venta y farmacias avanzan hacia la lectura nativa de códigos 2D.'],['QrCode',H.cyan,'Plataforma GS1 Digital Link Latam','','Disponible para afiliados de GS1 Venezuela.','Arte para QR Digital Link y GS1 DataMatrix.'],['Share2',H.teal,'EPCIS 2.0 e interoperabilidad con IA','','','Nuevo estándar global para compartir eventos de visibilidad en cadenas de suministro de salud con máxima ciberseguridad.'],['GraduationCap',H.orange,'Formación y acompañamiento técnico','','','Consultoría del Departamento de Estándares de GS1 Venezuela para adecuar líneas de empaque y catalogación.']];
for(let i=0;i<4;i++){const x=48+i*301.33,n=nw[i];dcard(s,x,274,280,340);badge(s,x+120,218,40,[H.orange,H.cyan,H.teal,H.orange][i],String(i+1),14);
 await ic(s,n[0],n[1],x+20,292,32);T(s,n[2],x+20,334,244,48,{sz:13,b:true,c:col.white,h:true});let y=388;
 if(n[3]){T(s,n[3],x+20,y,240,44,{sz:32,b:true,c:col.cyan,h:true});T(s,n[4],x+20,y+44,240,34,{sz:10.5,c:'CBD5E1'});y+=84}
 if(i===1){T(s,n[4],x+20,y,240,20,{sz:11,c:'CBD5E1'});T(s,'app.gs1digitallink.lat',x+20,y+42,244,16,{sz:9.5,c:col.cyan,mono:true});
  ['SVG','PNG','PDF','EPS'].forEach((f,j)=>{s.addShape(pres.ShapeType.roundRect,{x:p(x+20+j*54),y:p(y+68),w:p(46),h:p(24),rectRadius:.1,fill:{color:'FFFFFF',transparency:88},line:{type:'none'},objectName:'Formato '+f});T(s,f,x+20+j*54,y+68,46,24,{sz:9.5,b:true,c:col.white,al:'center',va:'middle',mono:true})});y+=104}
 T(s,n[5],x+20,y,244,100,{sz:11,c:'CBD5E1'})}

/* ===== 11 RONDA ABIERTA ===== */
s=pres.addSlide({masterName:'GS1_CLARO'});
kicker(s,'Mesa de trabajo del Comité Salud GS1');title(s,[R('Ronda ',col.navy),R('Abierta',col.cyan)]);
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
