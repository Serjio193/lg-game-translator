'use strict';
var assert=require('assert'),fs=require('fs'),os=require('os'),path=require('path');
var auth=require('./mobile-auth'),server=require('./mobile-server');
function fetch(url,options) {
  return new Promise(function(resolve,reject) {
    var request=require('http').request(url,{method:options.method,headers:options.headers},function(response) {
      var body='';response.on('data',function(chunk){body+=chunk;});
      response.on('end',function(){resolve({status:response.statusCode,
        headers:{get:function(name){var value=response.headers[name.toLowerCase()];return Array.isArray(value)?value[0]:value;}},
        json:function(){return Promise.resolve(JSON.parse(body));}});});
    });request.on('error',reject);request.end(options.body);
  });
}
async function main() {
  var now=0,credentials=auth.create(function(){return now;});
  var pin=credentials.newPin().pin;
  assert.throws(function(){credentials.pair('invalid');});
  var token=credentials.pair(pin);assert(credentials.valid(token));
  assert.throws(function(){credentials.pair(pin);},'PIN cannot be reused');
  credentials.logout(token);assert(!credentials.valid(token));
  pin=credentials.newPin().pin;now=300001;assert.throws(function(){credentials.pair(pin);});
  credentials=auth.create(function(){return now;});credentials.newPin();
  for(var i=0;i<5;i++)assert.throws(function(){credentials.pair('invalid');});
  assert.throws(function(){credentials.newPin();});now+=30001;assert(credentials.newPin());
  assert(server.privateAddress('192.168.1.3'));assert(!server.privateAddress('8.8.8.8'));
  var directory=fs.mkdtempSync(path.join(os.tmpdir(),'osd-mobile-')),file=path.join(directory,'layers.json'),changed=0;
  var instance=server.create({port:0,file:file,policyChanged:function(){changed++;}});
  await new Promise(function(resolve){instance.server.listen(0,'127.0.0.1',resolve);});
  var url='http://127.0.0.1:'+instance.server.address().port,cookie='';
  async function call(route,method,body,origin) {
    return fetch(url+route,{method:method||'GET',headers:{'Content-Type':'application/json',Origin:origin===undefined?url:origin,Cookie:cookie},body:body===undefined?undefined:JSON.stringify(body)});
  }
  try {
    assert.strictEqual((await call('/api/settings')).status,401);
    var response=await call('/api/pair','POST',{pin:instance.auth.newPin().pin},'http://evil.invalid');
    assert.strictEqual(response.status,403);
    response=await call('/api/pair','POST',{pin:instance.auth.newPin().pin});
    assert.strictEqual(response.status,200);cookie=response.headers.get('set-cookie').split(';')[0];
    assert(response.headers.get('set-cookie').includes('HttpOnly'));
    var value=await (await call('/api/settings')).json();
    response=await call('/api/settings','PATCH',{revision:value.revision,patch:{fontHeight:130,coverGrow:6,translationScope:'all'}});
    assert.strictEqual(response.status,200);value=await response.json();
    assert.strictEqual(value.settings.fontHeight,130);assert.strictEqual(changed,1);
    assert.strictEqual(JSON.parse(fs.readFileSync(file)).translationScope,'all');
    assert.strictEqual((await call('/api/settings','PATCH',{revision:0,patch:{text:false}})).status,409);
    assert.strictEqual((await call('/api/settings','PATCH',{revision:value.revision,patch:{speechEnabled:true}})).status,400);
    assert.strictEqual((await call('/api/settings','PATCH',{revision:value.revision,patch:{unknown:1}})).status,400);
    assert.strictEqual((await call('/api/settings','PATCH',{revision:value.revision,patch:{fontHeight:999}})).status,400);
    assert.strictEqual((await call('/api/logout','POST',{})).status,200);
    assert.strictEqual((await call('/api/settings')).status,401);
    console.log('PIN expiry/lock/single-use, anonymous denial, CSRF, persistence, revision and speech gate: PASS');
  }finally {
    await new Promise(function(resolve){instance.server.close(resolve);});
    if(fs.existsSync(file))fs.unlinkSync(file);fs.rmdirSync(directory);
  }
}
main().catch(function(error){console.error(error);process.exitCode=1;});
