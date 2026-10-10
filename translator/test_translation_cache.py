import sqlite3
import tempfile
import threading
import unittest
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import Mock

from translation_cache import TranslationCache


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "translations.sqlite3"
        self.cache = TranslationCache(self.path)

    def result(self, provider="madlad"):
        return {"provider": provider, "translation": "Следуй за мной.", "latency_ms": 3000}

    def test_persistence_normalization_and_original_pair(self):
        translator = Mock(return_value=self.result())
        first = self.cache.translate(" Follow   me! ", "madlad", "v1", translator)
        second = TranslationCache(self.path).translate("Follow me!", "madlad", "v1", translator)
        self.assertFalse(first["cache_hit"])
        self.assertTrue(second["cache_hit"])
        self.assertEqual(second["translation"], first["translation"])
        translator.assert_called_once_with("Follow me!")
        with closing(sqlite3.connect(self.path)) as connection:
            row = connection.execute("SELECT source_text, translation, hit_count FROM translations").fetchone()
        self.assertEqual(row, (" Follow   me! ", "Следуй за мной.", 1))

    def test_provider_revision_and_punctuation_separation(self):
        translator = Mock(return_value=self.result())
        self.cache.translate("Follow me!", "madlad", "v1", translator)
        self.cache.translate("Follow me!", "madlad", "v2", translator)
        self.cache.translate("Follow me?", "madlad", "v1", translator)
        google = Mock(return_value=self.result("google"))
        self.assertFalse(self.cache.translate("Follow me!", "google", "v1", google)["cache_hit"])
        self.assertEqual(translator.call_count, 3)
        google.assert_called_once()

    def test_errors_are_not_cached(self):
        translator = Mock(side_effect=RuntimeError("unavailable"))
        for _ in range(2):
            with self.assertRaises(RuntimeError):
                self.cache.translate("Follow me!", "madlad", "v1", translator)
        self.assertEqual(translator.call_count, 2)
        with self.assertRaises(ValueError):
            self.cache.translate("Follow me!", "madlad", "v1", lambda _: self.result("google"))

    def test_duplicate_inflight_and_nonblocking_hit(self):
        started, release = threading.Event(), threading.Event()
        self.cache.translate("Cached.", "madlad", "v1", lambda _: self.result())

        def slow(text):
            started.set()
            if not release.wait(3):
                raise RuntimeError("test timeout")
            return self.result()

        translator = Mock(side_effect=slow)
        with ThreadPoolExecutor(max_workers=3) as pool:
            first = pool.submit(self.cache.translate, "New.", "madlad", "v1", translator)
            self.assertTrue(started.wait(2))
            second = pool.submit(self.cache.translate, "New.", "madlad", "v1", translator)
            try:
                hit = pool.submit(self.cache.translate, "Cached.", "madlad", "v1", translator)
                self.assertTrue(hit.result(timeout=1)["cache_hit"])
            finally:
                release.set()
            self.assertFalse(first.result()["cache_hit"])
            self.assertTrue(second.result()["cache_hit"])
        translator.assert_called_once_with("New.")


if __name__ == "__main__":
    unittest.main()
