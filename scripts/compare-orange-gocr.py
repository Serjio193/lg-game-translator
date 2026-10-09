"""Compare isolated Orange results to a saved TV reference, not ground truth."""
import argparse
import gzip
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gocr_worker.profile_comparison import compare_lines


def load(path):
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("reports", type=Path, nargs="+")
    args = parser.parse_args()
    reference = {Path(row["frame"]).stem: row for row in load(args.reference)["runs"]}
    output = {"scope": "different architectures/runtimes; no numerical parity claim",
              "reference": str(args.reference), "profiles": []}
    for path in args.reports:
        report = load(path)
        rows = []
        for frame in report["frames"]:
            baseline = reference[Path(frame["frame"]).stem]
            comparison = compare_lines(baseline["samples"][0]["identity"],
                                       frame["samples"][0]["lines"])
            comparison.update(frame=frame["frame"],
                              orange_timings=frame["summary"],
                              repeat_identity=frame["repeat_identity"],
                              tv_medians={key: statistics.median(
                                  r["timings_ms"][key] for r in baseline["samples"])
                                  for key in baseline["samples"][0]["timings_ms"]})
            rows.append(comparison)
        profile = {"report": path.name, "runtime": report["runtime"],
                   "delegate": report["delegate"],
                   "detector_threads": report["detector_threads"],
                   "recognizer_threads": report["recognizer_threads"],
                   "initialization_ms": report["initialization_ms"], "frames": rows,
                   "matched": sum(r["matched"] for r in rows),
                   "exact_text_matches": sum(r["exact_text_matches"] for r in rows),
                   "character_distance": sum(r["character_distance"] for r in rows),
                   "missing": sum(len(r["missing_strict_indices"]) for r in rows),
                   "extra": sum(len(r["extra_fast_indices"]) for r in rows),
                   "corpus_medians_ms": {key: statistics.median(
                       r["orange_timings"][key]["median"] for r in rows)
                       for key in rows[0]["orange_timings"]}}
        output["profiles"].append(profile)
        print(json.dumps({k: v for k, v in profile.items() if k != "frames"}))
        for row in rows[-2:]:
            print(row["frame"], row["orange_timings"], "text exact",
                  row["exact_text_matches"], "/", row["matched"])
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
