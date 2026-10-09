"""Read/replay native debug state outside the timed OCR path."""
import ctypes as C
import hashlib
import numpy as np
from .native_detector import config_from_assets
from .native_postprocess import NativePostprocess, Proposal, Line, Stats


def tensor_hashes(detector):
    return {kind:[hashlib.sha256(detector.tensor_bytes(kind,i)).hexdigest()
                  for i in range(count)] for kind,count in (("input",4),("output",11))}


def snapshot(detector,assets,post):
    n=detector.lib.gocr_detector_copy_proposals(detector.context,None,0)
    raw=(Proposal*n)()
    if detector.lib.gocr_detector_copy_proposals(detector.context,raw,n)!=n:
        raise RuntimeError("proposal export failed")
    membership=(C.c_int32*n)()
    output=(Line*n)()
    stats=Stats()
    cfg=config_from_assets(assets)
    count=post.lib.gocr_postprocess(raw,n,C.byref(cfg.postprocess),output,n,membership,C.byref(stats))
    if count<0:
        raise RuntimeError("diagnostic postprocess replay failed")
    proposals=[{"quad":list(p.quad),"center":list(p.center),"width":p.width,"height":p.height,
                "angle":p.angle,"score":p.score,"head":p.head} for p in raw]
    kept=[i for i,component in enumerate(membership) if component>=0]
    # Native membership marks removed proposals/group heads -1. It refers to
    # pre-group-refinement components, not to final sorted API line IDs.
    if len(kept)!=stats.deduped_count:
        raise RuntimeError("deduped membership count mismatch")
    return {"tensors":tensor_hashes(detector),"decoded_proposals":proposals,
            "deduped_piece_indices":kept,"deduped_pieces":[proposals[i] for i in kept],
            "components":[[i for i,c in enumerate(membership) if c==component]
                          for component in range(stats.component_count)],
            "component_membership":list(membership),"raw_count":n,
            "deduped_count":stats.deduped_count,"component_count":stats.component_count,
            "pair_tests":stats.pair_tests,"final_native_line_count":count}


def tensor_differences(left,right):
    rows=[]
    for i in range(11):
        a=np.frombuffer(left.tensor_bytes("output",i),dtype="<f4")
        b=np.frombuffer(right.tensor_bytes("output",i),dtype="<f4")
        if a.shape!=b.shape:
            raise RuntimeError("output tensor shapes changed")
        delta=np.abs(a.astype(np.float64)-b.astype(np.float64))
        if not np.isfinite(delta).all():
            raise RuntimeError("non-finite detector tensor comparison")
        rows.append({"head":"Identity" if i==0 else f"Identity_{i}","elements":int(a.size),
                     "changed_count":int(np.count_nonzero(a!=b)),
                     "max_abs_diff":float(delta.max()),"mean_abs_diff":float(delta.mean())})
    return rows
