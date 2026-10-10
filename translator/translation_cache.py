"""Persistent multilingual, provider/version-isolated translation cache."""
import json
import sqlite3
import threading
import time
from concurrent.futures import Future
from contextlib import closing
from pathlib import Path
from cache_identity import NORMALIZATION_VERSION, identity
from cache_schema import initialize

KEY_WHERE = ("normalization_version=? AND source_lang=? AND target_lang=? AND text_type=? "
             "AND provider=? AND revision=? AND key_hash=?")


class TranslationCache:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.pending = {}
        with closing(self.connect()) as connection, connection:
            connection.execute("PRAGMA journal_mode=WAL")
            initialize(connection)

    def connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def translate(self, text, provider, revision, translator, *, source_lang="en",
                  target_lang="ru", text_type="dialogue",
                  normalization_version=NORMALIZATION_VERSION, expected_hash=None):
        key, normalized = identity(text, provider, revision, source_lang, target_lang,
                                   text_type, normalization_version, expected_hash)
        started = time.perf_counter()
        result = self.lookup(key, normalized, started)
        if result is None:
            pending_key = (*key, normalized)
            with self.lock:
                pending = self.pending.get(pending_key)
                owner = pending is None
                if owner:
                    pending = Future()
                    self.pending[pending_key] = pending
            if not owner:
                shared = pending.result()
                result = {**(self.lookup(key, normalized, started) or shared),
                          "cache_hit": True, "coalesced": True}
            else:
                try:
                    result = self.lookup(key, normalized, started)
                    if result is None:
                        result = self.generate(text, provider, translator, key, normalized)
                    pending.set_result(result)
                except BaseException as error:
                    pending.set_exception(error)
                    raise
                finally:
                    with self.lock:
                        self.pending.pop(pending_key, None)
        return {**result, "key_hash": key[-1].hex(), "normalization_version": key[0],
                "source_lang": source_lang, "target_lang": target_lang, "text_type": text_type,
                "model_version": revision}

    def generate(self, text, provider, translator, key, normalized):
        result = translator(normalized)
        if (result.get("provider") != provider
                or not isinstance(result.get("translation"), str)
                or not result["translation"].strip()):
            raise ValueError("Cannot cache an invalid provider result")
        now = time.time()
        with closing(self.connect()) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            collision = connection.execute(
                "SELECT COALESCE(MAX(collision_id)+1, 0) FROM translations WHERE " + KEY_WHERE,
                key).fetchone()[0]
            connection.execute("INSERT INTO translations VALUES "
                "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, 0)",
                (*key, collision, normalized, text, result["translation"],
                 json.dumps(result, ensure_ascii=False), now))
        return {**result, "cache_hit": False}

    def lookup(self, key, normalized, started):
        with closing(self.connect()) as connection, connection:
            rows = connection.execute("SELECT collision_id, normalized_source, result_json "
                "FROM translations WHERE " + KEY_WHERE, key)
            for collision, original, payload in rows:
                if original != normalized:
                    continue
                result = json.loads(payload)
                connection.execute("UPDATE translations SET hit_count=hit_count+1, last_hit_at=? "
                    "WHERE " + KEY_WHERE + " AND collision_id=?", (time.time(), *key, collision))
                result["original_latency_ms"] = result.get("latency_ms")
                result["latency_ms"] = round((time.perf_counter() - started) * 1000, 1)
                result["cache_hit"] = True
                return result
        return None
