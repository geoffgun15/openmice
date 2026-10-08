import test from 'node:test';
import assert from 'node:assert/strict';
import {validate,Protocol,buttons} from './protocol.js';
test('validation matches firmware constraints',()=>{assert.equal(validate({dpi:26000,bindings:[...buttons]}).dpi,26000);for(const dpi of [0,51,26050,800.5,true])assert.throws(()=>validate({dpi,bindings:[...buttons]}));assert.throws(()=>validate({dpi:800,bindings:['key:CTRL+FAKE',...buttons.slice(1)]}));});
test('fragmented replies, unsolicited motion and correlation',async()=>{let sent;const p=new Protocol(line=>{sent=JSON.parse(line);});const result=p.request('hello');await Promise.resolve();p.feed('{"motion":[0,0,0,0,[]]}\n{"id":'+sent.id+',"ok":');p.feed('true,"device":"OpenMice"}\n');assert.equal((await result).device,'OpenMice');p.close();});
test('negative acknowledgement and timeout',async()=>{const p=new Protocol(()=>{},10);const first=p.request('set');await Promise.resolve();p.feed('{"id":1,"ok":false,"error":"bad dpi"}\n');await assert.rejects(first,/bad dpi/);await assert.rejects(p.request('get'),/did not reply/);});
test('overflow is discarded and next frame recovers',async()=>{const p=new Protocol(()=>{});const result=p.request('get');p.feed('x'.repeat(2000)+'\n{"id":1,"ok":true}\n');assert.equal((await result).ok,true);p.close();});
test('disconnect rejects pending requests',async()=>{const p=new Protocol(()=>{});const request=p.request('get');p.close();await assert.rejects(request,/disconnected/);});
