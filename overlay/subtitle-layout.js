(function (root) {
  'use strict';
  var controls = typeof module !== 'undefined' ? require('./control-icons') : root.ControlIcons;
  var backdrop = typeof module !== 'undefined' ? require('./backdrop') : root.SubtitleBackdrop;
  var fitArea = typeof module !== 'undefined' ? require('./fit-area') : root.SubtitleFitArea;
  var glyphCover = typeof module !== 'undefined' ? require('./glyph-cover') : root.GlyphCover;
  var layerSettings = typeof module !== 'undefined' ? require('./layer-settings') : root.OsdLayerSettings;
  var manualStyle = typeof module !== 'undefined' ? require('./manual-style') : root.OsdManualStyle;
  var fittedLineHeight = 1.08;
  function color(value) {
    return Array.isArray(value) && value.length === 3 && value.every(function (c) {
      return typeof c === 'number' && isFinite(c) && c >= 0 && c <= 255;
    }) ? 'rgb(' + value.map(Math.round).join(',') + ')' : null;
  }
  function partition(text, lines, width, measure) {
    var words = text.trim().split(/\s+/), count = words.length;
    var needed = Math.min(lines, count), prefix = [0], space = measure(' ');
    words.forEach(function (word) { prefix.push(prefix[prefix.length - 1] + measure(word) + space); });
    var costs = [], breaks = [];
    for (var n = 0; n <= needed; n++) {
      costs[n] = []; breaks[n] = [];
      for (var j = 0; j <= count; j++) costs[n][j] = Infinity;
    }
    costs[0][0] = 0;
    var ideal = (prefix[count] - space) / needed;
    for (n = 1; n <= needed; n++) for (j = n; j <= count; j++) {
      for (var k = j - 1; k >= n - 1; k--) {
        var length = prefix[j] - prefix[k] - space;
        if (length > width) break;
        var score = costs[n - 1][k] + Math.pow(length - ideal, 2);
        if (score < costs[n][j]) { costs[n][j] = score; breaks[n][j] = k; }
      }
    }
    if (!isFinite(costs[needed][count])) return null;
    var result = [], end = count;
    for (n = needed; n > 0; n--) {
      var start = breaks[n][end]; result.unshift(words.slice(start, end).join(' ')); end = start;
    }
    while (result.length < lines) result.push('');
    return result;
  }
  function fit(text, appearance, viewport, measure, neighbours) {
    if (!appearance || !appearance.box || !text.trim()) return null;
    var box = appearance.box, fw = appearance.frame_width, fh = appearance.frame_height;
    if (!(fw > 0 && fh > 0 && box.width > 0 && box.height > 0 && box.x >= 0 && box.y >= 0
        && box.x + box.width <= fw && box.y + box.height <= fh)) return null;
    var lines = appearance.lines;
    if (!(Number.isInteger(lines) && lines >= 1 && lines <= 12)) return null;
    var sx = viewport.width / fw, sy = viewport.height / fh;
    var width = box.width * sx, height = box.height * sy;
    var icons = (appearance.icons || []).slice(0, 4).filter(controls.valid);
    var layoutHeight=Number.isFinite(appearance.layout_height) && appearance.layout_height>0
      ? appearance.layout_height*sy : height;
    var minimum = 18, maximum = Math.min(72, Math.floor((layoutHeight - 8) / (lines * fittedLineHeight)));
    var area = fitArea.limits(appearance, viewport, neighbours);
    var anchor = appearance.sentence_flow && appearance.flow_anchor;
    if (anchor && Number.isFinite(anchor.x) && anchor.x >= 0 && anchor.x <= box.x) {
      area.width += area.x - anchor.x*sx;
      area.x = anchor.x*sx;
    }
    if (appearance.sentence_flow) area.left = area.x;
    if (appearance.sentence_flow && appearance.preview_font_size > 0)
      maximum = Math.min(maximum, appearance.preview_font_size);
    var found = fitArea.search(area, maximum, minimum, function (available, size) {
      var result = (appearance.sentence_flow ? flow : partition)(text, lines, available - 8, function (word) {
        return controls.measure(word, size, icons, measure);
      });
      return result && result.every(function (line) {
        return controls.measure(line, size, icons, measure) <= available - 8;
      }) ? result : null;
    });
    if (found) {
        var result = found.value, size = found.size;
        width = found.width;
        var spacing = icons.length ? 0 : size * .04;
        result.forEach(function (line) {
          var characters = Array.from(line).length;
          if (characters > 1)
            spacing = Math.min(spacing, Math.max(0,
              (width - 8 - measure(line, size)) / characters));
        });
        return {text: result.join('\n'), size: size, spacing: spacing,
        x: found.x, y: anchor && Number.isFinite(anchor.y) && anchor.y >= 0 ? anchor.y*sy : box.y * sy,
        sourceWidth: box.width * sx,
        width: width, height: height, paddingTop: appearance.sentence_flow ? 4 : Math.max(4,
          (height - lines * size * fittedLineHeight) / 2), background: appearance.background_reliable
          ? color(appearance.background) : 'transparent',
        foreground: color(appearance.foreground) || 'white', outline: 'transparent', stroke: 0,
        patch: appearance.background_reliable ? null : appearance.backdrop, icons: icons};
    }
    return null;
  }
  function flow(text, lines, width, measure) {
    var result = [''], words=text.trim().split(/\s+/);
    for(var i=0;i<words.length;i++) {
      var word=words[i];
      if(measure(word)>width)return null;
      var last = result.length - 1, candidate = result[last] ? result[last] + ' ' + word : word;
      if (measure(candidate) <= width) result[last] = candidate;
      else result.push(word);
      if(result.length>lines)return null;
    }
    return result;
  }
  function render(element, text, appearance, neighbours) {
    var layers=layerSettings.get();
    var style = element.style;
    style.left = '8%'; style.right = '8%'; style.bottom = '6%'; style.top = 'auto';
    style.width = 'auto'; style.height = 'auto'; style.fontSize = '48px';
    style.background = 'transparent'; style.color = 'white'; style.padding = '0';
    style.boxSizing = 'border-box'; style.lineHeight = '1.3';
    style.textAlign = appearance && appearance.sentence_flow ? 'left' : 'center';
    style.letterSpacing = '0px';
    style.backgroundImage = 'none';
    style.backgroundOrigin = 'padding-box'; style.backgroundPosition = '0px 0px';
    style.imageRendering='auto';
    style.webkitTextStroke = '0px transparent'; style.textShadow = 'none';
    element.textContent = text;
    if (!text || !appearance) {
      delete element.translationLayout;
      style.transition = 'none';
      manualStyle.text(element,layers);
      return;
    }
    var viewport={width:window.innerWidth,height:window.innerHeight};
    var cacheKey=JSON.stringify([text,viewport.width,viewport.height,
      appearance.frame_width,appearance.frame_height]);
    var cached=element.translationLayout, result;
    if(cached && cached.key===cacheKey) result=Object.assign({},cached.result);
    else {
      var fittingAppearance=appearance;
      if(appearance.sentence_flow && cached && text.indexOf(cached.sourceText + ' ')===0)
        fittingAppearance=Object.assign({},appearance,{preview_font_size:cached.result.size});
      var canvas = document.createElement('canvas'), context = canvas.getContext('2d');
      result = fit(text, fittingAppearance, viewport,
        function (word, size) { context.font = '700 ' + size + 'px Arial'; return context.measureText(word).width; }, neighbours);
      if(result) element.translationLayout={key:cacheKey,sourceText:text,result:Object.assign({},result)};
    }
    if (!result) {
      var icons = (appearance.icons || []).slice(0, 4);
      if (icons.length && icons.every(controls.valid)) controls.render(element, text, icons, 48);
      manualStyle.text(element,layers);
      return; // Keep readable bottom subtitles when ROI cannot fit them.
    }
    // Freeze text layout, while sampling the current crop/background at its real scale.
    result.sourceWidth=appearance.box.width*viewport.width/appearance.frame_width;
    result.scaleY=viewport.height/appearance.frame_height;
    result.background=appearance.background_reliable ? color(appearance.background) : 'transparent';
    result.patch=appearance.background_reliable ? null : appearance.backdrop;
    result.foreground=color(appearance.foreground) || 'white';
    result.icons=(appearance.icons || []).slice(0,4).filter(controls.valid);
    element.textContent = result.text;
    style.left = result.x + 'px'; style.top = result.y + 'px'; style.right = 'auto'; style.bottom = 'auto';
    style.width = result.width + 'px'; style.height = result.height + 'px'; style.padding = '4px';
    style.paddingTop = result.paddingTop + 'px';
    style.fontSize = result.size + 'px'; style.lineHeight = String(fittedLineHeight);
    if(!cached) style.transition = 'none';
    else if(cached.key!==cacheKey) style.transition = 'font-size 180ms ease, letter-spacing 180ms ease';
    style.transformOrigin = 'left top';
    style.letterSpacing = result.spacing + 'px'; style.textAlign = 'left';
    style.background = result.background || 'transparent'; style.color = result.foreground;
    style.webkitTextStroke = result.stroke + 'px ' + result.outline; style.textShadow = 'none';
    var rectangle=false;
    if (layers.cover) {
      if (!glyphCover.render(element, appearance, result)) {
        if (layers.fillMode==='solid'||(!result.patch&&result.background!=='transparent')) rectangle=true;
        else backdrop.render(element, result.patch);
      }
    } else { style.background='transparent'; style.backgroundImage='none'; }
    if (result.icons.length) controls.render(element, result.text, result.icons, result.size);
    manualStyle.text(element,layers);
    if(rectangle) manualStyle.rectangle(element,layers,result.background);
  }
  var api = {partition: partition, fit: fit, render: render};
  if (typeof module !== 'undefined') module.exports = api;
  else root.SubtitleLayout = api;
}(this));
