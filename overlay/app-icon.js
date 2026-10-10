// Adapted from AmbiSun app-icon.js, MIT (c) 2026 Serjio193. See AmbiSun-LICENSE.txt.
'use strict';
var fs = require('fs');
var path = require('path');
var PARENTS = ['/media/cryptofs/apps/usr/palm/applications',
  '/media/developer/apps/usr/palm/applications', '/usr/palm/applications'];
var MAX_BYTES = 512 * 1024;

function inside(file, root) { return file.indexOf(root + path.sep) === 0; }

function toDataUri(app, parents) {
  if (!app || typeof app.id !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/.test(app.id)) return null;
  parents = parents || PARENTS;
  var roots = parents.map(function (parent) { return path.join(parent, app.id); });
  [app.activeFolderPath, app.folderPath, app.path, app.basePath].forEach(function (root) {
    if (typeof root === 'string' && parents.some(function (p) { return inside(root, p); })) roots.push(root);
  });
  var values = [app.icon, app.iconPath, app.iconUri, app.mediumLargeIcon, app.largeIcon, app.extraLargeIcon];
  var approved = parents.map(function (p) { try { return fs.realpathSync(p); } catch (_) { return null; } })
    .filter(function (p) { return p !== null; });
  for (var i = 0; i < values.length; i++) {
    var value = values[i];
    if (typeof value !== 'string' || /^(data:|https?:\/\/)/i.test(value)) continue;
    var candidates = path.isAbsolute(value) ? [value] : roots.map(function (root) { return path.join(root, value); });
    for (var j = 0; j < candidates.length; j++) {
      try {
        var file = fs.realpathSync(candidates[j]);
        if (!approved.some(function (root) { return inside(file, root); })) continue;
        var stat = fs.statSync(file);
        if (!stat.isFile() || stat.size <= 0 || stat.size > MAX_BYTES) continue;
        var bytes = fs.readFileSync(file), mime = null;
        if (bytes.length >= 8 && bytes.slice(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]))) mime = 'image/png';
        else if (bytes.length >= 3 && bytes[0] === 255 && bytes[1] === 216 && bytes[2] === 255) mime = 'image/jpeg';
        else if (bytes.length >= 12 && bytes.toString('ascii', 0, 4) === 'RIFF'
                 && bytes.toString('ascii', 8, 12) === 'WEBP') mime = 'image/webp';
        if (mime) return 'data:' + mime + ';base64,' + bytes.toString('base64');
      } catch (_) { /* Try the next installed icon size/path. */ }
    }
  }
  return null;
}

exports.toDataUri = toDataUri;
