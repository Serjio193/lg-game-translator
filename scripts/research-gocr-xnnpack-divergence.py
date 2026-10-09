"""Isolated runtime research; never modifies production environment/settings."""
import argparse
import ctypes as C
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gocr_worker.native_detector import NativeDetector, config_from_assets
from gocr_worker.native_postprocess import NativePostprocess, Proposal, Line, Stats
from gocr_worker.detector import rectify_crop
from gocr_worker.image_contract import fingerprint


def postprocess(detector,cfg,post):
    n=detector.lib.gocr_detector_copy_proposals(detector.context,None,0)
    proposals=(Proposal*n)()
    detector.lib.gocr_detector_copy_proposals(detector.context,proposals,n)
    membership=(C.c_int32*n)()
    output=(Line*n)()
    stats=Stats()
    count=post.lib.gocr_postprocess(proposals,n,C.byref(cfg.postprocess),output,n,membership,C.byref(stats))
    if count<0:
        raise RuntimeError("research postprocess failed")
    geometry=[{"quad":list(r.quad),"angle":r.angle,"score":r.score,"head":r.head} for r in proposals]
    return {"raw_proposal_count":n,"decoded_proposals_sha256":hashlib.sha256(
                json.dumps(geometry,sort_keys=True).encode()).hexdigest(),
            "deduped_count":stats.deduped_count,
            "components":stats.component_count,"pair_tests":stats.pair_tests,
            "component_membership_sha256":hashlib.sha256(bytes(membership)).hexdigest()}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--assets",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("frames",type=Path,nargs="+")
    a=p.parse_args()
    baseline=NativeDetector(a.assets,2,xnnpack=0)
    candidate=NativeDetector(a.assets,2,xnnpack=1)
    cfg=config_from_assets(a.assets)
    post=NativePostprocess()
    report={"scope":"system runtime no-XNNPACK vs explicit XNNPACK; research only","frames":[]}
    for path in a.frames:
        image=Image.open(path).convert("RGB")
        baseline.detect(image); candidate.detect(image)
        before=baseline.detect(image); after=candidate.detect(image)
        inputs_equal=all(baseline.tensor_bytes("input",i)==candidate.tensor_bytes("input",i) for i in range(4))
        outputs=[]
        for head in range(11):
            left=np.frombuffer(baseline.tensor_bytes("output",head),dtype=np.float32)
            right=np.frombuffer(candidate.tensor_bytes("output",head),dtype=np.float32)
            delta=np.abs(left-right)
            changed=np.flatnonzero(left!=right)
            outputs.append({"head":head,"elements":len(left),"changed_elements":len(changed),
                "first_changed_flat_index":int(changed[0]) if len(changed) else None,
                "max_abs_error":float(delta.max()),"mean_abs_error":float(delta.mean()),
                "reference_sha256":hashlib.sha256(left.tobytes()).hexdigest(),
                "xnnpack_sha256":hashlib.sha256(right.tobytes()).hexdigest()})
        stages={"baseline":postprocess(baseline,cfg,post),"xnnpack":postprocess(candidate,cfg,post)}
        crops=[]
        for name,result in (("baseline",before),("xnnpack",after)):
            crops.append({"backend":name,"lines":[{"quad":r["quad"],
                "crop_sha256":fingerprint(rectify_crop(image,r["quad"]))} for r in result["lines"]]})
        report["frames"].append({"frame":str(path),"inputs_equal":inputs_equal,
            "first_divergent_boundary":"detector output tensors" if inputs_equal and any(
                o["changed_elements"] for o in outputs) else "unresolved",
            "outputs":outputs,"postprocess":stages,"crops":crops})
        a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
        print(json.dumps({"frame":str(path),"inputs_equal":inputs_equal,
            "divergent_heads":[o["head"] for o in outputs if o["changed_elements"]],
            "postprocess":stages}),flush=True)
    baseline.close(); candidate.close()


if __name__=="__main__":
    main()
