"""Regression checks against the unchanged compiled PicCap policy."""
import argparse
from ppocr_translation_policy import TranslationPolicy


def line(text, box, confidence=95):
    return {"text": text, "appearance": {"box": box}, "recognition_lines": [{
        "text": text, "minimum_confidence": confidence, "average_confidence": confidence,
        "ocr_word_count": 1}]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("library")
    policy = TranslationPolicy(p.parse_args().library)
    body_box = {"x": 690, "y": 450, "width": 520, "height": 100}
    labels = [line(text, {"x": 100, "y": 230+i*50, "width": 350, "height": 40})
              for i, text in enumerate(("Defeating Enemies", "Avoid Game Overs", "Leveling Up",
                                        "Luigi Can Fight Too!", "B Back", "Gear"))]
    description = line("When it's your turn, choose and hit one of the Command blocks.", body_box)
    title = line("Command Blocks", {"x": 780, "y": 44, "width": 340, "height": 48})
    unrelated = line("Snoutlet School", {"x": 28, "y": 16, "width": 320, "height": 48})
    rows = labels + [description, title, unrelated]
    policy.apply(rows)
    assert all(not r["translation_allowed"] for r in labels)
    assert description["translation_allowed"]
    assert title["translation_allowed"]
    assert not unrelated["translation_allowed"]
    short = line("Follow me!", body_box)
    policy.apply([short])
    assert short["translation_allowed"]
    low = line(description["text"], body_box, 40)
    policy.apply([low])
    assert not low["translation_allowed"]
    policy.apply([title])
    assert not title["translation_allowed"], "Heading requires description in same panel"
    item = line("Gear", body_box)
    policy.apply([item], "all")
    assert item["translation_allowed"]
    policy.apply([item])
    assert not item["translation_allowed"], "Normal scope must reject single-word items"
    policy.apply([low], "all")
    assert not low["translation_allowed"], "All scope must preserve OCR quality gate"
    for text in ("[button]", "123", "Русский текст"):
        invalid = line(text, body_box)
        policy.apply([invalid], "all")
        assert not invalid["translation_allowed"], text
    print("PASS: six labels rejected; description and short sentence accepted; panel title gated; low confidence rejected")


if __name__ == "__main__":
    main()
