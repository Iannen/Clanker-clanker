import json
import urllib.request
from typing import Any, Callable

from backend.core import entities as e
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


def _shape_kb_emission(result: d.KbServiceEmission) -> dict:
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
        case d.BootstrapSuccess():
            payload["result_type"] = "bootstrap_success"
        case d.UnboundKeyResult():
            payload["result_type"] = "unbound_key"
        case d.DomainSelectedResult():
            payload["result_type"] = "domain_selected"
            payload["domain"] = result.btn.inhabitant.name if result.btn.inhabitant else ""
        case d.UninhabitedDomainResult():
            payload["result_type"] = "uninhabited_domain"
            payload["domain"] = result.btn.inhabitant.name if result.btn.inhabitant else ""
        case d.UninhabitedPromptResult():
            payload["result_type"] = "uninhabited_prompt"
        case d.PromptRenderResult():
            payload["result_type"] = "prompt_render"
            payload["prompt"] = result.cmd.prompt.name
            payload["domain"] = result.cmd.domain.name
            payload["lines"] = result.lines
            payload["chars"] = result.chars
            payload["prompt_mode"] = type(result.cmd).__name__
            payload["key"] = result.cmd.cmd.char
        case _:
            payload["result_type"] = "unknown"

    return payload


class ClankController:
    def __init__(self, kb_service, prompt_service, ingestion, gpu_box_url: str):
        self.kb_service = kb_service
        self.prompt_service = prompt_service
        self.ingestion = ingestion
        self.gpu_box_url = gpu_box_url

    @GET("/api/boot")
    def boot(self, params: dict) -> tuple[int, str, str]:
        result = self.ingestion.get_runtime_config()

        if isinstance(result, d.ClankerizeResult):
            result = self.ingestion.initialize_workspace()

        if isinstance(result, d.TerminateResult):
            return (500, "text/plain", f"Boot failed: {result.report.get_critical_complaints()}")

        if not isinstance(result, (d.StartCmd, d.StartResult)):
            return (500, "text/plain", f"Unexpected boot result: {type(result).__name__}")

        start_cmd = d.StartCmd(kb=result.kb, ui_render=result.ui_render)
        self.kb_service.handle_start(start_cmd)

        boot_message = "Bootstrap completed successfully"
        if isinstance(result, d.StartResult) and result.report.get_all_complaints():
            boot_message = f"Bootstrap completed with {len(result.report.get_all_complaints())} soft complaint(s)"

        return (200, "text/plain", boot_message)

    @GET("/api/char")
    def char(self, params: dict) -> tuple[int, str, dict]:
        char_values = params.get("char", [])
        char_val = char_values[0] if len(char_values) == 1 and char_values[0] else ""
        if not char_val:
            return (400, "text/plain", "Missing or invalid 'char' query param")

        result = self.kb_service.handle_key(d.KbCmd(char=char_val))

        if isinstance(result, (d.RenderNormalPromptCmd, d.RenderHotPromptCmd)):
            result = self.prompt_service.render_prompt(result)

        return (200, "application/json", _shape_kb_emission(result))

    @POST("/api/ingest")
    def ingest(self, body: dict, path: str) -> tuple[int, str, dict]:
        try:
            result = self.ingestion.apply_file_changes(body["content"])
        except Exception as ex:
            return (500, "text/plain", f"Ingest failed: {ex}")

        return (200, "application/json", {
            "written": result.written,
            "deleted": result.deleted,
            "errors": result.errors,
        })

    @POST("/v1/chat/completions")
    @POST("/api/desktop-mode")
    @POST("/api/inference-mode")
    def proxy_gpu(self, body: dict, path: str) -> tuple[int, str, Any]:
        req = urllib.request.Request(
            self.gpu_box_url + path,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        resp = urllib.request.urlopen(req)
        return (resp.status, resp.headers.get("Content-Type", "text/event-stream"), resp)