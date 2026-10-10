"""Conservative English sentence boundaries for independent MADLAD inputs."""

import re

_END = re.compile(r'[.!?]+["\'’”)]*(?=\s|$)')
_ABBREVIATIONS = {
    "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st", "vs", "etc",
    "e.g", "i.e", "no", "fig",
}


def completed_sentences(text: str) -> tuple[list[str], str]:
    parts = []
    start = 0
    for match in _END.finditer(text):
        ending = match.group().rstrip('"\'’”)')
        if ending == ".":
            previous = text[:match.start()].split()
            token = previous[-1].lower() if previous else ""
            # Titles, initials, dotted abbreviations and decimal points are
            # part of their sentence, not independent translation units.
            if token in _ABBREVIATIONS or re.fullmatch(r"(?:[a-z]\.)*[a-z]", token):
                continue
            next_text = text[match.end():].lstrip(' \t\r\n"\'‘“(')
            if next_text and next_text[0].islower():
                continue
        if "..." in ending:
            continue  # A pause can join two clauses of the same thought.
        part = text[start:match.end()].strip()
        if part:
            parts.append(part)
        start = match.end()
    remainder = text[start:].strip()
    return parts, remainder


def split_sentences(text: str) -> list[str]:
    parts, remainder = completed_sentences(text)
    return parts + ([remainder] if remainder else [])
