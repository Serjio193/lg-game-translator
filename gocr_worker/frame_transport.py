"""Lossless selected-frame protocol for local capture and explicit Orange relay."""
import json
import struct
from PIL import Image

HEADER = struct.Struct("!4sHHQQI")
WIDTH, HEIGHT = 1280, 720
MAX_REPLY = 4 * 1024 * 1024


def encode_frame(image, sequence=0, captured=0):
    if image.mode != "RGB" or image.size != (WIDTH, HEIGHT):
        raise ValueError("invalid selected-frame pixels")
    pixels = image.tobytes()
    return HEADER.pack(b"GFR1", WIDTH, HEIGHT, sequence, captured, len(pixels))+pixels


def read_exact(stream, size):
    chunks = bytearray()
    while len(chunks) < size:
        chunk = stream.recv(size-len(chunks))
        if not chunk:
            raise EOFError("selected-frame stream ended")
        chunks.extend(chunk)
    return bytes(chunks)


def receive_frame(stream):
    magic, width, height, sequence, captured, size = HEADER.unpack(read_exact(stream, HEADER.size))
    if magic != b"GFR1" or (width, height) != (WIDTH, HEIGHT) or size != WIDTH*HEIGHT*3:
        raise ValueError("invalid selected-frame contract")
    image = Image.frombytes("RGB", (width, height), read_exact(stream, size))
    return image, sequence, captured


def send_result(stream, result):
    raw = json.dumps(result, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode()
    if len(raw) > MAX_REPLY:
        raise ValueError("GOCR frame result exceeds transport budget")
    stream.sendall(struct.pack("!I", len(raw))+raw)
