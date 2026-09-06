from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FileSpecDTO:
    file: str
    tail_lines: int | None = None
    full_path_from_pud: bool = False

    @classmethod
    def from_raw(cls, raw: str | dict[str, Any]) -> FileSpecDTO:
        if isinstance(raw, dict):
            filename = raw.get("file", raw.get("name", ""))
            return cls(
                file=str(filename),
                tail_lines=raw.get("tail_lines"),
                full_path_from_pud=bool(raw.get("full_path_from_pud", False)),
            )
        return cls(file=str(raw))


@dataclass
class FileSetDTO:
    includes: list[str] = field(default_factory=list)
    excludes: list[str] = field(default_factory=list)

    @classmethod
    def from_raw(cls, raw: dict[str, Any] | list[str] | None) -> FileSetDTO:
        if isinstance(raw, dict):
            return cls(
                includes=list(raw.get("includes", [])),
                excludes=list(raw.get("excludes", [])),
            )
        if isinstance(raw, list):
            return cls(includes=[str(i) for i in raw], excludes=[])
        return cls()


@dataclass
class ResolverDTO:
    id: str
    type: str
    files: list[FileSpecDTO] = field(default_factory=list)
    fileset: str | FileSetDTO | None = None
    pud_fileset: str | FileSetDTO | None = None
    shared_fileset: str | FileSetDTO | None = None
    extra_fields: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ResolverDTO:
        data_copy = dict(data)
        res_id = str(data_copy.pop("id", ""))
        res_type = str(data_copy.pop("type", ""))

        raw_files = data_copy.pop("files", None)
        files = [FileSpecDTO.from_raw(f) for f in raw_files] if raw_files is not None else []

        raw_fileset = data_copy.pop("fileset", None)
        fileset = FileSetDTO.from_raw(raw_fileset) if isinstance(raw_fileset, (dict, list)) else raw_fileset

        raw_pud = data_copy.pop("pud_fileset", None)
        pud_fileset = FileSetDTO.from_raw(raw_pud) if isinstance(raw_pud, (dict, list)) else raw_pud

        raw_shared = data_copy.pop("shared_fileset", None)
        shared_fileset = FileSetDTO.from_raw(raw_shared) if isinstance(raw_shared, (dict, list)) else raw_shared

        return cls(
            id=res_id,
            type=res_type,
            files=files,
            fileset=fileset,
            pud_fileset=pud_fileset,
            shared_fileset=shared_fileset,
            extra_fields=data_copy,
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
        rows = data.get("rows", {})
        return cls(
            render=RenderDTO.from_dict(raw_render if isinstance(raw_render, dict) else {}),
            rows={str(k): str(v) for k, v in rows.items()} if isinstance(rows, dict) else {},
        )


@dataclass
class SystemCfgDTO:
    kb_def: KBDefDTO

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SystemCfgDTO:
        raw_kb = data.get("kb_def", {})
        return cls(kb_def=KBDefDTO.from_dict(raw_kb if isinstance(raw_kb, dict) else {}))