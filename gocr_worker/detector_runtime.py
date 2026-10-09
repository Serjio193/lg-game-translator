from __future__ import annotations

import math
import numpy as np

from .assets import DETECTOR_CONFIG, locate
from .detector import GoogleGroupRpnDetector, _quad_from_box, _bbox, _sigmoid
from .detector_config import parse_detector_binarypb


class GoogleConfiguredGroupRpnDetector(GoogleGroupRpnDetector):
    """GroupRPN detector whose launch constants are loaded from Google's binarypb."""

    def __init__(self, asset_root, threads=2):
        cfg_path=locate(asset_root,DETECTOR_CONFIG)
        self.launch=parse_detector_binarypb(cfg_path)
        super().__init__(asset_root,threads=threads,max_side=self.launch.profile_max_dim)

        self.MAX_HEIGHT_RATIO=self.launch.max_height_ratio
        self.SEARCH_RADIUS_FACTOR=self.launch.search_radius_factor
        self.MAX_ANGLE_DIFF_DEG=self.launch.maximum_angle_difference
        self.MAX_CENTERS_RELATIVE_DISTANCE=self.launch.max_centers_relative_distance
        self.OPTIMAL_CENTERS_RELATIVE_DISTANCE=self.launch.optimal_centers_relative_distance
        self.MIN_OVERLAP=self.launch.min_overlap
        self.MIN_OVERLAP_OPTIMAL=self.launch.min_overlap_optimal
        self.DUP_HORIZONTAL_OVERLAP=self.launch.duplicate_horizontal_overlap
        self.DUP_VERTICAL_OVERLAP=self.launch.duplicate_vertical_overlap
        from .native_postprocess import select_backend
        self.native_postprocess=select_backend()

    def _decode_head(self,raw,stride,anchor,sx,sy,head):
        grid=raw[0]
        t=min(max(self.launch.confidence_threshold,1e-6),1-1e-6)
        cutoff=math.log(t/(1.0-t))
        ys,xs=np.where(grid[:,:,0]>=cutoff)
        boxes=[]
        for y,x in zip(ys.tolist(),xs.tolist()):
            v=grid[y,x]
            cx=(x+self.launch.anchor_x_center+float(v[1]))*stride/sx
            cy=(y+self.launch.anchor_y_center+float(v[2]))*stride/sy
            w=anchor*math.exp(float(np.clip(v[3],-8,8)))/sx
            h=anchor*math.exp(float(np.clip(v[4],-8,8)))/sy
            angle=math.atan2(float(v[6]),float(v[5]))
            q=_quad_from_box(cx,cy,w,h,angle)
            boxes.append({
                "quad":q,"bbox":_bbox(q),"score":_sigmoid(float(v[0])),
                "angle":angle,"width":w,"height":h,"head":head,
                "center":np.asarray([cx,cy],dtype=np.float64),
            })
        return boxes

    def _run_network(self,image):
        import time
        started=time.perf_counter()
        tensors,scales=self._prepare(image)
        prepared=time.perf_counter()
        for d,a in zip(self.inputs,tensors):
            self.interpreter.set_tensor(d["index"],a)
        t=time.perf_counter(); self.interpreter.invoke()
        invoke_ms=(time.perf_counter()-t)*1000
        raw={d["name"]:self.interpreter.get_tensor(d["index"]) for d in self.interpreter.get_output_details()}
        copied=time.perf_counter()

        anchors=list(self.launch.anchor_widths)
        if len(anchors)<6:
            raise RuntimeError("Google binarypb has incomplete GroupRPN anchor list")
        heads=[
            (0,0,8,anchors[0]),(1,0,32,anchors[1]),
            (2,1,8,anchors[2]),(3,1,32,anchors[3]),
            (4,2,32,anchors[4]),(5,3,32,anchors[5]),
            (6,0,8,anchors[0]),(7,0,32,anchors[1]),
            (8,1,8,anchors[2]),(9,1,32,anchors[3]),
            (10,2,32,anchors[4]),
        ]
        decoded={}
        for idx,src,stride,anchor in heads:
            key="Identity" if idx==0 else f"Identity_{idx}"
            decoded[idx]=self._decode_head(raw[key],stride,anchor,*scales[src],idx)
        finished=time.perf_counter()
        self.network_timings={"pyramid_prepare_allocate":(prepared-started)*1000,
            "tensor_input_copy":(t-prepared)*1000,"tflite_invoke":invoke_ms,
            "tensor_output_copy":(copied-t)*1000-invoke_ms,
            "decode_heads":(finished-copied)*1000}
        return decoded,invoke_ms
