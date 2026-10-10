import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from contextlib import closing
from unittest.mock import Mock, patch

from cache_identity import identity, normalize
from translation_cache import KEY_WHERE, TranslationCache


LEGACY_SCHEMA = """CREATE TABLE translations (
    provider TEXT, revision TEXT, source_language TEXT, target_language TEXT,
    normalized_source TEXT, english_text TEXT, russian_text TEXT, result_json TEXT,
    created_at REAL, last_used_at REAL, hits INTEGER,
    PRIMARY KEY(provider, revision, source_language, target_language, normalized_source))"""


class IdentityTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "cache.sqlite3"
        self.translate = Mock(return_value={"provider": "madlad", "translation": "Где мы?", "latency_ms": 9})

    def test_languages_types_and_unicode_normalization_are_isolated(self):
        cache = TranslationCache(self.path)
        for language in ("en", "ja", "zh"):
            for kind in ("dialogue", "description", "heading", "menu"):
                first = cache.translate("共通", "madlad", "v1", self.translate,
                    source_lang=language, text_type=kind)
                second = cache.translate("共通", "madlad", "v1", self.translate,
                    source_lang=language, text_type=kind)
                self.assertFalse(first["cache_hit"])
                self.assertTrue(second["cache_hit"])
        self.assertEqual(self.translate.call_count, 12)
        cache.translate("e\u0301", "madlad", "v1", self.translate, normalization_version=2)
        self.assertTrue(cache.translate("é", "madlad", "v1", self.translate,
            normalization_version=2)["cache_hit"])
        self.assertFalse(cache.translate("é", "madlad", "v1", self.translate)["cache_hit"])
        for text, language in (("ここはどこですか？", "ja"), ("我们在哪里？", "zh")):
            result = cache.translate(text, "madlad", "v1", self.translate, source_lang=language)
            self.assertEqual(result["key_hash"], hashlib.sha256(text.encode("utf-8")).hexdigest())
        self.assertNotEqual(normalize("Ａ"), normalize("A"))
        self.assertNotEqual(normalize("Where?"), normalize("where"))

    def test_hash_validation_before_translation(self):
        cache = TranslationCache(self.path)
        with self.assertRaises(ValueError):
            cache.translate("Hello", "madlad", "v1", self.translate, expected_hash="0" * 64)
        self.translate.assert_not_called()
        for version in (True, 0, 3, "1"):
            with self.assertRaises(ValueError):
                identity("Hello", "madlad", "v1", "en", "ru", "dialogue", version)

    def test_collision_compares_normalized_text_and_uses_index(self):
        cache = TranslationCache(self.path)
        self.translate.side_effect = lambda text: {"provider": "madlad", "translation": "translated " + text}
        with patch("cache_identity.text_hash", return_value=b"x" * 32):
            for text in ("First", "Second"):
                self.assertFalse(cache.translate(text, "madlad", "v1", self.translate)["cache_hit"])
            for text in ("First", "Second"):
                hit = cache.translate(text, "madlad", "v1", self.translate)
                self.assertTrue(hit["cache_hit"])
                self.assertEqual(hit["translation"], "translated " + text)
            key, _ = identity("First", "madlad", "v1", "en", "ru", "dialogue", 1)
        self.assertEqual(self.translate.call_count, 2)
        with closing(sqlite3.connect(self.path)) as connection, connection:
            rows = connection.execute("SELECT normalized_source, hit_count, last_hit_at FROM translations").fetchall()
            plan = connection.execute("EXPLAIN QUERY PLAN SELECT normalized_source FROM translations WHERE "
                + KEY_WHERE, key).fetchall()
        self.assertEqual({row[0] for row in rows}, {"First", "Second"})
        self.assertTrue(all(row[1] == 1 and row[2] is not None for row in rows))
        self.assertIn("SEARCH translations USING INDEX", str(plan))

    def legacy(self):
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute(LEGACY_SCHEMA)
            connection.execute("INSERT INTO translations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("madlad", "v1", "en", "ru", "Hello", " Hello ", "Привет",
                 json.dumps({"provider": "madlad", "translation": "Привет", "latency_ms": 10}), 100, 200, 7))

    def test_migration_preserves_original_stats_and_cache_hit(self):
        self.legacy()
        cache = TranslationCache(self.path)
        with closing(sqlite3.connect(self.path)) as connection, connection:
            row = connection.execute("SELECT source_text, translation, created_at, last_hit_at, hit_count "
                "FROM translations").fetchone()
        self.assertEqual(row, (" Hello ", "Привет", 100, 200, 7))
        self.assertTrue(cache.translate("Hello", "madlad", "v1", self.translate)["cache_hit"])
        self.translate.assert_not_called()
        with closing(sqlite3.connect(self.path)) as connection, connection:
            self.assertEqual(connection.execute("SELECT hit_count FROM translations").fetchone()[0], 8)

    def test_failed_migration_rolls_back(self):
        self.legacy()
        with patch("cache_schema.text_hash", side_effect=RuntimeError("migration interrupted")):
            with self.assertRaises(RuntimeError):
                TranslationCache(self.path)
        with closing(sqlite3.connect(self.path)) as connection, connection:
            self.assertEqual(connection.execute("SELECT english_text, hits FROM translations").fetchone(),
                             (" Hello ", 7))
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
