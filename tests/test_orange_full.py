from pathlib import Path
import importlib.util
import tempfile
import threading
import unittest
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from PIL import Image
from gocr_worker.frame_client import FrameClient
from gocr_worker.frame_pipeline import FramePipeline
from gocr_worker.image_contract import fingerprint
from gocr_worker.orange_server import make_handler


class Worker:
    def __init__(self):
        self.pixels = None

    def ocr(self, image):
        self.pixels = image.tobytes()
        return {"schema": "gocr.worker.v1", "width": 1280, "height": 720,
                "lines": [{"text": "Hello", "source_quad": [[1, 1], [100, 1], [100, 40], [1, 40]],
                           "timings_ms": {"recognizer": 1}}],
                "timings_ms": {"total": 1, "recognizer": 1}}


class OrangeFullTests(unittest.TestCase):
    def setUp(self):
        self.worker = Worker()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(self.worker, "t"*32))
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.address = f"http://127.0.0.1:{self.server.server_port}"
        self.client = FrameClient(self.address, "t"*32)

    def tearDown(self):
        self.client.close()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def test_pixels_sequence_hash_and_persistent_second_frame(self):
        for sequence in (41, 42):
            image = Image.new("RGB", (1280, 720), (sequence, 90, 210))
            result, sent = self.client.ocr(image, sequence, 123)
            self.assertEqual(self.worker.pixels, image.tobytes())
            self.assertEqual(result["frame_sha256"], fingerprint(image))
            self.assertEqual((result["sequence"], result["capture_ts"]), (sequence, 123))
            self.assertEqual(sent, 1280*720*3+28)
            self.assertIn("frame_to_text", result["timings_ms"])

    def test_all_scope_requires_capability_and_is_forwarded(self):
        image = Image.new("RGB", (1280, 720))
        request = Request(self.address + "/v1/ocr-frame", data=b"short", headers={
            "Authorization": "Bearer " + "t"*32, "X-PP-OCR-Policy": "all",
            "Content-Type": "application/x-gocr-frame"})
        with self.assertRaises(HTTPError) as rejected:
            urlopen(request, timeout=2)
        self.assertEqual(rejected.exception.code, 400)
        with patch.object(FrameClient, "translation_scope", return_value="all"):
            original = self.worker.ocr
            seen = []

            def scoped(frame, scope="normal"):
                seen.append(scope)
                return original(frame)

            self.worker.supports_translation_scope = True
            self.worker.ocr = scoped
            result, _ = self.client.ocr(image)
            self.assertEqual(seen, ["all"])
            self.assertEqual(result["translation_scope"], "all")

    def test_auth_and_truncated_body_rejected(self):
        for token, status in (("wrong", 401), ("t"*32, 413)):
            request = Request(self.address+"/v1/ocr-frame", data=b"short",
                              headers={"Authorization": "Bearer "+token,
                                       "Content-Type": "application/x-gocr-frame"})
            with self.assertRaises(HTTPError) as error:
                urlopen(request, timeout=2)
            self.assertEqual(error.exception.code, status)
        self.assertIsNone(self.worker.pixels)

    def test_remote_mode_does_not_initialize_local_models(self):
        class Translator:
            def translate(self, text):
                return {"translation": "Привет", "bytes_sent": 5, "request_ms": 1}
        with patch("gocr_worker.frame_pipeline.verify_bundle") as assets, \
             patch("gocr_worker.frame_pipeline.FullGocrWorker") as full, \
             patch("gocr_worker.frame_pipeline.GoogleConfiguredGroupRpnDetector") as detector:
            pipeline = FramePipeline(Path("missing"), "ORANGE_FULL", frame_client=self.client,
                                     translator=Translator())
            result = pipeline.process(Image.new("RGB", (1280, 720)), 5, 7)
            self.assertEqual(result["lines"][0]["translation"]["translation"], "Привет")
            self.assertEqual(result["mode"], "ORANGE_FULL")
            assets.assert_not_called()
            full.assert_not_called()
            detector.assert_not_called()

    def test_frame_identity_mutation_rejected_and_connection_reset(self):
        original = self.worker.ocr
        def changed(image):
            result = original(image)
            result["width"] = 640
            return result
        self.worker.ocr = changed
        with self.assertRaisesRegex(ValueError, "identity"):
            self.client.ocr(Image.new("RGB", (1280, 720)))
        self.assertIsNone(self.client.connection)

    def test_remote_thread_override_rejected(self):
        with self.assertRaises(ValueError):
            FramePipeline(Path("."), "ORANGE_FULL", frame_client=self.client,
                          translator=object(), detector_threads=4)

    def test_existing_hook_refreshes_transport_without_changing_producer(self):
        root = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location("install_hook",
            root/"scripts/install-gocr-frame-hook.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target/"unicapture").mkdir()
            worker = target/"unicapture/ocr_worker.c"
            worker.write_text("ocr_color_snapshot(worker, &local_rgb, &color_capacity);\n"
                              "gocr_submit_selected_rgb\noriginal producer\n")
            cmake = target/"unicapture/CMakeLists.txt"
            cmake.write_text("original build\n")
            original_worker, original_cmake = worker.read_bytes(), cmake.read_bytes()
            module.install(target, root/"native")
            self.assertEqual(worker.read_bytes(), original_worker)
            self.assertEqual(cmake.read_bytes(), original_cmake)
            self.assertEqual((target/"unicapture/gocr_frame_transport.c").read_bytes(),
                             (root/"native/gocr_frame_transport.c").read_bytes())


if __name__ == "__main__":
    unittest.main()
