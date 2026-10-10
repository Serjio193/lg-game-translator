// Privileged server-to-server proxy. Credentials never enter browser responses.
'use strict';
var fs=require('fs'),http=require('http'),crypto=require('crypto');
var file='/media/developer/game-translator-provider.json';
function call(method,value,callback) {
  var config,address;
  try {
    config=JSON.parse(fs.readFileSync(file,'utf8'));
    address=new URL(config.address);
    if(address.protocol!=='http:'||!require('./mobile-server').privateAddress(address.hostname)||
        !/^[0-9a-f]{64}$/.test(config.controlKey)) throw new Error('Invalid config');
  } catch(error) {callback(new Error('Управление переводчиком ещё не установлено на ТВ'));return;}
  var body=value?JSON.stringify(value):'',done=false;
  function finish(error,result){if(done)return;done=true;callback(error,result);}
  var request=http.request({hostname:address.hostname,port:address.port||80,
    path:'/api/google-control',method:method,headers:{'X-OSD-Control-Key':config.controlKey,
      'Content-Type':'application/json','Content-Length':Buffer.byteLength(body)}},function(response){
    var chunks=[],size=0;
    response.on('data',function(chunk){size+=chunk.length;if(size>65536){request.destroy();finish(new Error('Ответ слишком большой'));}else chunks.push(chunk);});
    response.on('end',function(){
      try {var result=JSON.parse(Buffer.concat(chunks).toString('utf8'));
        if(response.statusCode!==200)throw new Error(result.error||'Ошибка сервера перевода');
        finish(null,result);
      }catch(error){finish(error);}
    });
    response.on('error',function(){finish(new Error('Нет связи с переводчиком'));});
  });
  request.setTimeout(5000,function(){request.destroy();finish(new Error('Нет связи с переводчиком'));});
  request.on('error',function(){finish(new Error('Нет связи с переводчиком'));});
  request.end(body);
}
function update(value,callback) {
  if(!value||typeof value!=='object'||Array.isArray(value)||Object.keys(value).some(function(key){return ['provider','encrypted_key'].indexOf(key)<0;})) {
    callback(new Error('Допустимы только переводчик и зашифрованный ключ'));return;
  }
  call('POST',value,callback);
}
exports.status=function(callback){call('GET',null,callback);};
exports.update=update;
exports.localUpdate=function(value,callback){
  if(!value||typeof value!=='object'||Object.keys(value).some(function(key){return ['provider','key'].indexOf(key)<0;}))return callback(new Error('Неверные настройки'));
  if(!value.key)return update({provider:value.provider},callback);
  if(typeof value.key!=='string'||!/^[A-Za-z0-9_-]{20,200}$/.test(value.key))return callback(new Error('Неверный формат API-ключа'));
  exports.status(function(error,state){
    if(error)return callback(error);
    try {
      var encrypted=crypto.publicEncrypt({key:state.public_key,padding:crypto.constants.RSA_PKCS1_OAEP_PADDING,oaepHash:'sha256'},Buffer.from(value.key,'utf8'));
      update({provider:value.provider,encrypted_key:encrypted.toString('base64')},callback);
    }catch(failed){callback(new Error('Не удалось зашифровать ключ'));}
  });
};
