// Execute on TV, after installing settings_0.1.9_all.ipk; preserves the watcher.
'use strict';
var fs=require('fs'),path=require('path'),crypto=require('crypto');
var staging=path.resolve(process.argv[2]||'.');
var app='/media/developer/apps/usr/palm/applications/com.serjio193.lggametranslator.overlay';
var menu='/media/developer/apps/usr/palm/applications/com.serjio193.lggametranslator.settings';
var relay='/media/developer/gocr-runtime/ppocr-probe-transport/gocr_worker';
var modules=['mobile-server.js','mobile-auth.js','mobile-store.js','qr-url.js','layer-settings.js',
  'translator-control.js','translator-menu-route.js','manual-menu-route.js','orange-state.js',
  'tv-power.js','luna-json-stream.js',
  'admission.js',
  'translation-pairs.js','layout-height.js','multi-subtitles.js',
  'manual-style.js','subtitle-layout.js','glyph-cover.js','mask-grow.js','mask-osd-raster.js',
  'line-cover-mask.js','mask-edge-blur.js','control-icons.js','backdrop.js','fit-area.js',
  'mobile/index.html','mobile/mobile.js','mobile/mobile.css','mobile/preview-variants.css',
  'mobile/provider-settings.js','mobile/provider-settings.css'];
var backup='/media/developer/gocr-runtime/backups/mobile-osd-'+Date.now();
function copy(source,target) {fs.mkdirSync(path.dirname(target),{recursive:true});fs.copyFileSync(source,target);}
if(!fs.existsSync(path.join(app,'translation-watcher.js'))||!fs.existsSync(path.join(menu,'mobile-pairing.js'))) throw new Error('Install the OSD and settings 0.1.3 first');
modules.forEach(function(name){if(!fs.existsSync(path.join(staging,name)))throw new Error('Incomplete bundle: '+name);});
if(!fs.existsSync(path.join(staging,'relay/frame_client.py')))throw new Error('Missing frame client');
var relayModules=['frame_client.py','frame_pipeline.py','translation_client.py','live_translation.py',
  'sentence_preview.py','sentence_boundaries.py'];
if(fs.existsSync(relay))relayModules.forEach(function(name){
  if(!fs.existsSync(path.join(staging,'relay',name)))throw new Error('Missing relay module: '+name);
});
var indexFile=path.join(app,'index.html'),index=fs.readFileSync(indexFile,'utf8');
if(index.indexOf('<script src="subtitle-layout.js">')<0)throw new Error('Unknown installed renderer; refusing update');
modules.forEach(function(name){
  if(fs.existsSync(path.join(app,name)))copy(path.join(app,name),path.join(backup,name));
  copy(path.join(staging,name),path.join(app,name));
});
copy(indexFile,path.join(backup,'index.html'));
if(index.indexOf('manual-style.js')<0)fs.writeFileSync(indexFile,index.replace('<script src="subtitle-layout.js">','<script src="manual-style.js"></script>\n  <script src="subtitle-layout.js">'));
if(fs.existsSync(relay)) {
  relayModules.forEach(function(name){
    if(fs.existsSync(path.join(relay,name)))copy(path.join(relay,name),path.join(backup,'relay',name));
    copy(path.join(staging,'relay',name),path.join(relay,name));
  });
}
var keyFile='/media/developer/game-translator-mobile-menu.key',key;
if(fs.existsSync(keyFile))key=fs.readFileSync(keyFile,'utf8').trim();
if(!/^[0-9a-f]{64}$/.test(key||''))key=crypto.randomBytes(32).toString('hex');
fs.writeFileSync(keyFile,key,{mode:384});fs.chmodSync(keyFile,384);
fs.writeFileSync(path.join(menu,'menu-key.js'),'window.OSD_MENU_KEY='+JSON.stringify(key)+';\n',{mode:420});
// This device-specific credential is provisioned separately over SSH, never packaged.
var providerFile=path.join(staging,'provider-config.json');
if(fs.existsSync(providerFile)){
  var config=JSON.parse(fs.readFileSync(providerFile,'utf8'));
  if(!/^http:\/\/192\.168\.1\.11:8765\/?$/.test(config.address)||!/^[0-9a-f]{64}$/.test(config.controlKey))throw new Error('Invalid provider configuration');
  var target='/media/developer/game-translator-provider.json';
  copy(providerFile,target);fs.chmodSync(target,384);
}
console.log('Mobile OSD files prepared; backup: '+backup);
