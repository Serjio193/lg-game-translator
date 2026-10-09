from pathlib import Path
import unittest
from unittest.mock import Mock
from PIL import Image
from gocr_worker.frame_pipeline import FramePipeline


class TranslationGateTests(unittest.TestCase):
    def test_rejected_or_missing_policy_never_calls_translator(self):
        lines = [{"text": "B Back", "translation_allowed": False, "timings_ms": {}},
                 {"text": "Avoid Game Overs", "timings_ms": {}},
                 {"text": "Follow me!", "translation_allowed": True, "timings_ms": {}}]
        client = Mock()
        client.ocr.return_value = ({"engine": "ppocr", "lines": lines, "timings_ms": {}}, 100)
        translator = Mock()
        translator.translate.return_value = {"translation": "За мной!", "bytes_sent": 10}
        pipeline = FramePipeline(Path("unused"), "ORANGE_FULL", frame_client=client,
                                 translator=translator)
        pipeline.process(Image.new("RGB", (1280, 720)), 1)
        translator.translate.assert_called_once_with("Follow me!")
        self.assertEqual(lines[0]["translation"]["skipped"], "translation_policy")
        self.assertEqual(len(lines), 3, "Rejected OCR remains available for diagnostics")
