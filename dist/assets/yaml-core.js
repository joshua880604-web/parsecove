import {parseDocument,stringify} from './vendor/yaml.js';
import {inputText,outputText,parseJson,jsonOutput,treeBudget,safeNumber} from './data-common.js';
import {requireUnicode} from './conversion-core.js';
export function yamlToJson(raw,{indent=2}={}){
 raw=inputText(raw);
 const doc=parseDocument(raw,{version:'1.2',schema:'core',strict:true,uniqueKeys:true,intAsBigInt:true,prettyErrors:true});
 if(doc.errors.length)throw Error(doc.errors[0].message);
 if(doc.warnings.length)throw Error(`Unsupported YAML: ${doc.warnings[0].message}`);
 if(doc.directives.yaml.version!=='1.2')throw Error('Only YAML 1.2 is supported. Remove the YAML 1.1 directive or convert its types explicitly.');
 const value=doc.toJS({mapAsMap:true,maxAliasCount:50});
 const check=treeBudget(),ancestors=new Set();
 function read(item,depth=0){
  check(depth);
  if(item===null||typeof item==='boolean')return item;
  if(typeof item==='string'){requireUnicode(item);return item;}
  if(typeof item==='number')return safeNumber(item);
  if(typeof item==='bigint'){
   if(item>BigInt(Number.MAX_SAFE_INTEGER)||item<BigInt(Number.MIN_SAFE_INTEGER))throw Error('A YAML integer exceeds the safe number range. Quote exact IDs and large integers as strings.');return Number(item);
  }
  if(ancestors.has(item))throw Error('Cyclic YAML aliases cannot be represented in JSON.');
  ancestors.add(item);let result;
  if(item instanceof Map){
   result=Object.create(null);
   for(const [key,v] of item){check(depth+1);if(typeof key!=='string')throw Error('JSON object keys must be strings. Quote numeric YAML keys; complex keys are unsupported.');requireUnicode(key);if(key==='<<')throw Error('YAML merge keys (<<) are unsupported. Expand the mapping explicitly.');result[key]=read(v,depth+1);}
  }else if(Array.isArray(item))result=item.map(v=>read(v,depth+1));
  else throw Error('This YAML value has no supported JSON representation. Use core strings, numbers, booleans, null, lists and mappings.');
  ancestors.delete(item);return result;
 }
 const data=read(value);return {data,output:jsonOutput(data,indent),note:'YAML 1.2 core types. Comments and source formatting are not retained.'};
}
export function jsonToYaml(raw,{indent=2}={}){
 const data=parseJson(raw);indent=Number(indent);if(![2,4].includes(indent))throw Error('Choose 2-space or 4-space YAML indentation.');
 const output=outputText(stringify(data,{version:'1.2',schema:'core',indent,lineWidth:0,defaultStringType:'QUOTE_DOUBLE',defaultKeyType:'PLAIN',blockQuote:false}));
 return {data,output,note:'String values are quoted to preserve their types. Comments and source formatting are not retained.'};
}
