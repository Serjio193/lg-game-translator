"""Keep captured control icons out of translation providers."""

import re
import time

MARKER = "[button]"


def translate_preserving_icons(text, translate):
    """Keep sentence context for final translation; validate every icon slot."""
    if MARKER not in text:
        return translate(text)
    started = time.perf_counter()
    prefix = "ZXICON"
    while prefix in text:
        prefix += "X"
    parts = text.split(MARKER)
    markers = [f"{prefix}{index}XZ" for index in range(len(parts) - 1)]
    masked = parts[0]
    for marker, part in zip(markers, parts[1:]):
        masked += marker + part
    result = translate(masked)
    output = result["translation"]
    valid = all(output.count(marker) == 1 for marker in markers)
    if valid:
        positions = [output.index(marker) for marker in markers]
        valid = positions == sorted(positions)
    for marker in markers:
        output = output.replace(marker, MARKER)
    valid = valid and prefix not in output and output.count(MARKER) == len(markers)
    if valid:
        result = {**result, "translation": output, "icon_strategy": "markers"}
    else:
        result = {**translate_around_icons(text, translate), "icon_strategy": "split_fallback"}
    result["latency_ms"] = round((time.perf_counter() - started) * 1000, 1)
    return result


def translate_around_icons(text, translate):
    if MARKER not in text:
        return translate(text)
    started = time.perf_counter()
    output = []
    result = {}
    tokens = 0
    sentences = 0
    for part in re.split(r"(\[button\])", text):
        part = part.strip()
        if not part:
            continue
        if part == MARKER or not any(char.isalpha() for char in part):
            output.append(part)
            continue
        translated = translate(part)
        output.append(translated["translation"])
        tokens += translated.get("generated_tokens", 0)
        sentences += translated.get("sentence_count", 1)
        result.update(translated)
    result["translation"] = re.sub(r"\s+([.,!?;:])", r"\1", " ".join(output))
    result["latency_ms"] = round((time.perf_counter() - started) * 1000, 1)
    result["generated_tokens"] = tokens
    result["sentence_count"] = sentences
    return result
