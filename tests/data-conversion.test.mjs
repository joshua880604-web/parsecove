import test from 'node:test';
import assert from 'node:assert/strict';
import {parseJson,decodeFile,LIMITS} from '../dist/assets/data-common.js';
import {yamlToJson,jsonToYaml} from '../dist/assets/yaml-core.js';
import {csvToJson,jsonToCsv} from '../dist/assets/csv-core.js';
const plain=v=>JSON.parse(JSON.stringify(v));

test('strict JSON validates before lossy number conversion and preserves prototype keys',()=>{
 assert.deepEqual(plain(parseJson('{"__proto__":{"ok":true},"constructor":2}')),JSON.parse('{"__proto__":{"ok":true},"constructor":2}'));
 for(const input of ['', '{"a":1,"\\u0061":2}','{"a":1,}','{/* comment */"a":1}','"\\ud800"','9007199254740993','-9007199254740993','1e500','[NaN]'])assert.throws(()=>parseJson(input),undefined,input);
 assert.equal(parseJson('9007199254740991'),Number.MAX_SAFE_INTEGER);
 assert.throws(()=>parseJson('['.repeat(82)+'0'+']'.repeat(82)),/nesting/);
 assert.throws(()=>parseJson(JSON.stringify(Array(50_001).fill(null))),/50,000/);
 assert.throws(()=>parseJson(' '.repeat(LIMITS.input+1)),/1,000,000/);
});
test('YAML core types, quoted IDs, BOM and complete round trips',()=>{
 const data=plain(yamlToJson('\ufeffyes: yes\nno: no\non: on\ndate: 2026-11-27\nready: true\nid: "001"\nlist: [1, 2, null]').data);
 assert.deepEqual(data,{yes:'yes',no:'no',on:'on',date:'2026-11-27',ready:true,id:'001',list:[1,2,null]});
 const input={text:'中文 👋\r\n\0',quoted:'true',empty:'',array:[false,null,1.25],literal:'001'};
 assert.deepEqual(plain(yamlToJson(jsonToYaml(JSON.stringify(input)).output).data),input);
 assert.equal(yamlToJson('').output,'null');
 assert.deepEqual(plain(yamlToJson('first: &a [red, blue]\nsecond: *a').data),{first:['red','blue'],second:['red','blue']});
 assert.equal(yamlToJson('n: 9007199254740991').data.n,Number.MAX_SAFE_INTEGER);
 assert.deepEqual(plain(yamlToJson('"__proto__": {safe: true}').data),JSON.parse('{"__proto__":{"safe":true}}'));
});
test('YAML rejects ambiguous, unsupported and excessive data',()=>{
 for(const raw of ['a: 1\na: 2','a: 1\n---\na: 2','%YAML 1.1\n---\na: yes','a: !custom hello','1: value','? [a, b]\n: value','a: .nan','a: .inf','a: 9007199254740993','a: -9007199254740993','a: &a [*a]','base: &b {a: 1}\nother: {<<: *b}'])assert.throws(()=>yamlToJson(raw),undefined,raw);
 assert.throws(()=>yamlToJson('a: &a [1,2]\nb: &b [*a,*a,*a,*a,*a,*a,*a,*a,*a,*a]\nc: &c [*b,*b,*b,*b,*b,*b,*b,*b,*b,*b]'),/alias/i);
 assert.throws(()=>jsonToYaml('{"a":1,"a":2}'),/Duplicate/);
 assert.throws(()=>jsonToYaml('{"id":9007199254740993}'),/safe/);
 assert.throws(()=>jsonToYaml('{}',{indent:0}),/indentation/);
});
test('CSV defaults preserve IDs, whitespace, empty cells and prototype fields',()=>{
 assert.deepEqual(plain(csvToJson('id,name,active,n\r\n001,"Lin, Mei",true,\r\n002, Ada ,false,9007199254740993\r\n').data),[{id:'001',name:'Lin, Mei',active:'true',n:''},{id:'002',name:' Ada ',active:'false',n:'9007199254740993'}]);
 assert.deepEqual(plain(csvToJson('__proto__,constructor\na,b').data),JSON.parse('[{"__proto__":"a","constructor":"b"}]'));
 assert.deepEqual(plain(csvToJson('a,b\n001,true',{headers:false}).data),[['a','b'],['001','true']]);
 assert.deepEqual(plain(csvToJson('id;name\n001;Ada').data),[{id:'001',name:'Ada'}]);
 assert.deepEqual(plain(csvToJson('a\tb\n1\t2',{delimiter:'\t'}).data),[{a:'1',b:'2'}]);
});
test('CSV handles exact quotes, multiline values and empty records',()=>{
 assert.deepEqual(plain(csvToJson('a,b\n"x""y","one\r\ntwo"').data),[{a:'x"y',b:'one\r\ntwo'}]);
 assert.deepEqual(plain(csvToJson('a\n""\n').data),[{a:''}]);
 assert.deepEqual(plain(csvToJson('a\n\n').data),[{a:''}]);
 assert.deepEqual(plain(csvToJson('a\n\n',{skipEmpty:true}).data),[]);
 assert.deepEqual(plain(csvToJson('\n',{headers:false}).data),[['']]);
 assert.deepEqual(plain(csvToJson('').data),[]);
 assert.deepEqual(plain(csvToJson('a,b').data),[]);
});
test('CSV type inference is explicit and never rounds integer identifiers',()=>{
 const converted=csvToJson('v\n001\n42\ntrue\nfalse\nnull\n""\n 2 \n9007199254740993\n1e500',{infer:true});
 assert.deepEqual(plain(converted.data),[{v:'001'},{v:42},{v:true},{v:false},{v:null},{v:''},{v:' 2 '},{v:'9007199254740993'},{v:'1e500'}]);
 assert.match(converted.note,/2 unsafe/);
});
test('CSV rejects duplicate headers, uneven rows, invalid quoting and excessive dimensions',()=>{
 for(const raw of ['a,a\n1,2',',a\n1,2','a,b\n1','a,b\n1,2,3','a,b\n"unclosed,x','a,b\nx"q,y','a,b\n"x"oops,y'])assert.throws(()=>csvToJson(raw,{delimiter:','}),undefined,raw);
 assert.throws(()=>csvToJson(Array(201).fill('x').join(','),{headers:false,delimiter:','}),/200/);
 assert.throws(()=>csvToJson('a\n'+'x\n'.repeat(10001),{delimiter:','}),/10,000/);
 assert.throws(()=>csvToJson('a,b',{delimiter:'&'}),/delimiter/);
});
test('JSON to CSV header union, missing values and nested-cell opt-in',()=>{
 const raw='[{"b":2,"a":"001"},{"a":"002","c":null}]';
 const out=jsonToCsv(raw,{protect:false,newline:'\n'}).output;
 assert.equal(out,'"b","a","c"\n"2","001",""\n"","002",""');
 assert.equal(jsonToCsv('[[1,"a"],[2,"b"]]',{newline:'\n'}).output,'"1","a"\n"2","b"');
 assert.equal(jsonToCsv('[]').output,'');
 assert.equal(jsonToCsv('[{"a":1}]',{headers:false}).output,'"1"');
 assert.throws(()=>jsonToCsv('[{"a":{"b":1}}]'),/Nested/);
 const nested=jsonToCsv('[{"a":{"b":1},"list":[true]}]',{nested:true,protect:false}).output;
 assert.deepEqual(plain(csvToJson(nested).data),[{a:'{"b":1}',list:'[true]'}]);
 for(const raw of ['{}','[null]','[{},[]]','[[1],[1,2]]','[{}]','[[]]','[{"a":9007199254740993}]'])assert.throws(()=>jsonToCsv(raw),undefined,raw);
});
test('spreadsheet protection is visible and applies only to strings, including headers',()=>{
 const raw='[{"=header":"=SUM(A1)","negative":-12,"stringNegative":"-12","tab":"\\tvalue"}]';
 const safe=csvToJson(jsonToCsv(raw).output).data[0];
 assert.equal(safe["'=header"],"'=SUM(A1)");assert.equal(safe.negative,'-12');assert.equal(safe.stringNegative,"'-12");assert.equal(safe.tab,"'\tvalue");
 assert.match(jsonToCsv(raw).note,/4 string cells/);
 const exact=csvToJson(jsonToCsv(raw,{protect:false}).output).data[0];assert.equal(exact['=header'],'=SUM(A1)');assert.equal(exact.stringNegative,'-12');
});
test('CSV byte-level round trips preserve Unicode, quoted CRLF, NUL and empty records',()=>{
 const rows=[['001','中文 👋','a\r\nb','x"y',''],['002','', '\0','a,b','end']];
 const out=jsonToCsv(JSON.stringify(rows),{protect:false,newline:'\r\n'}).output;
 assert.ok(out.includes('\r\n'));assert.deepEqual(plain(csvToJson(out,{headers:false}).data),rows);
 assert.equal(jsonToCsv('[[""]]').output,'""');
 assert.deepEqual(plain(csvToJson(jsonToCsv('[[""]]').output,{headers:false}).data),[['']]);
});
test('local UTF-8 file decoding accepts a BOM and rejects invalid bytes and size',()=>{
 assert.equal(decodeFile(Uint8Array.from([239,187,191,65]).buffer),'\ufeffA');
 assert.throws(()=>decodeFile(Uint8Array.from([255,254]).buffer),/UTF-8/);
 assert.throws(()=>decodeFile(new ArrayBuffer(LIMITS.file+1)),/2 MB/);
});
