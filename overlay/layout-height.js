'use strict';
// Only font sizing is filtered. Live crop geometry still anchors the cover mask.
exports.update=function (state, appearance, observation) {
  if (!appearance || !appearance.box) return appearance;
  var height=appearance.box.height;
  if (!(height>0 && Number.isFinite(height))) return appearance;
  if (state.lines!==appearance.lines || state.frameHeight!==appearance.frame_height) {
    state.samples=[];state.height=height;
    state.lines=appearance.lines;state.frameHeight=appearance.frame_height;
  }
  state.samples=state.samples || [];
  if(observation===undefined || state.observation!==observation) state.samples.push(height);
  state.observation=observation;
  if(state.samples.length>5) state.samples.shift();
  var ordered=state.samples.slice().sort(function(a,b){return a-b;});
  var median=ordered[Math.floor((ordered.length-1)/2)];
  if(!state.height || (state.samples.length>=3
      && Math.abs(median-state.height)>Math.max(2,state.height*.1))) state.height=median;
  var result=Object.assign({},appearance);
  result.layout_height=state.height;
  return result;
};
