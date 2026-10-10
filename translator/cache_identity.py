"""Versioned Unicode text identity shared by cache and HTTP validation."""
import hashlib
import re
import unicodedata

NORMALIZATION_VERSION = 1
TEXT_TYPES = {"dialogue", "description", "heading", "menu"}


def normalize(text, version=NORMALIZATION_VERSION):
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Text must be a nonempty string")
    if type(version) is not int or version not in (1, 2):
        raise ValueError("Unsupported normalization_version")
    if version == 2:
        text = unicodedata.normalize("NFC", text)
    return " ".join(text.split())  # Preserve case, punctuation and CJK characters.


def text_hash(normalized):
    return hashlib.sha256(normalized.encode("utf-8")).digest()


def language(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-z]{2,3}(?:-[A-Za-z]{2,8})?", value):
        raise ValueError("Invalid language code")
    return value


def identity(text, provider, revision, source_lang, target_lang, text_type, version, expected_hash=None):
    normalized = normalize(text, version)
    if not isinstance(text_type, str) or text_type not in TEXT_TYPES:
        raise ValueError("Unsupported text_type")
    if not isinstance(provider, str) or not provider or not isinstance(revision, str) or not revision:
        raise ValueError("Provider and model revision are required")
    digest = text_hash(normalized)
    if expected_hash is not None and (not isinstance(expected_hash, str) or expected_hash != digest.hex()):
        raise ValueError("Hash does not match normalized source text")
    return (version, language(source_lang), language(target_lang), text_type,
            provider, revision, digest), normalized
