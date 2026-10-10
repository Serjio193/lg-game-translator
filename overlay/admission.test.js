'use strict';
var assert = require('assert');
var admission = require('./admission');
var response = {admission: {track_id: 4, version_ms: 1200, text: 'follow me'}};
function gate(observations) {
  return {complete: true, timestamp_ms: 9000, observations: observations, required: 3,
    admission: {track_id: 4, version_ms: 1200, text: 'follow me'}};
}
assert.strictEqual(admission(response, gate(1), 9000), 'wait');
assert.strictEqual(admission(response, gate(2), 9000), 'wait');
assert.strictEqual(admission(response, gate(3), 9000), 'ready');
var changed = gate(3); changed.admission.text = 'follow me to the door';
assert.strictEqual(admission(response, changed, 9000), 'invalid');
changed = gate(3); changed.admission.version_ms++;
assert.strictEqual(admission(response, changed, 9000), 'invalid');
changed = gate(3); changed.admission.track_id++;
assert.strictEqual(admission(response, changed, 9000), 'invalid');
assert.strictEqual(admission(response, {}, 9000), 'invalid');
changed = gate(3); changed.complete = false;
assert.strictEqual(admission(response, changed, 9000), 'invalid');
assert.strictEqual(admission(response, gate(3), 14001), 'wait');
assert.strictEqual(admission(response, gate(3), 24000), 'wait');
assert.strictEqual(admission(response, gate(3), 24001), 'invalid');
assert.strictEqual(admission({translation: 'legacy'}, gate(3), 9000), 'invalid');
var preview={admission:response.admission,stage:'preliminary',engine:'bergamot',confirmation_policy:'three-final-v1'};
assert.strictEqual(admission(preview,gate(1),9000),'ready','Validated Bergamot can precede final confirmation');
assert.strictEqual(admission(Object.assign({},preview,{confirmation_policy:null}),gate(1),9000),'wait');
assert.strictEqual(admission(Object.assign({},preview,{stage:'final'}),gate(1),9000),'wait','Final still requires 3');
assert.strictEqual(admission(preview,changed,9000),'invalid','Previews cannot bypass identity checks');
console.log('Early response waits; changed, absent, failed and stale tracks block: PASS');
