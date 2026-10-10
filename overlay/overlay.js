(function () {
  'use strict';
  var subtitle = document.getElementById('subtitle');
  var blocks = document.getElementById('translation-blocks');
  var probe = document.getElementById('surface-probe');
  var hideTimer = null;
  var idleTimer = null;
  var lastResponseId = null;
  var visibleUntil = 0;
  var pending = null;

  function renewIdleTimer() {
    if (idleTimer) window.clearTimeout(idleTimer);
    idleTimer = window.setTimeout(function () {
      if ((window.OsdShell && window.OsdShell.open()) || subtitle.textContent || (blocks && blocks.children.length)
          || (window.OsdLayerSettings && window.OsdLayerSettings.get().probe!=='off')) renewIdleTimer();
      else window.close();
    }, 30 * 60 * 1000);
  }

  function parse(input) {
    try {
      var value = typeof input === 'string' ? JSON.parse(input) : input;
      return value && typeof value === 'object' ? value : {};
    } catch (error) {
      return {};
    }
  }

  function show(input) {
    if(window.OsdShell && window.OsdShell.accept(input)){renewIdleTimer();return;}
    var params = parse(input);
    if (params.params) params = parse(params.params);
    if (window.OsdLayerSettings) {
      var layers=window.OsdLayerSettings.set(params.layers);
      if (document.body) document.body.style.background=layers.redBackground ? 'red' : 'transparent';
      if (probe && window.SurfaceProbe) {
        var testing=window.SurfaceProbe.render(probe,layers.probe,window.innerWidth,window.innerHeight);
        if (blocks) blocks.style.display=testing ? 'none' : '';
        subtitle.style.display=testing ? 'none' : '';
        if (testing) {
          if (document.body) document.body.style.background='transparent';
          renewIdleTimer();
          return;
        }
      }
    }
    if (Array.isArray(params.blocks)) {
      if (hideTimer) window.clearTimeout(hideTimer);
      pending = null; visibleUntil = 0;
      renewIdleTimer();
      if (window.SubtitleLayout) {
        window.SubtitleLayout.render(subtitle,'',null);
        if (window.MultiSubtitles) window.MultiSubtitles.render(blocks,params.blocks,window.SubtitleLayout);
      }
      return;
    }
    if (params.responseId && params.responseId === lastResponseId) return;
    if (Date.now() < visibleUntil) {
      pending = params;
      return;
    }
    lastResponseId = params.responseId || null;
    renewIdleTimer();
    var text = typeof params.text === 'string'
      ? params.text.slice(0, 1000) : 'Тест: русский текст поверх игры';
    subtitle.textContent = text;
    if (window.SubtitleLayout) window.SubtitleLayout.render(subtitle, text, params.appearance);
    if (hideTimer) window.clearTimeout(hideTimer);
    if (!text) {
      visibleUntil = 0;
      return;
    }
    var duration = Number(params.durationMs);
    if (!isFinite(duration) || duration <= 0) duration = 5000;
    duration = Math.max(5000, duration);
    duration = Math.min(duration, 300000);
    var keepVisible = params.keepVisible === true;
    visibleUntil = Date.now() + duration;
    hideTimer = window.setTimeout(function () {
      visibleUntil = 0;
      if (pending) {
        var next = pending;
        pending = null;
        show(next);
        return;
      }
      if (!keepVisible) {
        subtitle.textContent = '';
        if (window.SubtitleLayout) window.SubtitleLayout.render(subtitle, '', null);
      }
      // Keep the transparent web view warm until the inactivity timer expires.
    }, duration);
  }

  window.webOSRelaunch = function () {
    show(window.PalmSystem ? window.PalmSystem.launchParams : {});
    return true;
  };
  document.addEventListener('webOSRelaunch', function (event) {
    var detail=event.detail;
    show(detail && Object.keys(detail).length ? detail :
      (window.PalmSystem ? window.PalmSystem.launchParams : {}));
  });
  document.addEventListener('keydown', function (event) {
    if (event.keyCode === 461 || event.key === 'Escape') {
      if(window.OsdShell && window.OsdShell.open())window.OsdShell.close();
      else window.close();
    }
  });
  show(window.PalmSystem ? window.PalmSystem.launchParams : {});
}());
