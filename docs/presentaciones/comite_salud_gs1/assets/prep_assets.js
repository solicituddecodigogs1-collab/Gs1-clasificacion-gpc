const sharp=require('sharp');const SRC='/tmp/claude-0/-home-user-Gs1-clasificacion-gpc/cd8fa01c-34d5-5ada-913c-548e65bdd653/images/1.webp';
(async()=>{
 // logo con fondo transparente
 const {data,info}=await sharp(SRC).extract({left:56,top:40,width:218,height:106}).resize(872,424,{kernel:'lanczos3'}).ensureAlpha().raw().toBuffer({resolveWithObject:true});
 for(let i=0;i<data.length;i+=4){if(Math.min(data[i],data[i+1],data[i+2])>222){data[i]=data[i+1]=data[i+2]=255}}
 await sharp(data,{raw:info}).png().toFile('logo_poster.png');
 // capsula
 const cw=520,ch=840,b=16;
 const ph=await sharp(SRC).extract({left:895,top:150,width:255,height:380}).resize(cw-2*b,ch-2*b,{fit:'cover'}).png().toBuffer();
 const mk=(w,h,r)=>Buffer.from(`<svg width="${w}" height="${h}"><rect width="${w}" height="${h}" rx="${r}" fill="#fff"/></svg>`);
 const inner=await sharp(ph).composite([{input:mk(cw-2*b,ch-2*b,56),blend:'dest-in'}]).png().toBuffer();
 await sharp({create:{width:cw,height:ch,channels:4,background:{r:255,g:255,b:255,alpha:0}}}).composite([{input:mk(cw,ch,72),blend:'over'},{input:inner,left:b,top:b}]).png().toFile('photo_capsula.png');
 // circulo
 const d=520,bb=18;
 const ci=await sharp(SRC).extract({left:680,top:560,width:470,height:470}).resize(d-2*bb,d-2*bb).png().toBuffer();
 const cm=(s)=>Buffer.from(`<svg width="${s}" height="${s}"><circle cx="${s/2}" cy="${s/2}" r="${s/2}" fill="#fff"/></svg>`);
 const cin=await sharp(ci).composite([{input:cm(d-2*bb),blend:'dest-in'}]).png().toBuffer();
 await sharp({create:{width:d,height:d,channels:4,background:{r:255,g:255,b:255,alpha:0}}}).composite([{input:cm(d),blend:'over'},{input:cin,left:bb,top:bb}]).png().toFile('photo_circulo.png');
})();
