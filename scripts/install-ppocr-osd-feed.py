"""Select the PP-OCR feed in an existing watcher; preserve its queue/rendering."""
import argparse
from pathlib import Path


def install(path):
    text = path.read_text(encoding="utf-8")
    if "ppocrFullFeed" in text:
        return
    if ("function readResponses(" not in text
            or "/tmp/piccap-translation-admission.json" not in text):
        raise ValueError("Unsupported existing OSD watcher")
    helper = ("function ppocrFullFeed() {\n"
              "  return fs.existsSync('/media/developer/ppocr-full-osd.enabled');\n"
              "}\n\n")
    for quote in ("'", '"'):
        text = text.replace(quote + "/tmp/piccap-translation-slot-" + quote,
                            "(ppocrFullFeed() ? '/tmp/ppocr-full-osd-slot-' : '/tmp/piccap-translation-slot-')")
        text = text.replace(quote + "/tmp/piccap-translation-admission.json" + quote,
                            "(ppocrFullFeed() ? '/tmp/ppocr-full-osd-admission.json' : '/tmp/piccap-translation-admission.json')")
    text += "\n" + helper
    backup = path.with_name(path.name + ".before-ppocr-full")
    if not backup.exists():
        backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("watcher", type=Path)
    install(parser.parse_args().watcher)
