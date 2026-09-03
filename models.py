from __future__ import annotations
from enum import Enum
from pathlib import Path
from typing import Any, Callable, ClassVar
from pydantic import BaseModel, ConfigDict, Field, model_validator

class SystemKeys:
    DELIM = "§"

class Constructed(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
class Config(Constructed):
    DEFAULT_REL_PATH: ClassVar[str] = "/.clanker/config.yaml"
    DEFAULT_ASSETS_DIR: ClassVar[Path] = Path(".clanker/assets")
    layout: str
    domains: list[str]

class Resolver(BaseModel):
    class Type(str, Enum):
        MULTI_DOC = "multi-document-retrieval"
        FULL_PATH_FILE = "full-path-file-retrieval"
        REPO_CONTENT = "repo_content"
        KB_INFO = "kb_info"
        REPO_MANIFEST = "repo-manifest"
    id: str
    type: Type
    payload: dict[str, Any] = {}

    @model_validator(mode="before")
    @classmethod
    def extract_payload(cls, data: Any) -> Any:
        if isinstance(data, dict):
            obj_id = data.get("id", "")
            obj_type = data.get("type", None)
            payload = {k: v for k, v in data.items() if k not in ("id", "type")}
            return {
                "id": obj_id,
                "type": obj_type,
                "payload": payload
            }
        return data

class Render(Constructed):
    name: str
    template: str = "prompt_template"
    resolvers: list[Resolver] = []
    inherit_base: bool = True
    inherit_domain: bool = True

class Domain(Constructed):
    name: str
    renders: list[Render] = []
    resolvers: list[Resolver] = []

class Button(Constructed):
    model_config = ConfigDict(
        extra="forbid",
        arbitrary_types_allowed=True  
    )
    type: str 
    primary_letter: str
    secondary_letter: str
    inhabitant: Domain | Render | None = None
    primary_action: Callable | None = None
    shift_action: Callable | None = None

    def get_repl_map(self, label: str, template: str) -> dict[str, str]:
        lines = template.strip("\n").splitlines()
        norm_label = label[:6].ljust(6)
        mapped_lines = [
            lines[0],
            lines[1],
            lines[2].replace(SystemKeys.DELIM, self.primary_letter, 1),
            lines[3],
            lines[4].replace(SystemKeys.DELIM * 6, norm_label, 1),
        ]
        return {f"{self.primary_letter}{idx}": line for idx, line in enumerate(mapped_lines)}

class Keyboard(Constructed):
    button_map: dict[str, Button] = Field(default_factory=dict)
    render: Render 
    resolvers: list[Resolver] = []
    selected_key: str | None = None

    def get_unique_buttons(self, btn_type: str | None = None) -> list[Button]:
        unique = {btn.primary_letter: btn for btn in self.button_map.values()}.values()
        if btn_type is None:
            return list(unique)
        return [btn for btn in unique if btn.type == btn_type]

    def handle_key(self, key: str) -> ActionResult | None:
        btn = self.button_map.get(key)
        if btn is None:
            return None
        if key == btn.primary_letter and callable(btn.primary_action):
            return btn.primary_action(btn.primary_letter)
        elif key == btn.secondary_letter and callable(btn.shift_action):
            return btn.shift_action(btn.primary_letter)
        return ActionResult(f"No action bound to key '{key}'")