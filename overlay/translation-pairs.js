'use strict';
var admission = require('./admission');
var layoutHeight = require('./layout-height');
function key(value) {
  var a = value.admission;
  return a && a.track_id + ':' + a.version_ms + ':' + a.text;
}
function overlaps(first, second) {
  if (first.response.admission.track_id === second.response.admission.track_id) return true;
  var a = first.block.appearance && first.block.appearance.box;
  var b = second.block.appearance && second.block.appearance.box;
  if (!a || !b) return false;
  var width = Math.max(0,Math.min(a.x+a.width,b.x+b.width)-Math.max(a.x,b.x));
  var height = Math.max(0,Math.min(a.y+a.height,b.y+b.height)-Math.max(a.y,b.y));
  return width * height > Math.min(a.width*a.height,b.width*b.height) * 0.5;
}
function upgrade(item, response, preview) {
  var sentencePreview=preview && response.stage==='preliminary' && response.engine==='bergamot'
    && response.confirmation_policy==='three-final-v1';
  if (key(item.response) !== key(response) || !(response.stage === 'final' || sentencePreview)
      || item.response.stage === 'final' || item.response === response) return false;
  var text = response.translation.slice(0,1000), changed = item.block.text !== text;
  item.block.text = text;
  item.response = response;
  if (changed) item.until = Infinity;
  return changed;
}
exports.create = function () {
  var visible = Object.create(null), pending = Object.create(null), retired = Object.create(null);
  return {update:function (gate, responses, now, provider, allowed) {
    if (!allowed) {
      visible = Object.create(null); pending = Object.create(null); retired = Object.create(null);
      return [];
    }
    var entries = gate && Array.isArray(gate.regions) ? gate.regions.slice(0,20) : [];
    var current = Object.create(null);
    entries.forEach(function (entry) { if (key(entry)) current[key(entry)] = entry; });
    Object.keys(retired).forEach(function (id) { if (!current[id]) delete retired[id]; });
    // A held/queued version has already passed 3/3. Its matching final may
    // upgrade it even after the original advances; an unrelated late reply cannot.
    Object.keys(responses).forEach(function (slot) {
      var response = responses[slot];
      if (!response || response.provider !== provider || typeof response.translation !== 'string'
          || !response.translation.trim()) return;
      var id = key(response);
      if (visible[id]) upgrade(visible[id],response);
      Object.keys(pending).forEach(function (blocked) {
        if (pending[blocked].block.id === id) upgrade(pending[blocked],response);
      });
    });
    Object.keys(visible).forEach(function (id) {
      var prior = visible[id], entry = current[id];
      var permission = entry && admission(prior.response, {
        admission:entry.admission, observations:entry.observations, required:gate.required,
        timestamp_ms:gate.timestamp_ms, complete:gate.complete
      }, now);
      if (prior.response.provider !== provider) {
        delete visible[id]; delete pending[id];
      } else if ((pending[id] || permission === 'invalid' || !entry) && now >= prior.until) {
        delete visible[id]; retired[id] = true;
        if (pending[id]) {
          var next = pending[id]; delete pending[id];
          visible[next.block.id] = next;
        }
      }
      else if (permission === 'ready' && entry.appearance)
        prior.block.appearance = layoutHeight.update(prior.layoutHeight,entry.appearance,gate.timestamp_ms);
    });
    entries.forEach(function (entry) {
      var id = key(entry), response = responses[entry.slot];
      if (!id || retired[id] || !response
          || response.provider !== provider || typeof response.translation !== 'string'
          || !response.translation.trim()) return;
      var permission = admission(response, {admission:entry.admission, observations:entry.observations,
        required:gate.required,timestamp_ms:gate.timestamp_ms,complete:gate.complete}, now);
      if (permission !== 'ready') return;
      if (visible[id]) {upgrade(visible[id],response,true);return;}
      var heightState={};
      var item = {response:response,until:Infinity,shownText:null,layoutHeight:heightState,
        block:{id:id,text:response.translation.slice(0,1000),source:entry.source_text || entry.admission.text,
          appearance:layoutHeight.update(heightState,entry.appearance,gate.timestamp_ms)}};
      var continuation=response.stage==='preliminary' && response.engine==='bergamot'
        && response.confirmation_policy==='three-final-v1' && entry.appearance.sentence_flow
        && Object.keys(visible).filter(function(priorId) {
          var prior=visible[priorId], source=prior.block.source;
          return !current[priorId] && prior.response.stage==='preliminary'
            && item.block.source.indexOf(source)===0 && overlaps(prior,item);
        })[0];
      if(continuation) {
        var prior=visible[continuation];
        item.block.id=prior.block.id; // Keep the same DOM node for size animation.
        item.layoutHeight=prior.layoutHeight;
        item.block.appearance=layoutHeight.update(item.layoutHeight,entry.appearance,gate.timestamp_ms);
        delete visible[continuation];delete pending[continuation];
        visible[id]=item;
        return;
      }
      var blocked = Object.keys(visible).filter(function (priorId) {
        return !current[priorId] && overlaps(visible[priorId],item);
      })[0];
      if (blocked) {
        if (pending[blocked] && pending[blocked].block.id === id) return;
        pending[blocked] = item;
      } else if (Object.keys(visible).length < 20) visible[id] = item;
    });
    return Object.keys(visible).map(function (id) { return visible[id].block; });
  },shown:function (blocks, now) {
    blocks.forEach(function (block) {
      var item = visible[block.id] || Object.keys(visible).map(function(id){return visible[id];})
        .filter(function(value){return value.block.id===block.id;})[0];
      if (item && item.block.text === block.text && item.shownText !== block.text) {
        item.shownText = block.text;
        item.until = now + 5000;
      }
    });
  }};
};
