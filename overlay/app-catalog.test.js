'use strict';
var assert = require('assert');
var fs = require('fs');
var os = require('os');
var path = require('path');
var icons = require('./app-icon');
var catalogue = require('./app-catalog').catalogue;
var root = fs.mkdtempSync(path.join(os.tmpdir(), 'translator-icons-'));
try {
  fs.mkdirSync(path.join(root, 'installed')); fs.mkdirSync(path.join(root, 'installed', 'app.test'));
  var bytes = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a6mwAAAAASUVORK5CYII=', 'base64');
  fs.writeFileSync(path.join(root, 'installed', 'app.test', 'icon.png'), bytes);
  fs.writeFileSync(path.join(root, 'secret.png'), bytes);
  var app = {id: 'app.test', icon: 'icon.png'};
  assert.strictEqual(icons.toDataUri(app, [path.join(root, 'installed')]), 'data:image/png;base64,' + bytes.toString('base64'));
  assert.strictEqual(icons.toDataUri({id: 'app.test', icon: '../../secret.png'}, [path.join(root, 'installed')]), null);
  assert.strictEqual(icons.toDataUri({id: 'app.test', icon: 'https://remote/icon.png'}, [path.join(root, 'installed')]), null);
  assert.strictEqual(icons.toDataUri({icon: 'icon.png'}, [path.join(root, 'installed')]), null);
  fs.writeFileSync(path.join(root, 'installed', 'app.test', 'bad.png'), 'not an image');
  assert.strictEqual(icons.toDataUri({id: 'app.test', icon: 'bad.png'}, [path.join(root, 'installed')]), null);
  var rows = catalogue({returnValue: true, apps: [
    {id: 'app.test', title: '<Sample>', visible: true},
    {id: 'app.test', title: 'Duplicate', visible: true},
    {id: 'hidden.app', title: 'Hidden', visible: true, class: {hidden: true}},
    {id: 'com.webos.app.hdmi1', title: 'HDMI', visible: true},
    {id: 'com.serjio193.lggametranslator.overlay', title: 'Overlay', visible: true},
    {title: 'No ID', visible: true}
  ]});
  assert.strictEqual(rows.length, 1);
  assert.strictEqual(rows[0].name, '<Sample>');
  assert.throws(function () { catalogue({returnValue: false}); });
} finally {
  var resolved = fs.realpathSync(root), parent = fs.realpathSync(os.tmpdir());
  assert(resolved.indexOf(parent + path.sep + 'translator-icons-') === 0, 'Cleanup must remain in the created temporary directory');
  fs.rmSync(resolved, {recursive: true, force: true});
}
console.log('Catalogue filtering and bounded local icon paths: PASS');
