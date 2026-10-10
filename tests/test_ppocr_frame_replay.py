"""Selected-frame byte contract before the existing native detector."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import threading
import sys

from PIL import Image

source = Path(__file__).resolve().parents[1] / "scripts/ppocr_frame_replay.py"
spec = importlib.util.spec_from_file_location("ppocr_replay_test", source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FrameContractTests(unittest.TestCase):
    def test_joined_regions_are_scheduled_first_but_output_order_is_original(self):
        from concurrent.futures import Future
        class Detector:
            def detect(self, gray):
                return [module.Region(0, 0, 1, 1, 1, 0), module.Region(1, 0, 1, 2, 1, 0)]
            def lines(self, box):
                return [module.Region(box.x, y, 1, 1, 1, 0) for y in range(box.height)]
        class Engine:
            def recognize(self, mode, pixels, width, height):
                return 0, "header\n5\t1\t1\t1\t1\t1\t0\t0\t1\t1\t95\tword\n"
        class Pool:
            def submit(self, function, row, gray):
                order.append((row.x, row.y))
                future = Future()
                future.set_result(function(row, gray))
                return future
            def worker_stats(self):
                return {}
        order, callbacks = [], []
        import numpy as np
        with patch.object(module, "gray_frame", return_value=np.zeros((2, 2), dtype=np.uint8)):
            result = module.Pipeline(Detector(), Engine(), Pool()).ocr(None,
                on_region=lambda index, region: callbacks.append(index))
        self.assertEqual(order, [(1, 0), (1, 1), (0, 0)])
        self.assertEqual([r["box"]["x"] for r in result["regions"]], [0, 1])
        self.assertEqual(set(callbacks), {0, 1})

    def test_queue_covers_separate_regions_and_preserves_output_order(self):
        sys.path.insert(0, str(source.parent))
        from ppocr_recognizer_pool import RecognizerPool
        class Engine:
            def __init__(self, mask):
                self.npu = {}
                self.local = threading.local()
            def recognize(self, mode, pixels, width, height):
                if pixels != b'd':
                    barrier.wait(timeout=5)
                return 0, "header\n5\t1\t1\t1\t1\t1\t0\t0\t1\t1\t95\t"+pixels.decode()+"\n"
        class Detector:
            def detect(self, gray):
                return [module.Region(i, 0, 1, 1, 1, 0) for i in range(4)]
            def lines(self, box):
                return [box]
        barrier = threading.Barrier(3)
        pool = RecognizerPool(Engine)
        try:
            import numpy as np
            with patch.object(module, "gray_frame", return_value=np.array([[97, 98, 99, 100]],
                                                                          dtype=np.uint8)):
                result = module.Pipeline(Detector(), pool, pool).ocr(None)
            self.assertEqual([r["text"] for r in result["regions"]], ["a", "b", "c", "d"])
            self.assertEqual(sum(pool.worker_stats()["completed_jobs"]), 4)
        finally:
            pool.close()

    def test_rgb_luminance_and_contiguous_frame(self):
        image = Image.new("RGB", (1280, 720), "white")
        for x, color in enumerate(((0, 0, 0), (255, 0, 0), (0, 255, 0), (0, 0, 255))):
            image.putpixel((x, 0), color)
        gray = module.gray_frame(image)
        self.assertEqual(gray[0, :5].tolist(), [0, 76, 149, 28, 255])
        self.assertEqual(gray.nbytes, 921600)
        self.assertTrue(gray.flags.c_contiguous)

    def test_rejects_changed_selected_frame_contract(self):
        for image in (Image.new("RGB", (1920, 1080)), Image.new("L", (1280, 720))):
            with self.assertRaises(ValueError):
                module.gray_frame(image)

    def test_tsv_ignores_non_word_rows_and_preserves_icon_marker(self):
        tsv = "header\n1\t1\t1\t1\t1\t1\t0\t0\t0\t0\t-1\tignored\n"
        tsv += "5\t1\t1\t1\t1\t1\t0\t0\t10\t10\t90\tHold\n"
        tsv += "5\t1\t1\t1\t1\t2\t10\t0\t10\t10\t80\t[button]\n"
        self.assertEqual(module.parse_tsv(tsv), "Hold [button]")


if __name__ == "__main__":
    unittest.main()
