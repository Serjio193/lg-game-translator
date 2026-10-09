"""Same-device crop/window/text parity and full native hot-path comparison."""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gocr_worker.detector import rectify_crop
from gocr_worker.image_contract import fingerprint
from gocr_worker.native_detector import NativeDetector
from gocr_worker.native_recognizer import NativeFull, NativeRecognizer
from gocr_worker.recognizer import GocrLineRecognizer


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--assets",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--threads",type=int,default=2)
    p.add_argument("frames",type=Path,nargs="+")
    a=p.parse_args()
    os.environ["GOCR_RECOGNIZER_DEBUG_WINDOWS"]="1"
    reference=GocrLineRecognizer(a.assets,a.threads)
    native=NativeRecognizer(a.assets,a.threads)
    detector=NativeDetector(a.assets,a.threads)
    full=NativeFull(detector,native)
    report={"scope":"current Python clean-room reference, not Google Lens", "frames":[]}
    for path in a.frames:
        image=Image.open(path).convert("RGB")
        detections=detector.detect(image)
        rows=[]
        for item in detections["lines"]:
            crop=rectify_crop(image,item["quad"])
            candidate=native.rectify(image,item["quad"])
            before=reference.recognize(crop)
            after=native.recognize(crop)
            raw_windows=native.windows_bytes()
            delta=np.asarray(crop,dtype=np.int16)-np.asarray(candidate,dtype=np.int16)
            rows.append({"line_id":item["line_id"],"reference":before,"native":after,
                "crop_size":list(crop.size),"crop_sha256":fingerprint(crop),
                "native_crop_sha256":fingerprint(candidate),
                "crop_changed_bytes":int(np.count_nonzero(delta)),
                "crop_max_error":int(np.max(np.abs(delta))),
                "windows_export_hash_valid":hashlib.sha256(raw_windows).hexdigest()==after["input_windows_sha256"],
                "windows_equal":before["input_windows_sha256"]==after["input_windows_sha256"],
                "text_equal":before["text"]==after["text"],
                "margin_equal":before["diagnostic_logit_margin_q"]==after["diagnostic_logit_margin_q"]})
        result,stats=full.run(image)
        combined=[]
        for original,candidate in zip(rows,result):
            combined.append({"line_id":candidate["line_id"],
                "crop_equal":original["crop_sha256"]==candidate["crop_sha256"],
                "windows_equal":original["reference"]["input_windows_sha256"]==candidate["recognizer"]["input_windows_sha256"],
                "text_equal":original["reference"]["text"]==candidate["text"]})
        passed=len(rows)==len(result) and all(
            r["crop_changed_bytes"]==0 and r["windows_equal"] and r["text_equal"] and
            r["margin_equal"] and r["windows_export_hash_valid"] for r in rows) and all(
            r["crop_equal"] and r["windows_equal"] and r["text_equal"] for r in combined)
        report["frames"].append({"frame":str(path),"lines":rows,"full":combined,"parity":passed,
            "full_ms":stats.total_ms,"recognizer_ms":stats.recognizer_ms,"rectify_ms":stats.rectify_ms})
        a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
        print(json.dumps({"frame":str(path),"lines":len(rows),"parity":passed,
            "bad_crops":sum(r["crop_changed_bytes"]>0 for r in rows),
            "bad_windows":sum(not r["windows_equal"] for r in rows),
            "bad_texts":sum(not r["text_equal"] for r in rows)},ensure_ascii=False),flush=True)
    full.close(); detector.close(); native.close()
    return 0 if all(f["parity"] for f in report["frames"]) else 1


if __name__=="__main__":
    raise SystemExit(main())
