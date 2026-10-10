"""Temporary authenticated PP-OCR probe, using existing lossless frame transport."""
import argparse
from http.server import ThreadingHTTPServer
from pathlib import Path
import sys
import threading
import numpy as np
import os

from ppocr_frame_replay import Detector, Pipeline
from ppocr_region_events import region_line


class Worker:
    supports_region_events = True
    supports_translation_scope = True

    def __init__(self, pipeline, policy=None):
        self.pipeline = pipeline
        self.policy = policy
        self.lock = threading.Lock()
        self.profiler = None
        if os.environ.get("PP_OCR_PROFILE_STAGES") == "1":
            from ppocr_stage_profiler import StageProfiler
            self.profiler = StageProfiler(pipeline)

    def ocr(self, image, on_region=None, scope="normal"):
        rgb = np.asarray(image)
        ready = {}
        def completed(index, region):
            line = region_line(index, region, rgb)
            ready[index] = line
            if self.policy is not None:
                self.policy.apply([line], scope)
            if on_region is not None and line.get("translation_allowed") is True:
                on_region(line)
        with self.lock:
            if self.profiler:
                self.profiler.begin()
            result = self.pipeline.ocr(image, completed)
            if self.profiler:
                result["ocr_stage_profile"] = self.profiler.snapshot()
        lines = [ready[i] for i in range(len(result["regions"]))]
        if self.policy is not None:
            self.policy.apply(lines, scope)
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
    pool = None
    workers = int(os.environ.get("PP_OCR_RECOGNIZER_WORKERS", "1"))
    if workers != 1 and os.environ.get("PP_OCR_PROFILE_STAGES") == "1":
        raise ValueError("Sequential stage profiler cannot measure concurrent workers")
    if workers == 3:
        from ppocr_recognizer_pool import RecognizerPool, pinned_engine
        pool = RecognizerPool(lambda mask: pinned_engine(
            args.runtime / "assets", os.environ["PP_OCR_CORE_LIBRARY"], mask))
        engines = pool
    elif workers == 1:
        engines = Engines(args.runtime / "assets")
    else:
        raise ValueError("Supported recognizer workers: 1 or 3")
    if os.environ.get("PP_OCR_EXACT_CROP_CACHE") == "1":
        from ppocr_crop_cache import ExactCropCache
        engines = ExactCropCache(engines)
    worker = Worker(Pipeline(detector, engines, pool), policy)
    try:
        with ThreadingHTTPServer((args.bind, args.port), make_handler(worker, token)) as server:
            server.serve_forever()
    finally:
        if worker.profiler:
            worker.profiler.close()
        detector.close()
        if pool is not None:
            pool.close()


if __name__ == "__main__":
    main()
