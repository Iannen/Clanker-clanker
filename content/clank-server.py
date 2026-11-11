#!/usr/bin/env -S python3 -B

import json
import sys
import traceback
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from http.client import HTTPResponse
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

from backend.adapters import LinuxDiskAdapter, RuamelYamlParserAdapter
from backend.asset_ingestion import IngestionServiceImpl
from backend.render_pipeline import PromptServiceImpl
from backend.keyboard import KBServiceImpl
from backend.controller import ROUTES, ClankController

_FRONTEND_DIR = Path(__file__).parent / "web-ui" / "frontend"
GPU_BOX_URL = "https://gpu-box.tailca68f1.ts.net:8787"
PORT = 8787


class _Handler(SimpleHTTPRequestHandler):
    def __init__(self, controller: ClankController, *args, **kwargs):
        self.controller = controller
        super().__init__(*args, directory=str(_FRONTEND_DIR), **kwargs)
        

    def do_GET(self):
        parsed = urlsplit(self.path)
        entry = ROUTES.get(("GET", parsed.path))
        if entry:
            params = dict(parse_qs(parsed.query))
            status, ctype, body = entry(self.controller, params)
            self._write(status, ctype, body)
        else:
            super().do_GET()

    def do_POST(self):
        entry = ROUTES.get(("POST", self.path))
        if not entry:
            self._write(404, "text/plain", "Not Found")
            return
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else None
        body = json.loads(raw) if raw is not None else None
        if body is None:
            # No body was sent – pass None so proxy_gpu can forward bodyless
            status, ctype, resp = entry(self.controller, None)
        else:
            status, ctype, resp = entry(self.controller, body)
        self._write(status, ctype, resp)


    def _write(self, status: int, ctype: str, body):
        if isinstance(body, HTTPResponse):
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            while chunk := body.read(1024):
                self.wfile.write(chunk)
                self.wfile.flush()
        elif isinstance(body, dict):
            encoded = json.dumps(body).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
        else:
            encoded = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)


class ClankServer(ThreadingHTTPServer):
    def __init__(self, controller: ClankController, port: int = PORT):
        super().__init__(
            ("127.0.0.1", port),
            lambda *a, **kw: _Handler(controller, *a, **kw),
        )
        self.port = port

    def run(self):
        print(f"Clanker server listening on http://127.0.0.1:{self.port}")
        try:
            self.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.server_close()


def main() -> None:
    files_adapter = LinuxDiskAdapter()
    cfg_ingestor = RuamelYamlParserAdapter()

    ingestion = IngestionServiceImpl(files=files_adapter, cfg_ingestor=cfg_ingestor)
    kb_service = KBServiceImpl()
    prompt_service = PromptServiceImpl(files=files_adapter)

    controller = ClankController(
        kb_service=kb_service,
        prompt_service=prompt_service,
        ingestion=ingestion,
        gpu_box_url=GPU_BOX_URL,
    )
    server = ClankServer(controller)
    server.run()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.stderr.write(
            "".join(traceback.format_exception(
                type(sys.exc_info()[0]), sys.exc_info()[1], sys.exc_info()[2]
            ))
        )
        sys.exit(1)