"""Use the existing PicCap C policy and panel-heading admission rules."""
import ctypes as C
from pathlib import Path


class PolicyResult(C.Structure):
    _fields_ = [("normalized", C.c_char*3001), ("word_count", C.c_int),
                ("line_count", C.c_int), ("length", C.c_size_t)] + [
                    (name, C.c_bool) for name in ("title_case", "all_caps", "period",
                                                "question", "exclamation", "ellipsis",
                                                "sentence_structure")] + [
                    ("score", C.c_int), ("classification", C.c_int),
                    ("reason_count", C.c_int), ("reasons", C.c_char_p*12)]


def same_panel(title, body, height):
    right = min(title["x"]+title["width"], body["x"]+body["width"])
    left = max(title["x"], body["x"])
    smaller = min(title["width"], body["width"])
    return (title["y"] <= height//4 and title["width"] >= title["height"]*2
            and body["y"]-title["y"]-title["height"] >= height*.12
            and right-left >= smaller*.7
            and abs(title["x"]+title["width"]//2-body["x"]-body["width"]//2) <= body["width"]//3)


class TranslationPolicy:
    def __init__(self, library):
        self.lib = C.CDLL(str(Path(library).resolve()))
        self.lib.ocr_policy_classify_evidence.argtypes = [C.c_char_p, C.c_float,
                                                        C.c_bool, C.c_bool, C.POINTER(PolicyResult)]
        self.lib.ocr_policy_classify_evidence.restype = None
        self.lib.ocr_policy_has_english_word.argtypes = [C.c_char_p]
        self.lib.ocr_policy_has_english_word.restype = C.c_bool

    def classify(self, text, minimum, average, word_count):
        result = PolicyResult()
        encoded = text.encode()
        truncated = len(encoded) > 3000
        self.lib.ocr_policy_classify_evidence(encoded, minimum, truncated, False, C.byref(result))
        if (result.classification == 0 and not truncated and minimum >= 60
                and average >= 80 and word_count >= 6):
            self.lib.ocr_policy_classify_evidence(encoded, average, False, False, C.byref(result))
        return result

    def apply(self, lines):
        candidates = []
        for line in lines:
            rows = line.get("recognition_lines", [])
            minimum = min((r.get("minimum_confidence", 0) for r in rows), default=0)
            words = sum(r.get("ocr_word_count", 0) for r in rows)
            average = (sum(r.get("average_confidence", 0)*r.get("ocr_word_count", 0)
                           for r in rows)/words if words else 0)
            policy = self.classify(line["text"], minimum, average, words)
            row_classes = [self.classify(r["text"], r.get("minimum_confidence", 0),
                                       r.get("average_confidence", 0), r.get("ocr_word_count", 0))
                           .classification for r in rows if r["text"]]
            whole = len(row_classes) > 1 and (1 not in row_classes or policy.classification == 2)
            classification = (policy.classification if whole else
                              2 if row_classes and all(c == 2 for c in row_classes) else
                              1 if row_classes and all(c == 1 for c in row_classes) else 0)
            b = line["appearance"]["box"]
            heading = (classification != 2 and minimum >= 80 and len(row_classes) == 1
                       and 1 <= policy.word_count <= 6 and policy.length <= 100
                       and b["y"] <= 720//4
                       and self.lib.ocr_policy_has_english_word(line["text"].encode()))
            line["translation_policy"] = {
                "classification": ("UNCERTAIN", "NON_TRANSLATABLE_LABEL", "TRANSLATABLE_TEXT")[classification],
                "score": policy.score, "minimum_confidence": minimum, "average_confidence": average,
                "heading_candidate": heading,
                "reasons": [policy.reasons[i].decode() for i in range(policy.reason_count)]}
            line["translation_allowed"] = classification == 2
            if classification == 2 or heading:
                candidates.append((line, heading))
        bodies = [line for line, heading in candidates if not heading]
        for line, heading in candidates:
            if heading:
                line["translation_allowed"] = any(same_panel(line["appearance"]["box"],
                                                             body["appearance"]["box"], 720)
                                                  for body in bodies)
                line["translation_policy"]["heading_panel_confirmed"] = line["translation_allowed"]
