'use strict';
var assert = require('assert');
var vm = require('vm');
var fs = require('fs');
function Element(tag) { this.tag = tag; this.children = []; this.events = {}; this.disabled = false; this.checked = false; }
Element.prototype.appendChild = function (child) { this.children.push(child); };
Element.prototype.addEventListener = function (name, handler) { this.events[name] = handler; };
Object.defineProperty(Element.prototype, 'textContent', {
  get: function () { return this.text || ''; },
  set: function (value) { this.text = value; this.children = []; }
});
Element.prototype.querySelectorAll = function () {
  var inputs = [];
  function visit(node) { if (node.tag === 'input') inputs.push(node); node.children.forEach(visit); }
  this.children.forEach(visit); return inputs;
};
var ids = {}, requests = [];
['app-list', 'app-status', 'status', 'refresh-apps'].forEach(function (id) { ids[id] = new Element('div'); });
var context = {
  window: {}, document: {getElementById: function (id) { return ids[id]; }, createElement: function (tag) { return new Element(tag); }},
  XMLHttpRequest: function () {
    this.open = function (method, url) {
      assert.strictEqual(method, 'GET');
      assert(['http://127.0.0.1:18779/apps', 'http://127.0.0.1:18779/apps?refresh=1'].indexOf(url) >= 0);
      this.url = url;
    };
    this.send = function () { requests.push(this); };
  }
};
vm.runInNewContext(fs.readFileSync(__dirname + '/app-picker.js', 'utf8'), context);
var picker = context.window.AppPicker;
picker.set(['saved.app']); picker.enable(true);
assert.strictEqual(picker.get()[0], 'saved.app');
picker.load();
var response = requests.pop(); response.status = 200;
response.responseText = JSON.stringify({applications: [{id: 'app.test', name: '<script>safe text</script>'}]});
response.onload();
assert.strictEqual(picker.controls().length, 2, 'Unavailable saved choice stays visible');
assert.strictEqual(ids['app-list'].children[0].children[1].textContent, '<script>safe text</script>');
var input = picker.controls()[0]; input.checked = true; input.events.change();
assert.deepStrictEqual(Array.from(picker.get()), ['app.test', 'saved.app']);
assert.strictEqual(ids.status.textContent, 'Изменения ещё не сохранены');
ids['refresh-apps'].events.click();
var refresh = requests.pop(); assert(refresh.url.endsWith('?refresh=1')); refresh.onerror();
assert.deepStrictEqual(Array.from(picker.get()), ['app.test', 'saved.app'], 'Failed catalogue does not clear choices');
picker.enable(false); assert(picker.controls().every(function (control) { return control.disabled; }));
console.log('Application rendering, selection and failure preservation: PASS');
