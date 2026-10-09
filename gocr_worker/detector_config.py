from __future__ import annotations
import struct
from dataclasses import dataclass
from pathlib import Path

def _vi(data,pos):
    v=0; s=0
    for _ in range(10):
        if pos>=len(data): raise ValueError("truncated varint")
        b=data[pos]; pos+=1; v|=(b&127)<<s
        if b<128: return v,pos
        s+=7
    raise ValueError("bad varint")

def _fields(data):
    p=0
    while p<len(data):
        tag,p=_vi(data,p); f,w=tag>>3,tag&7
        if w==0: v,p=_vi(data,p)
        elif w==1: v=data[p:p+8]; p+=8
        elif w==2:
            n,p=_vi(data,p); v=data[p:p+n]; p+=n
        elif w==5: v=data[p:p+4]; p+=4
        else: raise ValueError("unsupported wire")
        yield f,w,v

def _vals(msg,n): return [(w,v) for f,w,v in _fields(msg) if f==n]
def _msg(msg,n):
    x=_vals(msg,n)
    return None if not x else x[-1][1]
def _flt(msg,n,d=None):
    x=_vals(msg,n)
    return d if not x else struct.unpack("<f",x[-1][1])[0]
def _int(msg,n,d=None):
    x=_vals(msg,n)
    return d if not x else int(x[-1][1])
def _pf(msg,n):
    out=[]
    for w,v in _vals(msg,n):
        if w==5: out.append(struct.unpack("<f",v)[0])
        elif w==2: out.extend(struct.unpack("<"+"f"*(len(v)//4),v))
    return tuple(out)
def _pi(msg,n):
    out=[]
    for w,v in _vals(msg,n):
        if w==0: out.append(int(v))
        elif w==2:
            p=0
            while p<len(v):
                x,p=_vi(v,p); out.append(int(x))
    return tuple(out)

@dataclass(frozen=True)
class DetectorLaunchConfig:
    confidence_threshold: float
    anchor_widths: tuple
    anchor_heights: tuple
    anchor_x_center: float
    anchor_y_center: float
    max_height_ratio: float
    search_radius_factor: float
    maximum_angle_difference: float
    max_centers_relative_distance: float
    optimal_centers_relative_distance: float
    min_overlap: float
    min_overlap_optimal: float
    duplicate_horizontal_overlap: float
    duplicate_vertical_overlap: float
    predefined_shapes: tuple
    packing_sequence: tuple
    center_box_packing_sequence: tuple
    canonical_text_line_height: float
    skip_level1_nms: bool
    version: int

    @property
    def profile_max_dim(self):
        if self.predefined_shapes:
            return max(max(x) for x in self.predefined_shapes)
        return 1280

def parse_detector_binarypb(path: Path):
    anymsg=path.read_bytes()
    cfg=_msg(anymsg,2)
    if cfg is None: raise ValueError("missing Any.value")
    model=_msg(cfg,2); opt=_msg(cfg,3)
    if model is None or opt is None: raise ValueError("missing GroupRPN settings")
    l1=_msg(opt,2) or b""
    merge=_msg(opt,4) or b""
    image=_msg(opt,6) or b""
    shapes=[]
    for w,v in _vals(image,6):
        if w==2:
            ww=_int(v,1,0); hh=_int(v,2,0)
            if ww and hh: shapes.append((ww,hh))
    return DetectorLaunchConfig(
        confidence_threshold=float(_flt(model,1,0.5)),
        anchor_widths=_pf(model,4),
        anchor_heights=_pf(model,5),
        anchor_x_center=float(_flt(model,8,0.5)),
        anchor_y_center=float(_flt(model,9,0.5)),
        max_height_ratio=float(_flt(l1,1,1.75)),
        search_radius_factor=float(_flt(l1,2,0.8)),
        maximum_angle_difference=float(_flt(l1,3,30.0)),
        max_centers_relative_distance=float(_flt(l1,4,0.25)),
        optimal_centers_relative_distance=float(_flt(l1,5,0.1)),
        min_overlap=float(_flt(l1,6,0.4)),
        min_overlap_optimal=float(_flt(l1,7,0.3)),
        duplicate_horizontal_overlap=float(_flt(merge,5,0.75)),
        duplicate_vertical_overlap=float(_flt(merge,6,0.75)),
        predefined_shapes=tuple(shapes),
        packing_sequence=_pi(opt,13),
        center_box_packing_sequence=_pi(opt,16),
        canonical_text_line_height=float(_flt(opt,9,64.0)),
        skip_level1_nms=bool(_int(opt,14,0)),
        version=int(_int(opt,17,0)),
    )
