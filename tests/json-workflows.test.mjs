import test from 'node:test';
import assert from 'node:assert/strict';
import {jsonDocument,renderJson,transformJson,compareJson} from '../dist/assets/json-document.js';
import {csvToJson} from '../dist/assets/csv-core.js';

test('JSON layout preserves literal number and string tokens, key order and significant whitespace',()=>{
 const raw=String.raw` { "2" : 9007199254740993, "1": -0, "huge": 1e+500, "small": 1.2300e-500, "s": "keep  spaces\n\u0041\/\\" } `;
 const expected=String.raw`{"2":9007199254740993,"1":-0,"huge":1e+500,"small":1.2300e-500,"s":"keep  spaces\n\u0041\/\\"}`;
 assert.equal(transformJson(raw).output,expected);
 const pretty=transformJson(raw,{mode:'format',indent:4}).output;
 assert.match(pretty,/\n {4}"2": 9007199254740993/);
 assert.equal(transformJson(pretty).output,expected);
 assert.equal(transformJson(expected).output,expected);
 for(const primitive of ['null','false','"a  b"','9007199254740993','1e9999999999999999999999'])assert.equal(transformJson(' '+primitive+' ').output,primitive);
});
test('UTF-8 byte changes are measured and validation retains valid source layout',()=>{
 const raw='\ufeff { "text": "中文 😀" }\r\n',r=transformJson(raw);
 assert.equal(r.inputBytes,Buffer.byteLength(raw,'utf8'));
 assert.equal(r.outputBytes,Buffer.byteLength(r.output,'utf8'));
 assert.equal(r.savedBytes,r.inputBytes-r.outputBytes);
 assert.equal(r.savedPercent,100*r.savedBytes/r.inputBytes);
 assert.equal(transformJson(raw,{mode:'validate'}).output,raw.slice(1));
 assert.ok(transformJson('{"a":[1,2]}',{mode:'format'}).savedBytes<0);
});
test('strict document checks reject duplicate decoded keys, malformed JSON and unpaired surrogates',()=>{
 for(const raw of ['', '{"a":1,"\\u0061":2}', '{"x":1,}', '[1,]', '// comment\n1', '{/* note */"a":1}', 'NaN', 'undefined', '01', '1 2', '"\\ud800"', '"\\udfff"', '"literal\nnewline"'])assert.throws(()=>jsonDocument(raw),undefined,raw);
 assert.throws(()=>jsonDocument('{"a":\n }'),/line 2, column/);
 assert.equal(renderJson(jsonDocument('{"__proto__":1,"constructor":2}')),'{"__proto__":1,"constructor":2}');
});
test('preflight and output budgets reject pathological documents before unbounded work',()=>{
 assert.throws(()=>jsonDocument('['.repeat(81)+'0'+']'.repeat(81)),/nesting/);
 assert.throws(()=>jsonDocument(']'.repeat(1000)+'['.repeat(81)+'0'),/nesting/);
 assert.throws(()=>jsonDocument('['+Array(50001).fill('0').join(',')+']'),/50,000/);
 assert.throws(()=>jsonDocument(' '.repeat(1000001)),/1,000,000/);
 const wideNested='['.repeat(79)+Array(10000).fill('"x"').join(',')+']'.repeat(79);
 assert.throws(()=>transformJson(wideNested,{mode:'format',indent:4}),/3,000,000/);
});
test('structural comparison uses exact decimal values rather than binary floating point',()=>{
 for(const [a,b] of [['1','1.0'],['1e500','10e499'],['1e-500','10e-501'],['-0','0'],['-0.000e999','0'],['123.4500','12345e-2'],['1000','1e3']])assert.equal(compareJson(a,b).equal,true,`${a} == ${b}`);
 for(const [a,b] of [['9007199254740992','9007199254740993'],['1','1.0000000000000001'],['1e-500','0'],['1e500','2e500'],['-1','1']])assert.equal(compareJson(a,b).equal,false,`${a} != ${b}`);
 assert.throws(()=>compareJson('1e'+'9'.repeat(4095),'0'),/4,096/);
});
test('comparison ignores object layout, preserves array order and distinguishes types, missing and null',()=>{
 const same=compareJson('{"a":1,"s":"Ada"}','{ "s":"\\u0041da", "a":1.0 }');
 assert.equal(same.equal,true);assert.equal(same.textIdentical,false);
 assert.equal(compareJson('true','true').textIdentical,true);
 const r=compareJson('{"n":null,"t":1,"a":[1,2]}','{"t":"1","a":[2,1],"new":null}');
 assert.deepEqual(r.differences.map(d=>[d.path,d.change]),[['/a/0','changed'],['/a/1','changed'],['/n','removed'],['/new','added'],['/t','changed']]);
 assert.equal(r.differences[2].before.json,'null');assert.equal(r.differences[2].after,null);
 assert.equal(compareJson('1','"1"').differences[0].path,'');
 assert.deepEqual(compareJson('{"__proto__":1,"constructor":2}','{"constructor":2,"__proto__":3}').differences.map(d=>d.path),['/__proto__']);
 assert.throws(()=>compareJson('{bad}', '{}'),/Left document/);
 assert.throws(()=>compareJson('{}', '{"a":1,"a":2}'),/Right document: Duplicate/);
});
test('JSON Pointer paths escape keys and reports explicitly bound counts, previews and size',()=>{
 assert.deepEqual(compareJson('{"a/b":{"~key":1},"":true}','{"a/b":{"~key":2},"":false}').differences.map(d=>d.path),['/','/a~1b/~0key']);
 const many=compareJson(JSON.stringify(Array(201).fill(0)),JSON.stringify(Array(201).fill(1)));
 assert.equal(many.differences.length,200);assert.equal(many.limited,true);assert.equal(many.limitReason,'difference-count');
 assert.equal(compareJson(JSON.stringify(Array(200).fill(0)),JSON.stringify(Array(200).fill(1))).limited,false);
 const preview=compareJson(JSON.stringify('😀'.repeat(300)),'null').differences[0].before;
 assert.equal(preview.truncated,true);assert.ok(preview.json.endsWith('…'));assert.ok(!/[\ud800-\udbff]…$/.test(preview.json));
 const longKey='a'.repeat(4097);assert.throws(()=>compareJson(JSON.stringify({[longKey]:1}),JSON.stringify({[longKey]:2})),/path exceeds/);
 const a={},b={};for(let i=0;i<190;i++){const key='k'.repeat(3000)+i;a[key]=0;b[key]=1;}
 const bounded=compareJson(JSON.stringify(a),JSON.stringify(b));assert.equal(bounded.limited,true);assert.equal(bounded.limitReason,'report-size');assert.ok(JSON.stringify(bounded).length<510000);
});
test('CSV JSON Lines is one compact record per physical line with exact final LF and escaped field newlines',()=>{
 const raw='id,note\r\n001,"one\r\ntwo"\r\n002,"a ""quote"""\r\n';
 const r=csvToJson(raw,{format:'jsonl'});
 assert.equal(r.output,String.raw`{"id":"001","note":"one\r\ntwo"}`+'\n'+String.raw`{"id":"002","note":"a \"quote\""}`+'\n');
 assert.equal(r.output.split('\n').length,3);
 assert.deepEqual(r.output.trimEnd().split('\n').map(line=>JSON.parse(line)),JSON.parse(JSON.stringify(r.data)));
 assert.equal(csvToJson('a,b\n1,2',{headers:false,format:'jsonl'}).output,'["a","b"]\n["1","2"]\n');
 assert.equal(csvToJson('',{format:'jsonl'}).output,'');
 assert.equal(csvToJson('a,b\n',{format:'jsonl'}).output,'');
 assert.equal(csvToJson('id,n,flag\n001,9007199254740993,true',{format:'jsonl',infer:true}).output,'{"id":"001","n":"9007199254740993","flag":true}\n');
 assert.throws(()=>csvToJson('a,a\n1,2',{format:'jsonl'}),/Duplicate/);
 assert.throws(()=>csvToJson('a',{format:'bogus'}),/output/);
 assert.throws(()=>csvToJson('k'.repeat(10000)+'\n'+Array(400).fill('a').join('\n'),{format:'jsonl'}),/3,000,000/);
});
