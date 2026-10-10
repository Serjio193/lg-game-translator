// Only the installed TV menu can submit a key on this loopback-only server.
'use strict';
var fs=require('fs'),auth=require('./mobile-auth'),control=require('./translator-control');
exports.handle=function(request,response){
  response.setHeader('Access-Control-Allow-Headers','X-OSD-Menu-Key, Content-Type');
  response.setHeader('Access-Control-Allow-Methods','GET, POST, OPTIONS');
  function send(error,value){response.statusCode=error?400:200;response.end(JSON.stringify(error?{error:error.message}:value));}
  if(request.method==='OPTIONS'){response.end();return;}
  var key;
  try{key=fs.readFileSync('/media/developer/game-translator-mobile-menu.key','utf8').trim();}catch(error){key='';}
  if(!auth.equal(key,request.headers['x-osd-menu-key'])){response.statusCode=403;response.end('{"error":"Нужен доступ меню ТВ"}');return;}
  if(request.method==='GET'){control.status(send);return;}
  if(request.method!=='POST'){response.statusCode=405;response.end('{}');return;}
  if((request.headers['content-type']||'').split(';')[0]!=='application/json'){response.statusCode=415;response.end('{}');return;}
  var body='',large=false;
  request.on('data',function(chunk){if(large)return;body+=chunk;if(Buffer.byteLength(body)>4096){large=true;body='';response.statusCode=413;response.end('{}');}});
  request.on('end',function(){if(large)return;try{control.localUpdate(JSON.parse(body),send);}catch(error){send(new Error('Неверный JSON'));}});
};
