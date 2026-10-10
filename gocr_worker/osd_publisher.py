"""Bridge completed PP-OCR responses to the existing OSD admission queue."""
import json
from pathlib import Path
import time
import unicodedata


def normalized(text):
    return " ".join(unicodedata.normalize("NFC", text).casefold().split())


def overlap(a, b):
    w = max(0, min(a["x"]+a["width"], b["x"]+b["width"]) - max(a["x"], b["x"]))
    h = max(0, min(a["y"]+a["height"], b["y"]+b["height"]) - max(a["y"], b["y"]))
    area = w*h
    union = a["width"]*a["height"] + b["width"]*b["height"] - area
    return area/union if union else 0


def atomic(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    temporary.chmod(0o600)
    temporary.replace(path)


class OsdPublisher:
    def __init__(self, root=Path("/tmp"), clock=None):
        self.root = Path(root)
        self.clock = clock or (lambda: int(time.time()*1000))
        self.tracks, self.next_id, self.sequence = [], 1, None
        self.source = None

    def publish(self, result):
        if result.get("engine") != "ppocr":
            return
        source = tuple(result.get("source_session", ()))
        if source and source != self.source:
            self.tracks, self.sequence, self.source = [], None, source
        if result.get("sequence") == self.sequence:
            return
        now = self.clock()
        entries, tracks, used = [], [], set()
        for line in result.get("lines", []):
            text, appearance = line.get("text", ""), line.get("appearance")
            response = line.get("translation", {})
            if (line.get("translation_allowed") is not True
                    or not appearance or not response.get("translation")):
                continue
            box, key = appearance["box"], normalized(text)
            candidates = [(overlap(box, t["box"]), i, t) for i, t in enumerate(self.tracks)
                          if i not in used and t["text"] == key]
            score, index, prior = max(candidates, default=(0, -1, None), key=lambda r: r[0])
            if score >= .5:
                used.add(index)
                track = {**prior, "count": min(3, prior["count"]+1)}
                appearance = prior["appearance"]
            else:
                track = {"id": self.next_id, "version": now, "count": 1,
                         "text": key, "box": box, "appearance": appearance}
                self.next_id += 1
            slot = len(entries)
            if slot >= 20:
                break
            admission = {"track_id": track["id"], "version_ms": track["version"],
                         "text": key, "observations": track["count"]}
            entries.append({"slot": slot, "admission": admission, "observations": track["count"],
                            "source_text": text, "appearance": appearance})
            atomic(self.root / f"ppocr-full-osd-slot-{slot:02}.json",
                   {**response, "stage": "final", "provider": response.get("provider", "madlad"),
                    "admission": admission})
            tracks.append(track)
        atomic(self.root / "ppocr-full-osd-admission.json",
               {"timestamp_ms": now, "sequence": result["sequence"], "complete": True,
                "required": 3, "regions": entries})
        self.tracks, self.sequence = tracks, result["sequence"]
