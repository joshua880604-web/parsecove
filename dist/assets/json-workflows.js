import {transformJson,compareJson} from './json-document.js';
import {decodeFile,LIMITS,outputText} from './data-common.js';

const MINIFY_SAMPLE='{\n  "id": 9007199254740993,\n  "message": "keep  two spaces",\n  "values": [1e+30, true, null]\n}';
const COMPARE_SAMPLES={
 basic:['{\n  "id": "001",\n  "active": true,\n  "tags": ["red", "blue"],\n  "note": null\n}','{\n  "tags": ["blue", "red"],\n  "id": "001",\n  "active": false,\n  "note": null,\n  "region": "EU"\n}'],
 equal:['{"first":1,"second":{"ready":true,"name":"Ada"}}','{\n  "second": {"name":"\\u0041da","ready":true},\n  "first": 1.0\n}'],
 precision:['{"id":9007199254740992,"huge":1e500,"tiny":1e-500,"decimal":1}','{"id":9007199254740993,"huge":10e499,"tiny":10e-501,"decimal":1.0000000000000001}'],
 paths:['{"a/b":{"~key":1},"":true,"note":null,"type":1}','{"a/b":{"~key":2},"":false,"type":"1"}'],
};

export function initJsonWorkflow(page,{$,$$,text,showError,modes,download}){
 if(page==='json-minify')initMinify();else initCompare();
 function initMinify(){
  let mode='minify',result=null,revision=0;
  const input=$('#json-input'),output=$('#json-output'),copy=$('[data-copy="json-output"]');
  function reset(){result=null;output.value='';copy.disabled=true;$('#json-download').disabled=true;showError('#json-error',null);text('#json-status','Run the selected action to see a new result.');for(const id of ['#json-input-bytes','#json-output-bytes','#json-savings'])text(id,'—');}
  function changed(){revision++;$('#json-run').disabled=false;reset();}
  function labels(){text('#json-run',mode==='minify'?'Minify JSON':mode==='format'?'Format JSON':'Validate JSON');text('#json-output-label',mode==='minify'?'MINIFIED JSON':mode==='format'?'FORMATTED JSON':'VALIDATED DOCUMENT');$('#json-indent-wrap').hidden=mode!=='format';}
  function run(){
   reset();
   try{
    result=transformJson(input.value,{mode,indent:Number($('#json-indent').value)});output.value=result.output;copy.disabled=false;$('#json-download').disabled=false;
    text('#json-status',mode==='validate'?'Valid JSON. The original layout is retained; an initial BOM is removed.':`${mode==='minify'?'Minified':'Formatted'} valid JSON. Number tokens, string escapes and field order are preserved.`);
    text('#json-input-bytes',`${result.inputBytes.toLocaleString()} B`);text('#json-output-bytes',`${result.outputBytes.toLocaleString()} B`);
    text('#json-savings',result.savedBytes===0?'Unchanged':`${Math.abs(result.savedPercent).toFixed(1)}% ${result.savedBytes>0?'smaller':'larger'}`);
   }catch(e){showError('#json-error',e);text('#json-status','No valid result. Correct the input and try again.');}
  }
  input.addEventListener('input',()=>{changed();text('#json-file-note','');});
  modes('#json-modes',next=>{mode=next;changed();labels();});
  $('#json-indent').onchange=changed;
  $('#json-run').onclick=()=>{changed();run();};
  $('#json-clear').onclick=()=>{changed();input.value='';$('#json-file').value='';text('#json-file-note','');input.focus();};
  $('#json-download').onclick=()=>{if(result)download(result.output,`parsecove-${mode}.json`,'application/json;charset=utf-8');};
  const examples={basic:MINIFY_SAMPLE,strings:'{ "message": "keep  two spaces", "line": "one\\ntwo", "slash": "a\\/b", "letter": "\\u0041" }',invalid:'{"a":1,"\\u0061":2}'};
  $$('[data-json-example]').forEach(button=>button.onclick=()=>{changed();input.value=examples[button.dataset.jsonExample];text('#json-file-note','');run();});
  $('#json-file').onchange=async()=>{
   const file=$('#json-file').files[0];if(!file)return;changed();const ticket=revision;$('#json-run').disabled=true;text('#json-file-note','Reading file locally…');
   try{
    if(file.size>LIMITS.file)throw Error('File exceeds 2 MB (2,000,000 bytes).');
    const value=decodeFile(await file.arrayBuffer());if(ticket!==revision)return;
    input.value=value;text('#json-file-note',`${file.name} · ${file.size.toLocaleString()} bytes · read locally`);run();
   }catch(e){if(ticket===revision){text('#json-file-note','');showError('#json-error',e);text('#json-status','No result. Check the local file.');}}
   finally{if(ticket===revision)$('#json-run').disabled=false;if($('#json-file').files[0]===file)$('#json-file').value='';}
  };
  labels();run();
 }
 function initCompare(){
  let result=null;const tickets={left:0,right:0},pending={left:false,right:false};
  const copy=$('[data-copy="compare-report"]');
  function reset(){result=null;text('#compare-report','');$('#compare-rows').replaceChildren();$('#compare-table-wrap').hidden=true;$('#compare-scroll-hint').hidden=true;$('#compare-limit').hidden=true;copy.disabled=true;$('#compare-download').disabled=true;showError('#compare-error',null);text('#compare-summary','Compare the current documents to see their differences.');}
  function changed(side){tickets[side]++;pending[side]=false;reset();$('#compare-run').disabled=pending.left||pending.right;}
  function cancelAll(){changed('left');changed('right');}
  function run(){
   if(pending.left||pending.right)return;reset();
   try{
    const compared=compareJson($('#compare-left').value,$('#compare-right').value);
    const report=outputText(JSON.stringify(compared,null,2));
    result=report;text('#compare-report',report);copy.disabled=false;$('#compare-download').disabled=false;
    text('#compare-summary',compared.equal?(compared.textIdentical?'Same JSON values and identical source text.':'Same JSON values. Source layout, object key order, string escapes or number spelling differ.'):`${compared.differences.length} ${compared.limited?'listed ':''}${compared.differences.length===1?'difference':'differences'} found.${compared.limited?' More differences exist.':''}`);
    $('#compare-limit').hidden=!compared.limited;
    for(const difference of compared.differences){
     const row=document.createElement('tr');
     const path=document.createElement('th');path.scope='row';const pointer=document.createElement('code');pointer.textContent=difference.path===''?'(root)':difference.path;path.append(pointer);row.append(path);
     const change=document.createElement('td');const label=document.createElement('span');label.className=`diff-kind ${difference.change}`;label.textContent=difference.change;change.append(label);row.append(change);
     for(const value of [difference.before,difference.after]){
      const cell=document.createElement('td'),type=document.createElement('span');type.className='diff-value-type';type.textContent=value?`${value.type}${value.truncated?' · preview':''}`:'missing';cell.append(type);
      const content=document.createElement('pre');content.textContent=value?value.json:'—';cell.append(content);row.append(cell);
     }
     $('#compare-rows').append(row);
    }
    $('#compare-table-wrap').hidden=!compared.differences.length;$('#compare-scroll-hint').hidden=!compared.differences.length;
   }catch(e){showError('#compare-error',e);text('#compare-summary','No comparison report. Correct the input and compare again.');}
  }
  for(const side of ['left','right']){
   $(`#compare-${side}`).addEventListener('input',()=>{changed(side);text(`#compare-${side}-file-note`,'');});
   const field=$(`#compare-${side}-file`);
   field.onchange=async()=>{
    const file=field.files[0];if(!file)return;changed(side);const ticket=tickets[side];pending[side]=true;$('#compare-run').disabled=true;text(`#compare-${side}-file-note`,'Reading file locally…');
    try{
     if(file.size>LIMITS.file)throw Error('File exceeds 2 MB (2,000,000 bytes).');
     const value=decodeFile(await file.arrayBuffer());if(ticket!==tickets[side])return;
     $(`#compare-${side}`).value=value;text(`#compare-${side}-file-note`,`${file.name} · ${file.size.toLocaleString()} bytes · read locally`);pending[side]=false;
     if(!pending.left&&!pending.right)run();
    }catch(e){if(ticket===tickets[side]){$(`#compare-${side}`).value='';text(`#compare-${side}-file-note`,'');showError('#compare-error',Error(`${side==='left'?'Left':'Right'} file: ${e.message}`));}}
    finally{if(ticket===tickets[side]){pending[side]=false;$('#compare-run').disabled=pending.left||pending.right;}if(field.files[0]===file)field.value='';}
   };
  }
  $('#compare-run').onclick=run;
  $('#compare-swap').onclick=()=>{cancelAll();const a=$('#compare-left').value;$('#compare-left').value=$('#compare-right').value;$('#compare-right').value=a;for(const side of ['left','right'])text(`#compare-${side}-file-note`,'');run();};
  $('#compare-clear').onclick=()=>{cancelAll();for(const side of ['left','right']){$(`#compare-${side}`).value='';$(`#compare-${side}-file`).value='';text(`#compare-${side}-file-note`,'');}$('#compare-left').focus();};
  $('#compare-download').onclick=()=>{if(result)download(result,'parsecove-json-comparison.json','application/json;charset=utf-8');};
  $$('[data-compare-example]').forEach(button=>button.onclick=()=>{cancelAll();const [a,b]=COMPARE_SAMPLES[button.dataset.compareExample];$('#compare-left').value=a;$('#compare-right').value=b;for(const side of ['left','right'])text(`#compare-${side}-file-note`,'');run();});
  run();
 }
}
