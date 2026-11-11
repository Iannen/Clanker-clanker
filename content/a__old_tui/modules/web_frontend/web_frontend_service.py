import http.server
import json
import threading
import urllib.request
from dataclasses import asdict
from pathlib import Path
from queue import Queue
from urllib.parse import parse_qs, urlsplit

from core import entities as e
from core.engine_deps import (
    FrontendService,
    BootCmd,
    KbCmd,
    Command,
    Request,
    StartResult,
    BootstrapSuccess,
    ClankerizeResult,
    TerminateResult,
    PromptRenderResult,
    KbServiceEmission,
    UnboundKeyResult,
    DomainSelectedResult,
    UninhabitedDomainResult,
    UninhabitedPromptResult,
)

_FRONTEND_DIR = Path(__file__).parent.parent.parent.parent / "web-ui" / "frontend"


class _ReplySlot:
    def __init__(self) -> None:
        self._event = threading.Event()
        self._payload: bytes | None = None

    def wait(self) -> bytes:
        self._event.wait()
        return self._payload

    def resolve(self, payload: bytes) -> None:
        self._payload = payload
        self._event.set()


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
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Not Found")
        else:
            super().do_GET()

    def do_POST(self) -> None:
        if self.path in ("/v1/chat/completions", "/api/desktop-mode", "/api/inference-mode"):
            self._forward(self.path)
        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Not Found")

    def _handle_boot(self) -> None:
        frontend = self.server.frontend
        req = frontend._mint(BootCmd())
        slot = _ReplySlot()
        frontend._pending[req.id] = slot

        frontend._queue.put(req)
        body = slot.wait()

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_char(self) -> None:
        parsed = urlsplit(self.path)
        params = parse_qs(parsed.query)
        char_values = params.get("char", [])
        char_val = char_values[0] if len(char_values) == 1 and char_values[0] else None

        if char_val is None:
            body = b"Missing or invalid 'char' query param"
            self.send_response(400)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        frontend = self.server.frontend
        req = frontend._mint(KbCmd(char=char_val))
        slot = _ReplySlot()
        frontend._pending[req.id] = slot

        frontend._queue.put(req)
        body = slot.wait()

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _forward(self, path: str) -> None:
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else None

        req_headers: dict[str, str] = {}
        if self.headers.get("Authorization"):
            req_headers["Authorization"] = self.headers["Authorization"]
        if content_length:
            req_headers["Content-Type"] = self.headers.get("Content-Type", "application/json")

        gpu_box_url: str = self.server.gpu_box_url

        req = urllib.request.Request(
            gpu_box_url + path,
            data=body,
            headers=req_headers,
            method="POST",
        )

        try:
            resp = urllib.request.urlopen(req)
        except Exception as exc:
            self.send_response(502)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Upstream Error: {exc}".encode())
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


class WebFrontendServiceImpl(FrontendService):
    def __init__(self, port: int, gpu_box_url: str) -> None:
        self._queue: Queue[Request] = Queue()
        self._pending: dict[str, _ReplySlot] = {}
        self._counter = 0
        self._server = http.server.HTTPServer(("127.0.0.1", port), _Handler)
        self._server.frontend = self
        self._server.gpu_box_url = gpu_box_url
        self._thread: threading.Thread | None = None

    def _mint(self, item: Command) -> Request:
        self._counter += 1
        return Request(id=str(self._counter), item=item)

    def start(self) -> None:
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def get_request(self) -> Request:
        return self._queue.get()

    def post_response(self, req: Request) -> None:
        match req.item:
            case BootstrapSuccess() | StartResult() | TerminateResult() | ClankerizeResult():
                slot = self._pending.pop(req.id, None)
                if slot is not None:
                    slot.resolve(req.item.__class__.__name__.encode("utf-8"))
            case KbServiceEmission():
                slot = self._pending.pop(req.id, None)
                if slot is not None:
                    payload = _shape_kb_emission(req.item)
                    slot.resolve(json.dumps(payload).encode("utf-8"))
            case _:
                slot = self._pending.pop(req.id, None)
                if slot is not None:
                    slot.resolve(json.dumps(asdict(req.item), default=str).encode("utf-8"))