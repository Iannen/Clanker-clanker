from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from models import ConfigAssemblyFailure, Render

@dataclass
class SysCfgDTO:
    shared_domain_keys: str
    pud_domain_keys: str
    prompt_keys: str
    ui_render_data: dict[str, Any]

@dataclass
class RenderDTO:
    template: str
    inherit_base: bool
    inherit_domain: bool
    resolver_dicts: list[dict[str, Any]]

@dataclass
class ResolverDTO:
    anchor: str
    type: str
    files: list[Any] | None = None
    fileset: str | dict[str, Any] | None = None
    pud_fileset: str | dict[str, Any] | None = None
    shared_fileset: str | dict[str, Any] | None = None

@dataclass
class DomainDTO:
    name: str
    resolvers: list[dict[str, Any]]
    prompts: list[dict[str, Any]]

@dataclass
class PromptDTO:
    name: str
    render: dict[str, Any]

class DTOFactory:
    def sys_cfg(self, data: dict[str, Any]) -> SysCfgDTO:
        return SysCfgDTO(
            self.req_str(data, ["button_rows", "shared_domains_row"]),
            self.req_str(data, ["button_rows", "pud_domains_row"]),
            self.req_str(data, ["button_rows", "prompts_row"]),
            self.req_dict(data, ["ui_render"]),
        )
        
    def render_cfg(self, data: dict[str, Any]) -> RenderDTO:
        return RenderDTO(
            self.req_str(data, ["template"], Render.template),
            self.req_bool(data, ["inherit_base"], Render.inherit_base),
            self.req_bool(data, ["inherit_domain"], Render.inherit_domain),
            self.req_list(data, ["resolvers"]),
        )

    def resolver_cfg(self, data: dict[str, Any]) -> ResolverDTO:
        res_type = str(data["type"])
        fileset_val: str | dict[str, Any] | None = None

        if res_type == "repo_content":
            if "fileset" in data:
                fileset_val = data["fileset"]
            else:
                fileset_val = {
                    "includes": data.get("includes"),
                    "excludes": data.get("excludes", []),
                }
        return ResolverDTO(
            anchor=str(data["id"]),
            type=res_type,
            files=data.get("files"),
            fileset=fileset_val,
            pud_fileset=data.get("pud_fileset"),
            shared_fileset=data.get("shared_fileset"),
        )
    def domain_cfg(self, data: dict[str, Any]) -> DomainDTO:
        return DomainDTO(
            self.req_str(data, ["name"]),
            self.req_list(data, ["resolvers"]),
            self.req_list(data, ["prompts"]),
        )

    def prompt_cfg(self, data: dict[str, Any]) -> PromptDTO:
        return PromptDTO(
            self.req_str(data, ["name"]),
            self.req_dict(data, ["render"], default={}),
        )

    def _req(self, data: Any, path: list[str], target_type: type, default: Any = None) -> Any:
        curr = data
        path_str = " -> ".join(path)
        try:
            for k in path:
                curr = curr[k]
        except (KeyError, TypeError, IndexError):
            if default is not None:
                return default
            raise ConfigAssemblyFailure(f"Missing required config path: '{path_str}'")

        if not isinstance(curr, target_type) or (target_type is str and isinstance(curr, bool)):
            raise ConfigAssemblyFailure(
                f"Type mismatch at path '{path_str}': expected {target_type.__name__}, got {type(curr).__name__}"
            )
        return curr

    def req_str(self, data: Any, path: list[str], default: Any = None) -> str: 
        return self._req(data, path, str, default)

    def req_dict(self, data: Any, path: list[str], default: Any = None) -> dict[str, Any]: 
        return self._req(data, path, dict, default)

    def req_list(self, data: Any, path: list[str], default: Any = None) -> list[Any]: 
        return self._req(data, path, list, default)

    def req_bool(self, data: Any, path: list[str], default: Any = None) -> bool: 
        return self._req(data, path, bool, default)