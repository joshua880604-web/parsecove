import test from 'node:test';
import assert from 'node:assert/strict';
import {hexColor,rgbColor,escapeJson,unescapeJson,hexBytes,textBytes,hexString,utf8Text,TEXT_LIMIT,HEX_LIMIT,BYTE_LIMIT,JSON_LIMIT} from '../dist/assets/conversion-core.js';

test('HEX colors expand shorthand and preserve the alpha byte',()=>{
 const blue=hexColor('#244cda');assert.deepEqual([blue.r,blue.g,blue.b],[36,76,218]);assert.equal(blue.hex,'#244CDA');assert.equal(blue.rgb,'rgb(36, 76, 218)');
 assert.equal(hexColor('abc').hex,'#AABBCC');assert.equal(hexColor('#0f08').alphaByte,136);
 const alpha=hexColor('#33669980');assert.equal(alpha.alphaByte,128);assert.equal(alpha.alpha,128/255);assert.equal(alpha.rgb,'rgba(51, 102, 153, 0.501961)');
 assert.equal(hexColor('#0000').alpha,0);assert.equal(hexColor('#ffffffff').alpha,1);
 // Every shorthand triplet agrees with independent nibble arithmetic.
 for(let i=0;i<4096;i++){
  const s=i.toString(16).padStart(3,'0'),v=hexColor(s);
  assert.deepEqual([v.r,v.g,v.b],s.split('').map(x=>parseInt(x,16)*17));
 }
 for(const raw of ['','#12','#12345','#1234567','#123456789','#ggg','0xff','# 123','red','rgb(1,2,3)'])assert.throws(()=>hexColor(raw));
});
test('RGB channels validate bounds and report alpha quantization',()=>{
 assert.equal(rgbColor('36','76','218').hex,'#244CDA');
 const half=rgbColor(51,102,153,0.5);assert.equal(half.hex,'#33669980');assert.equal(half.quantized,true);
 assert.equal(rgbColor(51,102,153,128/255).quantized,false);
 assert.equal(rgbColor(0,255,0,0).hex,'#00FF0000');
 for(const args of [[-1,0,0],[256,0,0],['',0,0],['1.5',0,0],[0,0,0,-0.1],[0,0,0,1.1],[0,0,0,'NaN']])assert.throws(()=>rgbColor(...args));
});
test('JSON strings decode one layer and distinguish contents from a document',()=>{
 assert.equal(unescapeJson('"Hello\\nworld\\u0021"'),'Hello\nworld!');
 assert.equal(unescapeJson('Hello\\nworld','content'),'Hello\nworld');
 assert.equal(unescapeJson('"\\u4e2d\\u6587 \\ud83d\\udc4b"'),'中文 👋');
 assert.equal(unescapeJson('"\\r\\n\\t\\u0000"'),'\r\n\t\u0000');
 const text='{"ok":true}',twice=JSON.stringify(JSON.stringify(text));
 const first=unescapeJson(twice);assert.equal(first,JSON.stringify(text));assert.equal(unescapeJson(first),text);
 assert.equal(unescapeJson('""'),'');assert.equal(escapeJson(''),'""');
 assert.equal(escapeJson('a"b\\c\nd'),'"a\\"b\\\\c\\nd"');
 assert.equal(escapeJson('a"b',false),'a\\"b');
 assert.equal(unescapeJson(escapeJson('<script>throw 1</script>')),'<script>throw 1</script>');
 for(const raw of ['{}','[]','42','true','null','"\\x41"','"unterminated','"a\nb"'])assert.throws(()=>unescapeJson(raw));
 assert.throws(()=>unescapeJson('a"b','content'));
 for(const s of ['\ud800','\udfff','a\ud800x']){assert.throws(()=>escapeJson(s));assert.throws(()=>textBytes(s));}
 assert.throws(()=>unescapeJson('"\\ud800"'));
 assert.throws(()=>escapeJson('x'.repeat(JSON_LIMIT+1)));
});
test('HEX byte groups use strict complete bytes with explicit prefix handling',()=>{
 for(const s of ['48656c6c6f','0X48656C6C6F','48 65\n6c\t6c 6f','0x48 0x65 0x6c 0x6c 0x6f'])assert.equal(utf8Text(hexBytes(s)),'Hello');
 for(const s of ['4 8','123','0x','0x0x41','48,65','48-65','gg','0x4','48<script>'])assert.throws(()=>hexBytes(s));
 assert.equal(hexBytes(' \n ').length,0);
 const every=Uint8Array.from({length:256},(_,i)=>i);
 for(const upper of [true,false])for(const spaced of [true,false])assert.deepEqual(hexBytes(hexString(every,upper,spaced)),every);
 assert.equal(Buffer.from(hexBytes('00 ff 0a 80')).toString('hex'),'00ff0a80');
 assert.throws(()=>hexBytes(' '.repeat(HEX_LIMIT+1)));
 assert.throws(()=>hexBytes('00'.repeat(BYTE_LIMIT+1)));
 assert.throws(()=>textBytes('a'.repeat(TEXT_LIMIT+1)));
});
test('UTF-8 text and arbitrary bytes are separate, including BOM and CRLF',()=>{
 for(const s of ['Hello','中文 👋','a\u0000b','\r\n','\ufefftext','']){
  const bytes=textBytes(s);assert.equal(Buffer.from(bytes).toString('hex'),Buffer.from(s,'utf8').toString('hex'));
  assert.equal(utf8Text(hexBytes(hexString(bytes))),s);
 }
 for(const raw of ['fb ff ef','c0 af','ed a0 80','e4 b8']){
  const bytes=hexBytes(raw);assert.ok(bytes.length>0);assert.throws(()=>utf8Text(bytes));
 }
});
