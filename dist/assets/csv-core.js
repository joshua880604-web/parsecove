import {parse,unparse} from './vendor/papaparse.js';
import {LIMITS,inputText,outputText,parseJson,jsonOutput} from './data-common.js';
const DELIMITERS=[',','\t',';','|'];
function delimiterOption(value='auto'){if(value!=='auto'&&!DELIMITERS.includes(value))throw Error('Choose a supported delimiter.');return value;}
// Papa handles field decoding; this bounded preflight rejects bare quotes that its permissive mode accepts.
function quoteCheck(raw,delimiter){
 let state='start',record=1,fields=1;
 for(let i=0;i<raw.length;i++){
  const c=raw[i];
  if(state==='quoted'){if(c==='"'){if(raw[i+1]==='"')i++;else state='closed';}continue;}
  if(c===delimiter){if(++fields>LIMITS.columns)throw Error('CSV exceeds 200 columns.');state='start';continue;}
  if(c==='\r'||c==='\n'){if(c==='\r'&&raw[i+1]==='\n')i++;if(++record>LIMITS.rows+1)throw Error('CSV exceeds 10,000 data records.');state='start';fields=1;continue;}
  if(state==='closed')throw Error(`Unexpected character after a closing quote in CSV record ${record}.`);
  if(c==='"'){if(state!=='start')throw Error(`A quote inside an unquoted field in CSV record ${record} must be escaped in a quoted field.`);state='quoted';}
  else state='plain';
 }
 if(state==='quoted')throw Error(`Unclosed quoted field in CSV record ${record}.`);
}
export function csvToJson(raw,{delimiter='auto',headers=true,infer=false,skipEmpty=false,indent=2}={}){
 raw=inputText(raw);delimiterOption(delimiter);
 if(raw==='')return {data:[],output:jsonOutput([],indent),note:'0 records. Empty input produces an empty array.',delimiter:delimiter==='auto'?',':delimiter};
 // One final terminator ends the last record; extra empty records remain data.
 raw=raw.replace(/(?:\r\n|\r|\n)$/,'');
 if(raw==='')raw='""';
 const result=parse(raw,{header:false,dynamicTyping:false,skipEmptyLines:false,delimiter:delimiter==='auto'?'':delimiter,delimitersToGuess:DELIMITERS});
 const chosen=result.meta.delimiter||',';quoteCheck(raw,chosen);
 const errors=result.errors.filter(e=>e.code!=='UndetectableDelimiter');
 if(errors.length)throw Error(`CSV record ${(errors[0].row??0)+1}: ${errors[0].message}.`);
 let rows=result.data;
 if(skipEmpty)rows=rows.filter(row=>!row.every(cell=>cell===''));
 if(rows.length===0)return {data:[],output:jsonOutput([],indent),note:'0 records after skipping empty rows.',delimiter:chosen};
 const width=rows[0].length;
 if(width>LIMITS.columns)throw Error('CSV exceeds 200 columns.');
 for(const [i,row] of rows.entries())if(row.length!==width)throw Error(`CSV record ${i+1} has ${row.length} fields; expected ${width}. Check the delimiter and missing or extra values.`);
 let keys;
 if(headers){keys=rows[0];const seen=new Set();for(const key of keys){if(!key.trim())throw Error('CSV header names must not be empty. Turn off First row contains headers to keep array rows.');if(seen.has(key))throw Error(`Duplicate CSV header: ${JSON.stringify(key)}. Rename it or turn off headers.`);seen.add(key);}rows=rows.slice(1);}
 if(rows.length>LIMITS.rows)throw Error('CSV exceeds 10,000 data records.');
 let preserved=0;
 function cell(value){
  if(!infer)return value;
  if(value==='true')return true;if(value==='false')return false;if(value==='null')return null;
  if(/^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?$/.test(value)){
   const n=Number(value);if(Number.isFinite(n)&&(!Number.isInteger(n)||Number.isSafeInteger(n)))return n;preserved++;
  }
  return value;
 }
 const data=rows.map(row=>{if(!headers)return row.map(cell);const obj=Object.create(null);keys.forEach((key,i)=>{obj[key]=cell(row[i]);});return obj;});
 const named=chosen==='\t'?'tab':chosen;
 return {data,output:jsonOutput(data,indent),delimiter:chosen,note:`${data.length} records · ${width} columns · delimiter: ${named}. ${infer?'JSON type inference enabled.':'All cell values remain strings.'}${preserved?` ${preserved} unsafe numeric values retained as strings.`:''}${result.errors.some(e=>e.code==='UndetectableDelimiter')?' Auto detection was inconclusive; comma was used.':''}`};
}
export function jsonToCsv(raw,{delimiter=',',headers=true,nested=false,protect=true,newline='\r\n'}={}){
 delimiter=delimiter==='auto'?',':delimiter;delimiterOption(delimiter);if(!['\n','\r\n'].includes(newline))throw Error('Choose LF or CRLF line endings.');
 const data=parseJson(raw);
 if(!Array.isArray(data))throw Error('JSON to CSV requires an array of objects or an array of arrays.');
 if(data.length>LIMITS.rows)throw Error('JSON exceeds 10,000 records.');
 if(data.length===0)return {output:'',note:'0 records. An empty array produces an empty CSV file.'};
 const arrays=Array.isArray(data[0]);
 if(data.some(row=>arrays?!Array.isArray(row):row===null||typeof row!=='object'||Array.isArray(row)))throw Error('Use only object records or only array rows. Mixed row types and scalar records are unsupported.');
 let fields=[],rows;
 if(arrays){const width=data[0].length;if(width===0)throw Error('CSV rows need at least one column.');if(data.some(row=>row.length!==width))throw Error('JSON array rows must have the same number of columns.');fields=Array(width);rows=data;}
 else{const seen=new Set();for(const row of data)for(const key of Object.keys(row))if(!seen.has(key)){seen.add(key);fields.push(key);if(fields.length>LIMITS.columns)throw Error('JSON exceeds 200 columns.');}if(!fields.length)throw Error('Object records need at least one field.');rows=data.map(row=>fields.map(key=>Object.hasOwn(row,key)?row[key]:null));}
 if(fields.length>LIMITS.columns)throw Error('JSON exceeds 200 columns.');
 let protectedCells=0,serialized=0;
 function cell(value){
  if(value!==null&&typeof value==='object'){if(!nested)throw Error('Nested objects or arrays need Serialize nested values as JSON enabled.');value=JSON.stringify(value);serialized++;}
  if(value===null)return '';
  if(protect&&typeof value==='string'&&/^[=+\-@\t\r]/.test(value)){protectedCells++;return "'"+value;}
  return value;
 }
 const table=rows.map(row=>row.map(cell));if(!arrays&&headers)table.unshift(fields.map(cell));
 const output=outputText(unparse(table,{delimiter,newline,quotes:true,header:false,skipEmptyLines:false,escapeFormulae:false}));
 return {output,note:`${data.length} records · ${fields.length} columns. ${arrays?'Array rows have no generated header.':headers?'Header uses the union of object keys in first-seen order.':'Header omitted.'} Null and missing fields become empty cells.${serialized?` ${serialized} nested cells serialized as JSON.`:''}${protect?` Spreadsheet protection: ${protectedCells} string cells prefixed with an apostrophe.`:' Spreadsheet protection is off; original strings are retained.'}`};
}
