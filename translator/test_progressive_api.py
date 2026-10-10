import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch
from urllib.request import Request, urlopen
import server


class ProgressiveApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.thread.join()

    def request(self):
        return Request(f"http://127.0.0.1:{self.http.server_port}/api/translate",
            json.dumps({"text": "Hello friends!", "provider": "madlad", "progressive": True}).encode(),
            {"Content-Type": "application/json"})

    def test_preview_is_flushed_before_final_and_only_final_uses_cache(self):
        release = threading.Event()
        def final(*args, **kwargs):
            if not release.wait(3):
                raise RuntimeError("Final was not released")
            return {"provider": "madlad", "translation": "Здравствуйте, друзья!"}
        with patch.object(server, "_lookup_madlad", return_value=None), \
                patch.object(server, "_cached_translate", side_effect=final) as cache, \
                patch.object(server, "_preview", return_value={"provider": "bergamot",
                    "translation": "Привет, друзья!"}):
            try:
                with urlopen(self.request(), timeout=3) as response:
                    first = json.loads(response.readline())
                    self.assertEqual(first["stage"], "preliminary")
                    self.assertEqual(first["engine"], "bergamot")
                    self.assertFalse(release.is_set())
                    release.set()
                    self.assertEqual(json.loads(response.readline())["stage"], "final")
                    self.assertEqual(response.read(), b"")
                self.assertEqual(cache.call_count, 1)
                self.assertEqual(cache.call_args.args[1], "madlad")
            finally:
                release.set()

    def test_cache_hit_sends_one_final_and_skips_preview(self):
        with patch.object(server, "_lookup_madlad", return_value={"provider": "madlad",
                "translation": "Привет", "cache_hit": True}), \
                patch.object(server, "_preview") as preview, \
                patch.object(server, "_cached_translate") as final:
            with urlopen(self.request(), timeout=3) as response:
                events = [json.loads(line) for line in response]
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["stage"], "final")
            preview.assert_not_called()
            final.assert_not_called()
