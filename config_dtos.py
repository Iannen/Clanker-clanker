from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class SystemConfigDataDTO:
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
    renders: dict[str, Any]

    @property
    def render(self) -> dict[str, Any]:
        return self.renders

class DTOFactory:
    def sys_cfg(self, data: dict[str, Any]) -> SystemConfigDataDTO:
        return SystemConfigDataDTO(
            shared_domain_keys=str(data["button_rows"]["shared_domains_row"]),
            pud_domain_keys=str(data["button_rows"]["pud_domains_row"]),
            prompt_keys=str(data["button_rows"]["prompts_row"]),
            ui_render_data=data["ui_render"],
        )
        
    def render_cfg(self, data: dict[str, Any]) -> RenderDTO:
        return RenderDTO(
            template=str(data.get("template", "prompt_template")),
            inherit_base=bool(data.get("inherit_base", True)),
            inherit_domain=bool(data.get("inherit_domain", True)),
            resolver_dicts=list(data.get("resolvers", [])),
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
            name=str(data["name"]),
            resolvers=list(data.get("resolvers", [])),
            prompts=list(data.get("prompts", [])),
        )

    def prompt_cfg(self, data: dict[str, Any]) -> PromptDTO:
        return PromptDTO(
            name=str(data["name"]),
            renders=dict(data.get("render", {})),
        )