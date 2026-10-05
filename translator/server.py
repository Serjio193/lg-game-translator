#!/usr/bin/env python3
"""LAN translation API for the LG Game Translator prototype."""

from __future__ import annotations

import importlib.util
import json
import logging
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


LOG = logging.getLogger("lg-game-translator")
MODEL_PATH = Path(os.environ.get(
    "TRANSLATOR_MODEL", "/home/orangepi/translator-test/madlad3b"
))
UI_PATH = Path(os.environ.get(
    "TRANSLATOR_UI", str(Path(__file__).resolve().parent.parent / "packaging/index.html")
))
THREADS = max(1, int(os.environ.get("TRANSLATOR_THREADS", "4")))
MAX_BODY_BYTES = 64 * 1024
MAX_TEXT_CHARS = 4000

_model_lock = threading.Lock()
_model = None
_tokenizer = None
_model_load_ms = None


def _json_bytes(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False).encode("utf-8")


def _load_local_model():
    global _model, _tokenizer, _model_load_ms
    if _model is not None:
        return
    with _model_lock:
        if _model is not None:
            return
        import ctranslate2
        from tokenizers import Tokenizer

        started = time.perf_counter()
        tokenizer_path = MODEL_PATH / "tokenizer.json"
        if not (MODEL_PATH / "model.bin").is_file() or not tokenizer_path.is_file():
            raise FileNotFoundError("MADLAD model or tokenizer files are missing")
        tokenizer = Tokenizer.from_file(str(tokenizer_path))
        model = ctranslate2.Translator(
            str(MODEL_PATH), device="cpu", inter_threads=1, intra_threads=THREADS
        )
        _model_load_ms = round((time.perf_counter() - started) * 1000, 1)
        _tokenizer = tokenizer
        _model = model
        LOG.info("MADLAD loaded in %.1f ms", _model_load_ms)


def _translate_madlad(text: str) -> dict:
    _load_local_model()
    with _model_lock:
        pieces = _tokenizer.encode(f"<2ru> {text}").tokens
        started = time.perf_counter()
        hypotheses = _model.translate_batch(
            [pieces], beam_size=1, max_decoding_length=128
        )[0].hypotheses[0]
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        token_ids = [_tokenizer.token_to_id(piece) for piece in hypotheses]
        if any(token_id is None for token_id in token_ids):
            raise ValueError("MADLAD returned a token absent from its tokenizer")
        translation = _tokenizer.decode(token_ids, skip_special_tokens=True)
    return {
        "provider": "madlad",
        "translation": translation,
        "latency_ms": latency_ms,
        "generated_tokens": len(hypotheses),
        "model_load_ms": _model_load_ms,
    }


def _translate_google(text: str) -> dict:
    key = os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("Google provider is not configured on Orange Pi")
    body = _json_bytes({"q": text, "source": "en", "target": "ru", "format": "text"})
    request = Request(
        "https://translation.googleapis.com/language/translate/v2",
        data=body,
        headers={
            "X-goog-api-key": key,
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        detail = error.read(2048).decode("utf-8", errors="replace")
        raise RuntimeError(f"Google API returned HTTP {error.code}: {detail}") from None
    except URLError as error:
        raise RuntimeError(f"Google API connection failed: {error.reason}") from None
    translations = payload.get("data", {}).get("translations", [])
    if not translations or not translations[0].get("translatedText"):
        raise RuntimeError("Google API returned no translation")
    return {
        "provider": "google",
        "translation": translations[0]["translatedText"],
        "latency_ms": round((time.perf_counter() - started) * 1000, 1),
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "LGGameTranslator/0.1"

    def _headers(self, content_type: str):
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-store")

    def _send_json(self, status: int, value: dict):
        data = _json_bytes(value)
        self.send_response(status)
        self._headers("application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(204)
        self._headers("application/json")
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/health":
            self._send_json(200, {"status": "ok"})
            return
        if self.path == "/api/status":
            self._send_json(200, {
                "madlad": {
                    "available": (MODEL_PATH / "model.bin").is_file()
                    and importlib.util.find_spec("ctranslate2") is not None
                    and importlib.util.find_spec("tokenizers") is not None,
                    "loaded": _model is not None,
                },
                "google": {"available": bool(os.environ.get("GOOGLE_API_KEY"))},
            })
            return
        if self.path in ("/", "/index.html"):
            try:
                data = UI_PATH.read_bytes()
            except OSError:
                self._send_json(404, {"error": "UI file not found"})
                return
            self.send_response(200)
            self._headers("text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        if self.path != "/api/translate":
            self._send_json(404, {"error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_BODY_BYTES:
                self._send_json(413, {"error": "Request body must be 1–65536 bytes"})
                return
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            text = data.get("text")
            provider = data.get("provider")
            if not isinstance(text, str) or not text.strip() or len(text) > MAX_TEXT_CHARS:
                self._send_json(400, {"error": "Text must contain 1–4000 characters"})
                return
            if provider == "madlad":
                result = _translate_madlad(text.strip())
            elif provider == "google":
                result = _translate_google(text.strip())
            else:
                self._send_json(400, {"error": "Provider must be madlad or google"})
                return
            self._send_json(200, result)
        except RuntimeError as error:
            self._send_json(503, {"error": str(error)})
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError) as error:
            self._send_json(400, {"error": f"Invalid request: {error}"})
        except Exception as error:
            LOG.exception("Translation request failed")
            self._send_json(500, {"error": f"Translation failed: {type(error).__name__}"})

    def log_message(self, format_string, *args):
        LOG.info("%s %s", self.address_string(), format_string % args)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    host = os.environ.get("TRANSLATOR_BIND", "127.0.0.1")
    port = int(os.environ.get("TRANSLATOR_PORT", "8765"))
    server = ThreadingHTTPServer((host, port), Handler)
    LOG.info("Listening on %s:%s; model path: %s", host, port, MODEL_PATH)
    server.serve_forever()


if __name__ == "__main__":
    main()
