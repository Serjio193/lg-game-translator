from __future__ import annotations

import argparse
import base64
import io
import json
import logging
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PIL import Image

from .assets import verify_bundle
from .detector import rectify_crop
from .detector_runtime import GoogleConfiguredGroupRpnDetector
from .protocol import Line, OcrResult, Point, Quad
from .recognizer import GocrLineRecognizer

LOG=logging.getLogger("gocr-worker-full")


def _quad(value):
    p=[Point(float(x),float(y)) for x,y in value]
    return Quad(*p)


class FullGocrWorker:
    def __init__(self,assets:Path,threads:int=2):
        self.assets=assets
        self.asset_status=verify_bundle(assets)
        self.detector=GoogleConfiguredGroupRpnDetector(assets,threads=threads)
        self.recognizer=GocrLineRecognizer(assets,threads=threads)

    def ocr(self,image:Image.Image)->dict:
        start=time.perf_counter()
        det=self.detector.detect(image)
        lines=[]
        rec_total=0.0
        for item in det["lines"]:
            crop=rectify_crop(image,item["quad"])
            rec=self.recognizer.recognize(crop)
            rec_total+=rec["total_ms"]
            lines.append(Line(
                line_id=item["line_id"],
                text=rec["text"],
                source_quad=_quad(item["quad"]),
                angle=float(item["angle"]),
                detector_confidence=float(item["score"]),
                recognizer_confidence=None,
                timings_ms={"recognizer":rec["total_ms"],"tflite_invoke":rec["invoke_ms"]},
            ))
        total=(time.perf_counter()-start)*1000.0
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
        ).to_dict()


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
                return self.send_json(200,{"status":"ok","schema":"gocr.worker.v1","mode":"full"})
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
    sub=p.add_subparsers(dest="cmd",required=True)
    c=sub.add_parser("image"); c.add_argument("path",type=Path)
    s=sub.add_parser("serve"); s.add_argument("--bind",default="127.0.0.1"); s.add_argument("--port",type=int,default=8771)
    a=p.parse_args()
    logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(message)s")
    w=FullGocrWorker(a.assets,a.threads)
    if a.cmd=="image":
        with Image.open(a.path) as im:
            print(json.dumps(w.ocr(im.convert("RGB")),ensure_ascii=False,indent=2))
        return
    server=ThreadingHTTPServer((a.bind,a.port),make_handler(w))
    LOG.info("full GOCR worker listening on %s:%d",a.bind,a.port)
    server.serve_forever()


if __name__=="__main__":
    main()
