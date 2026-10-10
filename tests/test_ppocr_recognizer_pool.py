import sys
from pathlib import Path
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
from ppocr_recognizer_pool import RecognizerPool


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

    def test_repeated_pixels_are_recognized_for_each_job(self):
        pool = RecognizerPool(Engine)
        try:
            jobs = [pool.submit(pool.recognize, 4, b"a", 1, 1) for _ in range(10)]
            results = [job.result(timeout=5) for job in jobs]
            self.assertTrue(all(result == results[0] for result in results))
            self.assertEqual(sum(pool.worker_stats()["completed_jobs"]), 10)
        finally:
            pool.close()

    def test_initialization_failure_closes_other_workers(self):
        def factory(mask):
            if mask == 2:
                raise RuntimeError("Load failure")
            return Engine(mask)
        with self.assertRaises(RuntimeError):
            RecognizerPool(factory)
