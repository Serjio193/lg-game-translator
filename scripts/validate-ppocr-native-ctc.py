"""Adversarial exact semantics: ties, blanks, repeats, nonfinite and Unicode."""
import argparse
from pathlib import Path
import sys
import numpy as np
from ppocr_native_ctc import NativeCtc


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--library", required=True)
    p.add_argument("--runtime", type=Path, required=True)
    args = p.parse_args()
    sys.path[:0] = [str(args.runtime), str(args.runtime/"assets")]
    from ocr.ppocr_codec import decode
    native = NativeCtc(args.library)
    characters = ["", "A", "Б", "日", "中"]
    generator = np.random.default_rng(12345)
    count = 0
    for steps in (1, 2, 7, 40, 160, 640):
        for _ in range(10):
            scores = generator.random((len(characters), steps), dtype=np.float32)
            assert native.decode(scores, characters) == decode(scores, characters, "class-major")
            count += 1
    for ids in ([1, 1, 0, 1, 2, 2, 0, 2], [0]*8, [4, 3, 2, 1, 0]):
        scores = np.zeros((len(characters), len(ids)), dtype=np.float32)
        for t, token in enumerate(ids):
            scores[token, t] = 1.0001
        assert native.decode(scores, characters) == decode(scores, characters, "class-major")
        count += 1
    for fill in (0, -.5):
        scores = np.full((len(characters), 7), fill, dtype=np.float32)
        assert native.decode(scores, characters) == decode(scores, characters, "class-major")
        count += 1
    scores = np.zeros((len(characters), 7), dtype=np.float32)
    scores[1:3, :] = .9
    assert native.decode(scores, characters) == ("A", float(np.float32(.9)))
    for invalid in (np.nan, np.inf, -np.inf):
        scores[4, 0] = invalid  # Losing class must still cause rejection.
        for decoder in (native.decode, lambda s, c: decode(s, c, "class-major")):
            try:
                decoder(scores, characters)
            except RuntimeError:
                pass
            else:
                raise AssertionError("Nonfinite output accepted")
    print("PASS:", count+1, "exact cases and six nonfinite rejection checks")


if __name__ == "__main__":
    main()
