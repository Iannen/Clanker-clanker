from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class SystemConfigDataDTO:
    shared_domain_keys: str
    pud_domain_keys: str
    prompt_keys: str
    ui_render_data: dict[str, Any]
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SystemConfigDataDTO:
        return cls(
            shared_domain_keys=str(data["button_rows"]["shared_domains_row"]),
            pud_domain_keys=str(data["button_rows"]["pud_domains_row"]),
            prompt_keys=str(data["button_rows"]["prompts_row"]),
            ui_render_data=data["ui_render"],
        )