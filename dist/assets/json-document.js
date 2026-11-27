// JSON syntax trees retain source tokens; numbers never pass through JS Number.
import {parseTree,createScanner,SyntaxKind,printParseErrorCode} from './vendor/jsonc-parser.js';
import {inputText,outputText,treeBudget,LIMITS} from './data-common.js';
import {requireUnicode} from './conversion-core.js';

export function jsonDocument(raw){
 const source=inputText(raw),scanner=createScanner(source,true);let depth=0,values=0;
 // Bound nesting before the recursive third-party parser is entered.
 for(let token=scanner.scan();token!==SyntaxKind.EOF;token=scanner.scan()){
  if(token===SyntaxKind.OpenBraceToken||token===SyntaxKind.OpenBracketToken){if(++depth>LIMITS.depth)throw Error('Document nesting exceeds 80 levels.');}
  if(token===SyntaxKind.CloseBraceToken||token===SyntaxKind.CloseBracketToken)depth=Math.max(0,depth-1);
  if([1,3,7,8,9,10,11].includes(token)&&++values>LIMITS.nodes)throw Error('Document exceeds 50,000 values and fields.');
 }
 const errors=[],root=parseTree(source,errors,{allowTrailingComma:false,disallowComments:true,allowEmptyContent:false});
 if(errors.length||!root){const error=errors[0]||{offset:0,error:4};const lines=source.slice(0,error.offset).split(/\r\n|\r|\n/);throw Error(`Invalid JSON at line ${lines.length}, column ${lines.at(-1).length+1}: ${printParseErrorCode(error.error)}. Use double quotes, without comments or trailing commas.`);}
 const budget=treeBudget();
 function check(node,level=0){
  budget(level);
  if(node.type==='object'){
   const keys=new Set();
   for(const property of node.children||[]){budget(level+1);const key=property.children[0].value;requireUnicode(key);if(keys.has(key))throw Error(`Duplicate JSON key: ${JSON.stringify(key)}.`);keys.add(key);check(property.children[1],level+1);}
  }else if(node.type==='array'){for(const child of node.children||[])check(child,level+1);}
  else if(node.type==='string')requireUnicode(node.value);
 }
 check(root);return {source,root};
}

export function renderJson(document,indent=0){
 if(![0,2,4].includes(indent))throw Error('Choose compact, 2-space or 4-space JSON.');
 const {source,root}=document,parts=[];let length=0;
 function add(value){length+=value.length;if(length>LIMITS.output)throw Error('Result exceeds 3,000,000 characters. Use a smaller document.');parts.push(value);}
 function line(level){if(indent)add('\n'+' '.repeat(level*indent));}
 function write(node,level){
  if(node.type!=='object'&&node.type!=='array'){add(source.slice(node.offset,node.offset+node.length));return;}
  const object=node.type==='object',children=node.children||[];add(object?'{':'[');
  children.forEach((child,index)=>{
   if(index)add(',');line(level+1);
   if(object){const key=child.children[0];add(source.slice(key.offset,key.offset+key.length));add(indent?': ':':');write(child.children[1],level+1);}
   else write(child,level+1);
  });
  if(children.length)line(level);add(object?'}':']');
 }
 write(root,0);return outputText(parts.join(''));
}

export function transformJson(raw,{mode='minify',indent=2}={}){
 if(!['minify','format','validate'].includes(mode))throw Error('Choose Minify, Format or Validate.');
 const document=jsonDocument(raw),output=mode==='validate'?document.source:renderJson(document,mode==='minify'?0:indent);
 const encoder=new TextEncoder(),inputBytes=encoder.encode(raw).length,outputBytes=encoder.encode(output).length;
 return {output,inputBytes,outputBytes,savedBytes:inputBytes-outputBytes,savedPercent:inputBytes?100*(inputBytes-outputBytes)/inputBytes:0,mode};
}

function numberIdentity(token){
 if(token.length>4096)throw Error('JSON comparison supports number tokens up to 4,096 characters. Use a shorter exponent or quote exact identifiers.');
 const match=/^(-?)(\d+)(?:\.(\d+))?(?:[eE]([+-]?\d+))?$/.exec(token);
 const fraction=match[3]||'';let digits=(match[2]+fraction).replace(/^0+/,'');
 if(!digits)return '0';
 const trailing=digits.length-digits.replace(/0+$/,'').length;digits=digits.slice(0,digits.length-trailing);
 const exponent=BigInt(match[4]||'0')-BigInt(fraction.length)+BigInt(trailing);
 return `${match[1]}${digits}e${exponent}`;
}
export function pointerSegment(key){return String(key).replace(/~/g,'~0').replace(/\//g,'~1');}
export function compareJson(leftRaw,rightRaw,{maxDifferences=200}={}){
 if(!Number.isInteger(maxDifferences)||maxDifferences<1||maxDifferences>200)throw Error('The difference limit must be between 1 and 200.');
 let left,right;
 try{left=jsonDocument(leftRaw);}catch(e){throw Error(`Left document: ${e.message}`);}
 try{right=jsonDocument(rightRaw);}catch(e){throw Error(`Right document: ${e.message}`);}
 // Validate every numeric token even when an ancestor differs in type.
 for(const doc of [left,right]){
  const walk=node=>{if(node.type==='number')numberIdentity(doc.source.slice(node.offset,node.offset+node.length));for(const child of node.children||[])walk(child);};walk(doc.root);
 }
 const differences=[];let limited=false,reportSize=0,limitReason=null;
 function preview(doc,node){
  if(!node)return null;const raw=doc.source.slice(node.offset,node.offset+node.length),truncated=raw.length>500;
  return {type:node.type,json:truncated?raw.slice(0,500).replace(/[\uD800-\uDBFF]$/,'')+'…':raw,truncated};
 }
 function emit(path,a,b){
  if(differences.length===maxDifferences){limited=true;limitReason='difference-count';return;}
  if(path.length>4096)throw Error('A difference path exceeds 4,096 characters. Use shorter field names or compare a smaller subtree.');
  const difference={path,change:!a?'added':!b?'removed':'changed',before:preview(left,a),after:preview(right,b)};
  reportSize+=JSON.stringify(difference).length;
  if(reportSize>500_000){limited=true;limitReason='report-size';return;}
  differences.push(difference);
 }
 function walk(a,b,path){
  if(limited)return;
  if(!a||!b||a.type!==b.type){emit(path,a,b);return;}
  if(a.type==='object'){
   const first=new Map((a.children||[]).map(p=>[p.children[0].value,p.children[1]]));
   const second=new Map((b.children||[]).map(p=>[p.children[0].value,p.children[1]]));
   for(const key of [...new Set([...first.keys(),...second.keys()])].sort()){
    walk(first.get(key),second.get(key),path+'/'+pointerSegment(key));if(limited)break;
   }
  }else if(a.type==='array'){
   for(let i=0;i<Math.max(a.children?.length||0,b.children?.length||0);i++){walk(a.children?.[i],b.children?.[i],path+'/'+i);if(limited)break;}
  }else if(a.type==='number'){
   if(numberIdentity(left.source.slice(a.offset,a.offset+a.length))!==numberIdentity(right.source.slice(b.offset,b.offset+b.length)))emit(path,a,b);
  }else if(a.value!==b.value)emit(path,a,b);
 }
 walk(left.root,right.root,'');
 return {equal:!differences.length,textIdentical:leftRaw===rightRaw,limited,limitReason,differences,policy:'Object member order is ignored; array indexes matter. Numbers compare as exact base-10 values; 1 and 1.0 match, as do 0 and -0. Paths are JSON Pointers, limited to 4,096 characters. Previews over 500 characters are truncated. Difference entries are limited to 200 and 500,000 serialized characters. No patch or automatic merge is generated.'};
}
