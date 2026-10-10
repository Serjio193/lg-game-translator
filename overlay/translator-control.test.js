'use strict';
var assert=require('assert'),http=require('http'),fs=require('fs'),crypto=require('crypto');
var control=require('./translator-control');
async function main(){
  var pair=crypto.generateKeyPairSync('rsa',{modulusLength:2048});
  var key='unit-test-credential-'+ 'x'.repeat(30),observed=null,controlToken='a'.repeat(64);
  var server=http.createServer(function(request,response){
    assert.strictEqual(request.headers['x-osd-control-key'],controlToken);
    var body='';request.on('data',function(chunk){body+=chunk;});
    request.on('end',function(){
      if(request.method==='POST'){
        observed=JSON.parse(body);assert(!body.includes(key));assert(!('key' in observed));
        assert.strictEqual(crypto.privateDecrypt({key:pair.privateKey,padding:crypto.constants.RSA_PKCS1_OAEP_PADDING,oaepHash:'sha256'},Buffer.from(observed.encrypted_key,'base64')).toString(),key);
      }
      response.setHeader('Content-Type','application/json');response.end(JSON.stringify({provider:'madlad',
        public_key:pair.publicKey.export({type:'spki',format:'pem'}),key_configured:request.method==='POST',budget:{monthly_characters:0}}));
    });
  });
  await new Promise(function(resolve){server.listen(0,'127.0.0.1',resolve);});
  var read=fs.readFileSync;
  fs.readFileSync=function(file){if(file==='/media/developer/game-translator-provider.json')return JSON.stringify({address:'http://127.0.0.1:'+server.address().port,controlKey:controlToken});return read.apply(fs,arguments);};
  function call(method,value){return new Promise(function(resolve,reject){control[method](value,function(error,result){if(error)reject(error);else resolve(result);});});}
  try{
    await assert.rejects(call('update',{key:key}));
    var value=await call('localUpdate',{key:key});assert(value.key_configured);assert(observed.encrypted_key);
    assert(!JSON.stringify(value).includes(controlToken));assert(!JSON.stringify(value).includes(key));
    console.log('TV key RSA-OAEP encryption, plaintext rejection and secret-free responses: PASS');
  }finally{fs.readFileSync=read;await new Promise(function(resolve){server.close(resolve);});}
}
main().catch(function(error){console.error(error);process.exitCode=1;});
