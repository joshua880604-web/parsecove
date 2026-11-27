// Local, dependency-free conversions. Limits apply before parsing or allocation.
export const TEXT_LIMIT=250000, HEX_LIMIT=5000000, BYTE_LIMIT=1000000, JSON_LIMIT=1000000;

export function requireUnicode(value){
 for(let i=0;i<value.length;i++){
  const n=value.charCodeAt(i);
  if(n>=0xd800&&n<=0xdbff){const next=value.charCodeAt(++i);if(!(next>=0xdc00&&next<=0xdfff))throw Error('Text contains an unpaired Unicode surrogate. This tool requires well-formed Unicode text.');}
  else if(n>=0xdc00&&n<=0xdfff)throw Error('Text contains an unpaired Unicode surrogate. This tool requires well-formed Unicode text.');
 }
 return value;
}
function colorResult(r,g,b,alphaByte,hasAlpha,requestedAlpha=null){
 const alpha=alphaByte/255,part=n=>n.toString(16).padStart(2,'0').toUpperCase();
 const hex='#'+[r,g,b].map(part).join('')+(hasAlpha?part(alphaByte):'');
 const rgb=hasAlpha?`rgba(${r}, ${g}, ${b}, ${Number(alpha.toFixed(6))})`:`rgb(${r}, ${g}, ${b})`;
 return {r,g,b,alphaByte,alpha,hasAlpha,hex,rgb,quantized:requestedAlpha!==null&&Math.abs(requestedAlpha-alpha)>1e-12};
}
export function hexColor(value){
 const raw=String(value).trim();if(raw.length>9)throw Error('Use a 3-, 4-, 6- or 8-digit HEX color, optionally starting with #.');
 let hex=raw.replace(/^#/,'');
 if(!/^(?:[0-9a-f]{3}|[0-9a-f]{4}|[0-9a-f]{6}|[0-9a-f]{8})$/i.test(hex))throw Error('Use a 3-, 4-, 6- or 8-digit HEX color, optionally starting with #.');
 const hasAlpha=hex.length===4||hex.length===8;
 if(hex.length<5)hex=[...hex].map(c=>c+c).join('');
 const bytes=hex.match(/../g).map(h=>parseInt(h,16));
 return colorResult(...bytes.slice(0,3),hasAlpha?bytes[3]:255,hasAlpha);
}
export function rgbColor(red,green,blue,opacity=''){
 const channels=[red,green,blue].map((v,i)=>{
  const raw=String(v).trim(),n=Number(raw);
  if(!/^\d{1,3}$/.test(raw)||!Number.isInteger(n)||n>255)throw Error(`${['Red','Green','Blue'][i]} must be a whole number from 0 to 255.`);
  return n;
 });
 const raw=String(opacity).trim();
 if(!raw)return colorResult(...channels,255,false);
 const a=Number(raw);
 if(!/^(?:\d+(?:\.\d*)?|\.\d+)$/.test(raw)||!Number.isFinite(a)||a<0||a>1)throw Error('Alpha must be a number from 0 to 1, or left empty for opaque RGB.');
 return colorResult(...channels,Math.round(a*255),true,a);
}
export function escapeJson(value,wrap=true){
 const raw=String(value);if(raw.length>JSON_LIMIT)throw Error('Use no more than 1,000,000 UTF-16 code units.');
 const encoded=JSON.stringify(requireUnicode(raw));return wrap?encoded:encoded.slice(1,-1);
}
export function unescapeJson(value,kind='literal'){
 const raw=String(value);if(raw.length>JSON_LIMIT)throw Error('Use no more than 1,000,000 UTF-16 code units.');
 if(!['literal','content'].includes(kind))throw Error('Choose a JSON string input format.');
 let result;
 try{result=JSON.parse(kind==='literal'?raw:'"'+raw+'"');}
 catch(e){throw Error('Invalid JSON string: '+e.message.slice(0,180));}
 if(typeof result!=='string')throw Error('Enter a JSON string, including its outer double quotes. An object, array, number, boolean or null is not a string.');
 return requireUnicode(result);
}
export function hexBytes(value){
 const raw=String(value);if(raw.length>HEX_LIMIT)throw Error('Use no more than 5,000,000 HEX input characters.');
 const input=raw.trim();if(!input)return new Uint8Array();
 const parts=input.split(/\s+/);let count=0;
 for(let i=0;i<parts.length;i++){
  parts[i]=parts[i].replace(/^0x/i,'');
  if(!/^[0-9a-f]+$/i.test(parts[i]))throw Error(`Group ${i+1} contains an invalid HEX character. Use hex digits and whitespace-separated groups, optionally prefixed with 0x.`);
  if(parts[i].length%2)throw Error(`Group ${i+1} needs an even number of HEX digits so every byte is complete.`);
  count+=parts[i].length/2;
  if(count>BYTE_LIMIT)throw Error('Use no more than 1,000,000 decoded bytes.');
 }
 const hex=parts.join(''),bytes=new Uint8Array(count);
 for(let i=0;i<count;i++)bytes[i]=parseInt(hex.slice(i*2,i*2+2),16);
 return bytes;
}
export function textBytes(value){
 const raw=String(value);if(raw.length>TEXT_LIMIT)throw Error('Use no more than 250,000 UTF-16 code units of text.');
 return new TextEncoder().encode(requireUnicode(raw));
}
export function hexString(bytes,uppercase=false,spaced=true){
 if(bytes.length>BYTE_LIMIT)throw Error('Use no more than 1,000,000 bytes.');
 let result=Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join(spaced?' ':'');
 return uppercase?result.toUpperCase():result;
}
export function utf8Text(bytes){
 // Preserve an initial U+FEFF as content rather than silently dropping its bytes.
 return new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(bytes);
}
