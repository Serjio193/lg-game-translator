import base64
import io
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from PIL import Image

from gocr_worker.crop_client import CropClient
from gocr_worker.frame_pipeline import FramePipeline
from gocr_worker.frame_transport import HEADER, receive_frame
from gocr_worker.image_contract import fingerprint, quad_points
from gocr_worker.worker import make_handler
from gocr_worker.worker_full import FullGocrWorker

QUAD = [[20.,20.],[150.,20.],[150.,50.],[20.,50.]]


class Detector:
    def detect(self, image):
        return {"lines": [{"line_id": "7", "quad": QUAD, "angle": 0.0, "score": .97}],
                "invoke_ms": 1, "total_ms": 2, "postprocess": "test_double"}


class Recognizer:
    def recognize(self, image):
        return {"text": "Hello", "total_ms": 3, "invoke_ms": 2}


class Translator:
    def translate(self, text):
        return {"translation": "Привет", "bytes_sent": len(text), "request_ms": 4}


class CropWorker:
    def recognize_crop(self, image, meta):
        if fingerprint(image) != meta["crop_sha256"]:
            raise ValueError("changed crop")
        return {"schema": "gocr.worker.v1", "lines": [{
            "line_id": meta["line_id"],
            "source_quad": {f"p{i}": {"x": p[0], "y": p[1]} for i, p in enumerate(meta["source_quad"])},
            "angle": meta["angle"], "detector_confidence": meta["detector_confidence"],
            "crop_sha256": fingerprint(image), "text": "Hello", "timings_ms": {"recognizer": 3}}]}


class IntegrationTests(unittest.TestCase):
    def test_full_pipeline_forwards_independent_thread_counts(self):
        with patch("gocr_worker.frame_pipeline.verify_bundle",return_value={}), \
             patch("gocr_worker.frame_pipeline.FullGocrWorker") as full:
            FramePipeline(Path("."),"TV_FULL",translator=Translator(),
                          detector_threads=4,recognizer_threads=1)
            full.assert_called_once_with(Path("."),2,detector_threads=4,recognizer_threads=1)

    def test_crop_mode_rejects_a_local_recognizer_thread_override(self):
        with self.assertRaises(ValueError):
            FramePipeline(Path("."),"TV_CROP",crop_client=object(),recognizer_threads=1)

    def test_transport_preserves_crop_pixels_and_original_geometry(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(CropWorker(), Translator(), "x"*32))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            peer = CropClient(f"http://127.0.0.1:{server.server_port}", "x"*32)
            image = Image.new("RGB", (130,30), (123,45,67))
            meta = {"line_id": "7", "source_quad": QUAD, "angle": .2, "detector_confidence": .97}
            line, sent = peer.recognize(image, meta)
            self.assertEqual(quad_points(line["source_quad"]), QUAD)
            self.assertEqual(line["crop_sha256"], fingerprint(image))
            self.assertEqual(line["translation"]["translation"], "Привет")
            self.assertGreater(sent, 0)
            bad = CropClient(f"http://127.0.0.1:{server.server_port}", "wrong")
            with self.assertRaises(HTTPError):
                bad.recognize(image, meta)
        finally:
            server.shutdown(); server.server_close(); thread.join()

    def test_both_modes_reuse_the_identical_rectification(self):
        full = FullGocrWorker.__new__(FullGocrWorker)
        full.detector, full.recognizer = Detector(), Recognizer()
        full.native_full=None
        full.profile="strict"
        full.detector_threads=full.recognizer_threads=2
        full.runner_contract=None
        full.lock=threading.Lock()
        image = Image.new("RGB", (1280,720), (20,40,60))
        reference = full.ocr(image)
        class Peer:
            def recognize(self, crop, meta):
                return CropWorker().recognize_crop(crop, {**meta, "crop_sha256": fingerprint(crop)})["lines"][0], 10
        with patch("gocr_worker.frame_pipeline.verify_bundle", return_value={}), \
             patch("gocr_worker.frame_pipeline.GoogleConfiguredGroupRpnDetector", return_value=Detector()), \
             patch("gocr_worker.frame_pipeline.FullGocrWorker", return_value=full):
            crop = FramePipeline(Path("."), "TV_CROP", crop_client=Peer()).process(image)
            entire = FramePipeline(Path("."), "TV_FULL", translator=Translator()).process(image)
        for key in ("source_quad", "angle", "detector_confidence", "crop_sha256", "text"):
            self.assertEqual(crop["lines"][0][key], entire["lines"][0][key])
        self.assertEqual(reference["lines"][0]["crop_sha256"], crop["lines"][0]["crop_sha256"])
        with self.assertRaises(ValueError):
            FramePipeline.__new__(FramePipeline).process(Image.new("RGB", (640,360)))

    def test_selected_frame_header_exact_dimensions_and_partial_reads(self):
        payload = HEADER.pack(b"GFR1",1280,720,42,1000,1280*720*3)+bytes(1280*720*3)
        class Stream:
            def __init__(self, data): self.data = io.BytesIO(data)
            def recv(self, size): return self.data.read(min(size, 4096))
        image, sequence, captured = receive_frame(Stream(payload))
        self.assertEqual(image.size, (1280,720))
        self.assertEqual((sequence,captured), (42,1000))
        with self.assertRaises(ValueError):
            receive_frame(Stream(HEADER.pack(b"GFR1",640,360,1,2,3)))
        with self.assertRaises(EOFError):
            receive_frame(Stream(payload[:50]))

    def test_quad_rejects_invalid_coordinates(self):
        with self.assertRaises(ValueError):
            quad_points([[float("nan"),0]]*4)


if __name__ == "__main__":
    unittest.main()
