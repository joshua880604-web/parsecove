import test from 'node:test';
import assert from 'node:assert/strict';
import {timestamp,fromISO,encodeText,decodeText,fromBase64,parseImage,convertUnits,csv} from '../dist/assets/core.js';
test('timestamp units, epoch, negatives and range',()=>{
 assert.equal(timestamp('1700000000','seconds').iso,'2023-11-14T22:13:20.000Z');
 assert.equal(timestamp('1700000000000','milliseconds').iso,'2023-11-14T22:13:20.000Z');
 assert.equal(timestamp('-1','seconds').iso,'1969-12-31T23:59:59.000Z');
 assert.equal(timestamp('0').ms,'0');
 assert.equal(timestamp('1700000000000').unit,'milliseconds');
 assert.throws(()=>timestamp('8640000000000001','milliseconds'));
 for(const n of ['1.5','1e10','NaN',''])assert.throws(()=>timestamp(n));
});
test('ISO calendar validation and explicit offsets',()=>{
 assert.equal(fromISO('2023-11-14T17:13:20-05:00').ms,'1700000000000');
 assert.equal(fromISO('2024-02-29T00:00:00.123Z').seconds,'1709164800.123');
 assert.equal(fromISO('1970-01-01T00:00:00Z').ms,'0');
 for(const s of ['2023-02-29T00:00:00Z','2024-04-31T00:00:00Z','2024-01-01T24:00:00Z','2024-01-01T00:00:00','2024-01-01T00:00:00+24:00'])assert.throws(()=>fromISO(s));
});
test('Base64 UTF-8 round trips and variant handling',()=>{
 for(const s of ['Hello, world!','中文 🧑‍💻','', 'a\u0000b'])for(const variant of ['standard','url'])for(const pad of [true,false])assert.equal(decodeText(encodeText(s,variant,pad),variant),s);
 assert.equal(decodeText('SG Vs\nbG8='),'Hello');
 assert.equal(decodeText('Zg'),'f');
 for(const s of ['Z','====','Zg=','Z===','Zh==','a$bc'])assert.throws(()=>fromBase64(s));
 assert.throws(()=>decodeText('/w=='));
 assert.throws(()=>fromBase64('_w==','standard'));
 assert.equal(fromBase64('_w==','url')[0],255);
});
test('image type detection, mismatch and unsupported files',()=>{
 const png='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j5r8AAAAASUVORK5CYII=';
 assert.equal(parseImage(png).mime,'image/png');
 assert.equal(parseImage('data:image/jpeg;base64,'+png).mismatch,true);
 assert.throws(()=>parseImage(encodeText('<svg></svg>')));
 assert.throws(()=>parseImage('data:image/png,abc'));
});
test('PX REM conversion and numeric bounds',()=>{
 assert.equal(convertUnits('24',16)[0].output,'1.5');
 assert.equal(convertUnits('1.5',16,'rem')[0].output,'24');
 assert.equal(convertUnits('24',20)[0].output,'1.2');
 assert.deepEqual(convertUnits('4, 8\n16',16).map(x=>x.output),['0.25','0.5','1']);
 assert.equal(convertUnits('1',16,'px',2)[0].output,'0.06');
 for(const base of ['',0,-1,'NaN'])assert.throws(()=>convertUnits('24',base));
 assert.throws(()=>convertUnits('16px',16));assert.throws(()=>convertUnits('Infinity',16));
});
test('CSV quotes and line breaks',()=>{assert.equal(csv([['a,b','say "hi"']]),'"a,b","say ""hi"""');});
