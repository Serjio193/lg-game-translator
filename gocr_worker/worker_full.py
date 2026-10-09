from __future__ import annotations

import argparse
import base64
import io
import json
import logging
import os
import time
import threading
import warnings
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PIL import Image

from .assets import verify_bundle
from .detector import rectify_crop
from .detector_backend import create_detector
from .protocol import Line, OcrResult, Point, Quad
from .recognizer import GocrLineRecognizer
from .image_contract import fingerprint
from .execution_profile import execution_profile, google_runner_contract

LOG=logging.getLogger("gocr-worker-full")


def _quad(value):
    p=[Point(float(x),float(y)) for x,y in value]
    return Quad(*p)


class FullGocrWorker:
    def __init__(self,assets:Path,threads:int=2,*,detector_threads=None,recognizer_threads=None):
        self.assets=assets
        self.profile=execution_profile()
        self.asset_status=verify_bundle(assets)
        self.detector_threads=threads if detector_threads is None else detector_threads
        self.recognizer_threads=threads if recognizer_threads is None else recognizer_threads
        self.runner_contract=None
        if self.profile=="google_runner_experimental":
            self.runner_contract=google_runner_contract(assets)
            required=self.runner_contract["interpreter_num_threads"]
            if detector_threads not in (None,required) or recognizer_threads not in (None,2):
                raise ValueError("google_runner_experimental requires detector 4 / recognizer 2")
            self.detector_threads,self.recognizer_threads=required,2
        if not all(isinstance(n,int) and 1<=n<=4 for n in (self.detector_threads,self.recognizer_threads)):
            raise ValueError("detector/recognizer threads must be 1..4")
        mode=os.environ.get("GOCR_RECOGNIZER","native")
        if mode not in ("native","python"):
            raise ValueError("GOCR_RECOGNIZER must be native or python")
        if self.profile!="strict" and mode!="native":
            raise ValueError("experimental profile requires the native full hot path")
        self.detector=create_detector(assets,threads=self.detector_threads)
        self.native_full=None
        self.lock=threading.Lock()
        if mode=="native" and hasattr(self.detector,"native"):
            try:
                from .native_recognizer import NativeFull, NativeRecognizer
                self.recognizer=NativeRecognizer(assets,self.recognizer_threads)
                self.native_full=NativeFull(self.detector.native,self.recognizer)
            except (OSError,RuntimeError) as exc:
                close=getattr(getattr(self,"recognizer",None),"close",None)
                if close:
                    close()
                if self.profile!="strict":
                    self.detector.close()
                    raise RuntimeError("experimental profile requires the native full hot path") from exc
                warnings.warn(f"native recognizer unavailable; using Python reference: {exc}",RuntimeWarning)
        if self.native_full is None:
            self.recognizer=GocrLineRecognizer(assets,threads=self.recognizer_threads)
        self.reference_recognizer=None

    def ocr(self,image:Image.Image)->dict:
        # Persistent interpreter buffers and returned native string pointers are
        # owned by this worker; serialize concurrent HTTP requests per worker.
        with self.lock:
            return self._ocr(image)

    def _ocr(self,image:Image.Image)->dict:
        if self.profile!="strict" and (image.mode!="RGB" or image.size!=(1280,720)):
            raise ValueError("experimental profile requires selected RGB1280x720")
        start=time.perf_counter()
        native=self.native_full is not None and image.mode=="RGB" and image.size==(1280,720)
        if native:
            rows,stats=self.native_full.run(image)
            d,g=stats.detector,stats.detector.grouping
            det={"lines":rows,"invoke_ms":d.invoke_ms,"total_ms":d.total_ms,
                "postprocess":"google_config_cleanroom_v1","backend":"native","detector_execution":"native",
                "stages_ms":{"pyramid_prepare_allocate":d.prepare_ms,"decode_heads":d.decode_ms,
                             "native_total_postprocess":d.postprocess_ms},
                "counts":{"pieces_after_dedupe":g.deduped_count,"pair_tests":g.pair_tests,
                          "components":g.component_count},
                "raw_piece_count":d.raw_pieces,"raw_group_count":d.raw_groups}
        else:
            det=self.detector.detect(image)
        lines=[]
        rec_total=0.0
        crop_total=0.0
        for item in det["lines"]:
            if native:
                rec=item["recognizer"]
                crop_hash=item["crop_sha256"]
            else:
                crop_started=time.perf_counter()
                crop=rectify_crop(image,item["quad"])
                crop_total+=(time.perf_counter()-crop_started)*1000
                recognizer=self.recognizer
                if self.native_full is not None:
                    if self.reference_recognizer is None:
                        self.reference_recognizer=GocrLineRecognizer(self.assets,self.recognizer_threads)
                    recognizer=self.reference_recognizer
                rec=recognizer.recognize(crop)
                crop_hash=fingerprint(crop)
            rec_total+=rec["total_ms"]
            lines.append(Line(
                line_id=item["line_id"],
                text=rec["text"],
                source_quad=_quad(item["quad"]),
                angle=float(item["angle"]),
                detector_confidence=float(item["score"]),
                recognizer_confidence=None,
                timings_ms={"recognizer":rec["total_ms"],"tflite_invoke":rec["invoke_ms"],
                            **({"recognizer_prepare":rec["stages_ms"]["prepare"],
                                "recognizer_decode":rec["stages_ms"]["decode"]} if native else {})},
                crop_sha256=crop_hash,
                recognizer_input_sha256=rec.get("input_windows_sha256"),
            ))
        total=(time.perf_counter()-start)*1000.0
        if native:
            crop_total=stats.rectify_ms
        return OcrResult(
            schema="gocr.worker.v1",
            width=image.width,
            height=image.height,
            mode="full",
            lines=lines,
            timings_ms={
                "detector":det["total_ms"],
                "detector_tflite_invoke":det["invoke_ms"],
                "recognizer":round(rec_total,3),
                "crop_rectify":round(crop_total,3),
                "total":round(total,3),
            },
            parity={
                "detector_model":"google_original",
                "detector_config_values":"google_original",
                "detector_postprocess":det["postprocess"],
                "detector_native_parity":"validation_in_progress",
                "recognizer_model":"google_original",
                "recognizer_decoder":"greedy_ctc",
                "production_lm_fst_applied":False,
                "window_contract":"google_config_16_136_16",
            },
            telemetry={"gocr_profile":self.profile,"detector_xnnpack":self.profile!="strict",
                       "detector_threads":self.detector_threads,"recognizer_threads":self.recognizer_threads,
                       "google_runner_contract":self.runner_contract,
                       "detector_backend":det.get("backend","python"),
                       "ocr_execution":"native" if native else "python_orchestration",
                       "detector_execution":det.get("detector_execution","python"),
                       "detector_stages_ms":det.get("stages_ms",{}),
                       "detector_counts":det.get("counts",{}),
                       "raw_piece_count":det.get("raw_piece_count"),
                       "raw_group_count":det.get("raw_group_count")},
        ).to_dict()

    def close(self):
        if self.native_full is not None:
            self.native_full.close()
        close=getattr(self.detector,"close",None)
        if close:
            close()
        for recognizer in (self.recognizer,self.reference_recognizer):
            if recognizer is not None:
                target=getattr(recognizer,"interpreter",recognizer)
                close=getattr(target,"close",None)
                if close:
                    close()


def _decode_b64(value:str)->Image.Image:
    raw=base64.b64decode(value,validate=True)
    im=Image.open(io.BytesIO(raw)); im.load(); return im


def make_handler(worker:FullGocrWorker):
    class Handler(BaseHTTPRequestHandler):
        server_version="GOCRFullWorker/0.1"
        def send_json(self,status,obj):
            data=json.dumps(obj,ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type","application/json; charset=utf-8")
            self.send_header("Content-Length",str(len(data)))
            self.end_headers(); self.wfile.write(data)
        def do_GET(self):
            if self.path=="/v1/health":
                return self.send_json(200,{"status":"ok","schema":"gocr.worker.v1","mode":"full",
                                          "gocr_profile":worker.profile})
            if self.path=="/v1/assets":
                return self.send_json(200,worker.asset_status)
            return self.send_json(404,{"error":"not found"})
        def do_POST(self):
            try:
                if self.path!="/v1/ocr":
                    return self.send_json(404,{"error":"not found"})
                n=int(self.headers.get("Content-Length","0"))
                if n<=0 or n>20*1024*1024:
                    return self.send_json(413,{"error":"invalid body size"})
                body=json.loads(self.rfile.read(n).decode("utf-8"))
                image=_decode_b64(body["image_b64"])
                return self.send_json(200,worker.ocr(image))
            except Exception as exc:
                LOG.exception("OCR request failed")
                return self.send_json(400,{"error":f"{type(exc).__name__}: {exc}"})
        def log_message(self,fmt,*args):
            LOG.info(fmt,*args)
    return Handler


def main():
    p=argparse.ArgumentParser(description="Full-frame GOCR worker")
    p.add_argument("--assets",type=Path,required=True)
    p.add_argument("--threads",type=int,default=max(1,int(os.environ.get("GOCR_THREADS","2"))))
    p.add_argument("--detector-threads",type=int,choices=range(1,5))
    p.add_argument("--recognizer-threads",type=int,choices=range(1,5))
    sub=p.add_subparsers(dest="cmd",required=True)
    c=sub.add_parser("image"); c.add_argument("path",type=Path)
    s=sub.add_parser("serve"); s.add_argument("--bind",default="127.0.0.1"); s.add_argument("--port",type=int,default=8771)
    a=p.parse_args()
    logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(message)s")
    w=FullGocrWorker(a.assets,a.threads,detector_threads=a.detector_threads,
                     recognizer_threads=a.recognizer_threads)
    if a.cmd=="image":
        with Image.open(a.path) as im:
            print(json.dumps(w.ocr(im.convert("RGB")),ensure_ascii=False,indent=2))
        return
    server=ThreadingHTTPServer((a.bind,a.port),make_handler(w))
    LOG.info("full GOCR worker listening on %s:%d",a.bind,a.port)
    server.serve_forever()


if __name__=="__main__":
    main()
