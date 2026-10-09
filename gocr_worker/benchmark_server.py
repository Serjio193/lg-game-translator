"""OCR-only replay servers. Translation is explicitly marked unmeasured."""
import argparse
from pathlib import Path
from .crop_client import CropClient
from .frame_pipeline import FramePipeline
from .http_security import read_token
from .tv_server import FrameServer


class UnmeasuredTranslation:
    def translate(self, text):
        return {"translation": None, "request_ms": 0.0, "bytes_sent": 0,
                "latency_ms": 0.0, "measured": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", required=True, type=Path)
    parser.add_argument("--mode", required=True, choices=("TV_CROP", "TV_FULL"))
    parser.add_argument("--socket", required=True)
    parser.add_argument("--recognizer")
    parser.add_argument("--token-file", type=Path)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--detector-threads",type=int,choices=range(1,5))
    parser.add_argument("--recognizer-threads",type=int,choices=range(1,5),help="TV_FULL only")
    args = parser.parse_args()
    peer = CropClient(args.recognizer, read_token(args.token_file), translate=False) if args.mode == "TV_CROP" else None
    pipeline = FramePipeline(args.assets, args.mode, args.threads,
                             crop_client=peer,translator=UnmeasuredTranslation(),
                             detector_threads=args.detector_threads,recognizer_threads=args.recognizer_threads)
    with FrameServer(args.socket, pipeline) as server:
        try:
            server.serve_forever()
        finally:
            Path(args.socket).unlink(missing_ok=True)


if __name__ == "__main__":
    main()
