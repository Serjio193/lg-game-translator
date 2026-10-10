'use strict';
var assert=require('assert'),vm=require('vm'),fs=require('fs');
var elements={},requests=[];
function element(id){if(!elements[id])elements[id]={value:'',disabled:true,events:{},
  addEventListener:function(name,callback){this.events[name]=callback;},focus:function(){},scrollIntoView:function(){}};return elements[id];}
function Xhr(){requests.push(this);}
Xhr.prototype.open=function(method,url){this.method=method;this.url=url;};
Xhr.prototype.setRequestHeader=function(name,value){this.headers=this.headers||{};this.headers[name]=value;};
Xhr.prototype.send=function(value){this.body=value;};
var context={XMLHttpRequest:Xhr,window:{OSD_MENU_KEY:'fixture-menu-key'},
  document:{getElementById:element,addEventListener:function(){}},JSON:JSON,Object:Object};
vm.runInNewContext(fs.readFileSync(__dirname+'/menu.js','utf8'),context);
assert.strictEqual(requests.length,1);
assert.strictEqual(requests[0].url,'http://127.0.0.1:18779/translator-settings','Opening the menu only reads local state');
assert.strictEqual(requests[0].headers['X-OSD-Menu-Key'],'fixture-menu-key');
requests[0].status=200;requests[0].responseText='{"server_settings":null}';requests[0].onload();
assert(elements.status.textContent.includes('нет в кэше'));
assert.strictEqual(requests.length,1,'Missing cache never triggers an automatic Orange retry');
elements['refresh-settings'].events.click();
assert.strictEqual(requests[1].url,'http://192.168.1.11:8765/api/settings','An explicit user refresh may contact Orange');
var html=fs.readFileSync(__dirname+'/index.html','utf8');
assert(html.indexOf('src="menu-key.js"')<html.indexOf('src="menu.js"'),'Capability loads before the authenticated cache request');
console.log('TV menu bootstrap remains local, cache miss stays silent, explicit refresh and key ordering: PASS');
