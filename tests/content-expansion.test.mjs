import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {rgbaFromHex} from '../dist/assets/rgba-core.js';
import {inspectJsonLayer} from '../dist/assets/json-layer.js';
import {yamlToJson} from '../dist/assets/yaml-core.js';
const fixtures=JSON.parse(readFileSync(new URL('../guide-fixtures.json',import.meta.url),'utf8'));
test('RGBA opacity remains independent from the nearest HEX alpha byte',()=>{
 const r=rgbaFromHex('#336699','0.5');assert.equal(r.rgba,'rgba(51, 102, 153, 0.5)');assert.equal(r.hex,'#33669980');assert.equal(r.alpha,0.5);assert.equal(r.hexAlpha,128/255);assert.equal(r.quantized,true);
 assert.equal(rgbaFromHex('#000','0').rgba,'rgba(0, 0, 0, 0)');assert.equal(rgbaFromHex('abc','1').hex,'#AABBCCFF');assert.equal(rgbaFromHex('abc','').rgba,'rgba(170, 187, 204, 1)');
 const transparent=rgbaFromHex('#00000000','0.9');assert.equal(transparent.alpha,0);assert.equal(transparent.embeddedAlpha,true);
 const embedded=rgbaFromHex('#0f08','bad');assert.equal(embedded.rgba,'rgba(0, 255, 0, 0.533333)');assert.equal(embedded.hex,'#00FF0088');assert.equal(embedded.alpha,136/255);
 for(const alpha of ['-1','1.1','NaN','1e-1','0x1','abc'])assert.throws(()=>rgbaFromHex('#abc',alpha),/Opacity/);
 for(const color of ['red','#12','#abcdefghi','#ggg','rgba(1,2,3,0.5)'])assert.throws(()=>rgbaFromHex(color,'0.5'));
});
test('published YAML guide fixtures use actual parser rules and expected values',()=>{
 for(const c of fixtures.yaml){if(c.error)assert.throws(()=>yamlToJson(c.input),undefined,c.id);else assert.deepEqual(JSON.parse(yamlToJson(c.input).output),c.expected,c.id);}
});
test('JSON guide inspects one layer and never recursively changes string fields',()=>{
 for(const c of fixtures.json){if(c.error)assert.throws(()=>inspectJsonLayer(c.input),undefined,c.id);else assert.equal(inspectJsonLayer(c.input).kind,c.expected_kind,c.id);}
 const encoded=inspectJsonLayer(fixtures.json[0].input);assert.equal(encoded.output,'{"id":"001","ready":true}');assert.equal(encoded.kind,'string');
 const field=inspectJsonLayer(fixtures.json.find(c=>c.id==='field').input);assert.equal(typeof field.value.payload,'string');assert.equal(field.value.payload,'{"id":"001"}');
 const path=inspectJsonLayer(fixtures.json.find(c=>c.id==='path').input);assert.equal(path.value.path,'C:\\temp\\report.txt');assert.equal(path.value.message,'Line 1\nLine 2');
 assert.equal(inspectJsonLayer('"001"').output,'001');assert.throws(()=>inspectJsonLayer('{"id":9007199254740993}'),/safe/);
});
