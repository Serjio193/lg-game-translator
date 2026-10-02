#!/usr/bin/env python3
"""Receive HyperHDR NetworkForwarder FlatBuffers frames and preview them in a browser.

TCP input: 0.0.0.0:32949
Browser UI: http://127.0.0.1:8000/

Implements the subset of HyperHDR's FlatBuffers protocol needed by NetworkForwarder:
Register + RawImage RGB24 + Reply acknowledgements.
"""
import argparse
import io
import json
import socket
import struct
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import flatbuffers
from flatbuffers.table import Table
from PIL import Image

CMD_IMAGE = 2
CMD_REGISTER = 4
IMG_RAW = 1
MAX_MESSAGE = 16 * 1024 * 1024


class State:
    def __init__(self):
        self.lock = threading.Lock()
        self.connected = False
        self.peer = None
        self.width = self.height = 0
        self.frames = self.bytes = 0
        self.started = self.last_frame = 0.0
        self.latest_jpeg = None
        self.latest_rgb_len = 0
        self.error = ""
        self.preview_fps = 10.0
        self.last_preview_encode = 0.0

    def connect(self, peer):
        with self.lock:
            self.connected = True
            self.peer = str(peer)
            self.started = time.monotonic()
            self.frames = self.bytes = 0
            self.error = ""

    def disconnect(self):
        with self.lock:
            self.connected = False
            self.peer = None

    def frame(self, width, height, rgb):
        now = time.monotonic()
        expected = width * height * 3
        if width <= 0 or height <= 0 or len(rgb) != expected:
            with self.lock:
                self.error = f"Bad RawImage {width}x{height}: {len(rgb)} B, expected {expected}"
            return

        with self.lock:
            self.width, self.height = width, height
            self.frames += 1
            self.bytes += len(rgb)
            self.latest_rgb_len = len(rgb)
            self.last_frame = now
            encode = now - self.last_preview_encode >= 1.0 / max(self.preview_fps, 0.1)
            if encode:
                self.last_preview_encode = now

        if encode:
            try:
                img = Image.frombytes("RGB", (width, height), rgb)
                if width > 1280:
                    img = img.resize((1280, max(1, int(height * 1280 / width))), Image.Resampling.BILINEAR)
                out = io.BytesIO()
                img.save(out, "JPEG", quality=78)
                with self.lock:
                    self.latest_jpeg = out.getvalue()
            except Exception as exc:
                with self.lock:
                    self.error = f"JPEG encode failed: {exc}"

    def snapshot(self):
        with self.lock:
            now = time.monotonic()
            elapsed = max(now - self.started, 1e-6) if self.started else 0
            return {
                "connected": self.connected,
                "peer": self.peer,
                "width": self.width,
                "height": self.height,
                "format": "RGB24" if self.width else "",
                "frames": self.frames,
                "fps": self.frames / elapsed if self.connected and elapsed else 0,
                "mib_s": self.bytes / elapsed / 1024 / 1024 if self.connected and elapsed else 0,
                "frame_bytes": self.latest_rgb_len,
                "age": now - self.last_frame if self.last_frame else None,
                "error": self.error,
                "jpeg": self.latest_jpeg,
            }


STATE = State()


def root_table(buf):
    return Table(buf, struct.unpack_from("<I", buf, 0)[0])


def union_table(parent, vtable_offset):
    off = parent.Offset(vtable_offset)
    if not off:
        return None
    return Table(parent.Bytes, parent.Indirect(off + parent.Pos))


def parse_request(buf):
    req = root_table(buf)
    off = req.Offset(4)
    cmd_type = req.Get(flatbuffers.number_types.Uint8Flags, off + req.Pos) if off else 0
    cmd = union_table(req, 6)
    if cmd is None:
        return ("other", cmd_type)

    if cmd_type == CMD_REGISTER:
        off = cmd.Offset(6)
        priority = cmd.Get(flatbuffers.number_types.Int32Flags, off + cmd.Pos) if off else 0
        return ("register", priority)

    if cmd_type == CMD_IMAGE:
        off = cmd.Offset(4)
        image_type = cmd.Get(flatbuffers.number_types.Uint8Flags, off + cmd.Pos) if off else 0
        image = union_table(cmd, 6)
        if image_type != IMG_RAW or image is None:
            return ("image_other", image_type)

        ow, oh, od = image.Offset(6), image.Offset(8), image.Offset(4)
        width = image.Get(flatbuffers.number_types.Int32Flags, ow + image.Pos) if ow else -1
        height = image.Get(flatbuffers.number_types.Int32Flags, oh + image.Pos) if oh else -1
        if od:
            start = image.Vector(od)
            data = bytes(image.Bytes[start:start + image.VectorLen(od)])
        else:
            data = b""
        return ("raw", width, height, data)

    return ("other", cmd_type)


def build_reply(error=None, video=-1, registered=-1):
    b = flatbuffers.Builder(128)
    err = b.CreateString(error) if error else 0
    b.StartObject(3)
    if err:
        b.PrependUOffsetTRelativeSlot(0, err, 0)
    b.PrependInt32Slot(1, int(video), -1)
    b.PrependInt32Slot(2, int(registered), -1)
    obj = b.EndObject()
    b.Finish(obj)
    return bytes(b.Output())


def send_packet(sock, payload):
    sock.sendall(struct.pack(">I", len(payload)) + payload)


def recv_exact(sock, count):
    out = bytearray()
    while len(out) < count:
        chunk = sock.recv(count - len(out))
        if not chunk:
            return None
        out.extend(chunk)
    return bytes(out)


def handle_client(sock, peer):
    print(f"[TCP] connected {peer}")
    STATE.connect(peer)
    try:
        sock.settimeout(10)
        while True:
            hdr = recv_exact(sock, 4)
            if hdr is None:
                break
            size = struct.unpack(">I", hdr)[0]
            if size <= 0 or size > MAX_MESSAGE:
                raise ValueError(f"invalid message size {size}")
            payload = recv_exact(sock, size)
            if payload is None:
                break

            try:
                msg = parse_request(payload)
            except Exception as exc:
                send_packet(sock, build_reply(error=f"decode error: {exc}"))
                continue

            if msg[0] == "register":
                print(f"[TCP] register priority={msg[1]}")
                send_packet(sock, build_reply(registered=msg[1]))
            elif msg[0] == "raw":
                _, w, h, rgb = msg
                STATE.frame(w, h, rgb)
                send_packet(sock, build_reply(video=0))
            elif msg[0] == "image_other":
                send_packet(sock, build_reply(error=f"unsupported image type {msg[1]}"))
            else:
                send_packet(sock, build_reply(video=0))
    except (OSError, ConnectionError, ValueError) as exc:
        print(f"[TCP] ended: {exc}")
    finally:
        try:
            sock.close()
        except Exception:
            pass
        STATE.disconnect()
        print(f"[TCP] disconnected {peer}")


def tcp_server(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((host, port))
        srv.listen(8)
        print(f"[TCP] listening on {host}:{port}")
        while True:
            client, peer = srv.accept()
            threading.Thread(target=handle_client, args=(client, peer), daemon=True).start()


HTML = """<!doctype html>
<meta charset="utf-8">
<title>HyperHDR Frame Receiver</title>
<style>
body{margin:0;background:#111;color:#eee;font:15px system-ui,Segoe UI,sans-serif}
header{padding:12px 16px;background:#1b1b1b;position:sticky;top:0}
#s{display:flex;gap:16px;flex-wrap:wrap}.ok{color:#7dff9b}.bad{color:#ff7676}
main{padding:14px}img{display:block;max-width:100%;height:auto;background:#000;border:1px solid #333}
</style>
<header><b>HyperHDR → PC</b><div id="s">waiting...</div></header>
<main><img id="f" src="/frame.jpg"></main>
<script>
const s=document.getElementById('s'),f=document.getElementById('f');
async function poll(){
  try{
    const x=await (await fetch('/stats',{cache:'no-store'})).json();
    const age=x.age==null?'-':x.age.toFixed(2)+' s';
    s.innerHTML='<span class="'+(x.connected?'ok':'bad')+'">'+(x.connected?'CONNECTED':'DISCONNECTED')+'</span>'+
      '<span>'+x.width+'×'+x.height+' '+(x.format||'')+'</span>'+
      '<span>'+x.fps.toFixed(1)+' FPS</span><span>'+x.mib_s.toFixed(1)+' MiB/s</span>'+
      '<span>frame '+x.frame_bytes+' B</span><span>age '+age+'</span>'+
      (x.error?'<span class="bad">'+x.error+'</span>':'');
  }catch(e){s.textContent=e}
}
setInterval(poll,500);setInterval(()=>f.src='/frame.jpg?t='+Date.now(),100);poll();
</script>"""


class Web(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path.startswith("/?"):
            body = HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
        elif self.path.startswith("/stats"):
            snap = STATE.snapshot()
            snap.pop("jpeg")
            body = json.dumps(snap, ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
        elif self.path.startswith("/frame.jpg"):
            body = STATE.snapshot()["jpeg"]
            if not body:
                self.send_response(204)
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Cache-Control", "no-store")
        else:
            self.send_response(404)
            self.end_headers()
            return

        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        pass


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tcp-host", default="0.0.0.0")
    p.add_argument("--tcp-port", type=int, default=32949)
    p.add_argument("--web-host", default="127.0.0.1")
    p.add_argument("--web-port", type=int, default=8000)
    p.add_argument("--preview-fps", type=float, default=10)
    a = p.parse_args()
    STATE.preview_fps = a.preview_fps
    threading.Thread(target=tcp_server, args=(a.tcp_host, a.tcp_port), daemon=True).start()
    print(f"[WEB] http://127.0.0.1:{a.web_port}/")
    ThreadingHTTPServer((a.web_host, a.web_port), Web).serve_forever()


if __name__ == "__main__":
    main()
