import {timestamp,fromISO,encodeText,decodeText,toBase64,fromBase64,parseImage,detectImage,convertUnits,csv} from './core.js';
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const text=(id,value)=>$(id).textContent=value;
const showError=(id,e)=>{const el=$(id);el.hidden=!e;el.textContent=e?.message||String(e||'');};
let toastTimer;
let pauseCurrentClock=null;
function toast(message){$('.toast').textContent=message;$('.toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('.toast').hidden=true,3000);}
async function copy(value){if(!value){toast('Nothing to copy yet.');return;}try{await navigator.clipboard.writeText(value);toast('Copied to clipboard.');}catch{toast('Clipboard unavailable. Select the result and copy it manually.');}}
$$('[data-copy]').forEach(b=>b.addEventListener('click',()=>{if(b.hasAttribute('data-clock-copy'))pauseCurrentClock?.();const el=document.getElementById(b.dataset.copy);copy(el.value??el.textContent);}));
function modes(id,handler){$$(`${id} button`).forEach(b=>b.addEventListener('click',()=>{if(b.getAttribute('aria-pressed')==='true')return;$$(`${id} button`).forEach(x=>{x.classList.toggle('selected',x===b);x.setAttribute('aria-pressed',String(x===b));});handler(b.dataset.mode);}));}
function filter(input,list,empty){const q=input.value.trim().toLowerCase();let count=0;list.forEach(a=>{a.hidden=!a.dataset.search.includes(q);if(!a.hidden)count++;});if(empty)empty.hidden=count>0;}
const dialog=$('#search-dialog');$('.search-trigger').addEventListener('click',()=>{dialog.showModal();$('#global-search').focus();});$('#search-close').onclick=()=>dialog.close();dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close();}});$('#global-search').addEventListener('input',()=>filter($('#global-search'),$$('#search-list a'),$('#search-empty')));
document.addEventListener('keydown',e=>{if(e.key==='/'&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)&&!e.metaKey&&!e.ctrlKey&&!e.altKey){e.preventDefault();if($('#tool-filter'))$('#tool-filter').focus();else{if(!dialog.open)dialog.showModal();$('#global-search').focus();}}if(e.key==='Escape'){$('#sidebar').classList.remove('open');$('.mobile-menu').setAttribute('aria-expanded','false');}});
$('.sidebar-close').onclick=()=>{$('#sidebar').classList.remove('open');$('.mobile-menu').setAttribute('aria-expanded','false');$('.mobile-menu').focus();};
$('.mobile-menu').onclick=()=>{const open=$('#sidebar').classList.toggle('open');$('.mobile-menu').setAttribute('aria-expanded',String(open));};
document.addEventListener('click',e=>{if(!e.target.closest('.sidebar,.mobile-menu')&&$('#sidebar').classList.contains('open')){$('#sidebar').classList.remove('open');$('.mobile-menu').setAttribute('aria-expanded','false');}});
if($('#tool-filter'))$('#tool-filter').addEventListener('input',()=>filter($('#tool-filter'),$$('.tools-grid .tool-card'),$('#filter-empty')));
function download(data,name,type='text/plain;charset=utf-8'){const u=URL.createObjectURL(new Blob([data],{type}));const a=document.createElement('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);}
const page=document.body.dataset.page;
if(page==='guides/rem-vs-em'){
 const px=n=>`${Number(n.toFixed(4))}px`;
 function runUnits(){
  showError('#unit-error',null);
  try{
   const read=(selector,name,min,max)=>{
    const raw=$(selector).value,value=Number(raw);
    if(!raw.trim()||!Number.isFinite(value)||value<min||value>max)throw Error(`${name} must be between ${min} and ${max}.`);
    return value;
   };
   const root=read('#unit-root','Root font size',1,64),parent=read('#unit-parent','Parent font size',1,96),ratio=read('#unit-ratio','Child em multiplier',0.1,4),child=parent*ratio;
   const longest=Math.max(16,root,child);
   for(const [unit,value] of [['px',16],['rem',root],['em',child]]){
    text(`#unit-${unit}-length`,px(value));$(`#unit-${unit}-bar`).style.width=`${100*value/longest}%`;
   }
   text('#unit-summary',`Child font size: ${px(parent)} × ${ratio} = ${px(child)}.`);
   text('#unit-font-em',px(parent));text('#unit-font-rem',px(root));text('#unit-padding-em',px(child));text('#unit-padding-rem',px(root));
   text('#unit-css',`html { font-size: ${root}px; }\n.parent { font-size: ${parent}px; }\n.child { font-size: ${ratio}em; }`);
   $('#unit-results').hidden=false;
  }catch(e){$('#unit-results').hidden=true;text('#unit-css','');showError('#unit-error',e);}
 }
 ['#unit-root','#unit-parent','#unit-ratio'].forEach(id=>$(id).addEventListener('input',runUnits));
 $('#unit-reset').onclick=()=>{$('#unit-root').value='16';$('#unit-parent').value='20';$('#unit-ratio').value='1.25';runUnits();};
 runUnits();
}

if(page==='guides/unix-timestamp-seconds-vs-milliseconds'){
 function compareEpochUnits(){
  showError('#epoch-guide-error',null);
  for(const unit of ['seconds','milliseconds']){
   $(`#epoch-guide-${unit}`).value='';showError(`#epoch-guide-${unit}-error`,null);
   $(`[data-copy="epoch-guide-${unit}"]`).disabled=true;
  }
  const raw=$('#epoch-guide-input').value.trim();if(!raw)return;
  if(raw.length>24||!/^-?\d+$/.test(raw)){
   showError('#epoch-guide-error',Error('Enter a whole-number timestamp, up to 24 characters.'));return;
  }
  for(const unit of ['seconds','milliseconds']){
   try{$(`#epoch-guide-${unit}`).value=timestamp(raw,unit).iso;$(`[data-copy="epoch-guide-${unit}"]`).disabled=false;}
   catch(e){showError(`#epoch-guide-${unit}-error`,e);}
  }
 }
 $('#epoch-guide-input').addEventListener('input',compareEpochUnits);
 $('#epoch-guide-reset').onclick=()=>{$('#epoch-guide-input').value='1700000000';compareEpochUnits();};
 $('#epoch-guide-clear').onclick=()=>{$('#epoch-guide-input').value='';compareEpochUnits();};
 const samples=new Map([['seconds','1700000000'],['milliseconds','1700000000000'],['early','999'],['negative','-1']]);
 $$('[data-epoch-example]').forEach(button=>button.onclick=()=>{$('#epoch-guide-input').value=samples.get(button.dataset.epochExample);compareEpochUnits();});
 compareEpochUnits();
}

if(page==='unix-timestamp-converter'){
 let clockPaused=false,clockTimer;
 function tickClock(){if(clockPaused||document.hidden)return;const now=Date.now();$('#clock-seconds').value=String(Math.floor(now/1000));$('#clock-ms').value=String(now);text('#clock-iso',new Date(now).toISOString());}
 function setClockPaused(paused){clockPaused=paused;$('#clock-toggle').setAttribute('aria-pressed',String(paused));text('#clock-toggle',paused?'Resume updates':'Pause updates');text('#clock-state',paused?'Paused · this snapshot stays visible':'Device time · updates once a second');if(!paused)tickClock();}
 pauseCurrentClock=()=>setClockPaused(true);
 $('#clock-toggle').onclick=()=>setClockPaused(!clockPaused);
 function startClock(){clearInterval(clockTimer);tickClock();clockTimer=setInterval(tickClock,1000);}
 window.addEventListener('pagehide',()=>clearInterval(clockTimer));window.addEventListener('pageshow',startClock);document.addEventListener('visibilitychange',tickClock);startClock();
 let mode='timestamp',batchCSV='';
 function clearResult(){['#time-readable','#time-zone-label','#time-iso','#time-seconds','#time-ms','#time-detected'].forEach(id=>text(id,''));$('#time-copy').value='';$('#batch-output').value='';text('#batch-summary','');batchCSV='';$('#batch-download').disabled=true;}
 function run(){showError('#time-error',null);clearResult();try{
  if(mode==='batch'){
   const lines=$('#batch-input').value.split(/\r?\n/).filter(x=>x.trim());if(lines.length>2000)throw Error('Use no more than 2,000 non-empty lines.');if(!lines.length)return;
   let bad=0;const rows=lines.map(line=>{try{const v=timestamp(line,$('#batch-unit').value);return [line.trim(),v.iso,''];}catch(e){bad++;return [line.trim(),'',e.message];}});
   const all=[['input','iso_utc','error'],...rows];batchCSV=csv(all);$('#batch-output').value=batchCSV;$('#time-copy').value=batchCSV;$('#batch-download').disabled=false;text('#batch-summary',`${lines.length-bad} converted · ${bad} invalid · UTC output`);return;
  }
  const raw=mode==='timestamp'?$('#timestamp-input').value:$('#iso-input').value;if(!raw.trim())return;
  const v=mode==='timestamp'?timestamp(raw,$('#time-unit').value):fromISO(raw);
  const zone=$('#time-zone').value==='local'?Intl.DateTimeFormat().resolvedOptions().timeZone:$('#time-zone').value;
  const options={timeZone:zone,year:'numeric',month:'short',day:'numeric',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'};
  const rendered=new Intl.DateTimeFormat('en-US',options).format(v.date);
  text('#time-readable',rendered);text('#time-zone-label',`${zone} · Same instant, different display`);text('#time-iso',v.iso);text('#time-seconds',v.seconds);text('#time-ms',v.ms);text('#time-detected',mode==='date'?'ISO date with explicit timezone':v.unit+($('#time-unit').value==='auto'?' (auto-detected)':''));
  $('#time-copy').value=`${v.iso}\nUnix seconds: ${v.seconds}\nUnix milliseconds: ${v.ms}\n${zone}: ${rendered}`;
 }catch(e){showError('#time-error',e);}}
 modes('#time-modes',next=>{mode=next;$('#time-single').hidden=next!=='timestamp';$('#time-date').hidden=next!=='date';$('#time-batch').hidden=next!=='batch';$('#time-result').hidden=next==='batch';$('#batch-result').hidden=next!=='batch';run();});
 ['#timestamp-input','#iso-input','#batch-input'].forEach(id=>$(id).addEventListener('input',()=>{clearResult();showError('#time-error',null);}));
 $('#time-convert').onclick=run;$('#time-unit').onchange=run;$('#time-zone').onchange=run;$('#batch-unit').onchange=run;
 ['#timestamp-input','#iso-input'].forEach(id=>$(id).addEventListener('keydown',e=>{if(e.key==='Enter')run();}));
 $('#time-now').onclick=()=>{const now=Date.now();if(mode==='batch')$('#batch-input').value=String($('#batch-unit').value==='seconds'?Math.floor(now/1000):now);else if(mode==='date')$('#iso-input').value=new Date(now).toISOString();else $('#timestamp-input').value=String($('#time-unit').value==='milliseconds'?now:Math.floor(now/1000));run();};
 $('#time-sample').onclick=()=>{if(mode==='batch')$('#batch-input').value=$('#batch-unit').value==='seconds'?'1700000000\n1700086400\ninvalid':'1700000000000\n1700086400000\ninvalid';else if(mode==='date')$('#iso-input').value='2023-11-14T22:13:20Z';else $('#timestamp-input').value=$('#time-unit').value==='milliseconds'?'1700000000000':'1700000000';run();};
 $('#time-clear').onclick=()=>{$(mode==='timestamp'?'#timestamp-input':mode==='date'?'#iso-input':'#batch-input').value='';run();};
 $('#batch-download').onclick=()=>{if(batchCSV)download(batchCSV,'parsecove-timestamps.csv','text/csv;charset=utf-8');};
 const preset=new URLSearchParams(location.search).get('example');
 if(preset==='seconds'||preset==='milliseconds'){
  $('#time-unit').value=preset;$('#timestamp-input').value=preset==='seconds'?'1700000000':'1700000000000';
 }
 run();
}
if(page==='px-to-rem'||page==='rem-to-px'){
 let direction=page==='rem-to-px'?'rem':'px',conversionCSV='';
 function run(){
  showError('#px-error',null);$('#px-output').value='';text('#px-value','');text('#px-equation','');$('#px-preview').style.fontSize='24px';
  conversionCSV='';$('#px-download').disabled=true;
  const table=$('#px-table');let referenceReady=false;
  try{
   const base=$('#px-base').value,precision=+$('#px-precision').value;
   const common=JSON.parse(table.dataset.values),tableDirection=table.dataset.sourceUnit;
   const references=convertUnits(common.join(' '),base,tableDirection,precision),half=references.length/2;
   const tableSource=tableDirection==='px'?'px':'rem',tableTarget=tableDirection==='px'?'rem':'px';
   table.replaceChildren();
   for(let i=0;i<half;i++){
    const tr=document.createElement('tr');
    for(const row of [references[i],references[i+half]]){
     for(const value of [`${row.input}${tableSource}`,`${row.output}${tableTarget}`]){
      const td=document.createElement('td');td.textContent=value;tr.append(td);
     }
    }
    table.append(tr);
   }
   text('#px-table-base',`At a ${Number(base)}px root size`);referenceReady=true;
   const rows=convertUnits($('#px-input').value,base,direction,precision);
   if(!rows.length)return;
   const source=direction==='px'?'px':'rem',unit=direction==='px'?'rem':'px';
   $('#px-output').value=rows.map(r=>`${r.output}${unit}`).join('\n');
   const first=rows[0],span=document.createElement('span');span.textContent=unit;$('#px-value').textContent=first.output;$('#px-value').append(span);
   text('#px-equation',rows.length===1?`${first.input}${source} ${direction==='px'?'÷':'×'} ${Number(base)} = ${first.output}${unit}`:`${rows.length} values converted · ${precision} decimal places maximum`);
   const size=direction==='px'?first.input:first.value;$('#px-preview').style.fontSize=`${Math.max(8,Math.min(72,Math.abs(size)))}px`;
   conversionCSV=csv([['input','input_unit','root_px','output','output_unit'],...rows.map(r=>[r.input,source,Number(base),r.output,unit])]);
   $('#px-download').disabled=false;
  }catch(e){
   if(!referenceReady){table.replaceChildren();text('#px-table-base','Set a valid root size');}
   showError('#px-error',e);
  }
 }
 modes('#px-modes',m=>{direction=m;text('#px-input-label',m==='px'?'Pixels':'REM values');run();});
 ['#px-base','#px-input','#px-precision'].forEach(id=>$(id).addEventListener('input',run));
 $('#px-sample').onclick=()=>{$('#px-input').value=direction==='px'?'4, 8, 12, 16, 24, 32, 48, 64':'0.25, 0.5, 0.75, 1, 1.5, 2, 3, 4';run();};
 $('#px-clear').onclick=()=>{$('#px-input').value='';run();};
 for(const mode of ['px','rem'])$$(`[data-${mode}-quick]`).forEach(b=>b.onclick=()=>{$(`#px-modes [data-mode=${mode}]`).click();$('#px-input').value=b.getAttribute(`data-${mode}-quick`);run();});
 $('#px-download').onclick=()=>{if(conversionCSV)download(conversionCSV,`parsecove-${direction==='px'?'px-to-rem':'rem-to-px'}.csv`,'text/csv;charset=utf-8');};
 run();
}
if(page==='base64'){
 let mode='decode';
 function run(){showError('#b64-error',null);$('#b64-output').value='';text('#b64-stats','');try{
  const input=$('#b64-input').value;if(!input)return;
  const output=mode==='decode'?decodeText(input,$('#b64-variant').value):encodeText(input,$('#b64-variant').value,$('#b64-padding').checked);
  $('#b64-output').value=output;text('#b64-stats',`${new TextEncoder().encode(input).length.toLocaleString()} input bytes · ${new TextEncoder().encode(output).length.toLocaleString()} output bytes`);
 }catch(e){showError('#b64-error',e);}}
 modes('#b64-modes',m=>{const previous=$('#b64-output').value;mode=m;if(previous)$('#b64-input').value=previous;text('#b64-input-label',m==='decode'?'Base64 input':'Text to encode');text('#b64-result-label',m==='decode'?'DECODED TEXT':'ENCODED BASE64');text('#b64-convert',m==='decode'?'Decode text':'Encode text');$('#b64-padding').disabled=m==='decode';run();});$('#b64-padding').disabled=true;
 $('#b64-convert').onclick=run;$('#b64-variant').onchange=run;$('#b64-padding').onchange=run;$('#b64-input').addEventListener('input',()=>{$('#b64-output').value='';text('#b64-stats','');showError('#b64-error',null);});$('#b64-sample').onclick=()=>{$('#b64-input').value=mode==='decode'?encodeText('Hello, 世界 👋',$('#b64-variant').value):'Hello, 世界 👋';run();};$('#b64-clear').onclick=()=>{$('#b64-input').value='';run();};run();
}
if(page==='base64url-decode'){
 let mode='decode',decodedBytes=null,lastText=null,lastEncoded='';
 function reset(){
  decodedBytes=null;lastText=null;lastEncoded='';
  $('#url-output').value='';$('#url-standard').value='';text('#url-stats','');
  showError('#url-error',null);$('#url-note').hidden=true;text('#url-note','');
  $('#url-download').disabled=true;$('#url-bytes-download').disabled=true;
 }
 function run(){
  reset();
  try{
   const input=$('#url-input').value;
   if(mode==='decode'&&input.length>2000000)throw Error('Use no more than 2 million encoded characters.');
   if(!input||(mode==='decode'&&!input.trim()))return;
   let bytes,plain=null,output;
   if(mode==='encode'){
    bytes=new TextEncoder().encode(input);
    if(bytes.length>1000000)throw Error('Use no more than 1 MB (1,000,000 bytes) of UTF-8 text.');
    output=encodeText(input,'url',$('#url-padding').checked);plain=input;
   }else{
    if(input.includes('.'))throw Error('Paste one Base64URL value. For a JWT, use one encoded segment; decoding does not verify its signature.');
    bytes=fromBase64(input,'url');
    try{plain=new TextDecoder('utf-8',{fatal:true}).decode(bytes);}catch{}
    if($('#url-format').value==='hex'){
     output=Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join(' ');
    }else if(plain!==null){output=plain;}
    else{
     output='';text('#url-note','Valid Base64URL, but these bytes are not UTF-8 text. Choose Hex bytes or download the original bytes.');$('#url-note').hidden=false;
    }
   }
   const standard=toBase64(bytes);
   decodedBytes=bytes;lastText=plain;lastEncoded=toBase64(bytes,'url',$('#url-padding').checked);
   $('#url-output').value=output;$('#url-standard').value=standard;
   text('#url-stats',mode==='encode'?`${bytes.length.toLocaleString()} UTF-8 bytes · ${output.length.toLocaleString()} encoded characters`:`${bytes.length.toLocaleString()} decoded bytes · ${input.trim().endsWith('=')?'padded':'unpadded'} input`);
   $('#url-download').disabled=!output.length;$('#url-bytes-download').disabled=!bytes.length;
  }catch(e){reset();showError('#url-error',e);}
 }
 function labels(){
  const decode=mode==='decode';
  text('#url-input-label',decode?'Base64URL input':'Text to encode');
  text('#url-output-label',decode?($('#url-format').value==='hex'?'DECODED HEX BYTES':'DECODED TEXT'):'ENCODED BASE64URL');
  text('#url-convert',decode?'Decode Base64URL':'Encode Base64URL');
  $('#url-format-wrap').hidden=!decode;$('#url-padding-wrap').hidden=decode;
  text('#url-hint',decode?'Paste one URL-safe value using A–Z, a–z, 0–9, - and _. Valid padded or unpadded input is accepted; whitespace is ignored. Up to 2 million encoded characters.':'Text is encoded as UTF-8. Padding is omitted unless selected above. Up to 1 MB (1,000,000 bytes) of UTF-8 text.');
 }
 modes('#url-modes',m=>{const next=m==='decode'?lastEncoded:(lastText??'');mode=m;$('#url-input').value=next;labels();run();});
 $('#url-convert').onclick=run;
 $('#url-input').addEventListener('input',reset);
 $('#url-padding').onchange=run;
 $('#url-format').onchange=()=>{labels();run();};
 $('#url-clear').onclick=()=>{$('#url-input').value='';reset();};
 $$('[data-url-example]').forEach(b=>b.onclick=()=>{
  const kind=b.dataset.urlExample;
  if(kind==='binary'){
   $('#url-modes [data-mode=decode]').click();$('#url-format').value='hex';$('#url-input').value='-__v';
  }else{
   const plain=kind==='emoji'?'😀':'{"message":"Hello"}';$('#url-format').value='text';
   $('#url-input').value=mode==='decode'?encodeText(plain,'url',false):plain;
  }
  labels();run();
 });
 $('#url-download').onclick=()=>{
  const value=$('#url-output').value;if(!value)return;
  const name=mode==='encode'?'parsecove-base64url.txt':$('#url-format').value==='hex'?'parsecove-decoded-hex.txt':'parsecove-decoded.txt';
  download(value,name);
 };
 $('#url-bytes-download').onclick=()=>{if(decodedBytes?.length)download(decodedBytes,'parsecove-decoded.bin','application/octet-stream');};
 labels();run();
}

if(page==='base64-to-image'||page==='image-to-base64'){
 let mode=page==='image-to-base64'?'encode':'decode',url='',bytes=null,type=null,task=0;
 function syncMode(){
  $('#image-decode-input').hidden=mode!=='decode';
  $('#image-encode-input').hidden=mode!=='encode';
  text('#image-result-title',mode==='encode'?'IMAGE TO BASE64':'IMAGE PREVIEW');
  $('#image-download').classList.toggle('primary',mode==='decode');
  text('#image-error-title',mode==='encode'?'Check the file':'Check the source');
  text('#image-error-detail',mode==='encode'?'Choose a valid PNG, JPEG, GIF or WebP image within the size and preview limits.':'Paste the Base64 value or a data URI, not a complete HTML tag or JSON response. The decoded bytes must be a supported image.');
  $('#image-error-link').href=mode==='encode'?(page==='image-to-base64'?'#encoding-help':'/image-to-base64/#encoding-help'):(page==='base64-to-image'?'#image-troubleshooting':'/base64-to-image/#image-troubleshooting');
 }
 function reset(){
  task++;
  if(url)URL.revokeObjectURL(url);
  url='';bytes=null;type=null;
  $('#image-output').hidden=true;$('#image-output').removeAttribute('src');
  $('#image-empty').hidden=false;$('#image-meta').hidden=true;
  $('#image-download').hidden=true;$('#image-download').removeAttribute('href');
  $('#image-text-wrap').hidden=mode!=='encode';$('#image-text').value='';
  $('#image-text-copy').disabled=true;$('#image-text-download').disabled=true;
  text('#image-file-name','No image selected.');
  for(const id of ['#image-mime','#image-dimensions','#image-size'])text(id,'');
  text('#image-status',mode==='encode'?'Waiting for an image':'Waiting for input');
  showError('#image-error',null);$('#image-warning').hidden=true;
  $('#image-error-help').hidden=true;$('#image-preservation').hidden=true;
 }
 function encoded(){
  if(!bytes||mode!=='encode')return;
  const raw=toBase64(bytes),uri=`data:${type.mime};base64,${raw}`,format=$('#image-format').value;
  $('#image-text').value=format==='raw'?raw:format==='html'?`<img src="${uri}" alt="">`:format==='css'?`background-image: url("${uri}");`:uri;
  $('#image-text-wrap').hidden=false;
  $('#image-text-copy').disabled=false;$('#image-text-download').disabled=false;
 }
 async function display(info,ticket){
  const candidate=URL.createObjectURL(new Blob([info.bytes],{type:info.mime})),probe=new Image();
  try{
   probe.src=candidate;await probe.decode();
   if(probe.naturalWidth*probe.naturalHeight>40000000)throw Error('Image dimensions exceed the 40-megapixel preview limit.');
  }catch(e){
   URL.revokeObjectURL(candidate);
   throw Error(e.message.includes('megapixel')?e.message:'The bytes have an image signature, but your browser could not decode this image.');
  }
  if(ticket!==task){URL.revokeObjectURL(candidate);return;}
  url=candidate;bytes=info.bytes;type=info;
  $('#image-output').src=url;$('#image-output').hidden=false;$('#image-empty').hidden=true;
  $('#image-meta').hidden=false;$('#image-download').href=url;
  $('#image-download').download=`parsecove-image.${info.ext}`;$('#image-download').hidden=false;
  text('#image-status','Ready');text('#image-mime',info.mime);
  text('#image-dimensions',`${probe.naturalWidth} × ${probe.naturalHeight}`);
  text('#image-size',`${info.bytes.length.toLocaleString()} B`);$('#image-preservation').hidden=false;
  if(info.mismatch){text('#image-warning',`Declared type ${info.declared} differs from detected ${info.mime}. Download uses the detected format.`);$('#image-warning').hidden=false;}
  encoded();
 }
 async function decode(){
  reset();const ticket=task;
  if(!$('#image-input').value.trim())return;
  try{
   const info=parseImage($('#image-input').value);text('#image-status','Checking image…');await display(info,ticket);
  }catch(e){if(ticket===task){text('#image-status','Check your input');showError('#image-error',e);$('#image-error-help').hidden=false;}}
 }
 async function file(selected){
  reset();const ticket=task;
  if(!selected)return;
  text('#image-file-name',selected.name);
  try{
   if(selected.size>10485760)throw Error('Choose an image of 10 MB or smaller.');
   const data=new Uint8Array(await selected.arrayBuffer());
   if(ticket!==task)return;
   const info={...detectImage(data),bytes:data};
   text('#image-status','Checking image…');await display(info,ticket);
  }catch(e){if(ticket===task){text('#image-status','Check your file');showError('#image-error',e);$('#image-error-help').hidden=false;}}
 }
 async function loadImageExample(key){
  reset();const ticket=task,exampleMode=mode;text('#image-status','Loading local example…');
  try{
   const {examples}=await import('./image-examples.js');
   if(ticket!==task)return;
   const sample=examples[key];if(!sample)throw Error('Unknown image example.');
   if(exampleMode==='encode'){
    const info=parseImage(sample.base64);
    $('#image-file').value='';
    await file(new File([info.bytes],`example-${key}.${info.ext}`,{type:info.mime}));
   }else{
    $('#image-input').value=`data:${sample.mime};base64,${sample.base64}`;await decode();
   }
  }catch(e){if(ticket===task){showError('#image-error',Error('The local example could not be loaded. Reload the page or try an image from your device.'));text('#image-status','Check the example');}}
 }
 modes('#image-modes',next=>{mode=next;syncMode();reset();$('#image-file').value='';});
 $('#image-convert').onclick=decode;$('#image-input').addEventListener('input',reset);
 $('#image-sample').onclick=()=>loadImageExample('png');
 $$('[data-image-example]').forEach(button=>button.onclick=()=>loadImageExample(button.dataset.imageExample));
 $$('[data-image-encode-example]').forEach(button=>button.onclick=()=>loadImageExample(button.dataset.imageEncodeExample));
 $('#image-file').onchange=event=>file(event.target.files[0]);$('#image-format').onchange=encoded;
 $('#image-text-download').onclick=()=>{
  const value=$('#image-text').value;if(!value)return;
  const format=$('#image-format').value;
  const name=format==='html'?'parsecove-image.html':format==='css'?'parsecove-image.css':format==='raw'?'parsecove-image-base64.txt':'parsecove-image-data-url.txt';
  download(value,name);
 };
 $('#image-clear').onclick=()=>{reset();$('#image-input').value='';$('#image-file').value='';};
 const drop=$('#image-drop');
 ['dragenter','dragover'].forEach(name=>drop.addEventListener(name,event=>{event.preventDefault();drop.classList.add('dragging');}));
 ['dragleave','drop'].forEach(name=>drop.addEventListener(name,event=>{event.preventDefault();drop.classList.remove('dragging');}));
 drop.addEventListener('drop',event=>{
  const files=event.dataTransfer.files;
  if(files.length!==1){reset();showError('#image-error',Error('Choose one image at a time.'));return;}
  $('#image-file').value='';file(files[0]);
 });
 window.addEventListener('pagehide',()=>{if(url)URL.revokeObjectURL(url);});
 syncMode();reset();
 const preset=new URLSearchParams(location.search).get('example');
 if(['png','jpeg','webp'].includes(preset))loadImageExample(preset);
}
