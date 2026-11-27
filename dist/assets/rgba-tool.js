import {rgbaFromHex} from './rgba-core.js';
export function initRgbaTool({$,text,showError}){
 const input=$('#rgba-input'),alpha=$('#rgba-alpha');
 function clear(){['#rgba-output','#rgba-hex-output'].forEach(id=>$(id).value='');text('#rgba-note','');text('#rgba-alpha-note','');$('#rgba-fill').style.backgroundColor='transparent';$('#rgba-css').textContent='';document.querySelectorAll('.rgba-workbench [data-copy]').forEach(b=>b.disabled=true);showError('#rgba-error',null);}
 function run(){clear();alpha.disabled=false;if(!input.value.trim())return;
  try{
   const embedded=/^#?(?:[a-f\d]{4}|[a-f\d]{8})$/i.test(input.value.trim());alpha.disabled=embedded;
   if(!embedded&&alpha.validity.badInput)throw Error('Enter a decimal opacity from 0 to 1.');
   const r=rgbaFromHex(input.value,alpha.value);$('#rgba-output').value=r.rgba;$('#rgba-hex-output').value=r.hex;$('#rgba-fill').style.backgroundColor=r.rgba;
   text('#rgba-css',`.overlay {\n  background-color: ${r.rgba};\n}`);
   text('#rgba-alpha-note',r.embeddedAlpha?`The HEX value supplies alpha: ${r.alphaByte}/255 = ${Number(r.alpha.toFixed(6))}. The separate opacity control is ignored.`:'Opacity applies to this 3- or 6-digit HEX color. Empty means 1 (opaque).');
   text('#rgba-note',r.quantized?`RGBA keeps opacity ${r.alpha}. The nearest HEX alpha is ${r.alphaByte}/255 (${Number(r.hexAlpha.toFixed(6))}); the two notations differ slightly.`:`Alpha byte ${r.alphaByte}/255. ${r.embeddedAlpha?'RGBA alpha is displayed to six decimal places.':'RGBA and HEX use the same opacity.'}`);
   document.querySelectorAll('.rgba-workbench [data-copy]').forEach(b=>b.disabled=false);
  }catch(e){showError('#rgba-error',e);}
 }
 input.oninput=run;alpha.oninput=run;
 document.querySelectorAll('[data-rgba-example]').forEach(b=>b.onclick=()=>{input.value=b.dataset.rgbaExample;alpha.value=b.dataset.opacity||'0.5';run();});
 $('#rgba-clear').onclick=()=>{input.value='';alpha.value='';alpha.disabled=false;clear();input.focus();};run();
}
