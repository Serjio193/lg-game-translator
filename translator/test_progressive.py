import threading
import unittest
from unittest.mock import Mock, patch
from progressive import results


class ProgressiveTests(unittest.TestCase):
    def test_cache_hit_never_starts_models(self):
        final, preview = Mock(), Mock()
        events = list(results("Hello", lambda: {"provider": "madlad", "translation": "Привет"},
                              final, preview))
        self.assertEqual([event["stage"] for event in events], ["final"])
        final.assert_not_called()
        preview.assert_not_called()

    def test_preview_is_uncached_and_final_runs_in_parallel(self):
        started, release = threading.Event(), threading.Event()
        def final():
            started.set()
            self.assertTrue(release.wait(3))
            return {"provider": "madlad", "translation": "Окончательный", "cache_hit": False}
        def preview(text):
            self.assertTrue(started.wait(3))
            return {"provider": "bergamot", "translation": "Предварительный"}
        stream = results("Hello", lambda: None, final, preview)
        first = next(stream)
        self.assertEqual(first["stage"], "preliminary")
        self.assertEqual(first["engine"], "bergamot")
        self.assertFalse(first["cache_hit"])
        release.set()
        self.assertEqual(next(stream)["stage"], "final")
        with self.assertRaises(StopIteration):
            next(stream)

    def test_failed_preview_does_not_lose_final(self):
        release = threading.Event()
        def failed_preview(text):
            raise RuntimeError("preview unavailable")
        def final():
            self.assertTrue(release.wait(3))
            return {"provider": "madlad", "translation": "Привет"}
        with patch("progressive.LOG.exception", side_effect=lambda *_: release.set()) as logged:
            events = list(results("Hello", lambda: None,
                final, failed_preview))
            logged.assert_called_once()
        self.assertEqual([event["stage"] for event in events], ["final"])

    def test_final_ready_first_skips_late_preview(self):
        completed = threading.Event()
        def final():
            completed.set()
            return {"provider": "madlad", "translation": "Привет"}
        def preview(text):
            self.assertTrue(completed.wait(3))
            # Wait for the submitted final future to have published its result.
            from progressive import _finals
            _finals.submit(lambda: None).result(timeout=3)
            return {"provider": "bergamot", "translation": "Поздний"}
        events = list(results("Hello", lambda: None, final, preview))
        self.assertEqual([event["stage"] for event in events], ["final"])

    def test_final_does_not_wait_for_blocked_preview(self):
        release = threading.Event()
        def preview(text):
            release.wait(3)
            return {"provider": "bergamot", "translation": "Поздний"}
        try:
            stream = results("Hello", lambda: None,
                lambda: {"provider": "madlad", "translation": "Привет"}, preview)
            self.assertEqual(next(stream)["stage"], "final")
            self.assertFalse(release.is_set())
        finally:
            release.set()
