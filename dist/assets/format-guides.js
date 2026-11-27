export async function initFormatGuide(page,{$,text,showError}){
 const yaml=page==='guides/yaml-vs-json';
 const convert=yaml?(await import('./yaml-core.js')).yamlToJson:(await import('./json-layer.js')).inspectJsonLayer;
 const cases=JSON.parse($('#format-cases').textContent),byId=new Map(cases.map(c=>[c.id,c]));
 function run(){const c=byId.get($('#format-case').value)||cases[0];$('#format-input').value=c.input;$('#format-output').value='';text('#format-copy','');text('#format-explanation',c.note);text('#format-status','');showError('#format-error',null);$('[data-copy="format-copy"]').disabled=true;
  try{const r=convert(c.input);$('#format-output').value=r.output;text('#format-copy',r.output);text('#format-status',yaml?'Converted with the same YAML 1.2 core parser as the tool.':`After one parse: ${r.kind}. ${r.unwrapped?'One top-level string layer was decoded.':'No top-level string layer to unwrap.'}`);$('[data-copy="format-copy"]').disabled=!r.output.length;}
  catch(e){showError('#format-error',e);text('#format-status','Rejected. No previous result is retained.');}
 }
 $('#format-case').onchange=run;$('#format-reset').onclick=()=>{$('#format-case').value=cases[0].id;run();};run();
}
