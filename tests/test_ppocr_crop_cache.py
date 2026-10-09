import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

path = Path(__file__).resolve().parents[1]/"scripts/ppocr_crop_cache.py"
spec = importlib.util.spec_from_file_location("crop_cache", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Engine:
    model_name = "v6"
    model_directory = "models"
    output_layout = "class-major"

    def __init__(self):
        self.calls = 0
        self.status = 0

    def recognize(self, mode, pixels, width, height):
        self.calls += 1
        return self.status, "5\t1\t1\t1\t1\t1\t0\t0\t8\t8\t95\tHello\n"


class CropCacheTests(unittest.TestCase):
    def test_exact_hit_one_pixel_shape_mode_and_namespace_miss(self):
        engine = Engine()
        cache = module.ExactCropCache(engine)
        pixels = bytes(64)
        result = cache.recognize(4, pixels, 8, 8)
        self.assertEqual(cache.recognize(4, bytes(pixels), 8, 8), result)
        self.assertEqual(engine.calls, 1)
        cache.recognize(4, b'\x01'+pixels[1:], 8, 8)
        cache.recognize(4, pixels, 16, 4)
        cache.recognize(3, pixels, 8, 8)
        engine.model_name = "different-model"
        cache.recognize(4, pixels, 8, 8)
        self.assertEqual(engine.calls, 5)
        self.assertEqual(cache.cache_stats()["entries"], 1)

    def test_hash_collision_does_not_return_old_text(self):
        engine = Engine()
        cache = module.ExactCropCache(engine)
        class Digest:
            def digest(self):
                return b"collision"
        with patch.object(module.hashlib, "sha256", return_value=Digest()):
            cache.recognize(4, bytes(64), 8, 8)
            cache.recognize(4, bytes([1])*64, 8, 8)
        self.assertEqual(engine.calls, 2)

    def test_lru_bound_errors_and_empty_not_retained(self):
        engine = Engine()
        cache = module.ExactCropCache(engine, max_bytes=400, max_entries=2)
        for n in range(4):
            cache.recognize(4, bytes([n])*64, 8, 8)
        self.assertEqual(cache.cache_stats()["entries"], 2)
        self.assertLessEqual(cache.cache_stats()["payload_bytes"], 400)
        engine.status = 1
        cache.recognize(4, bytes([9])*64, 8, 8)
        cache.recognize(4, bytes([9])*64, 8, 8)
        self.assertEqual(engine.calls, 6)
        with self.assertRaises(ValueError):
            cache.recognize(4, bytes(63), 8, 8)

    def test_whitespace_error_and_oversized_entries_are_not_cached(self):
        engine = Engine()
        cache = module.ExactCropCache(engine, max_bytes=1)
        for _ in range(2):
            cache.recognize(4, bytes(64), 8, 8)
        self.assertEqual(engine.calls, 2)
        self.assertEqual(cache.cache_stats()["entries"], 0)
        cache = module.ExactCropCache(engine)
        with patch.object(engine, "recognize", return_value=(0, "5\t1\t1\t1\t1\t1\t0\t0\t8\t8\t95\t  \n")) as recognize:
            cache.recognize(4, bytes(64), 8, 8)
            cache.recognize(4, bytes(64), 8, 8)
            self.assertEqual(recognize.call_count, 2)
        with patch.object(engine, "recognize", return_value=(-1, "error")) as recognize:
            cache.recognize(4, bytes(64), 8, 8)
            cache.recognize(4, bytes(64), 8, 8)
            self.assertEqual(recognize.call_count, 2)
