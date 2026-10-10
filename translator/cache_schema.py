"""Transactional migration from the original English/Russian SQLite cache."""
from cache_identity import text_hash

CREATE_TABLE = """CREATE TABLE translations (
    normalization_version INTEGER NOT NULL,
    source_lang TEXT NOT NULL, target_lang TEXT NOT NULL, text_type TEXT NOT NULL,
    provider TEXT NOT NULL, revision TEXT NOT NULL, key_hash BLOB NOT NULL,
    collision_id INTEGER NOT NULL DEFAULT 0,
    normalized_source TEXT NOT NULL, source_text TEXT NOT NULL,
    translation TEXT NOT NULL, result_json TEXT NOT NULL,
    created_at REAL NOT NULL, last_hit_at REAL, hit_count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (normalization_version, source_lang, target_lang, text_type,
                 provider, revision, key_hash, collision_id)
)"""


def initialize(connection):
    connection.execute("BEGIN IMMEDIATE")
    columns = {row[1] for row in connection.execute("PRAGMA table_info(translations)")}
    if not columns:
        connection.execute(CREATE_TABLE)
    elif "key_hash" not in columns:
        connection.execute("ALTER TABLE translations RENAME TO translations_legacy")
        connection.execute(CREATE_TABLE)
        rows = connection.execute("SELECT provider, revision, source_language, target_language,"
            "normalized_source, english_text, russian_text, result_json, created_at,"
            "last_used_at, hits FROM translations_legacy")
        for provider, revision, source, target, normalized, original, translated, result, created, used, hits in rows:
            namespace = (1, source, target, "dialogue", provider, revision, text_hash(normalized))
            collision = connection.execute("SELECT COALESCE(MAX(collision_id)+1, 0) FROM translations "
                "WHERE normalization_version=? AND source_lang=? AND target_lang=? AND text_type=? "
                "AND provider=? AND revision=? AND key_hash=?", namespace).fetchone()[0]
            connection.execute("INSERT INTO translations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (*namespace, collision, normalized, original, translated, result, created, used if hits else None, hits))
        connection.execute("DROP TABLE translations_legacy")
    connection.execute("PRAGMA user_version=2")
