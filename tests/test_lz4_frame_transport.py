"""Wire integration, using a deterministic stand-in codec on any host."""
import os
import threading
import unittest
from unittest.mock import patch
import zlib
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from PIL import Image
from gocr_worker.frame_client import FrameClient
from gocr_worker.orange_server import make_handler


class TestCodec:
    size = 2764828
    bound = size+20000

    def __init__(self, *args):
        pass

    def compress(self, raw):
        return zlib.compress(raw)

    def decompress(self, raw):
        decoded = zlib.decompress(raw)
        if len(decoded) != self.size:
            raise ValueError("Changed block size")
        return decoded


class Worker:
    def ocr(self, image):
        self.pixels = image.tobytes()
        return {"schema": "gocr.worker.v1", "width": 1280, "height": 720,
                "lines": [], "timings_ms": {}}


class CompressedFrameTests(unittest.TestCase):
    def test_compressed_pixels_sequence_identity_and_invalid_length(self):
        worker = Worker()
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(worker, "t"*32))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        address = f"http://127.0.0.1:{server.server_port}"
        try:
            with patch.dict(os.environ, {"PP_OCR_FRAME_COMPRESSION": "lz4"}), \
                    patch("gocr_worker.lz4_block.Lz4Block", TestCodec):
                client = FrameClient(address, "t"*32)
                try:
                    image = Image.new("RGB", (1280, 720), (130, 50, 20))
                    result, sent = client.ocr(image, 12, 12345)
                    self.assertEqual(worker.pixels, image.tobytes())
                    self.assertEqual(result["sequence"], 12)
                    self.assertEqual(result["capture_ts"], 12345)
                    self.assertLess(sent, TestCodec.size)
                    self.assertIn("frame_decompress", result["timings_ms"])
                finally:
                    client.close()
                request = Request(address+"/v1/ocr-frame", zlib.compress(b"short"), headers={
                    "Authorization": "Bearer "+"t"*32, "Content-Encoding": "lz4-block",
                    "Content-Type": "application/x-gocr-frame"})
                with self.assertRaises(HTTPError) as error:
                    urlopen(request)
                self.assertEqual(error.exception.code, 400)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
