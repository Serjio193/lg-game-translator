"""Export an inspected frame, detector boxes and OCR results; runs on the PC."""

import argparse
import csv
import json
import pathlib
import shutil

from PIL import Image, ImageDraw


def words(path):
    with path.open(encoding="utf-8") as file:
        return [{"text": row["text"], "confidence": float(row["conf"]),
                 "box": [int(row[k]) for k in ("left", "top", "width", "height")]}
                for row in csv.DictReader(file, delimiter="\t")
                if row["level"] == "5" and row["text"].strip()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=pathlib.Path)
    parser.add_argument("destination", type=pathlib.Path)
    args = parser.parse_args()
    args.destination.mkdir(parents=True, exist_ok=True)
    measurements = json.loads((args.source / "comparison/results.json").read_text())
    results = measurements["results"]
    frame = Image.open(args.source / "input.pgm").convert("RGB")
    frame.save(args.destination / "input.png")
    canvas = Image.new("RGB", (1280, ((len(results) + 1) // 2) * 392), "#202020")
    summary = {"baseline_fps": measurements["baseline_fps"], "cases": [], "ocr": {}}
    for i, result in enumerate(results):
        panel = frame.copy()
        for box in result.get("boxes", []):
            ImageDraw.Draw(panel).rectangle((box["x"], box["y"],
                box["x"] + box["width"], box["y"] + box["height"]), outline="#00ff00", width=3)
        x, y = i % 2 * 640, i // 2 * 392
        canvas.paste(panel.resize((640, 360)), (x, y + 32))
        title = f'{result["backend"]} {result["max_edge"]} | CPU {result.get("mean_cpu_ms", 0):.1f} ms/search'
        ImageDraw.Draw(canvas).text((x + 8, y + 9), title, fill="white")
        fps = result["piccap_fps_samples"]
        summary["cases"].append({"backend": result["backend"], "max_edge": result["max_edge"],
            "mean_cpu_ms": result.get("mean_cpu_ms"), "four_core_cpu_percent": result.get("four_core_cpu_percent"),
            "mean_piccap_fps": sum(fps) / len(fps) if fps else None,
            "candidates": len(result.get("boxes", [])), "aborted": result.get("aborted", False)})
    canvas.save(args.destination / "boxes.png")
    shutil.copyfile(args.source / "comparison/results.json", args.destination / "comparison.json")
    shutil.copyfile(args.source / "comparison/telemetry.jsonl", args.destination / "telemetry.jsonl")
    for path in args.source.glob("*.tsv"):
        shutil.copyfile(path, args.destination / path.name)
        parsed = words(path)
        summary["ocr"][path.name] = {"words": parsed, "text": " ".join(w["text"] for w in parsed)}
    for path in args.source.glob("*.pgm"):
        if path.name != "input.pgm":
            Image.open(path).save(args.destination / (path.stem + ".png"))
    (args.destination / "analysis.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
                                                 encoding="utf-8")
    print(json.dumps(summary["cases"], indent=2))


if __name__ == "__main__":
    main()
