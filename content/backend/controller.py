import json
import urllib.request
from dataclasses import asdict
from typing import Any, Callable

from backend.core import engine_deps as d

ROUTES: dict[tuple[str, str], Callable] = {}


def GET(path: str):
    def deco(fn):
        ROUTES[("GET", path)] = fn
        return fn
    return deco


def POST(path: str):
    def deco(fn):
        def wrapper(controller, body, _path=path):
            return fn(controller, body, _path)
        ROUTES[("POST", path)] = wrapper
        return fn
    return deco


class ClankController:
    def __init__(self, prompt_service, ingestion, gpu_box_url: str):
        self.prompt_service = prompt_service
        self.ingestion = ingestion
        self.gpu_box_url = gpu_box_url

    @GET("/api/boot")
    def boot(self, params: dict) -> tuple[int, str, str | dict]:
        result = self.ingestion.get_runtime_config()
        return (200, "application/json", asdict(result))

    @POST("/api/clankerize")
    def clankerize(self, body: dict, path: str) -> tuple[int, str, dict]:
        result = self.ingestion.initialize_workspace()
        return (200, "application/json", asdict(result))

    @POST("/api/render-prompt")
    def render_prompt(self, body: dict, path: str) -> tuple[int, str, dict | str]:
        try:
            domain, prompt = self.ingestion.deserialize_domain_prompt(body)
        except ValueError as ex:
            return (400, "text/plain", str(ex))
        except Exception as ex:
            return (500, "text/plain", str(ex))

        try:
            result = self.prompt_service.render_from_entities(domain, prompt)
            return (200, "application/json", asdict(result))
        except Exception as ex:
            return (500, "text/plain", str(ex))

    @POST("/api/ingest")
    def ingest(self, body: dict, path: str) -> tuple[int, str, dict]:
        try:
            result = self.ingestion.apply_file_changes(body["content"])
        except Exception as ex:
            return (500, "text/plain", f"Ingest failed: {ex}")

        has_errors = bool(result.missing_paths or result.unexpected_paths or result.parse_errors)
        status = 400 if has_errors else 200
        return (status, "application/json", asdict(result))

    @POST("/v1/chat/completions")
    @POST("/api/mode/desktop")
    @POST("/api/mode/llama_cpp")
    @POST("/api/mode/strata")
    def proxy_gpu(self, body: dict | None, path: str) -> tuple[int, str, Any]:
        req_headers: dict[str, str] = {}
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            req_headers["Content-Type"] = "application/json"

        req = urllib.request.Request(
            self.gpu_box_url + path,
            data=data,
            headers=req_headers,
            method="POST",
        )
        resp = urllib.request.urlopen(req)
        return (resp.status, resp.headers.get("Content-Type", "text/plain"), resp)