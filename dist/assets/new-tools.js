import {hexColor,rgbColor,escapeJson,unescapeJson,hexBytes,textBytes,hexString,utf8Text} from './conversion-core.js';

export function initNewTool(page,{$,$$,text,showError,modes,download}){
 const setCopy=(id,enabled)=>{$(`[data-copy="${id}"]`).disabled=!enabled;};
 if(page==='hex-to-rgb'){
  let mode='hex',current=null;
  function reset(){current=null;showError('#color-error',null);['#color-hex-output','#color-rgb-output'].forEach(id=>$(id).value='');['#color-red-value','#color-green-value','#color-blue-value','#color-alpha-value','#color-note'].forEach(id=>text(id,''));$('#color-fill').style.backgroundColor='transparent';setCopy('color-hex-output',false);setCopy('color-rgb-output',false);}
  function run(){reset();if(mode==='hex'&&!$('#color-input').value.trim())return;
   try{
    if(mode==='rgb'&&$('#color-a').validity.badInput)throw Error('Enter a decimal alpha from 0 to 1, or leave it empty.');
    current=mode==='hex'?hexColor($('#color-input').value):rgbColor($('#color-r').value,$('#color-g').value,$('#color-b').value,$('#color-a').value);
    $('#color-hex-output').value=current.hex;$('#color-rgb-output').value=current.rgb;$('#color-fill').style.backgroundColor=current.rgb;
    for(const [id,v] of [['red',current.r],['green',current.g],['blue',current.b],['alpha',`${current.alphaByte}/255`]])text(`#color-${id}-value`,String(v));
    text('#color-note',current.quantized?'Alpha was rounded to the nearest 8-bit value for HEX. RGB output and preview use that same value.':current.hasAlpha?'HEX stores alpha as an 8-bit value. The RGB alpha shown is rounded to six decimal places.':'Opaque RGB color. Add an alpha value to include transparency.');
    setCopy('color-hex-output',true);setCopy('color-rgb-output',true);
   }catch(e){showError('#color-error',e);}
  }
  modes('#color-modes',next=>{const old=current;mode=next;$('#color-hex-fields').hidden=next!=='hex';$('#color-rgb-fields').hidden=next!=='rgb';if(old){if(next==='hex')$('#color-input').value=old.hex;else{for(const key of ['r','g','b'])$(`#color-${key}`).value=old[key];$('#color-a').value=old.hasAlpha?old.alpha:'';}}run();});
  ['#color-input','#color-r','#color-g','#color-b','#color-a'].forEach(id=>$(id).addEventListener('input',run));
  $$('[data-color-example]').forEach(b=>b.onclick=()=>{$('#color-modes [data-mode=hex]').click();$('#color-input').value=b.dataset.colorExample;run();});
  $('#color-clear').onclick=()=>{if(mode==='hex')$('#color-input').value='';else ['#color-r','#color-g','#color-b','#color-a'].forEach(id=>$(id).value='');reset();};
  run();
 }
 if(page==='json-unescape'){
  let mode='unescape',result=null;
  function reset(){result=null;$('#json-output').value='';text('#json-copy','');text('#json-stats','');showError('#json-error',null);$('#json-download').disabled=true;$('#json-next-layer').hidden=true;setCopy('json-copy',false);}
  function labels(){const decode=mode==='unescape';$('#json-kind-wrap').hidden=!decode;$('#json-wrap-field').hidden=decode;text('#json-input-label',decode?'Escaped JSON string':'Plain text to escape');text('#json-output-label',decode?'UNESCAPED TEXT':'ESCAPED JSON STRING');text('#json-convert',decode?'Unescape one layer':'Escape text');}
  function run(explicit=false){reset();const raw=$('#json-input').value;if(!raw&&!explicit)return;
   try{result=mode==='unescape'?unescapeJson(raw,$('#json-input-kind').value):escapeJson(raw,$('#json-wrap').checked);$('#json-output').value=result;text('#json-copy',result);text('#json-stats',`${result.length.toLocaleString()} output UTF-16 code units · ${new TextEncoder().encode(result).length.toLocaleString()} UTF-8 bytes${result.length?'':' · valid empty string'}${mode==='unescape'?' · one layer decoded':''}`);$('#json-download').disabled=false;setCopy('json-copy',!!result.length);if(mode==='unescape'){try{$('#json-next-layer').hidden=typeof JSON.parse(result)!=='string';}catch{}}}
   catch(e){showError('#json-error',e);}
  }
  modes('#json-modes',next=>{const old=result;mode=next;if(old!==null){$('#json-input').value=old;if(next==='unescape')$('#json-input-kind').value=$('#json-wrap').checked?'literal':'content';}labels();run(old!==null);});
  $('#json-input').addEventListener('input',reset);$('#json-input-kind').onchange=()=>run();$('#json-wrap').onchange=()=>run(true);$('#json-convert').onclick=()=>run(true);
  $('#json-clear').onclick=()=>{$('#json-input').value='';reset();};
  $('#json-download').onclick=()=>{if(result!==null)download(result,mode==='escape'?'parsecove-escaped-json.txt':'parsecove-unescaped.txt');};
  $('#json-next-layer').onclick=()=>{if(result===null)return;$('#json-input').value=result;$('#json-input-kind').value='literal';run(true);};
  $$('[data-json-example]').forEach(button=>button.onclick=()=>{
   const key=button.dataset.jsonExample,plain='Hello, 世界 👋\n"quoted" \\ path';
   if(key==='double'||key==='content'){$('#json-modes [data-mode=unescape]').click();$('#json-input-kind').value=key==='content'?'content':'literal';$('#json-input').value=key==='double'?JSON.stringify(JSON.stringify('{"ok":true}')):'Line 1\\nLine 2\\t\\"quoted\\"';}
   else{$('#json-input-kind').value='literal';$('#json-input').value=mode==='unescape'?JSON.stringify(key==='empty'?'':plain):key==='empty'?'':plain;}
   labels();run(true);
  });
  labels();run();
 }
 if(page==='hex-to-text'){
  let mode='decode',bytes=null,plain=null,encoded='';
  function reset(){bytes=null;plain=null;encoded='';$('#hex-main-result').hidden=false;$('#hex-output').value='';text('#hex-copy','');$('#hex-normalized').value='';text('#hex-stats','');showError('#hex-error',null);$('#hex-note').hidden=true;text('#hex-note','');$('#hex-normalized-wrap').hidden=true;$('#hex-download').disabled=true;$('#hex-bytes-download').disabled=true;setCopy('hex-copy',false);setCopy('hex-normalized',false);}
  function labels(){text('#hex-input-label',mode==='decode'?'HEX bytes':'UTF-8 text to encode');text('#hex-output-label',mode==='decode'?'DECODED UTF-8 TEXT':'ENCODED HEX');text('#hex-convert',mode==='decode'?'Decode HEX':'Encode text');text('#hex-download',mode==='decode'?'Download text':'Download HEX');text('#hex-input-hint',mode==='decode'?'Use complete byte groups, optionally prefixed with 0x, separated by whitespace. Up to 5 million input characters and 1 million decoded bytes.':'Up to 250,000 UTF-16 code units. Text is encoded as UTF-8; unpaired Unicode surrogates are rejected.');}
  function render(){if(bytes===null)return;$('#hex-main-result').hidden=mode==='decode'&&plain===null;encoded=hexString(bytes,$('#hex-uppercase').checked,$('#hex-spaced').checked);$('#hex-normalized').value=encoded;$('#hex-normalized-wrap').hidden=mode!=='decode';$('#hex-output').value=mode==='encode'?encoded:(plain??'');text('#hex-copy',mode==='encode'?encoded:(plain??''));setCopy('hex-copy',!!$('#hex-output').value.length);setCopy('hex-normalized',!!encoded.length);$('#hex-download').disabled=mode==='decode'&&plain===null;$('#hex-bytes-download').disabled=false;text('#hex-stats',`${bytes.length.toLocaleString()} bytes · ${mode==='encode'?'UTF-8 encoded':plain===null?'valid HEX; not UTF-8 text':'valid UTF-8'+(plain.length?'':' · empty string')}`);if(mode==='decode'&&plain===null){text('#hex-note','These are valid bytes, but they are not valid UTF-8 text. The HEX and original bytes remain available. Identify the original data format.');$('#hex-note').hidden=false;}}
  function run(explicit=false){reset();const raw=$('#hex-input').value;if(!raw.trim()&&!explicit)return;try{bytes=mode==='decode'?hexBytes(raw):textBytes(raw);if(mode==='encode')plain=raw;else{try{plain=utf8Text(bytes);}catch{plain=null;}}render();}catch(e){reset();showError('#hex-error',e);}}
  modes('#hex-modes',next=>{const oldBytes=bytes,oldText=plain,oldHex=encoded;mode=next;$('#hex-input').value=oldBytes!==null?(next==='encode'?(oldText??''):oldHex):'';labels();run(oldBytes!==null&&!(next==='encode'&&oldText===null));});
  $('#hex-input').addEventListener('input',reset);$('#hex-convert').onclick=()=>run(true);$('#hex-clear').onclick=()=>{$('#hex-input').value='';reset();};
  ['#hex-uppercase','#hex-spaced'].forEach(id=>$(id).onchange=render);
  const samples=new Map([['hello','48 65 6c 6c 6f'],['unicode','e4 b8 ad e6 96 87 20 f0 9f 91 8b'],['binary','fb ff ef'],['prefix','0x48 0x65 0x6c 0x6c 0x6f']]);
  $$('[data-hex-example]').forEach(button=>button.onclick=()=>{const key=button.dataset.hexExample;$('#hex-modes [data-mode=decode]').click();$('#hex-input').value=samples.get(key);run(true);});
  $('#hex-download').onclick=()=>{if(bytes!==null&&(mode==='encode'||plain!==null))download(mode==='encode'?encoded:plain,mode==='encode'?'parsecove-encoded-hex.txt':'parsecove-decoded.txt');};
  $('#hex-bytes-download').onclick=()=>{if(bytes!==null)download(bytes,'parsecove-decoded.bin','application/octet-stream');};
  labels();run();
 }
}
