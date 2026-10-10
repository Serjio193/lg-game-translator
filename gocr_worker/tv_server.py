"""TV-local consumer of PicCap's selected frames; contains no capture code."""
import argparse
import logging
import os
from pathlib import Path
import socketserver
import stat
import time

from .crop_client import CropClient
from .frame_client import FrameClient
from .frame_pipeline import FramePipeline
from .frame_transport import receive_frame, send_result
from .http_security import read_token
from .translation_client import TranslationClient

LOG = logging.getLogger("gocr-tv")


class FrameServer(socketserver.UnixStreamServer):
    def __init__(self, path, pipeline):
        self.pipeline = pipeline
        self.osd_publisher = None
        self.timeout = 1
        socket_path = Path(path)
        if socket_path.exists():
            existing = socket_path.stat()
            if not stat.S_ISSOCK(existing.st_mode) or existing.st_uid != os.getuid():
                raise ValueError("refusing to replace an unrelated socket path")
            import socket
            with socket.socket(socket.AF_UNIX) as probe:
                if probe.connect_ex(str(socket_path)) == 0:
                    raise ValueError("GOCR frame server is already running")
            socket_path.unlink()
        super().__init__(str(socket_path), FrameHandler)
        os.chmod(socket_path, 0o600)


class FrameHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.request.settimeout(30)
        try:
            image, sequence, captured = receive_frame(self.request)
            accepted_ms = time.monotonic()*1000
            result = self.server.pipeline.process(image, sequence, captured)
            if "relay_to_detector_upper_ms" in result.get("timings_ms", {}):
                from .capture_timing import capture_age_ms
                age, source = capture_age_ms(captured, accepted_ms)
                timing = result["timings_ms"]
                timing["capture_clock_source"] = source
                timing["capture_to_relay_ms"] = age
                if age is not None:
                    timing["capture_to_detector_upper_ms"] = age+timing["relay_to_detector_upper_ms"]
            if self.server.osd_publisher is not None:
                self.server.osd_publisher.publish(result)
        except Exception as error:
            LOG.exception("selected GOCR frame failed")
            result = {"schema": "gocr.worker.error.v1", "error": type(error).__name__}
        send_result(self.request, result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", required=True, type=Path)
    parser.add_argument("--mode", required=True, choices=("TV_CROP", "TV_FULL", "ORANGE_FULL"))
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--detector-threads",type=int,choices=range(1,5))
    parser.add_argument("--recognizer-threads",type=int,choices=range(1,5),help="TV_FULL only")
    parser.add_argument("--socket", default="/tmp/gocr-frame.sock")
    parser.add_argument("--recognizer", help="Orange crop worker base URL (TV_CROP)")
    parser.add_argument("--frame-worker", help="Orange full-frame worker base URL (ORANGE_FULL)")
    parser.add_argument("--token-file", type=Path)
    parser.add_argument("--translator", help="Existing translator base URL (TV_FULL)")
    args = parser.parse_args()
    if args.threads < 1:
        parser.error("threads must be positive")
    logging.basicConfig(level=logging.INFO)
    if args.mode == "TV_CROP" and not args.recognizer:
        parser.error("TV_CROP requires --recognizer")
    if args.mode in ("TV_FULL", "ORANGE_FULL") and not args.translator:
        parser.error("full-frame modes require --translator")
    if args.mode == "ORANGE_FULL" and not args.frame_worker:
        parser.error("ORANGE_FULL requires --frame-worker")
    crop_client = CropClient(args.recognizer, read_token(args.token_file)) if args.mode == "TV_CROP" else None
    translator = TranslationClient(args.translator) if args.mode in ("TV_FULL", "ORANGE_FULL") else None
    frame_client = (FrameClient(args.frame_worker, read_token(args.token_file))
                    if args.mode == "ORANGE_FULL" else None)
    pipeline = FramePipeline(args.assets,args.mode,args.threads,crop_client,translator,
                             detector_threads=args.detector_threads,recognizer_threads=args.recognizer_threads,
                             frame_client=frame_client)
    with FrameServer(args.socket, pipeline) as server:
        if os.environ.get("PP_OCR_FULL_OSD") == "1":
            from .osd_publisher import OsdPublisher
            server.osd_publisher = OsdPublisher()
        try:
            server.serve_forever()
        finally:
            Path(args.socket).unlink(missing_ok=True)
            pipeline.close()


if __name__ == "__main__":
    main()
