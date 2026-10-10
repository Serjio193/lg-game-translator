import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import server
from cache_identity import normalize, text_hash


class CacheApiTests(unittest.TestCase):
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

    def post(self, payload):
        url = f"http://127.0.0.1:{self.http.server_port}/api/translate"
        request = Request(url, json.dumps(payload).encode("utf-8"),
            {"Content-Type": "application/json"})
        try:
            response = urlopen(request, timeout=3)
        except HTTPError as error:
            response = error
        with response:
            return response.status, json.loads(response.read())

    def test_existing_clients_keep_defaults_and_original_text(self):
        with patch.object(server, "_cached_translate", return_value={"translation": "Привет"}) as translate:
            status, _ = self.post({"text": " Hello ", "provider": "madlad"})
        self.assertEqual(status, 200)
        translate.assert_called_once_with(" Hello ", "madlad", source_lang="en",
            target_lang="ru", text_type="dialogue", normalization_version=1, expected_hash=None)

    def test_cjk_hash_and_namespace_forwarded(self):
        for language, text in (("ja", "ここはどこですか？"), ("zh", "我们在哪里？")):
            digest = text_hash(normalize(text, 2)).hex()
            with patch.object(server, "_cached_translate", return_value={"translation": "Где мы?"}) as translate:
                status, _ = self.post({"text": text, "provider": "madlad", "source_lang": language,
                    "text_type": "description", "normalization_version": 2, "hash": digest})
            self.assertEqual(status, 200)
            self.assertEqual(translate.call_args.kwargs["source_lang"], language)
            self.assertEqual(translate.call_args.kwargs["expected_hash"], digest)

    def test_invalid_identity_never_reaches_model(self):
        for extra in ({"hash": "bad"}, {"source_lang": "xx"}, {"target_lang": "ja"},
                      {"text_type": "unknown"}, {"normalization_version": True}):
            with patch.object(server, "_cached_translate") as translate:
                status, _ = self.post({"text": "Hello", "provider": "madlad", **extra})
            self.assertEqual(status, 400)
            translate.assert_not_called()

    def test_google_receives_actual_source_language(self):
        import io
        body = io.BytesIO(b'{"data":{"translations":[{"translatedText":"test"}]}}')
        with patch.dict(server.os.environ, {"GOOGLE_API_KEY": "test-key"}), \
                patch.object(server, "urlopen", return_value=body) as request:
            server._translate_google("你好", "zh", "ru")
        payload = json.loads(request.call_args.args[0].data)
        self.assertEqual(payload["source"], "zh")
        self.assertEqual(payload["target"], "ru")


if __name__ == "__main__":
    unittest.main()
