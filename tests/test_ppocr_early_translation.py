from concurrent.futures import ThreadPoolExecutor
from http.server import ThreadingHTTPServer
from pathlib import Path
import threading
import time
import unittest
import io
import json
from PIL import Image
from gocr_worker.orange_server import make_handler
from gocr_worker.frame_client import FrameClient
from gocr_worker.frame_pipeline import FramePipeline


def line(index, text, allowed=True):
    return {"line_id": str(index), "text": text, "translation_allowed": allowed,
            "timings_ms": {}, "source_quad": {f"p{i}": {"x": x, "y": y}
                for i, (x, y) in enumerate(((0, 0), (10, 0), (10, 10), (0, 10)))}}


class EarlyTranslationTests(unittest.TestCase):
    def test_event_identity_and_final_framing_fail_closed(self):
        class Response(io.BytesIO):
            def getheader(self, *args):
                return "application/x-ndjson"
        client = FrameClient("http://127.0.0.1:18775")
        context = {"sequence": 1, "capture_ts": 2, "frame_sha256": "hash"}
        event = {"event": "region", **context, "line": line(0, "Follow me!")}
        final = {"event": "final", **context, "result": {"lines": []}}
        cases = [[{**event, "sequence": 9}], [event], [final, event],
                 [event, event, final], [{**event, "line": line(0, "Items", False)}, final]]
        for values in cases:
            raw = b"".join(json.dumps(v).encode()+b"\n" for v in values)
            with self.assertRaises(ValueError):
                client.read_events(Response(raw), 1, 2, "hash", lambda value: None)

    def test_real_stream_starts_translation_while_other_ocr_is_pending(self):
        translating = threading.Event()
        class Worker:
            supports_region_events = True
            def ocr(self, image, on_region=None):
                body = line(0, "Follow me!")
                on_region(body)
                if not translating.wait(5):
                    raise AssertionError("Translation waited until OCR ended")
                return {"schema": "gocr.worker.v1", "engine": "ppocr", "width": 1280,
                        "height": 720, "lines": [body, line(1, "Items", False)], "timings_ms": {}}
        class Translator:
            def translate(self, text):
                translating.set()
                return {"translation": "За мной!", "bytes_sent": 1}
        http = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Worker(), "test-token"))
        thread = threading.Thread(target=http.serve_forever)
        thread.start()
        client = FrameClient(f"http://127.0.0.1:{http.server_port}", "test-token")
        client.early_translation = True
        pipeline = FramePipeline(Path("unused"), "ORANGE_FULL", frame_client=client,
                                 translator=Translator())
        try:
            result = pipeline.process(Image.new("RGB", (1280, 720)), 7, 8)
            self.assertEqual(result["lines"][0]["translation"]["translation"], "За мной!")
            self.assertEqual(result["lines"][1]["translation"]["skipped"], "translation_policy")
            self.assertEqual(result["timings_ms"]["early_translation_regions"], 1)
            self.assertGreater(result["lines"][0]["timings_ms"]["translation_overlap_ocr_ms"], 0)
        finally:
            pipeline.close()
            client.close()
            http.shutdown()
            http.server_close()
            thread.join()

    def test_changed_final_text_cannot_use_early_translation(self):
        class Client:
            early_translation = True
            def ocr(self, image, sequence, captured, on_region):
                on_region(line(0, "Old text."))
                return {"engine": "ppocr", "lines": [line(0, "New text.")], "timings_ms": {}}, 1
        class Translator:
            def translate(self, text):
                return {"translation": text, "bytes_sent": 1}
        pipeline = FramePipeline(Path("unused"), "ORANGE_FULL", frame_client=Client(),
                                 translator=Translator())
        try:
            result = pipeline.process(Image.new("RGB", (1280, 720)))
            self.assertEqual(result["lines"][0]["translation"]["translation"], "New text.")
        finally:
            pipeline.close()

    def test_ocr_only_stream_does_not_wait_for_other_regions(self):
        from tempfile import TemporaryDirectory
        from gocr_worker.live_translation import LiveTranslations
        from gocr_worker.osd_publisher import OsdPublisher
        translated = threading.Event()
        class PreviewClient:
            def preview(self, text, **metadata):
                translated.set()
                return {'provider': 'madlad', 'translation': 'За мной!',
                        'stage': 'preliminary', 'engine': 'bergamot'}
        class Worker:
            supports_region_events = True
            def ocr(self, image, on_region=None):
                body = {**line(0, 'Follow me!'), 'appearance':
                        {'box': {'x': 0, 'y': 0, 'width': 10, 'height': 10}, 'lines': 1}}
                on_region(body)
                if not translated.wait(3):
                    raise AssertionError('Live preview waited for remaining OCR')
                return {'schema': 'gocr.worker.v1', 'engine': 'ppocr', 'width': 1280,
                        'height': 720, 'lines': [body], 'timings_ms': {}}
        http = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(Worker(), 'test-token'))
        thread = threading.Thread(target=http.serve_forever)
        thread.start()
        client = FrameClient(f'http://127.0.0.1:{http.server_port}', 'test-token')
        pipeline = FramePipeline(Path('unused'), 'ORANGE_FULL', frame_client=client,
                                 translator=object())
        session = ('hdmi', 'madlad', 'localhost', '8765', '1')
        try:
            with TemporaryDirectory() as folder:
                live = LiveTranslations(OsdPublisher(Path(folder)),
                        client_factory=lambda _: PreviewClient(), guard=lambda _: None)
                try:
                    context = {'sequence': 1, 'capture_ts': 2, 'source_session': session}
                    result = pipeline.process(Image.new('RGB', (1280, 720)), 1, 2,
                            ocr_only=True, on_region=lambda row: live.observe_region(context, row))
                    live.observe({**result, 'source_session': session})
                    self.assertTrue(translated.is_set())
                    self.assertEqual(live.publisher.tracks[0]['count'], 1)
                finally:
                    live.close()
        finally:
            pipeline.close(); client.close()
            http.shutdown(); http.server_close(); thread.join()
