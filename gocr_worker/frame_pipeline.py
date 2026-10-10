"""Run on TV against an already selected frame; this module never captures."""
import threading
import time
from concurrent.futures import ThreadPoolExecutor, wait
from pathlib import Path

from .assets import verify_bundle
from .detector import rectify_crop
from .detector_runtime import GoogleConfiguredGroupRpnDetector
from .image_contract import fingerprint
from .worker_full import FullGocrWorker
from .execution_profile import execution_profile


class FramePipeline:
    def __init__(self, assets: Path, mode, threads=2, crop_client=None, translator=None,
                 *,detector_threads=None,recognizer_threads=None,frame_client=None):
        if mode not in ("TV_CROP", "TV_FULL", "ORANGE_FULL"):
            raise ValueError("unknown GOCR execution mode")
        self.mode = mode
        self.crop_client, self.translator = crop_client, translator
        self.lock = threading.Lock()
        if mode == "ORANGE_FULL":
            if frame_client is None or translator is None:
                raise ValueError("ORANGE_FULL needs frame and translation clients")
            if detector_threads is not None or recognizer_threads is not None:
                raise ValueError("ORANGE_FULL thread counts belong to the Orange server")
            self.frame_client = frame_client
            self.translation_pool = (ThreadPoolExecutor(max_workers=2, thread_name_prefix="region-translation")
                                     if getattr(frame_client, "early_translation", False) is True else None)
            self.asset_status = {"execution_location": "orange", "experimental": True}
        elif mode == "TV_CROP":
            if execution_profile()!="strict":
                raise ValueError("FAST_XNNPACK is currently supported only in TV_FULL")
            if recognizer_threads is not None:
                raise ValueError("recognizer threads belong to the Orange worker in TV_CROP")
            if crop_client is None:
                raise ValueError("TV_CROP needs an Orange crop client")
            self.asset_status = verify_bundle(assets, "detector")
            self.detector = GoogleConfiguredGroupRpnDetector(
                assets,threads if detector_threads is None else detector_threads)
        else:
            if translator is None:
                raise ValueError("TV_FULL needs the existing translator client")
            self.asset_status = verify_bundle(assets, "full", require_support_files=True)
            self.full = FullGocrWorker(assets,threads,detector_threads=detector_threads,
                                      recognizer_threads=recognizer_threads)

    def process(self, image, sequence=0, capture_ts=None, *, ocr_only=False, on_region=None):
        if image.size != (1280, 720) or image.mode != "RGB":
            raise ValueError("GOCR needs the existing selected RGB 1280x720 frame")
        started = time.perf_counter()
        region_times = []
        def region_ready(line):
            region_times.append((time.perf_counter()-started)*1000)
            on_region(line)
        with self.lock:
            if ocr_only:
                if self.mode != "ORANGE_FULL":
                    raise ValueError("Deferred translations require ORANGE_FULL")
                result, sent = (self.frame_client.ocr(image, sequence, capture_ts, on_region=region_ready)
                                if on_region is not None else
                                self.frame_client.ocr(image, sequence, capture_ts))
            elif self.mode in ("TV_FULL", "ORANGE_FULL"):
                early = {}
                submitted = []
                def submit(line):
                    source_text = line["text"]
                    source_quad = {key: dict(point) for key, point in line["source_quad"].items()}
                    timing = {"queued_after_ms": (time.perf_counter()-started)*1000}
                    def translate():
                        timing["started_after_ms"] = (time.perf_counter()-started)*1000
                        return self.translator.translate(source_text)
                    future = self.translation_pool.submit(translate)
                    submitted.append(future)
                    early[line["line_id"]] = (source_text, source_quad, future, timing)
                if self.mode == "ORANGE_FULL":
                    if self.translation_pool is None:
                        result, sent = self.frame_client.ocr(image, sequence, capture_ts)
                    else:
                        try:
                            result, sent = self.frame_client.ocr(image, sequence, capture_ts, on_region=submit)
                        except BaseException:
                            for _, _, future, _ in early.values():
                                future.cancel()
                            wait(submitted)
                            raise
                else:
                    result, sent = self.full.ocr(image), 0
                ocr_ready = (time.perf_counter()-started)*1000
                # Schedule deferred headings/final-only blocks before waiting on any translation.
                if self.mode == "ORANGE_FULL" and self.translation_pool is not None:
                    for line in result["lines"]:
                        if line.get("translation_allowed") is True:
                            entry = early.get(line["line_id"])
                            if entry is None or entry[:2] != (line["text"], line["source_quad"]):
                                if entry is not None:
                                    entry[2].cancel()
                                submit(line)
                    wait(submitted)
                    result["timings_ms"]["early_translation_regions"] = sum(
                        entry[3].get("started_after_ms", float("inf")) < ocr_ready for entry in early.values())
                for line in result["lines"]:
                    if result.get("engine") == "ppocr" and line.get("translation_allowed") is not True:
                        line["translation"] = {"translation": "", "bytes_sent": 0,
                                               "request_ms": 0, "skipped": "translation_policy"}
                        continue
                    entry = early.get(line.get("line_id"))
                    if entry is not None and entry[:2] == (line["text"], line["source_quad"]):
                        line["translation"] = entry[2].result()
                        line["timings_ms"]["translation_queued_after_ms"] = entry[3]["queued_after_ms"]
                        line["timings_ms"]["translation_started_after_ms"] = entry[3]["started_after_ms"]
                        line["timings_ms"]["translation_overlap_ocr_ms"] = max(0, ocr_ready-entry[3]["started_after_ms"])
                    else:
                        line["translation"] = self.translator.translate(line["text"])
                    sent += line["translation"]["bytes_sent"]
            else:
                det = self.detector.detect(image)
                lines, crop_ms, sent = [], 0.0, 0
                for item in det["lines"]:
                    tick = time.perf_counter()
                    crop = rectify_crop(image, item["quad"])
                    crop_ms += (time.perf_counter()-tick)*1000
                    meta = {"line_id": item["line_id"], "source_quad": item["quad"],
                            "angle": item["angle"], "detector_confidence": item["score"]}
                    line, size = self.crop_client.recognize(crop, meta)
                    lines.append(line)
                    sent += size
                result = {"schema": "gocr.worker.v1", "width": 1280, "height": 720,
                          "lines": lines, "timings_ms": {"detector": det["total_ms"],
                          "detector_tflite_invoke": det["invoke_ms"], "crop_rectify": crop_ms},
                          "parity": {"detector_postprocess": det["postprocess"],
                                     "production_lm_fst_applied": False, "recognizer_decoder": "greedy_ctc"},
                          "telemetry":{"detector_backend":det.get("backend","python"),
                              "detector_stages_ms":det.get("stages_ms",{}),
                              "detector_counts":det.get("counts",{}),
                              "raw_piece_count":det.get("raw_piece_count"),
                              "raw_group_count":det.get("raw_group_count")}}
        stages = result["timings_ms"]
        if region_times:
            stages.update(early_region_count=len(region_times), first_region_ready=region_times[0])
        stages.update({"recognizer": sum(line["timings_ms"].get("recognizer", 0) for line in result["lines"]),
                       "network": stages.get("frame_network", 0)+sum(line["timings_ms"].get("network", 0) + max(0,
                           line.get("translation", {}).get("request_ms", 0) -
                           line.get("translation", {}).get("latency_ms", 0)) for line in result["lines"]),
                       "translation": sum(line.get("translation", {}).get("latency_ms",
                           line.get("translation", {}).get("request_ms", 0)) for line in result["lines"]),
                       "end_to_end": (time.perf_counter()-started)*1000})
        result.update(mode=self.mode, sequence=sequence, capture_ts=capture_ts,
                      bytes_sent=sent, frame_sha256=fingerprint(image))
        return result

    def close(self):
        pool = getattr(self, "translation_pool", None)
        if pool is not None:
            pool.shutdown(wait=True, cancel_futures=True)
