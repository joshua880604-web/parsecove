export function timestamp(value, unit='auto') {
  const raw=String(value).trim();
  if(!/^-?\d+$/.test(raw))throw Error('Enter a whole-number Unix timestamp. Use the date tab for ISO dates.');
  let n=BigInt(raw); const abs=n<0n?-n:n;
  const detected=unit==='auto'?(abs<100000000000n?'seconds':'milliseconds'):unit;
  if(!['seconds','milliseconds'].includes(detected))throw Error('Choose seconds or milliseconds.');
  let ms=detected==='seconds'?n*1000n:n;
  if(ms>8640000000000000n||ms< -8640000000000000n)throw Error('This timestamp is outside the supported date range.');
  const date=new Date(Number(ms));
  return {ms:String(ms),seconds:ms%1000n===0n?String(ms/1000n):String(Number(ms)/1000),iso:date.toISOString(),date,unit:detected};
}
export function fromISO(value){
  const s=String(value).trim();
  const match=s.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2})(?:\.(\d{1,3}))?)?(Z|[+-]\d{2}:\d{2})$/i);
  if(!match)throw Error('Use an ISO date with a timezone, e.g. 2023-11-14T22:13:20Z or 2023-11-14T17:13:20-05:00.');
  const [,y,m,d,h,min,sec='0',,zone]=match; const year=+y,month=+m,day=+d;
  const leap=year%4===0&&(year%100!==0||year%400===0);
  const max=[31,leap?29:28,31,30,31,30,31,31,30,31,30,31][month-1];
  if(month<1||month>12||day<1||day>max||+h>23||+min>59||+sec>59)throw Error('That calendar date or time is invalid.');
  if(zone.toUpperCase()!=='Z'&&(+zone.slice(1,3)>23||+zone.slice(4)>59))throw Error('The timezone offset is invalid.');
  const ms=Date.parse(s);if(!Number.isFinite(ms))throw Error('This date cannot be converted.');
  return timestamp(String(ms),'milliseconds');
}
export function toBase64(bytes,variant='standard',padding=true){
  let s=''; for(let i=0;i<bytes.length;i+=16384)s+=String.fromCharCode(...bytes.subarray(i,i+16384));
  let out=btoa(s); if(variant==='url')out=out.replace(/\+/g,'-').replace(/\//g,'_');
  return padding?out:out.replace(/=+$/,'');
}
export function fromBase64(value,variant='standard'){
  let s=String(value).replace(/\s/g,'');
  if(s.length>15000000)throw Error('Input is too large. Keep encoded input below 15 million characters.');
  if(!s)return new Uint8Array();
  const valid=variant==='url'?/^[A-Za-z0-9_-]*={0,2}$/:/^[A-Za-z0-9+/]*={0,2}$/;
  if(!valid.test(s))throw Error('Invalid characters or misplaced padding. Check the selected Base64 alphabet.');
  let normalized=s.replace(/-/g,'+').replace(/_/g,'/'); const bare=normalized.replace(/=+$/,'');
  if(bare.length%4===1||(normalized.includes('=')&&normalized.length%4!==0))throw Error('Invalid Base64 length or padding.');
  let decoded;try{decoded=atob(bare+'='.repeat((4-bare.length%4)%4));}catch{throw Error('This is not valid Base64.');}
  const bytes=Uint8Array.from(decoded,c=>c.charCodeAt(0));
  if(toBase64(bytes).replace(/=+$/,'')!==bare)throw Error('Non-canonical Base64: trailing bits are invalid.');
  return bytes;
}
export function encodeText(s,variant='standard',padding=true){
  if(s.length>2000000)throw Error('Text is too large. Use fewer than 2 million characters.');
  if(s.isWellFormed&&!s.isWellFormed())throw Error('Text contains an invalid Unicode surrogate.');
  return toBase64(new TextEncoder().encode(s),variant,padding);
}
export function decodeText(s,variant='standard'){
  const bytes=fromBase64(s,variant);try{return new TextDecoder('utf-8',{fatal:true}).decode(bytes);}catch{throw Error('Decoded bytes are not valid UTF-8 text. Try the Base64 image tool for image data.');}
}
export function detectImage(bytes){
  const b=bytes;
  if(b.length>=8&&[137,80,78,71,13,10,26,10].every((n,i)=>b[i]===n))return {mime:'image/png',ext:'png'};
  if(b.length>=3&&b[0]===255&&b[1]===216&&b[2]===255)return {mime:'image/jpeg',ext:'jpg'};
  const head=String.fromCharCode(...b.slice(0,12));
  if(head.startsWith('GIF87a')||head.startsWith('GIF89a'))return {mime:'image/gif',ext:'gif'};
  if(head.startsWith('RIFF')&&head.slice(8,12)==='WEBP')return {mime:'image/webp',ext:'webp'};
  throw Error('Supported image bytes: PNG, JPEG, GIF or WebP. SVG and other file types are not supported in this version.');
}
export function parseImage(value){
  let raw=String(value).trim(),declared='';
  if(/^data:/i.test(raw)){
    const m=raw.match(/^data:([^;,]+);base64,([\s\S]*)$/i);
    if(!m)throw Error('Use a Base64 data URI: data:image/png;base64,...');
    declared=m[1].toLowerCase();raw=m[2];
  }
  const bytes=fromBase64(raw);
  if(bytes.length>10485760)throw Error('Decoded images must be 10 MB or smaller.');
  const type=detectImage(bytes);
  return {...type,bytes,declared,mismatch:!!declared&&declared!==type.mime};
}
export function convertUnits(raw,base,direction='px',precision=4){
  if(String(base).trim()===''||!Number.isFinite(Number(base))||Number(base)<=0||Number(base)>10000)throw Error('Root font size must be greater than 0 and no more than 10,000px.');
  if(!Number.isInteger(+precision)||+precision<0||+precision>8)throw Error('Choose 0–8 decimal places.');
  const tokens=String(raw).trim().split(/[\s,;]+/).filter(Boolean);
  if(tokens.length>1000)throw Error('Convert up to 1,000 values at a time.');
  return tokens.map(t=>{
    if(!/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$/.test(t)||!Number.isFinite(+t)||Math.abs(+t)>1e9)throw Error('Enter numbers separated by spaces, commas or new lines (maximum magnitude: 1 billion).');
    const value=direction==='px'?+t/+base:+t*+base;
    if(!Number.isFinite(value)||Math.abs(value)>=1e15)throw Error('The result is too large. Adjust the values or root size.');
    return {input:+t,value,output:String(Number(value.toFixed(+precision)))};
  });
}
export function csv(rows){return rows.map(r=>r.map(v=>'"'+String(v).replace(/"/g,'""')+'"').join(',')).join('\r\n');}
