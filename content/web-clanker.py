#!/usr/bin/env -S python3 -B
import http.server
import urllib.request
import os

from adapters.disk_adapter import LinuxDiskAdapter
from adapters.yaml_parser import RuamelYamlParserAdapter
from modules.asset_ingestion.ingestion_service import IngestionServiceImpl
from modules.render_pipeline.render_service import PromptServiceImpl
from modules.keyboard.keyboard_service import KBServiceImpl
from core.engine_deps import BootCmd, KbCmd, StartResult

GPU_BOX_URL = "https://gpu-box.tailca68f1.ts.net:8787"
PORT = 8787

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "web-ui", "frontend")

TEST_PROMPT = "Hello, world!"


class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def do_GET(self) -> None:
        if self.path == "/api/test-prompt":
            body = TEST_PROMPT.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/api/prompt":
            self._handle_prompt_request()
        elif self.path.startswith("/api/"):
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Not Found")
        else:
            super().do_GET()

    def _handle_prompt_request(self) -> None:
        try:
            disk = LinuxDiskAdapter()
            yaml_parser = RuamelYamlParserAdapter()
            ingestion = IngestionServiceImpl(files=disk, cfg_ingestor=yaml_parser)
            render_service = PromptServiceImpl(files=disk, io_bridge=None)
            kb_service = KBServiceImpl(prompt_service=render_service, ingestion=ingestion)

            boot_result = kb_service.handle_cmd(BootCmd())
            if not isinstance(boot_result, StartResult):
                self.send_response(503)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Service unavailable: ingestion did not return StartResult")
                return

            kb_service.handle_cmd(KbCmd(char='r'))

            btn = kb_service.kb.get('a')
            if btn is None or btn.inhabitant is None:
                self.send_response(404)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Prompt button 'a' not found or uninhabited")
                return

            ctx = kb_service.build_render_context(btn)
            if ctx is None:
                self.send_response(404)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Could not build render context")
                return

            text = render_service.render_prompt_text(ctx)
            body = text.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Internal error: {e}".encode())

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