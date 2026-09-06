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
            template=str(data["template"]),
            inherit_base=bool(data["inherit_base"]),
            inherit_domain=bool(data["inherit_domain"]),
            resolver_dicts=list(data["resolvers"]),
        )