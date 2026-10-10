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
from sentences import split_sentences
from translation_cache import TranslationCache
from translation_settings import read_settings, save_settings
from control_icons import translate_around_icons, translate_preserving_icons
from cache_identity import identity, NORMALIZATION_VERSION
from abbreviated_names import has_abbreviated_names, translate_preserving_names
from progressive import results as progressive_results
from bergamot import translate as translate_bergamot


LOG = logging.getLogger("lg-game-translator")
MODEL_PATH = Path(os.environ.get(
    "TRANSLATOR_MODEL", "/home/orangepi/translator-test/madlad3b"
))
THREADS = max(1, int(os.environ.get("TRANSLATOR_THREADS", "4")))
MODEL_WORKERS = max(1, min(2, int(os.environ.get("TRANSLATOR_WORKERS", "1"))))
_inference_slots = threading.BoundedSemaphore(MODEL_WORKERS)
MAX_BODY_BYTES = 64 * 1024
MAX_TEXT_CHARS = 4000

_model_lock = threading.Lock()
_model = None
_tokenizer = None
_model_load_ms = None
_cache = None
_cache_lock = threading.Lock()


def _cache_config(text: str, provider: str, metadata):
    global _cache
    with _cache_lock:
        if _cache is None:
            _cache = TranslationCache(os.environ.get("TRANSLATOR_CACHE",
                str(Path.home() / ".local/share/lg-game-translator/translations.sqlite3")))
    if provider == "madlad":
        model = MODEL_PATH / "model.bin"
        tokenizer = MODEL_PATH / "tokenizer.json"
        # Replacement model/tokenizer files invalidate old results; explicit
        # revision also permits intentional invalidation after model changes.
        identity = ":".join(f"{path.stat().st_size}:{path.stat().st_mtime_ns}"
                            for path in (model, tokenizer))
        revision = f"{MODEL_PATH.resolve()}:{identity}:sentence-batch-v1:beam1:max128"
        revision += ":" + os.environ.get("TRANSLATOR_MODEL_REVISION", "default")
        translator = _translate_madlad
    else:
        revision = "google-nmt-v2:whole-reply-v1"
        translator = lambda source: _translate_google(source,
            metadata.get("source_lang", "en"), metadata.get("target_lang", "ru"))
    if "[button]" in text:
        revision += (":preserved-control-icons-markers-v2" if provider == "madlad"
                     else ":preserved-control-icons-v1")
    if has_abbreviated_names(text):
        revision += ":abbreviated-names-v1"
    return revision, translator


def _cached_translate(text: str, provider: str, **metadata) -> dict:
    revision, translator = _cache_config(text, provider, metadata)
    icons = translate_preserving_icons if provider == "madlad" else translate_around_icons
    return _cache.translate(text, provider, revision,
        lambda source: icons(source,
            lambda part: translate_preserving_names(part, translator)), **metadata)


def _lookup_madlad(text, metadata):
    revision, _ = _cache_config(text, "madlad", metadata)
    key, normalized = identity(text, "madlad", revision, metadata["source_lang"],
        metadata["target_lang"], metadata["text_type"], metadata["normalization_version"],
        metadata["expected_hash"])
    return _cache.lookup(key, normalized, time.perf_counter())


def _preview(text):
    return translate_around_icons(text,
        lambda part: translate_preserving_names(part, translate_bergamot))


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
            str(MODEL_PATH), device="cpu", inter_threads=MODEL_WORKERS, intra_threads=THREADS
        )
        _model_load_ms = round((time.perf_counter() - started) * 1000, 1)
        _tokenizer = tokenizer
        _model = model
        LOG.info("MADLAD loaded in %.1f ms", _model_load_ms)


def _translate_madlad(text: str) -> dict:
    _load_local_model()
    with _inference_slots:
        sentences = split_sentences(text)
        pieces = [_tokenizer.encode(f"<2ru> {sentence}").tokens for sentence in sentences]
        started = time.perf_counter()
        results = _model.translate_batch(pieces, beam_size=1, max_decoding_length=128)
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        translations = []
        generated_tokens = 0
        if len(results) != len(sentences):
            raise ValueError("MADLAD returned an incomplete sentence batch")
        for result in results:
            hypotheses = result.hypotheses[0]
            token_ids = [_tokenizer.token_to_id(piece) for piece in hypotheses]
            if any(token_id is None for token_id in token_ids):
                raise ValueError("MADLAD returned a token absent from its tokenizer")
            translated = _tokenizer.decode(token_ids, skip_special_tokens=True).strip()
            if not translated:
                raise ValueError("MADLAD returned an empty sentence")
            translations.append(translated)
            generated_tokens += len(hypotheses)
        translation = " ".join(translations)
    return {
        "provider": "madlad",
        "translation": translation,
        "latency_ms": latency_ms,
        "generated_tokens": generated_tokens,
        "sentence_count": len(sentences),
        "model_load_ms": _model_load_ms,
    }


def _translate_google(text: str, source_lang="en", target_lang="ru") -> dict:
    key = os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("Google provider is not configured on Orange Pi")
    body = _json_bytes({"q": text, "source": source_lang, "target": target_lang, "format": "text"})
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
        if self.path == "/api/settings":
            try:
                self._send_json(200, read_settings())
            except (ValueError, OSError):
                self._send_json(503, {"error": "Settings unavailable"})
            return
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
        self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        if self.path not in ("/api/translate", "/api/translate-progressive", "/api/settings"):
            self._send_json(404, {"error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_BODY_BYTES:
                self._send_json(413, {"error": "Request body must be 1–65536 bytes"})
                return
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            if self.path == "/api/settings":
                try:
                    self._send_json(200, save_settings(data))
                except ValueError as error:
                    self._send_json(400, {"error": str(error)})
                return
            text = data.get("text")
            provider = data.get("provider")
            if not isinstance(text, str) or not text.strip() or len(text) > MAX_TEXT_CHARS:
                self._send_json(400, {"error": "Text must contain 1–4000 characters"})
                return
            if provider not in ("madlad", "google"):
                self._send_json(400, {"error": "Provider must be madlad or google"})
                return
            metadata = {"source_lang": data.get("source_lang", "en"),
                "target_lang": data.get("target_lang", "ru"),
                "text_type": data.get("text_type", "dialogue"),
                "normalization_version": data.get("normalization_version", NORMALIZATION_VERSION),
                "expected_hash": data.get("hash")}
            try:
                identity(text, provider, "server-managed", metadata["source_lang"],
                    metadata["target_lang"], metadata["text_type"],
                    metadata["normalization_version"], metadata["expected_hash"])
                if metadata["source_lang"] not in ("en", "ja", "zh") or metadata["target_lang"] != "ru":
                    raise ValueError("Supported language routes: en/ja/zh to ru")
            except ValueError as error:
                self._send_json(400, {"error": str(error)})
                return
            if self.path == "/api/translate-progressive" or data.get("progressive") is True:
                if provider != "madlad" or metadata["source_lang"] != "en":
                    self._send_json(400, {"error": "Progressive route requires English to Russian MADLAD"})
                    return
                self._send_progressive(text, metadata)
                return
            result = _cached_translate(text, provider, **metadata)
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

    def _send_progressive(self, text, metadata):
        stream = progressive_results(text, lambda: _lookup_madlad(text, metadata),
            lambda: _cached_translate(text, "madlad", **metadata), _preview)
        # Resolve the first event before committing HTTP success headers.
        first = next(stream)
        self.send_response(200)
        self._headers("application/x-ndjson; charset=utf-8")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True
        def send(event):
            self.wfile.write(json.dumps(event, ensure_ascii=False,
                separators=(",", ":")).encode("utf-8") + b"\n")
            self.wfile.flush()
        try:
            send(first)
            for event in stream:
                send(event)
        except (BrokenPipeError, ConnectionResetError):
            LOG.info("Progressive client disconnected")
        except Exception:
            LOG.exception("Final progressive translation failed")
            try:
                send({"stage": "error", "error": "Final translation failed"})
            except (BrokenPipeError, ConnectionResetError):
                pass


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    host = os.environ.get("TRANSLATOR_BIND", "127.0.0.1")
    port = int(os.environ.get("TRANSLATOR_PORT", "8765"))
    server = ThreadingHTTPServer((host, port), Handler)
    LOG.info("Listening on %s:%s; model path: %s", host, port, MODEL_PATH)
    server.serve_forever()


if __name__ == "__main__":
    main()
