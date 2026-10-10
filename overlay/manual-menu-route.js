'use strict';
var fs=require('fs'),auth=require('./mobile-auth');
exports.handle=function(request,response,store){
  response.setHeader('Access-Control-Allow-Headers','X-OSD-Menu-Key, Content-Type');
  response.setHeader('Access-Control-Allow-Methods','GET, POST, OPTIONS');
  function send(status,value){response.statusCode=status;response.end(JSON.stringify(value));}
  if(request.method==='OPTIONS'){response.end();return;}
  var key;try{key=fs.readFileSync('/media/developer/game-translator-mobile-menu.key','utf8').trim();}catch(error){key='';}
  if(!auth.equal(key,request.headers['x-osd-menu-key']))return send(403,{error:'Нужен доступ меню ТВ'});
  if(request.method==='GET'){try{return send(200,store.read());}catch(error){return send(503,{error:'Настройки недоступны'});}}
  if(request.method!=='POST')return send(405,{error:'Method not allowed'});
  if((request.headers['content-type']||'').split(';')[0]!=='application/json')return send(415,{error:'Нужен JSON'});
  var body='',large=false;
  request.on('data',function(chunk){if(large)return;body+=chunk;if(Buffer.byteLength(body)>1024){large=true;body='';send(413,{error:'Слишком большой запрос'});}});
  request.on('end',function(){
    if(large)return;
    try{
      var value=JSON.parse(body);
      if(!value||Object.keys(value).some(function(k){return ['revision','enabled'].indexOf(k)<0;})||typeof value.enabled!=='boolean')throw new Error('Нужен переключатель');
      send(200,store.update({revision:value.revision,patch:{translationEnabled:value.enabled}}));
    }catch(error){send(error.status||400,{error:error.message});}
  });
};
