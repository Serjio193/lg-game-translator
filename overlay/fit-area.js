(function (root) {
  'use strict';
  // Only the drawing area grows; detector geometry is never modified.
  function limits(appearance, viewport, neighbours) {
    var box = appearance.box, sx = viewport.width / appearance.frame_width;
    var sy = viewport.height / appearance.frame_height, gap = 8 * sx;
    var left = Math.max(0, box.x * sx - box.width * sx * .175);
    var right = Math.min(viewport.width, (box.x + box.width * 1.175) * sx);
    var panel = appearance.panel_box;
    if (panel && panel.x <= box.x && panel.x + panel.width >= box.x + box.width
        && panel.y <= box.y && panel.y + panel.height >= box.y + box.height) {
      left = Math.max(left, panel.x * sx);
      right = Math.min(right, (panel.x + panel.width) * sx);
    }
    (neighbours || []).forEach(function (other) {
      if (!other || other === box || !(other.width > 0 && other.height > 0)) return;
      if (other.y + other.height <= box.y - 4 || other.y >= box.y + box.height + 4) return;
      // Reserve half the free gap for each expanding neighbour.
      if (other.x + other.width <= box.x)
        left = Math.max(left, ((other.x + other.width + box.x) / 2) * sx + gap / 2);
      else if (other.x >= box.x + box.width)
        right = Math.min(right, ((other.x + box.x + box.width) / 2) * sx - gap / 2);
      else { left = Math.max(left, box.x * sx); right = Math.min(right, (box.x + box.width) * sx); }
    });
    return {left: Math.min(left, box.x * sx), right: Math.max(right, (box.x + box.width) * sx),
      x: box.x * sx, width: box.width * sx, height: box.height * sy, step: 8 * sx};
  }
  function search(area, maximum, minimum, attempt) {
    var x = area.x, width = area.width, size = maximum, expand = true;
    while (size >= minimum) {
      var result = attempt(width, size);
      if (result) return {value: result, x: x, width: width, size: size};
      var free = area.right - area.left - width;
      if (expand && free > .01) {
        var growth = Math.min(area.step, free);
        var addLeft = Math.min(growth / 2, x - area.left);
        var addRight = Math.min(growth - addLeft, area.right - x - width);
        addLeft = Math.min(growth - addRight, x - area.left);
        x -= addLeft; width += addLeft + addRight;
        expand = false;
      } else { size--; expand = true; }
    }
    return null;
  }
  var api = {limits: limits, search: search};
  if (typeof module !== 'undefined') module.exports = api;
  else root.SubtitleFitArea = api;
}(this));
