import http.server
import threading
import urllib.request
from pathlib import Path
from queue import Queue

from core.engine_deps import (
    FrontendService,
    BootCmd,
    KbCmd,
    Command,
    Result,
    StartResult,
    ExitResult,
)

_FRONTEND_DIR = Path(__file__).parent.parent.parent / "web-ui" / "frontend"


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


class _Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, directory=str(_FRONTEND_DIR), **kwargs)

    def do_GET(self) -> None:
        if self.path == "/api/prompt":
            self._handle_prompt()
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

    def _handle_prompt(self) -> None:
        frontend = self.server.frontend
        cmd_q = KbCmd(char="q")
        cmd_a = KbCmd(char="a")

        slot = _ReplySlot()
        frontend._pending[id(cmd_a)] = slot

        frontend._queue.put(cmd_q)
        frontend._queue.put(cmd_a)

        body = slot.wait()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
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
        self._queue: Queue = Queue()
        self._queue.put(BootCmd())
        self._pending: dict[int, _ReplySlot] = {}
        self._server = http.server.HTTPServer(("127.0.0.1", port), _Handler)
        self._server.frontend = self
        self._server.gpu_box_url = gpu_box_url
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def get_request(self) -> Command:
        return self._queue.get()

    def post_response(self, result: Result) -> None:
        match result:
            case StartResult():
                print("Web frontend ready.")
            case ExitResult():
                pass
            case _:
                slot = self._pending.pop(id(result.cmd), None)
                if slot is not None:
                    slot.resolve(result.text.encode("utf-8"))