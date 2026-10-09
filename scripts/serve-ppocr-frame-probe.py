"""Temporary authenticated PP-OCR probe, using existing lossless frame transport."""
import argparse
from http.server import ThreadingHTTPServer
from pathlib import Path
import sys
import threading
import numpy as np
import os

from ppocr_frame_replay import Detector, Pipeline


class Worker:
    def __init__(self, pipeline, policy=None):
        self.pipeline = pipeline
        self.policy = policy
        self.lock = threading.Lock()
        self.profiler = None
        if os.environ.get("PP_OCR_PROFILE_STAGES") == "1":
            from ppocr_stage_profiler import StageProfiler
            self.profiler = StageProfiler(pipeline)

    def ocr(self, image):
        with self.lock:
            if self.profiler:
                self.profiler.begin()
            result = self.pipeline.ocr(image)
            if self.profiler:
                result["ocr_stage_profile"] = self.profiler.snapshot()
        lines = []
        rgb = np.asarray(image)
        for i, region in enumerate(result["regions"]):
            b = region["box"]
            points = [(b["x"], b["y"]), (b["x"] + b["width"], b["y"]),
                      (b["x"] + b["width"], b["y"] + b["height"]),
                      (b["x"], b["y"] + b["height"])]
            crop = rgb[b["y"]:b["y"]+b["height"], b["x"]:b["x"]+b["width"]]
            edges = np.concatenate((crop[0], crop[-1], crop[:, 0], crop[:, -1]))
            bg = np.median(edges, axis=0)
            reliable = np.percentile(np.max(np.abs(edges.astype(float)-bg), axis=1), 90) < 20
            appearance = {"frame_width": 1280, "frame_height": 720, "box": b,
                          "lines": max(1, min(12, len(region["lines"]))),
                          "background_reliable": bool(reliable), "background": bg.astype(int).tolist(),
                          "foreground": [255, 255, 255] if bg.mean() < 128 else [0, 0, 0]}
            lines.append({"line_id": str(i), "text": region["text"], "appearance": appearance,
                          "recognition_lines": region["lines"],
                          "timings_ms": {},
                          "source_quad": {f"p{k}": {"x": x, "y": y}
                                          for k, (x, y) in enumerate(points)}})
        if self.policy is not None:
            self.policy.apply(lines)
        # Reuse the project's validated wire envelope, identifying PP-OCR explicitly.
        result.update(schema="gocr.worker.v1", engine="ppocr", width=1280, height=720,
                      lines=lines, recognizer=self.pipeline.engines.model_name)
        return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--library", type=Path, required=True)
    p.add_argument("--detector-prefix", type=Path, required=True)
    p.add_argument("--runtime", type=Path, required=True)
    p.add_argument("--gocr-runtime", type=Path, required=True)
    p.add_argument("--token-file", type=Path, required=True)
    p.add_argument("--bind", required=True)
    p.add_argument("--port", type=int, default=18775)
    args = p.parse_args()
    sys.path[:0] = [str(args.runtime), str(args.runtime / "assets"), str(args.gocr_runtime)]
    from ocr.engines import Engines
    if os.environ.get("PP_OCR_CTC_LIBRARY"):
        import ocr.engines as engines_module
        from ppocr_native_ctc import select_decoder
        select_decoder(engines_module, os.environ["PP_OCR_CTC_LIBRARY"])
    from gocr_worker.http_security import read_token, require_private_bind
    from gocr_worker.orange_server import make_handler
    token = read_token(args.token_file)
    require_private_bind(args.bind, token)
    detector = Detector(args.library, args.detector_prefix)
    policy = None
    if os.environ.get("PP_OCR_POLICY_LIBRARY"):
        from ppocr_translation_policy import TranslationPolicy
        policy = TranslationPolicy(os.environ["PP_OCR_POLICY_LIBRARY"])
    engines = Engines(args.runtime / "assets")
    if os.environ.get("PP_OCR_EXACT_CROP_CACHE") == "1":
        from ppocr_crop_cache import ExactCropCache
        engines = ExactCropCache(engines)
    worker = Worker(Pipeline(detector, engines), policy)
    try:
        with ThreadingHTTPServer((args.bind, args.port), make_handler(worker, token)) as server:
            server.serve_forever()
    finally:
        if worker.profiler:
            worker.profiler.close()
        detector.close()


if __name__ == "__main__":
    main()
