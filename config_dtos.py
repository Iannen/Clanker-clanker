from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ResolverDTO:
    id: str
    type: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ResolverDTO:
        return cls(
            id=str(data.get("id", "")),
            type=str(data.get("type", "")),
        )


@dataclass
class RenderDTO:
    template: str = "prompt_template"
    resolvers: list[ResolverDTO] = field(default_factory=list)
    inherit_base: bool = True
    inherit_domain: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RenderDTO:
        raw_resolvers = data.get("resolvers", [])
        return cls(
            template=str(data.get("template", "prompt_template")),
            resolvers=[ResolverDTO.from_dict(r) for r in raw_resolvers if isinstance(r, dict)],
            inherit_base=bool(data.get("inherit_base", True)),
            inherit_domain=bool(data.get("inherit_domain", True)),
        )


@dataclass
class KBDefDTO:
    render: RenderDTO
    rows: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KBDefDTO:
        raw_render = data.get("render", {})
        raw_rows = data.get("rows", {})
        return cls(
            render=RenderDTO.from_dict(raw_render if isinstance(raw_render, dict) else {}),
            rows={str(k): str(v) for k, v in raw_rows.items()} if isinstance(raw_rows, dict) else {},
        )


@dataclass
class SystemCfgDTO:
    kb_def: KBDefDTO

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SystemCfgDTO:
        raw_kb = data.get("kb_def", {})
        return cls(kb_def=KBDefDTO.from_dict(raw_kb if isinstance(raw_kb, dict) else {}))