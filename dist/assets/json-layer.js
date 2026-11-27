import {parseJson,jsonOutput} from './data-common.js';
export function inspectJsonLayer(raw){
 const value=parseJson(raw);const kind=value===null?'null':Array.isArray(value)?'array':typeof value;
 return {value,kind,output:typeof value==='string'?value:jsonOutput(value,2),unwrapped:typeof value==='string'};
}
