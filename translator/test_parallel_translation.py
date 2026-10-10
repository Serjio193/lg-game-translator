from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from translation_cache import TranslationCache
import server


class ParallelTranslationTests(unittest.TestCase):
    def test_different_cache_keys_generate_concurrently(self):
        barrier = threading.Barrier(2)
        def translate(text):
            barrier.wait(timeout=5)
            return {"provider": "madlad", "translation": text}
        with tempfile.TemporaryDirectory() as root, ThreadPoolExecutor(max_workers=2) as pool:
            cache = TranslationCache(Path(root)/"cache.sqlite")
            jobs = [pool.submit(cache.translate, text, "madlad", "v1", translate)
                    for text in ("First reply.", "Second reply.")]
            self.assertTrue(all(not job.result(timeout=5)["cache_hit"] for job in jobs))
            self.assertFalse(cache.pending)

    def test_same_key_is_generated_once(self):
        entered, release = threading.Event(), threading.Event()
        calls = []
        def translate(text):
            calls.append(text)
            entered.set()
            release.wait(5)
            return {"provider": "madlad", "translation": "Привет!"}
        with tempfile.TemporaryDirectory() as root, ThreadPoolExecutor(max_workers=2) as pool:
            cache = TranslationCache(Path(root)/"cache.sqlite")
            first = pool.submit(cache.translate, "Hello!", "madlad", "v1", translate)
            self.assertTrue(entered.wait(5))
            second = pool.submit(cache.translate, "Hello!", "madlad", "v1", translate)
            release.set()
            self.assertEqual(first.result(timeout=5)["translation"], second.result(timeout=5)["translation"])
            self.assertEqual(calls, ["Hello!"])

    def test_madlad_has_two_slots_without_serial_model_lock(self):
        from types import SimpleNamespace
        barrier = threading.Barrier(2)
        class Model:
            def translate_batch(self, pieces, **options):
                barrier.wait(timeout=5)
                return [SimpleNamespace(hypotheses=[["ok"]]) for _ in pieces]
        tokenizer = SimpleNamespace(encode=lambda text: SimpleNamespace(tokens=[text]),
                                    token_to_id=lambda text: 1,
                                    decode=lambda ids, **kwargs: "Готово.")
        with patch.object(server, "_model", Model()), patch.object(server, "_tokenizer", tokenizer), \
             patch.object(server, "_inference_slots", threading.BoundedSemaphore(2)), \
             ThreadPoolExecutor(max_workers=2) as pool:
            jobs = [pool.submit(server._translate_madlad, text) for text in ("Go!", "Follow me!")]
            self.assertEqual([job.result(timeout=5)["translation"] for job in jobs], ["Готово."]*2)
