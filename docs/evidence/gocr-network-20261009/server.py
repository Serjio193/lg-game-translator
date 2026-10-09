import json
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def setup(self):
        super().setup()
        self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    def do_POST(self):
        if self.client_address[0] != "192.168.1.3":
            self.send_error(403)
            return
        length = int(self.headers.get("Content-Length", "0"))
        if length < 0 or length > 16*1024*1024:
            self.send_error(413)
            return
        body = self.rfile.read(length)
        reply = json.dumps({"received": len(body), "text": "Test response"}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(reply)))
        self.end_headers()
        self.wfile.write(reply)
        if self.path == "/stop":
            threading.Thread(target=self.server.shutdown, daemon=True).start()

    def log_message(self, *args):
        pass


with HTTPServer(("192.168.1.11", 18773), Handler) as server:
    print("Temporary TV-only transfer test ready", flush=True)
    server.serve_forever()
