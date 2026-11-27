import {decodeFile,LIMITS} from './data-common.js';
export async function initDataTool(page,{$,$$,text,showError,modes,download}){
 const yaml=page==='yaml-to-json';
 const core=yaml?await import('./yaml-core.js'):await import('./csv-core.js');
 let mode='forward',result=null,revision=0;
 const input=$('#data-input'),output=$('#data-output');
 let source=input.value;
 const copyButton=$('[data-copy="data-copy"]');
 function reset(){result=null;output.value='';text('#data-copy','');text('#data-status','Convert to see a new result.');showError('#data-error',null);$('#data-download').disabled=true;copyButton.disabled=true;}
 function changed(){revision++;reset();}
 function delimiter(){const v=$('#data-delimiter')?.value;return v==='tab'?'\t':v;}
 function run(){
  reset();
  try{
   const opts={indent:Number($('#data-indent').value)};
   if(!yaml)Object.assign(opts,{delimiter:delimiter(),headers:$('#data-headers').checked,infer:$('#data-infer').checked,skipEmpty:$('#data-skip').checked,nested:$('#data-nested').checked,protect:$('#data-protect').checked,newline:$('#data-newline').value==='lf'?'\n':'\r\n'});
   result=yaml?(mode==='forward'?core.yamlToJson(source,opts):core.jsonToYaml(source,opts)):(mode==='forward'?core.csvToJson(source,opts):core.jsonToCsv(source,opts));
   output.value=result.output;text('#data-copy',result.output);text('#data-status',result.note);copyButton.disabled=!result.output.length;$('#data-download').disabled=false;
  }catch(e){showError('#data-error',e);}
 }
 function labels(){
  const target=mode==='forward'?'JSON':yaml?'YAML':'CSV';
  text('#data-input-label',`${mode==='reverse'?'JSON':yaml?'YAML':'CSV'} input`);text('#data-output-label',`${target} RESULT`);text('#data-convert',`Convert to ${target}`);text('#data-download',`Download ${target}`);
  text('#data-indent-label',yaml&&mode==='reverse'?'YAML indentation':'JSON indentation');
  const compact=$('#data-indent option[value="0"]');compact.disabled=yaml&&mode==='reverse';if(compact.disabled&&$('#data-indent').value==='0')$('#data-indent').value='2';
  if(!yaml){$('#data-delimiter option[value="auto"]').textContent=mode==='forward'?'Auto (CSV input)':'Comma (default)';$('#data-indent').parentElement.hidden=mode==='reverse';text('#data-headers-label',mode==='forward'?'First row contains headers':'Include object headers');$$('.data-forward').forEach(el=>el.hidden=mode!=='forward');$$('.data-reverse').forEach(el=>el.hidden=mode!=='reverse');}
 }
 modes('#data-modes',next=>{const previous=result?.output;mode=next;changed();if(previous!==undefined){source=previous;input.value=previous;}labels();});
 function selectMode(next){if(mode!==next)$(`#data-modes [data-mode="${next}"]`).click();}
 input.addEventListener('input',()=>{source=input.value;changed();text('#data-file-note','');});
 $$('.data-options select,.data-options input').forEach(el=>el.addEventListener('change',changed));
 $('#data-convert').onclick=()=>{revision++;run();};
 $('#data-clear').onclick=()=>{changed();source='';input.value='';$('#data-file').value='';text('#data-file-note','');input.focus();};
 $('#data-download').onclick=()=>{if(!result)return;const ext=mode==='forward'?'json':yaml?'yaml':'csv';download(result.output,`parsecove-result.${ext}`,ext==='json'?'application/json;charset=utf-8':ext==='csv'?'text/csv;charset=utf-8':'text/yaml;charset=utf-8');};
 const examples=yaml?{
  basic:['forward','app: ParseCove\nready: true\nports:\n  - 3000\n  - 8080\nowner:\n  name: Ada\n  id: "001"'],
  types:['forward','enabled: true\nanswer: yes\nid: "001"\ndate: 2026-11-27\nmissing: null'],
  aliases:['forward','primary: &colors\n  - blue\n  - green\nsecondary: *colors'],
  json:['reverse','{"app":"ParseCove","ready":true,"owner":{"name":"Ada","id":"001"}}'],
 }:{
  basic:['forward','id,name,active\n001,Ada,true\n002,"Lin, Mei",false'],
  quoted:['forward','name,note\n"Lin, Mei","A \"\"quoted\"\" word"\nAda,"Line one\nLine two"'],
  tab:['forward','id\tname\tactive\n001\tAda\ttrue\n002\tLin\tfalse'],
  json:['reverse','[{"id":"001","name":"Ada","active":true},{"id":"002","name":"Lin, Mei","active":false}]'],
 };
 $$('[data-data-example]').forEach(button=>button.onclick=()=>{const [next,value]=examples[button.dataset.dataExample];selectMode(next);changed();source=value;input.value=value;text('#data-file-note','');if(!yaml)$('#data-delimiter').value=button.dataset.dataExample==='tab'?'tab':'auto';run();});
 $('#data-file').onchange=async()=>{
  const file=$('#data-file').files[0];if(!file)return;changed();const ticket=revision;text('#data-file-note','Reading file locally…');
  try{
   if(file.size>LIMITS.file)throw Error('File exceeds 2 MB (2,000,000 bytes).');
   const value=decodeFile(await file.arrayBuffer());if(ticket!==revision)return;
   const extension=file.name.split('.').at(-1).toLowerCase();
   selectMode(extension==='json'?'reverse':(yaml?['yaml','yml']:['csv','tsv']).includes(extension)?'forward':mode);
   if(!yaml&&['csv','tsv'].includes(extension))$('#data-delimiter').value=extension==='tsv'?'tab':'auto';
   source=value;input.value=value;revision++;text('#data-file-note',`${file.name} · ${file.size.toLocaleString()} bytes · read locally`);run();
  }catch(e){if(ticket===revision){text('#data-file-note','');showError('#data-error',e);}}
  finally{if($('#data-file').files[0]===file)$('#data-file').value='';}
 };
 labels();run();
}
