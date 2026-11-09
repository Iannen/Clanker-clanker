import http.server
import json
import urllib.request
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from core import entities as e
from core.engine_deps import (
    BootstrapSuccess,
    ClankerizeResult,
    DomainSelectedResult,
    KbCmd,
    KbServiceEmission,
    PromptRenderResult,
    RenderHotPromptCmd,
    RenderNormalPromptCmd,
    StartCmd,
    StartResult,
    TerminateResult,
    UnboundKeyResult,
    UninhabitedDomainResult,
    UninhabitedPromptResult,
)

_FRONTEND_DIR = Path(__file__).parent.parent / "web-ui" / "frontend"
GPU_BOX_URL = "https://gpu-box.tailca68f1.ts.net:8787"
PORT = 8787

GPU_BOX_PATHS = frozenset(("/v1/chat/completions", "/api/desktop-mode", "/api/inference-mode"))


def _shape_kb_emission(result: KbServiceEmission) -> dict:
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
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, directory=str(_FRONTEND_DIR), **kwargs)

    def do_GET(self) -> None:
        if self.path.startswith("/api/boot"):
            self._handle_boot()
        elif self.path.startswith("/api/char"):
            self._handle_char()
        elif self.path.startswith("/api/"):
            self._send_plain(404, "Not Found")
        else:
            super().do_GET()

    def do_POST(self) -> None:
        if self.path in GPU_BOX_PATHS:
            self._forward_gpu_box(self.path)
        else:
            self._send_plain(404, "Not Found")

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

    def _handle_boot(self) -> None:
        ingestion = self.server.ingestion
        kb_service = self.server.kb_service

        result = ingestion.get_runtime_config()

        if isinstance(result, ClankerizeResult):
            result = ingestion.initialize_workspace()

        if isinstance(result, TerminateResult):
            self._send_plain(500, f"Boot failed: {result.report.get_critical_complaints()}")
            return

        if not isinstance(result, (StartCmd, StartResult)):
            self._send_plain(500, f"Unexpected boot result: {type(result).__name__}")
            return

        start_cmd = StartCmd(kb=result.kb, ui_render=result.ui_render)
        kb_service.handle_start(start_cmd)

        boot_message = "Bootstrap completed successfully"
        if isinstance(result, StartResult) and result.report.get_all_complaints():
            boot_message = f"Bootstrap completed with {len(result.report.get_all_complaints())} soft complaint(s)"

        self._send_plain(200, boot_message)

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


class ClankServer(http.server.HTTPServer):
    def __init__(
        self,
        ingestion,
        kb_service,
        prompt_service,
        port: int = PORT,
        gpu_box_url: str = GPU_BOX_URL,
    ) -> None:
        super().__init__(("127.0.0.1", port), _Handler)
        self.ingestion = ingestion
        self.kb_service = kb_service
        self.prompt_service = prompt_service
        self.port = port
        self.gpu_box_url = gpu_box_url

    def run(self) -> None:
        print(f"Clanker server listening on http://127.0.0.1:{self.port}")
        try:
            self.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.server_close()