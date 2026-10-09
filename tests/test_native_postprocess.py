"""Run with GOCR_POSTPROCESS_LIBRARY pointing at the built library."""
import ctypes as C
import os
import json
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from gocr_worker.detector import GoogleGroupRpnDetector, _bbox, _quad_from_box
from gocr_worker.native_postprocess import NativePostprocess, Config, Line, Proposal, Stats, select_backend


def box(cx,cy,w,h,angle,score,head):
    q=_quad_from_box(cx,cy,w,h,angle)
    return {"quad":q,"bbox":_bbox(q),"center":np.asarray([cx,cy]),
            "width":w,"height":h,"angle":angle,"score":score,"head":head}


class NativeTests(unittest.TestCase):
    def setUp(self):
        self.reference=GoogleGroupRpnDetector.__new__(GoogleGroupRpnDetector)
        self.native=NativePostprocess(os.environ["GOCR_POSTPROCESS_LIBRARY"])

    def compare(self,pieces,groups):
        ref=self.reference
        a=ref._postprocess_python(pieces,groups)
        counts=dict(ref.cluster_counts)
        membership=list(ref.component_membership)
        b=self.native.run(ref,pieces,groups)
        self.assertEqual(counts,ref.cluster_counts)
        self.assertEqual(membership,ref.component_membership)
        self.assertEqual(len(a),len(b))
        for x,y in zip(a,b):
            self.assertEqual(x["pieces"],y["pieces"])
            for name in ("quad","center","width","height","angle","score"):
                np.testing.assert_allclose(x[name],y[name],rtol=0,atol=1e-9)

    def test_empty_single_duplicates_and_equal_scores(self):
        self.compare([],[])
        a=box(20,20,15,10,0,.9,0)
        self.compare([a],[])
        self.compare([a,a,box(40,20,15,10,0,.9,1)],[])

    def test_seeded_rotated_dense_and_group_refinement(self):
        rng=np.random.default_rng(20261009)
        for _ in range(12):
            pieces=[box(float(x),float(y),float(w),float(h),float(a),float(s),0)
                    for x,y,w,h,a,s in zip(rng.uniform(0,500,60),rng.uniform(0,100,60),
                        rng.uniform(10,60,60),rng.uniform(8,20,60),
                        rng.uniform(-.5,.5,60),rng.uniform(.5,1,60))]
            self.compare(pieces,[box(250,50,500,20,0,.95,6)])
        self.compare([box(x,30,20,10,0,.9,0) for x in (10,40,70)],
                     [box(40,30,100,10,0,.95,6)])

    def test_abi_capacity_and_invalid_head(self):
        cfg=Config(1.75,.8,30,.25,.1,.4,.3,.75,.75,.75)
        p=(Proposal*1)()
        q=box(20,20,10,10,0,.9,0)
        p[0].quad[:]=q["quad"].ravel()
        p[0].center[:]=q["center"]
        p[0].width=p[0].height=10
        p[0].score=.9
        stats=Stats()
        member=(C.c_int32*1)()
        call=self.native.lib.gocr_postprocess
        self.assertEqual(call(p,1,C.byref(cfg),None,0,member,C.byref(stats)),-2)
        p[0].head=11
        self.assertEqual(call(p,1,C.byref(cfg),(Line*1)(),1,member,C.byref(stats)),-1)

    def test_explicit_python_backend(self):
        old=os.environ.get("GOCR_POSTPROCESS")
        try:
            os.environ["GOCR_POSTPROCESS"]="python"
            self.assertIsNone(select_backend())
            os.environ["GOCR_POSTPROCESS"]="invalid"
            with self.assertRaises(ValueError):
                select_backend()
        finally:
            if old is None:
                os.environ.pop("GOCR_POSTPROCESS",None)
            else:
                os.environ["GOCR_POSTPROCESS"]=old

    def test_saved_real_proposals(self):
        directory=Path(__file__).resolve().parents[1]/"docs/evidence/gocr-native-postprocess-20261009"
        files=list(directory.glob("*-proposals.json"))
        self.assertEqual(len(files),2,"both real proposal fixtures must be present")
        for path in files:
            raw=json.loads(path.read_text())
            for b in raw:
                b["quad"]=np.asarray(b["quad"],dtype=np.float64)
                b["center"]=np.asarray(b["center"],dtype=np.float64)
            self.compare([b for b in raw if b["head"]<6],[b for b in raw if b["head"]>=6])

    def test_runtime_failure_falls_back_to_reference(self):
        class Broken:
            def run(self,*args):
                raise RuntimeError("test ABI failure")
        ref=self.reference
        ref.native_postprocess=Broken()
        ref._run_network=lambda image: ({i:[] for i in range(11)},0)
        with self.assertWarns(RuntimeWarning):
            result=ref.detect(Image.new("RGB",(1280,720)))
        self.assertEqual(result["backend"],"python")
        self.assertEqual(result["lines"],[])
        self.assertIsNone(ref.native_postprocess)


if __name__=="__main__":
    unittest.main()
