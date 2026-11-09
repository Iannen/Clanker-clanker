"""Class-based Clanker HTTP server."""

import http.server
import json
import urllib.request
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from core import entities as e
from core.engine_deps import (
    KbCmd,
    KbServiceEmission,
    PromptRenderResult,
    RenderNormalPromptCmd,
    RenderHotPromptCmd,
    BootstrapSuccess,
    UnboundKeyResult,
    DomainSelectedResult,
    UninhabitedDomainResult,
    UninhabitedPromptResult,
)

_FRONTEND_DIR = Path(__file__).parent.parent / "web-ui" / "frontend"
GPU_BOX_URL = "https://gpu-box.tailca68f1.ts.net:8787"
PORT = 8787

GPU_BOX_PATHS = frozenset(("/v1/chat/completions", "/api/desktop-mode", "/api/inference-mode"))


def _shape_kb_emission(result: KbServiceEmission) -> dict:
    """Shape a KbServiceEmission into a JSON-serialisable dict for the frontend."""
    kb = result.kb
    payload: dict = {
        "buttons": {},
        "key": getattr(result.cmd, "char", ""),
        "prompt_text": getattr(result, "text", ""),
    }

    for key, btn in kb.buttons.items():
        label = btn.inhabitant.name if btn.inhabitant else ""
        if isinstance(btn, e.DomButton):
            if btn == kb.selected_dom_btn:
                state = "highlighted"
            elif btn.inhabitant:
                state = "active"
            else:
                state = "inactive"
        else:
            state = "active" if btn.inhabitant else "inactive"
        payload["buttons"][key] = {"label": label, "state": state}

    match result:
        case BootstrapSuccess():
            payload["result_type"] = "bootstrap_success"
        case UnboundKeyResult():
            payload["result_type"] = "unbound_key"
        case DomainSelectedResult():
            payload["result_type"] = "domain_selected"
            payload["domain"] = result.btn.inhabitant.name if result.btn.inhabitant else ""
        case UninhabitedDomainResult():
            payload["result_type"] = "uninhabited_domain"
            payload["domain"] = result.btn.inhabitant.name if result.btn.inhabitant else ""
        case UninhabitedPromptResult():
            payload["result_type"] = "uninhabited_prompt"
        case PromptRenderResult():
            payload["result_type"] = "prompt_render"
            payload["prompt"] = result.cmd.prompt.name
            payload["domain"] = result.cmd.domain.name
            payload["lines"] = result.lines
            payload["chars"] = result.chars
        case _:
            payload["result_type"] = "unknown"

    return payload


class _Handler(http.server.SimpleHTTPRequestHandler):
    """Single-threaded synchronous HTTP handler."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, directory=str(_FRONTEND_DIR), **kwargs)

    # ------------------------------------------------------------------ GET

    def do_GET(self) -> None:
        if self.path.startswith("/api/boot"):
            self._handle_boot()
        elif self.path.startswith("/api/char"):
            self._handle_char()
        elif self.path.startswith("/api/"):
            self._send_plain(404, "Not Found")
        else:
            super().do_GET()

    # ----------------------------------------------------------------- POST

    def do_POST(self) -> None:
        if self.path in GPU_BOX_PATHS:
            self._forward_gpu_box(self.path)
        else:
            self._send_plain(404, "Not Found")

    # ------------------------------------------------------------- helpers

    def _send_plain(self, status: int, text: str) -> None:
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: int, obj: dict) -> None:
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # --------------------------------------------------------------- routes

    def _handle_boot(self) -> None:
        self._send_plain(200, self.server.boot_message)

    def _handle_char(self) -> None:
        parsed = urlsplit(self.path)
        params = parse_qs(parsed.query)
        char_values = params.get("char", [])
        char_val = char_values[0] if len(char_values) == 1 and char_values[0] else None

        if char_val is None:
            self._send_plain(400, "Missing or invalid 'char' query param")
            return

        result = self.server.kb_service.handle_key(KbCmd(char=char_val))

        if isinstance(result, (RenderNormalPromptCmd, RenderHotPromptCmd)):
            result = self.server.prompt_service.render_prompt(result)

        payload = _shape_kb_emission(result)
        self._send_json(200, payload)

    def _forward_gpu_box(self, path: str) -> None:
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else None

        req_headers: dict[str, str] = {}
        if self.headers.get("Authorization"):
            req_headers["Authorization"] = self.headers["Authorization"]
        if content_length:
            req_headers["Content-Type"] = self.headers.get("Content-Type", "application/json")

        req = urllib.request.Request(
            self.server.gpu_box_url + path,
            data=body,
            headers=req_headers,
            method="POST",
        )

        try:
            resp = urllib.request.urlopen(req)
        except Exception as exc:
            self._send_plain(502, f"Upstream Error: {exc}")
            return

        self.send_response(resp.status)
        self.send_header("Content-Type", resp.headers.get("Content-Type", "text/plain"))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        while True:
            chunk = resp.read(1024)
            if not chunk:
                break
            self.wfile.write(chunk)
            self.wfile.flush()


class ClankServer:
    """Class-based Clanker HTTP server.

    Accepts pre-built services via DI and runs the HTTP loop.
    """

    def __init__(
        self,
        kb_service,
        prompt_service,
        boot_message: str,
        port: int = PORT,
        gpu_box_url: str = GPU_BOX_URL,
    ) -> None:
        self.kb_service = kb_service
        self.prompt_service = prompt_service
        self.boot_message = boot_message
        self.port = port
        self.gpu_box_url = gpu_box_url

    def run(self) -> None:
        server = http.server.HTTPServer(("127.0.0.1", self.port), _Handler)
        server.kb_service = self.kb_service
        server.prompt_service = self.prompt_service
        server.boot_message = self.boot_message
        server.gpu_box_url = self.gpu_box_url

        print(f"Clanker server listening on http://127.0.0.1:{self.port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()