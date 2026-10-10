'use strict';
var assert=require('assert'),fs=require('fs'),vm=require('vm');
async function main(){
  var elements={},calls=[],timers=[],intervals=[];
  function element(id){
    if(!elements[id])elements[id]={style:{},hidden:false,events:{},textContent:'',value:'',
      addEventListener:function(name,callback){this.events[name]=callback;}};
    return elements[id];
  }
  var toggle=element('manual');toggle.type='checkbox';toggle.dataset={key:'translationEnabled'};toggle.checked=false;
  var revision=1;
  var context={window:{TranslatorSettings:{start:function(){}}},location:{search:''},
    localStorage:{setItem:function(){},getItem:function(){return null;}},
    document:{body:{dataset:{}},getElementById:element,
      querySelectorAll:function(selector){return selector==='[data-key]'?[toggle]:[];}},
    setTimeout:function(callback,delay){var task={callback:callback,delay:delay};timers.push(task);return task;},
    clearTimeout:function(task){timers=timers.filter(function(item){return item!==task;});},
    setInterval:function(callback){intervals.push(callback);},
    fetch:async function(path,options){
      calls.push({path:path,method:options.method,body:options.body&&JSON.parse(options.body)});
      if(options.method==='PATCH'){
        revision=2;
        return {ok:false,status:409,json:async function(){return {error:'Power session changed'};}};
      }
      return {ok:true,json:async function(){return {revision:revision,settings:{translationEnabled:false}};}};
    },console:console};
  vm.runInNewContext(fs.readFileSync(__dirname+'/mobile.js','utf8'),context);
  for(var i=0;i<5;i++)await Promise.resolve();
  toggle.checked=true;toggle.events.input();
  assert.strictEqual(timers.length,1);var save=timers.shift();await save.callback();
  assert.strictEqual(calls.filter(function(call){return call.method==='PATCH';}).length,1);
  assert.strictEqual(timers.length,0,'A conflicted ON is never scheduled for automatic retry');
  assert.strictEqual(toggle.checked,false,'Phone shows the new OFF after the power boundary');
  assert(elements['save-status'].textContent.includes('ещё раз'));
  await intervals[0]();
  assert.strictEqual(calls.filter(function(call){return call.method==='PATCH';}).length,1);
  assert(calls.every(function(call){return call.path==='/api/settings';}),'UI refresh only uses the TV-local endpoint');
  console.log('Phone ON conflict requires a new click; local refresh never resurrects the command: PASS');
}
main().catch(function(error){console.error(error);process.exitCode=1;});
