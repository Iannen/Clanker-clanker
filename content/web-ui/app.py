#!/usr/bin/env python3
import http.server
import urllib.request
import os

GPU_BOX_URL = "https://gpu-box.tailca68f1.ts.net:8787"
PORT = 8787

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")


class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def _forward(self, path: str) -> None:
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else None

        req_headers = {}
        if self.headers.get("Authorization"):
            req_headers["Authorization"] = self.headers["Authorization"]
        if content_length:
            req_headers["Content-Type"] = self.headers.get(
                "Content-Type", "application/json"
            )

        req = urllib.request.Request(
            GPU_BOX_URL + path,
            data=body,
            headers=req_headers,
            method="POST",
        )

        try:
            resp = urllib.request.urlopen(req)
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Upstream Error: {e}".encode())
            return

        self.send_response(resp.status)
        self.send_header(
            "Content-Type",
            resp.headers.get("Content-Type", "text/plain"),
        )
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        while True:
            chunk = resp.read(1024)
            if not chunk:
                break
            self.wfile.write(chunk)
            self.wfile.flush()

    def do_POST(self) -> None:
        if self.path in (
            "/api/desktop-mode",
            "/api/inference-mode",
            "/v1/chat/completions",
        ):
            self._forward(self.path)
        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Not Found")


if __name__ == "__main__":
    server = http.server.HTTPServer(("127.0.0.1", PORT), ProxyHandler)
    print(f"Control server on http://127.0.0.1:{PORT} → {GPU_BOX_URL}")
    server.serve_forever()