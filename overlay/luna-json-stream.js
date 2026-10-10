'use strict';

// luna-send -f emits concatenated, possibly multiline JSON objects.
exports.create = function (receive) {
  var buffer = '';
  return function (chunk) {
    buffer += chunk;
    if (Buffer.byteLength(buffer, 'utf8') > 65536) throw new Error('Luna response too large');
    while (buffer.trim()) {
      buffer = buffer.replace(/^\s+/, '');
      if (buffer[0] !== '{') throw new Error('Invalid Luna response');
      var depth = 0, quoted = false, escaped = false, end = -1;
      for (var i = 0; i < buffer.length; i++) {
        var c = buffer[i];
        if (quoted) {
          if (escaped) escaped = false;
          else if (c === '\\') escaped = true;
          else if (c === '"') quoted = false;
        } else if (c === '"') quoted = true;
        else if (c === '{') depth++;
        else if (c === '}' && --depth === 0) { end = i + 1; break; }
      }
      if (end < 0) return;
      var value = JSON.parse(buffer.slice(0, end));
      buffer = buffer.slice(end);
      receive(value);
    }
    buffer = '';
  };
};
