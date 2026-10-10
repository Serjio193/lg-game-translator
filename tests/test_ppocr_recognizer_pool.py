import sys
from pathlib import Path
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
from ppocr_recognizer_pool import RecognizerPool
from ppocr_crop_cache import ExactCropCache


class Engine:
    model_name = "test"
    model_directory = "test"
    output_layout = "class-major"

    def __init__(self, mask):
        self.mask = mask
        self.owner = threading.get_ident()
        self.npu = {}
        self.local = threading.local()

    def recognize(self, mode, pixels, width, height):
        if self.owner != threading.get_ident():
            raise AssertionError("Engine used from another worker")
        if pixels == b"!":
            raise RuntimeError("Bad crop")
        return 0, "5\t1\t1\t1\t1\t1\t0\t0\t1\t1\t95\t"+pixels.decode()+"\n"


class PoolTests(unittest.TestCase):
    def test_three_owners_and_queue_preserve_order_and_errors(self):
        pool = RecognizerPool(Engine)
        barrier = threading.Barrier(3)
        try:
            def blocked_crop(pixel):
                barrier.wait(timeout=5)
                return threading.get_ident(), pool.recognize(4, pixel, 1, 1)
            jobs = [pool.submit(blocked_crop, pixel) for pixel in (b"a", b"b", b"c")]
            results = [job.result(timeout=5) for job in jobs]
            self.assertEqual(len({r[0] for r in results}), 3)
            self.assertEqual([r[1][1].splitlines()[0].split("\t")[-1] for r in results],
                             ["a", "b", "c"])
            bad = pool.submit(pool.recognize, 4, b"!", 1, 1)
            with self.assertRaises(RuntimeError):
                bad.result(timeout=5)
            self.assertEqual(pool.submit(pool.recognize, 4, b"d", 1, 1).result(timeout=5)[0], 0)
        finally:
            pool.close()
        self.assertFalse(any(t.is_alive() for t in pool.threads))

    def test_duplicate_inflight_crops_share_success_and_exception(self):
        class SlowEngine(Engine):
            def recognize(self, *args):
                entered.set()
                release.wait(timeout=5)
                return super().recognize(*args)
        pool = RecognizerPool(SlowEngine)
        cache = ExactCropCache(pool)
        try:
            for pixels in (b"a", b"!"):
                entered, release = threading.Event(), threading.Event()
                first = pool.submit(cache.recognize, 4, pixels, 1, 1)
                self.assertTrue(entered.wait(timeout=5))
                second = pool.submit(cache.recognize, 4, pixels, 1, 1)
                # A third job waits until the duplicate has entered the cache wait path.
                import time
                deadline = time.monotonic()+5
                target = 1 if pixels == b"a" else 2
                while cache.cache_stats()["shared_waits"] < target and time.monotonic() < deadline:
                    time.sleep(0.001)
                self.assertEqual(cache.cache_stats()["shared_waits"], target)
                release.set()
                if pixels == b"!":
                    for job in (first, second):
                        with self.assertRaises(RuntimeError):
                            job.result(timeout=5)
                else:
                    self.assertEqual(first.result(timeout=5), second.result(timeout=5))
            self.assertEqual(cache.cache_stats()["recognize_calls"], 2)
            self.assertFalse(cache.pending)
        finally:
            release.set()
            pool.close()

    def test_initialization_failure_closes_other_workers(self):
        def factory(mask):
            if mask == 2:
                raise RuntimeError("Load failure")
            return Engine(mask)
        with self.assertRaises(RuntimeError):
            RecognizerPool(factory)
