"""Run native codec round-trip and malformed-input checks on host or TV."""
import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gocr_worker.lz4_block import Lz4Block


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("library")
    args = p.parse_args()
    codec = Lz4Block(args.library, 4096)
    generator = random.Random(12345)
    samples = [bytes(4096), bytes(range(256))*16,
               bytes(generator.randrange(256) for _ in range(4096))]
    for raw in samples:
        for acceleration in (1, 4):
            compressed = codec.compress(raw, acceleration)
            assert codec.decompress(compressed) == raw
    for invalid in (b"", b"\x00", bytes(codec.bound+1)):
        try:
            codec.decompress(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid block accepted")
    for invalid in (b"", bytes(4095), bytes(4097)):
        try:
            codec.compress(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError("Changed input size accepted")
    print("PASS: six exact round trips and six malformed/size checks")


if __name__ == "__main__":
    main()
