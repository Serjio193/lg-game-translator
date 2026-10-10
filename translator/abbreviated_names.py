"""Preserve title-plus-initial names without splitting sentence context."""
import re

PATTERN = re.compile(r"\b(?:Mr|Mrs|Ms|Dr)\.\s*[A-Z](?:\.\s*[A-Z])*\.?(?![A-Za-z])")


def has_abbreviated_names(text):
    return bool(PATTERN.search(text))


def translate_preserving_names(text, translate):
    matches = list(PATTERN.finditer(text))
    if not matches:
        return translate(text)
    prefix = "ZXQ"
    while prefix in text:
        prefix += "X"
    originals = {}

    def substitute(match):
        marker = f"{prefix}{len(originals)}QXZ"
        originals[marker] = match.group()
        return marker

    result = translate(PATTERN.sub(substitute, text))
    output = result["translation"]
    for marker, original in originals.items():
        if output.count(marker) != 1:
            raise RuntimeError("Translation did not preserve an abbreviated-name marker")
        output = output.replace(marker, original)
    return {**result, "translation": output}
