#!/usr/bin/env python3
import http.server
import json
import os
import socketserver
from datetime import datetime, timezone

PORT = 8848
ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, "data")
STATE_FILE = os.path.join(DATA_DIR, "state.json")
CHAT_IN_FILE = os.path.join(DATA_DIR, "chat_in.json")
CHAT_OUT_FILE = os.path.join(DATA_DIR, "chat_out.json")

os.makedirs(DATA_DIR, exist_ok=True)
if not os.path.exists(STATE_FILE):
    with open(STATE_FILE, "w") as f:
        json.dump({}, f)
if not os.path.exists(CHAT_IN_FILE):
    with open(CHAT_IN_FILE, "w") as f:
        json.dump([], f)
if not os.path.exists(CHAT_OUT_FILE):
    with open(CHAT_OUT_FILE, "w") as f:
        json.dump([], f)


def read_json(path):
    with open(path, "r") as f:
        return json.load(f)


def write_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def do_GET(self):
        if self.path == "/api/state":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            with open(STATE_FILE, "rb") as f:
                self.wfile.write(f.read())
            return
        if self.path == "/api/chat":
            chat_in = read_json(CHAT_IN_FILE)
            chat_out = read_json(CHAT_OUT_FILE)
            messages = (
                [{"role": "user", "text": m["text"], "ts": m["ts"]} for m in chat_in]
                + [{"role": "assistant", "text": m["text"], "ts": m["ts"]} for m in chat_out]
            )
            messages.sort(key=lambda m: m["ts"])
            self._send_json(messages)
            return
        super().do_GET()

    def do_POST(self):
        if self.path == "/api/state":
            data = self._read_json_body()
            if data is None:
                return
            write_json(STATE_FILE, data)
            self._send_json({"ok": True})
            return
        if self.path == "/api/chat":
            data = self._read_json_body()
            if data is None:
                return
            chat_in = read_json(CHAT_IN_FILE)
            next_id = (max([m["id"] for m in chat_in], default=0)) + 1
            chat_in.append({
                "id": next_id,
                "text": data.get("text", ""),
                "ts": datetime.now(timezone.utc).isoformat(),
            })
            write_json(CHAT_IN_FILE, chat_in)
            self._send_json({"ok": True})
            return
        self.send_response(404)
        self.end_headers()

    def _read_json_body(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return None

    def _send_json(self, obj):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    def log_message(self, format, *args):
        pass


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    with ReusableTCPServer(("", PORT), Handler) as httpd:
        print(f"Corriendo en http://localhost:{PORT}  (Ctrl+C para detener)")
        httpd.serve_forever()
