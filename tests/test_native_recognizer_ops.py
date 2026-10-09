"""Standalone native probe regression tests; GOCR_NATIVE_PROBE points to build."""
import hashlib
import math
import os
import random
import subprocess
import tempfile
import unicodedata
import unittest
from pathlib import Path

from PIL import Image
import numpy as np
from gocr_worker.detector import rectify_crop


class NativeOpsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.probe=os.environ["GOCR_NATIVE_PROBE"]

    def batch(self,mode,values):
        data="\n".join(v.hex() for v in values)+"\n"
        result=subprocess.run([self.probe,mode],input=data,text=True,capture_output=True,check=True)
        return result.stdout.splitlines()

    def test_sha256_known_and_multiblock(self):
        values=[b"",b"abc",b"a"*55,b"a"*56,b"a"*64,b"a"*1000000,bytes(range(256))]
        self.assertEqual(self.batch("sha",values),[hashlib.sha256(v).hexdigest() for v in values])

    def test_nfc_all_canonical_decompositions_and_combining_sequences(self):
        values=["  Привет е\u0308 и\u0306  ","a\u0315\u0300", "\u1100\u1161\u11a8",
                "\u1ea5", "\u00a0hello\u2003", "\U0001f600"]
        for cp in range(0x110000):
            raw=unicodedata.decomposition(chr(cp))
            if raw and not raw.startswith("<"):
                values.append("".join(chr(int(n,16)) for n in raw.split()))
        rng=random.Random(41)
        marks=[chr(cp) for cp in range(0x300,0x370) if unicodedata.combining(chr(cp))]
        values += [rng.choice("aeёЙ\u1100")+"".join(rng.choices(marks,k=6)) for _ in range(1000)]
        actual=self.batch("nfc",[v.encode() for v in values])
        expected=[unicodedata.normalize("NFC",v).strip().encode().hex() for v in values]
        self.assertEqual(actual,expected)

    def test_resize_windows_rgb_gray_and_last_zero_padding(self):
        rng=np.random.default_rng(23)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for mode in ("L","RGB"):
                for w,h in ((1,1),(8,17),(34,64),(135,32),(136,32),(137,32),
                            (168,32),(272,32),(655,43),(182,92),(379,18),(32,32)):
                    shape=(h,w,3) if mode=="RGB" else (h,w)
                    image=Image.fromarray(rng.integers(0,256,shape,dtype=np.uint8),mode)
                    image.save(root/"input.ppm")
                    subprocess.run([self.probe,"windows",str(root/"input.ppm"),str(root/"output.bin")],check=True)
                    width=max(1,round(w*32/h))
                    gray=image.convert("L").resize((width,32),Image.Resampling.LANCZOS)
                    padded=Image.new("L",(width+32,32),255); padded.paste(gray,(16,0))
                    expected=b"".join(padded.crop((x,0,x+168,32)).tobytes() for x in range(0,width,136))
                    with self.subTest(mode=mode,w=w,h=h):
                        self.assertEqual((root/"output.bin").read_bytes(),expected)

    def test_rectification_rotated_borders_and_ties_even(self):
        rng=np.random.default_rng(49)
        image=Image.fromarray(rng.integers(0,256,(80,120,3),dtype=np.uint8),"RGB")
        quads=[[[0,0],[120,0],[120,80],[0,80]],
               [[-5,-3],[31.5,-3],[31.5,15.5],[-5,15.5]],
               [[10,20],[42.5,20],[42.5,36.5],[10,36.5]],
               [[13.7,21.8],[80.6,25.2],[84.1,58.3],[11.9,49.8]]]
        for angle in (-0.8,-0.2,0.15,0.6,1.2):
            u=[70*math.cos(angle),70*math.sin(angle)]
            v=[-16*math.sin(angle),16*math.cos(angle)]
            origin=[22,18]
            quads.append([origin,[origin[i]+u[i] for i in (0,1)],
                          [origin[i]+u[i]+v[i] for i in (0,1)],
                          [origin[i]+v[i] for i in (0,1)]])
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); image.save(root/"input.ppm")
            for q in quads:
                subprocess.run([self.probe,"rectify",str(root/"input.ppm"),str(root/"crop.ppm")]+
                               [str(v) for p in q for v in p],check=True)
                candidate=Image.open(root/"crop.ppm")
                expected=rectify_crop(image,q)
                self.assertEqual(candidate.size,expected.size)
                self.assertEqual(candidate.tobytes(),expected.tobytes())


if __name__=="__main__":
    unittest.main()
