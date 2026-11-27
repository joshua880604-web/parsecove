import {parseTree,printParseErrorCode} from './vendor/jsonc-parser.js';
import {requireUnicode} from './conversion-core.js';
export const LIMITS=Object.freeze({input:1_000_000,output:3_000_000,file:2_000_000,depth:80,nodes:50_000,rows:10_000,columns:200});
export function inputText(raw){
 if(typeof raw!=='string')throw Error('Enter text to convert.');
 if(raw.length>LIMITS.input)throw Error('Input exceeds 1,000,000 UTF-16 code units. Use a smaller document.');
 requireUnicode(raw);return raw.charCodeAt(0)===0xfeff?raw.slice(1):raw;
}
export function outputText(raw){if(raw.length>LIMITS.output)throw Error('Result exceeds 3,000,000 characters. Use a smaller document.');return raw;}
export function indentation(value=2){const n=Number(value);if(![0,2,4].includes(n))throw Error('Choose compact, 2-space or 4-space JSON.');return n;}
export function jsonOutput(value,indent=2){return outputText(JSON.stringify(value,null,indentation(indent)));}
export function treeBudget(){let nodes=0;return depth=>{if(depth>LIMITS.depth)throw Error('Document nesting exceeds 80 levels.');if(++nodes>LIMITS.nodes)throw Error('Document exceeds 50,000 values and fields.');};}
export function safeNumber(n){if(!Number.isFinite(n))throw Error('Non-finite numbers cannot be represented in JSON.');if(Number.isInteger(n)&&!Number.isSafeInteger(n))throw Error('An integer exceeds the safe number range. Quote exact IDs and large integers as strings.');return n;}
export function parseJson(raw){
 raw=inputText(raw);const errors=[];
 const root=parseTree(raw,errors,{allowTrailingComma:false,disallowComments:true,allowEmptyContent:false});
 if(errors.length||!root){const e=errors[0]||{offset:0,error:4};const prefix=raw.slice(0,e.offset);const lines=prefix.split(/\r\n|\r|\n/);throw Error(`Invalid JSON at line ${lines.length}, column ${lines.at(-1).length+1}: ${printParseErrorCode(e.error)}. JSON requires double quotes and no comments or trailing commas.`);}
 const check=treeBudget();
 function read(node,depth=0){
  check(depth);
  if(node.type==='object'){
   const out=Object.create(null),keys=new Set();
   for(const prop of node.children||[]){check(depth+1);const key=prop.children[0].value;requireUnicode(key);if(keys.has(key))throw Error(`Duplicate JSON key: ${JSON.stringify(key)}.`);keys.add(key);out[key]=read(prop.children[1],depth+1);}
   return out;
  }
  if(node.type==='array')return (node.children||[]).map(c=>read(c,depth+1));
  if(node.type==='string'){requireUnicode(node.value);return node.value;}
  if(node.type==='number'){
   const token=raw.slice(node.offset,node.offset+node.length);
   if(/^-?(?:0|[1-9]\d*)$/.test(token)){
    const exact=BigInt(token);if(exact>BigInt(Number.MAX_SAFE_INTEGER)||exact<BigInt(Number.MIN_SAFE_INTEGER))throw Error('An integer exceeds the safe number range. Quote exact IDs and large integers as strings.');
   }
   return safeNumber(node.value);
  }
  return node.value;
 }
 return read(root);
}
export function decodeFile(bytes){if(bytes.byteLength>LIMITS.file)throw Error('File exceeds 2 MB (2,000,000 bytes).');try{const raw=new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(bytes);inputText(raw);return raw;}catch(e){if(e instanceof TypeError)throw Error('This file is not valid UTF-8. Export it as UTF-8 and try again.');throw e;}}
