import http.server
import os
import urllib.request

from stdlib import dataclass
from core.engine_deps import IngestionService, PromptService, KBService, StartResult, PromptRenderPending, KbCmd

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web-ui", "frontend")


class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def do_GET(self) -> None:
        if self.path == "/api/test-prompt":
            body = b"Hello, world!"
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
            ingestion: IngestionService = self.server.ingestion
            render_service: PromptService = self.server.prompt_service
            kb_service: KBService = self.server.kb_service

            boot_result = ingestion.get_runtime_config()
            if not isinstance(boot_result, StartResult):
                self.send_response(503)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Service unavailable: ingestion did not return StartResult")
                return

            kb_service.set_runtime(boot_result)

            kb_service.handle_cmd(KbCmd(char='q'))

            pending = kb_service.handle_cmd(KbCmd(char='a'))
            if not isinstance(pending, PromptRenderPending):
                self.send_response(404)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Prompt button 'a' not found or uninhabited")
                return

            render_out = render_service.render_prompt(pending.ctx)
            body = render_out.text.encode("utf-8")
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

        gpu_box_url: str = self.server.gpu_box_url

        req = urllib.request.Request(
            gpu_box_url + path,
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


@dataclass
class WebServer:
    ingestion: IngestionService
    prompt_service: PromptService
    kb_service: KBService
    port: int
    gpu_box_url: str

    def run(self) -> None:
        httpd = http.server.HTTPServer(("127.0.0.1", self.port), ProxyHandler)
        httpd.ingestion = self.ingestion
        httpd.prompt_service = self.prompt_service
        httpd.kb_service = self.kb_service
        httpd.gpu_box_url = self.gpu_box_url
        print(f"Control server on http://127.0.0.1:{self.port} → {self.gpu_box_url}")
        httpd.serve_forever()