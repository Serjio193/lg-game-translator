"""Isolated uncached full-reply single/two-worker quality and pair completion gate."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import statistics
import sys
import time

PAIRS = [
    ["Did you pack a toothbrush? Oh, I'm sure you did. Take care now!",
     "Oh, caring for the Uni-Tree is my job."],
    ["Check the details of your gear in the menu. Gear can have many useful effects in battle—be sure to equip what you find.",
     "Your items can be used from the menu."],
]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--runtime", type=Path, required=True)
    p.add_argument("--workers", type=int, choices=(1, 2), required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    os.environ["TRANSLATOR_WORKERS"] = str(args.workers)
    sys.path.insert(0, str(args.runtime/"translator"))
    import server
    server._load_local_model()
    report = {"workers": args.workers, "intra_threads": server.THREADS,
              "cache": "bypassed; direct unchanged backend", "pairs": []}
    with ThreadPoolExecutor(max_workers=2) as executor:
        for pair in PAIRS:
            warmup = [server._translate_madlad(text) for text in pair]
            runs = []
            for repeat in range(5):
                start = time.perf_counter()
                jobs = [executor.submit(server._translate_madlad, text) for text in pair]
                results = [job.result() for job in jobs]
                runs.append({"pair_ms": (time.perf_counter()-start)*1000, "results": results})
                assert [r["translation"] for r in results] == [r["translation"] for r in warmup]
            report["pairs"].append({"text": pair, "warmup": warmup, "runs": runs,
                                    "median_pair_ms": statistics.median(r["pair_ms"] for r in runs)})
            args.output.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
            print(args.workers, report["pairs"][-1]["median_pair_ms"], flush=True)


if __name__ == "__main__":
    main()
