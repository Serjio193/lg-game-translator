// LAN settings endpoint owned by the persistent OSD controller.
'use strict';
var http=require('http'),fs=require('fs'),path=require('path'),os=require('os');
var authModule=require('./mobile-auth'),storeModule=require('./mobile-store'),qr=require('./qr-url');
var running=null;
function privateAddress(address) {
  address=(address||'').replace(/^::ffff:/,'');
  var p=address.split('.').map(Number);
  return address==='::1'||(p.length===4&&p.every(function(n){return Number.isInteger(n)&&n>=0&&n<=255;})&&
    (p[0]===127||p[0]===10||p[0]===192&&p[1]===168||p[0]===172&&p[1]>=16&&p[1]<=31));
}
function addresses() {
  var result=['127.0.0.1'];
  var interfaces=os.networkInterfaces();
  Object.keys(interfaces).forEach(function(name){interfaces[name].forEach(function(item){
    if((item.family==='IPv4'||item.family===4)&&privateAddress(item.address)) result.push(item.address);
  });});
  return result;
}
function create(options) {
  options=options||{};
  var auth=authModule.create(),store=storeModule.create(options.file||'/media/developer/game-translator-layers.json',options.policyChanged,options.canTranslate);
  var port=options.port===undefined?18780:options.port;
  function json(response,status,value) {response.writeHead(status,{'Content-Type':'application/json; charset=utf-8'});response.end(JSON.stringify(value));}
  function token(request) {var match=/(?:^|;\s*)osd_session=([0-9a-f]{64})(?:;|$)/.exec(request.headers.cookie||'');return match?match[1]:'';}
  function pairing() {
    var ip=addresses().filter(function(value){return value!=='127.0.0.1';})[0];
    if(!ip) throw new Error('Нет адреса локальной сети');
    var value=auth.newPin(),url='http://'+ip+':'+port+'/';
    return Object.assign(value,{url:url,qrSvg:qr.svg(url)});
  }
  var server=http.createServer(function(request,response) {
    response.setHeader('Cache-Control','no-store');
    response.setHeader('X-Content-Type-Options','nosniff');
    response.setHeader('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-ancestors 'none'");
    var host=request.headers.host||'';
    if(!privateAddress(request.socket.remoteAddress)||!addresses().some(function(ip){return host===ip+':'+port;})) return json(response,403,{error:'Только локальная сеть ТВ'});
    if(request.method==='GET'&&['/','/index.html','/mobile.js','/mobile.css','/preview-variants.css','/provider-settings.js','/provider-settings.css'].indexOf(request.url.split('?')[0])>=0) {
      var name=request.url.split('?')[0].slice(1)||'index.html';
      fs.readFile(path.join(__dirname,'mobile',name),function(error,body) {
        if(error) return json(response,503,{error:'Меню недоступно'});
        response.writeHead(200,{'Content-Type':name.endsWith('.js')?'application/javascript; charset=utf-8':name.endsWith('.css')?'text/css; charset=utf-8':'text/html; charset=utf-8'});response.end(body);
      });return;
    }
    var session=token(request);
    if(request.url!=='/api/pair'&&!auth.valid(session)) return json(response,401,{error:'Введите PIN с экрана ТВ'});
    if(request.method==='GET'&&request.url==='/api/settings') {
      try{return json(response,200,store.read());}catch(error){return json(response,503,{error:'Не удалось прочитать настройки'});}
    }
    var translator=options.translator||require('./translator-control');
    if(request.method==='GET'&&request.url==='/api/translator') {
      translator.status(function(error,value){json(response,error?503:200,error?{error:error.message}:value);});return;
    }
    if(!((request.method==='POST'&&['/api/pair','/api/logout','/api/translator','/api/translator-key'].indexOf(request.url)>=0)||request.method==='PATCH'&&request.url==='/api/settings')) return json(response,404,{error:'Not found'});
    if(request.headers.origin!=='http://'+host) return json(response,403,{error:'Запрос должен исходить из меню ТВ'});
    if((request.headers['content-type']||'').split(';')[0]!=='application/json') return json(response,415,{error:'Нужен JSON'});
    var body='',tooLarge=false;
    request.on('data',function(chunk){if(tooLarge)return;body+=chunk;if(Buffer.byteLength(body)>16384){tooLarge=true;body='';json(response,413,{error:'Запрос слишком большой'});}});
    request.on('end',function(){
      if(tooLarge)return;
      var value;try{value=JSON.parse(body);}catch(error){return json(response,400,{error:'Неверный JSON'});}
      try {
        if(request.url==='/api/translator-key') {
          if(!value||Array.isArray(value)||typeof value!=='object'||Object.keys(value).length)return json(response,400,{error:'Нужен пустой запрос настройки ключа'});
          translator.liveStatus(function(error,result){json(response,error?503:200,error?{error:error.message}:result);});return;
        }
        if(request.url==='/api/translator') {
          translator.update(value,function(error,result){json(response,error?400:200,error?{error:error.message}:result);});return;
        }
        if(request.url==='/api/pair') {
          var credential=auth.pair(value&&value.pin);
          response.setHeader('Set-Cookie','osd_session='+credential+'; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800');
          return json(response,200,{paired:true});
        }
        if(request.url==='/api/logout') {
          auth.logout(session);response.setHeader('Set-Cookie','osd_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0');
          return json(response,200,{paired:false});
        }
        return json(response,200,store.update(value));
      }catch(error){json(response,error.status||400,{error:error.message});}
    });
  });
  server.on('listening',function(){port=server.address().port;});
  server.requestTimeout=5000;server.headersTimeout=5000;
  return {server:server,pairing:pairing,auth:auth,store:store};
}
exports.create=create;exports.privateAddress=privateAddress;
exports.start=function(options){
  if(running)return running;
  running=create(options);running.server.on('error',function(){console.error('Mobile OSD settings unavailable');});
  running.server.listen(18780,'0.0.0.0');return running;
};
