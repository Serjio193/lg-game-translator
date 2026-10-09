from __future__ import annotations

import math
import time
import warnings
from pathlib import Path

import numpy as np
from PIL import Image

from .assets import DETECTOR_MODEL, locate


def _sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def _angle_diff_deg(a: float, b: float) -> float:
    d = abs(math.degrees(a - b)) % 180.0
    return min(d, 180.0 - d)


def _quad_from_box(cx, cy, w, h, angle):
    c, s = math.cos(angle), math.sin(angle)
    return np.asarray([
        [cx + dx*c - dy*s, cy + dx*s + dy*c]
        for dx,dy in [(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)]
    ], dtype=np.float64)


def _bbox(quad):
    return [
        float(quad[:,0].min()), float(quad[:,1].min()),
        float(quad[:,0].max()), float(quad[:,1].max())
    ]


def _oriented_dims(q):
    u=q[1]-q[0]; v=q[3]-q[0]
    return float(np.linalg.norm(u)), float(np.linalg.norm(v))


def _iou_axis(a,b):
    ax1,ay1,ax2,ay2=a["bbox"]; bx1,by1,bx2,by2=b["bbox"]
    ix=max(0,min(ax2,bx2)-max(ax1,bx1)); iy=max(0,min(ay2,by2)-max(ay1,by1))
    inter=ix*iy
    aa=max(0,ax2-ax1)*max(0,ay2-ay1); bb=max(0,bx2-bx1)*max(0,by2-by1)
    return inter/max(aa+bb-inter,1e-9)


class GoogleGroupRpnDetector:
    """Portable GroupRPN network + Google-configured grouping.

    Network decode is experimentally validated against the Google model.
    Grouping constants are copied from the production binarypb schema. The
    clustering implementation is a clean-room reconstruction and is parity-
    checked against native ScreenAI in CI.
    """

    # GocrDetectorLevel1GroupingConfig from Google's production config.
    MAX_HEIGHT_RATIO=1.75
    SEARCH_RADIUS_FACTOR=0.8
    MAX_ANGLE_DIFF_DEG=30.0
    MAX_CENTERS_RELATIVE_DISTANCE=0.25
    OPTIMAL_CENTERS_RELATIVE_DISTANCE=0.1
    MIN_OVERLAP=0.4
    MIN_OVERLAP_OPTIMAL=0.3

    # GocrDetectorMergeLevel1Config from Google's production config.
    NEIGHBOR_SEARCH_EXPANSION=4.0
    MINIMUM_BOX_DISSIMILARITY=-4.0
    NOT_ALIGNED_VERTICAL_OVERLAP=0.5
    NOT_ALIGNED_CENTERS_DISTANCE=0.5
    DUP_HORIZONTAL_OVERLAP=0.75
    DUP_VERTICAL_OVERLAP=0.75
    OVERLAP_NOT_ALIGNED_HORIZONTAL=0.1
    OVERLAP_NOT_ALIGNED_VERTICAL=0.75

    CONFIDENCE_THRESHOLD=0.5
    # Existing clean-room conditions; separate from parsed Google parameters.
    REFERENCE_DUPLICATE_IOU=0.75
    REFERENCE_GROUP_ACROSS_FACTOR=0.75

    def __init__(self, asset_root: Path, threads: int=2, max_side: int=1280):
        from .interpreter import create_interpreter
        self.model_path=locate(asset_root, DETECTOR_MODEL)
        self.interpreter=create_interpreter(self.model_path, threads)
        self.inputs=self.interpreter.get_input_details()
        self.max_side=max_side

    def _prepare(self, image: Image.Image):
        gray=image.convert("L")
        tensors=[]; scales=[]
        # Android Lens 1280 profile. This matches the validated model-head probe:
        # primary + second branch 1280, then 640 and 160.
        for d,limit in zip(self.inputs,[self.max_side,1280,640,160]):
            if limit==self.max_side:
                scale=min(1.0, limit/max(gray.size))
            else:
                scale=limit/max(gray.size)
            cw=max(1,round(gray.width*scale)); ch=max(1,round(gray.height*scale))
            w=math.ceil(cw/32)*32; h=math.ceil(ch/32)*32
            canvas=Image.new("L",(w,h),255)
            canvas.paste(gray.resize((cw,ch),Image.Resampling.BILINEAR),(0,0))
            arr=np.asarray(canvas,dtype=np.uint8)[None,:,:,None]
            self.interpreter.resize_tensor_input(d["index"],arr.shape,strict=False)
            tensors.append(arr)
            scales.append((cw/gray.width,ch/gray.height))
        self.interpreter.allocate_tensors()
        return tensors,scales

    def _decode_head(self, raw, stride, anchor, sx, sy, head):
        grid=raw[0]
        cutoff=0.0  # logit threshold corresponding to sigmoid(0)=0.5
        ys,xs=np.where(grid[:,:,0] >= cutoff)
        boxes=[]
        for y,x in zip(ys.tolist(),xs.tolist()):
            v=grid[y,x]
            cx=(x+0.5+float(v[1]))*stride/sx
            cy=(y+0.5+float(v[2]))*stride/sy
            w=anchor*math.exp(float(np.clip(v[3],-8,8)))/sx
            h=anchor*math.exp(float(np.clip(v[4],-8,8)))/sy
            angle=math.atan2(float(v[6]),float(v[5]))
            q=_quad_from_box(cx,cy,w,h,angle)
            boxes.append({
                "quad":q, "bbox":_bbox(q), "score":_sigmoid(float(v[0])),
                "angle":angle, "width":w, "height":h, "head":head,
                "center":np.asarray([cx,cy],dtype=np.float64),
            })
        return boxes

    def _run_network(self,image):
        tensors,scales=self._prepare(image)
        for d,a in zip(self.inputs,tensors):
            self.interpreter.set_tensor(d["index"],a)
        t=time.perf_counter(); self.interpreter.invoke()
        invoke_ms=(time.perf_counter()-t)*1000
        raw={d["name"]:self.interpreter.get_tensor(d["index"]) for d in self.interpreter.get_output_details()}
        heads=[
            (0,0,8,16),(1,0,32,64),(2,1,8,16),(3,1,32,64),(4,2,32,64),(5,3,32,64),
            (6,0,8,16),(7,0,32,64),(8,1,8,16),(9,1,32,64),(10,2,32,64)
        ]
        decoded={}
        for idx,src,stride,anchor in heads:
            key="Identity" if idx==0 else f"Identity_{idx}"
            decoded[idx]=self._decode_head(raw[key],stride,anchor,*scales[src],idx)
        return decoded,invoke_ms

    @staticmethod
    def _basis(box):
        q=box["quad"]
        u=q[1]-q[0]; w=float(np.linalg.norm(u))
        if w<1e-6: return np.asarray([1.0,0.0]),np.asarray([0.0,1.0])
        u=u/w; return u,np.asarray([-u[1],u[0]])

    def _pair_compatible(self,a,b):
        ha,hb=a["height"],b["height"]
        if max(ha,hb)/max(min(ha,hb),1e-6) > self.MAX_HEIGHT_RATIO:
            return False
        if _angle_diff_deg(a["angle"],b["angle"]) > self.MAX_ANGLE_DIFF_DEG:
            return False

        # Symmetric line basis to avoid order sensitivity.
        ua,_=self._basis(a); ub,_=self._basis(b)
        u=ua+ub
        if np.linalg.norm(u)<1e-6: u=ua
        u=u/max(np.linalg.norm(u),1e-6)
        n=np.asarray([-u[1],u[0]])
        delta=b["center"]-a["center"]
        along=abs(float(delta@u))
        across=abs(float(delta@n))
        typical=max(ha,hb)

        # Center alignment and vertical overlap are the quantities named by the
        # recovered production schema.
        center_rel=across/max(typical,1e-6)
        projected_overlap=max(0.0, (ha+hb)/2.0-across)/max(min(ha,hb),1e-6)
        required_overlap=(self.MIN_OVERLAP_OPTIMAL
                          if center_rel<=self.OPTIMAL_CENTERS_RELATIVE_DISTANCE
                          else self.MIN_OVERLAP)
        if center_rel > self.MAX_CENTERS_RELATIVE_DISTANCE and projected_overlap < required_overlap:
            return False

        # Breadth gap between oriented fragments. Google names the governing
        # factor search_radius_factor; keep the production 0.8 unchanged.
        gap=along-(a["width"]+b["width"])/2.0
        if gap > self.SEARCH_RADIUS_FACTOR*typical:
            return False
        return True

    def _dedupe(self,boxes):
        # Production skips level1 NMS; merge config contains explicit duplicate
        # overlap thresholds. Apply only strong duplicate suppression.
        order=sorted(boxes,key=lambda b:b["score"],reverse=True)
        keep=[]
        for b in order:
            duplicate=False
            for a in keep:
                if _angle_diff_deg(a["angle"],b["angle"])>self.MAX_ANGLE_DIFF_DEG:
                    continue
                if _iou_axis(a,b) >= self.REFERENCE_DUPLICATE_IOU:
                    duplicate=True; break
                # small box substantially contained in same-oriented box
                ax1,ay1,ax2,ay2=a["bbox"]; bx1,by1,bx2,by2=b["bbox"]
                ix=max(0,min(ax2,bx2)-max(ax1,bx1)); iy=max(0,min(ay2,by2)-max(ay1,by1))
                inter=ix*iy
                ba=max((bx2-bx1)*(by2-by1),1e-9)
                aa=max((ax2-ax1)*(ay2-ay1),1e-9)
                if inter/min(aa,ba) >= self.DUP_HORIZONTAL_OVERLAP:
                    duplicate=True; break
            if not duplicate: keep.append(b)
        return keep

    def _merge_component(self,comp):
        weights=np.asarray([max(b["score"],1e-6) for b in comp])
        dirs=[]
        for b in comp:
            u,_=self._basis(b)
            if dirs and float(u@dirs[0])<0: u=-u
            dirs.append(u)
        direction=np.average(np.asarray(dirs),axis=0,weights=weights)
        direction=direction/max(np.linalg.norm(direction),1e-6)
        normal=np.asarray([-direction[1],direction[0]])
        pts=np.concatenate([b["quad"] for b in comp],axis=0)
        us=pts@direction; vs=pts@normal
        q=np.asarray([
            direction*us.min()+normal*vs.min(),
            direction*us.max()+normal*vs.min(),
            direction*us.max()+normal*vs.max(),
            direction*us.min()+normal*vs.max(),
        ])
        w,h=_oriented_dims(q)
        return {
            "quad":q,"bbox":_bbox(q),"score":float(np.average([b["score"] for b in comp],weights=weights)),
            "angle":math.atan2(direction[1],direction[0]),"width":w,"height":h,
            "center":q.mean(axis=0),"pieces":len(comp),
        }

    def _cluster_pieces(self,pieces):
        started=time.perf_counter()
        original=pieces
        pieces=self._dedupe(pieces)
        deduped=time.perf_counter()
        n=len(pieces); parent=list(range(n))
        def find(i):
            while parent[i]!=i:
                parent[i]=parent[parent[i]]; i=parent[i]
            return i
        for i in range(n):
            for j in range(i+1,n):
                if self._pair_compatible(pieces[i],pieces[j]):
                    a,b=find(i),find(j)
                    if a!=b: parent[b]=a
        groups={}
        for i in range(n): groups.setdefault(find(i),[]).append(pieces[i])
        self.component_membership=[-1]*len(original)
        original_indices={}
        for i,b in enumerate(original):
            original_indices.setdefault(id(b),[]).append(i)
        for k,v in enumerate(groups.values()):
            for b in v:
                self.component_membership[original_indices[id(b)].pop(0)]=k
        connected=time.perf_counter()
        result=[self._merge_component(v) for v in groups.values()]
        self.cluster_timings={"piece_dedupe":(deduped-started)*1000,
            "pairwise_connections":(connected-deduped)*1000,
            "component_fit":(time.perf_counter()-connected)*1000}
        self.cluster_counts={"pieces_after_dedupe":n,"pair_tests":n*(n-1)//2,
                             "components":len(result)}
        return result

    def _refine_with_group_heads(self,lines,groups):
        # Group heads are whole-line/whole-group proposals. Use only groups that
        # contain >=2 compatible level1 lines and whose height agrees with them.
        for g in sorted(groups,key=lambda x:x["width"]*x["height"]):
            gu,gn=self._basis(g)
            members=[]
            for idx,line in enumerate(lines):
                if _angle_diff_deg(g["angle"],line["angle"]) > self.MAX_ANGLE_DIFF_DEG:
                    continue
                delta=line["center"]-g["center"]
                along=float(delta@gu); across=abs(float(delta@gn))
                if abs(along) <= g["width"]/2 + line["width"]/2 and across <= g["height"]*self.REFERENCE_GROUP_ACROSS_FACTOR:
                    # overlap along group axis
                    members.append(idx)
            if len(members)<2: continue
            hs=[lines[i]["height"] for i in members]
            typical=float(np.median(hs))
            if g["height"] > self.MAX_HEIGHT_RATIO*typical:
                continue
            merged=self._merge_component([lines[i] for i in members])
            lines=[x for i,x in enumerate(lines) if i not in set(members)] + [merged]
        return self._dedupe(lines)

    def _postprocess_python(self,pieces,groups):
        lines=self._cluster_pieces(pieces)
        refine_started=time.perf_counter()
        lines=self._refine_with_group_heads(lines,self._dedupe(groups))
        self.cluster_timings["group_refine_dedupe"]=(time.perf_counter()-refine_started)*1000
        return lines

    def detect(self,image: Image.Image):
        started=time.perf_counter()
        decoded,invoke_ms=self._run_network(image)
        pieces=[b for i in range(6) for b in decoded[i]]
        groups=[b for i in range(6,11) for b in decoded[i]]
        backend=getattr(self,"native_postprocess",None)
        if backend:
            try:
                lines=backend.run(self,pieces,groups)
            except RuntimeError as exc:
                warnings.warn(f"GOCR native failed; using Python reference: {exc}",RuntimeWarning)
                self.native_postprocess=None
                backend=None
                lines=self._postprocess_python(pieces,groups)
        else:
            lines=self._postprocess_python(pieces,groups)
        out=[]
        for i,b in enumerate(sorted(lines,key=lambda x:(x["bbox"][1],x["bbox"][0]))):
            x1,y1,x2,y2=b["bbox"]
            if x2<=0 or y2<=0 or x1>=image.width or y1>=image.height: continue
            q=b["quad"]
            out.append({
                "line_id":str(i),
                "quad":[[float(x),float(y)] for x,y in q],
                "bbox":[max(0.0,x1),max(0.0,y1),min(float(image.width),x2),min(float(image.height),y2)],
                "angle":float(b["angle"]),
                "score":float(b["score"]),
                "pieces":int(b.get("pieces",1)),
            })
        return {
            "lines":out,
            "invoke_ms":round(invoke_ms,3),
            "total_ms":round((time.perf_counter()-started)*1000,3),
            "raw_piece_count":len(pieces),
            "raw_group_count":len(groups),
            "postprocess":"google_config_cleanroom_v1",
            "backend":"native" if backend else "python",
            "stages_ms":{**getattr(self,"network_timings",{}),**self.cluster_timings},
            "counts":self.cluster_counts,
        }


def rectify_crop(image: Image.Image, quad, padding: float=0.0):
    q=np.asarray(quad,dtype=np.float64)
    u=q[1]-q[0]; v=q[3]-q[0]
    w=float(np.linalg.norm(u)); h=float(np.linalg.norm(v))
    if w<1 or h<1: raise ValueError("degenerate Google line quad")
    u=u/w; v=v/h
    if padding:
        p=h*padding
        q=q+np.asarray([-u-v,u-v,u+v,-u+v])*p
        w+=2*p; h+=2*p
    return image.transform(
        (max(1,round(w)),max(1,round(h))),
        Image.Transform.QUAD,
        tuple(q[[0,3,2,1]].ravel()),
        Image.Resampling.BICUBIC,
        fillcolor="white",
    )
