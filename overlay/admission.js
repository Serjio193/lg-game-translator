'use strict';

// Compare the exact native-normalized text and track/version, never coordinates.
module.exports = function (response, gate, now) {
  var key = response && response.admission;
  var current = gate && gate.admission;
  if (!key || !current || !key.track_id || !key.version_ms || !key.text
      || key.track_id !== current.track_id || key.version_ms !== current.version_ms
      || key.text !== current.text || !gate.complete) return 'invalid';
  if (!Number.isFinite(gate.timestamp_ms) || now - gate.timestamp_ms > 15000
      || gate.timestamp_ms - now > 1000) return 'invalid';
  // Slow menu scans must not hide an already displayed unchanged subtitle.
  // Do not publish a new translation until a fresh observation arrives.
  if (now - gate.timestamp_ms > 5000) return 'wait';
  if (gate.required === 3 && response.confirmation_policy === 'three-final-v1' && gate.observations >= 1
      && response.stage === 'preliminary' && response.engine === 'bergamot') return 'ready';
  return gate.required === 3 && gate.observations >= 3 ? 'ready' : 'wait';
};
