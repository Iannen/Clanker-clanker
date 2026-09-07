from __future__ import annotations
from dataclasses import dataclass, field
from abc import ABC
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
class ResolverDTO(ABC):
    anchor: str
    type: str

@dataclass
class TruncationSpecDTO:
    tail_lines: int | None = None

@dataclass
class FileDTO:
    name: str
    full_path_from_pud: bool = False
    truncation_spec: TruncationSpecDTO | None = None

@dataclass
class FilelistDTO:
    files: list[FileDTO] = field(default_factory=list)

@dataclass
class MultiDocResolverDTO(ResolverDTO):
    files: FilelistDTO = field(default_factory=FilelistDTO)

@dataclass
class RepoContentResolverDTO(ResolverDTO):
    fileset: str | dict[str, Any] = field(default_factory=dict)

@dataclass
class ManifestResolverDTO(ResolverDTO):
    pud_fileset: str | dict[str, Any] = field(default_factory=dict)
    shared_fileset: str | dict[str, Any] | None = None

@dataclass
class KBStateResolverDTO(ResolverDTO):
    pass

@dataclass
class DomainDTO:
    name: str
    resolvers: list[dict[str, Any]]
    prompts: list[dict[str, Any]]

@dataclass
class PromptDTO:
    name: str
    render: dict[str, Any]

@dataclass
class FileSetDTO:
    includes: list[str]
    excludes: list[str]

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
        res_type = self.req_str(data, ["type"])
        anchor = self.req_str(data, ["id"])

        if res_type in ("multi-document-retrieval", "full-path-file-retrieval"):
            return self._mdr_cfg(data, anchor, res_type)
        if res_type == "repo_content":
            return self._repo_cfg(data, anchor, res_type)
        if res_type == "repo-manifest":
            return self._manif_cfg(data, anchor, res_type)
        if res_type in ("kb_info", "kb_state"):
            return self._ui_cfg(anchor, res_type)
        raise ConfigAssemblyFailure(f"Unsupported resolver type: '{res_type}'")

    def truncation_spec_cfg(self, data: Any) -> TruncationSpecDTO:
        return TruncationSpecDTO(
            tail_lines=self.req_int(data, ["tail_lines"]) if isinstance(data, dict) and "tail_lines" in data else None
        )

    def file_cfg(self, data: Any) -> FileDTO:
        if isinstance(data, dict):
            name = self.req_str(data, ["file"]) if "file" in data else self.req_str(data, ["name"])
            full_path = self.req_bool(data, ["full_path_from_pud"], default=False)
            trunc_spec = self.truncation_spec_cfg(data) if "tail_lines" in data else None
            return FileDTO(name=name, full_path_from_pud=full_path, truncation_spec=trunc_spec)
        return FileDTO(name=self.req_str({"file": data}, ["file"]))

    def filelist_cfg(self, data: Any) -> FilelistDTO:
        raw_list = self.req_list({"files": data}, ["files"]) if not isinstance(data, list) else data
        return FilelistDTO(files=[self.file_cfg(f) for f in raw_list])

    def _mdr_cfg(self, data: dict[str, Any], anchor: str, res_type: str) -> MultiDocResolverDTO:
        raw_files = self.req_list(data, ["files"], default=[])
        filelist_dto = self.filelist_cfg(raw_files)
        if res_type == "full-path-file-retrieval":
            for f in filelist_dto.files:
                f.full_path_from_pud = True
        return MultiDocResolverDTO(
            anchor=anchor,
            type=res_type,
            files=filelist_dto,
        )

    def _repo_cfg(self, data: dict[str, Any], anchor: str, res_type: str) -> RepoContentResolverDTO:
        if "fileset" in data:
            fileset_val = self.req_str_or_dict(data, ["fileset"])
        else:
            fileset_val = {
                "includes": self.req_list(data, ["includes"]),
                "excludes": self.req_list(data, ["excludes"], default=[]),
            }
        return RepoContentResolverDTO(
            anchor=anchor,
            type=res_type,
            fileset=fileset_val,
        )

    def _manif_cfg(self, data: dict[str, Any], anchor: str, res_type: str) -> ManifestResolverDTO:
        if "pud_fileset" not in data and "shared_fileset" not in data:
            raise ConfigAssemblyFailure(
                f"Manifest resolver '{anchor}' must specify at least 'pud_fileset' or 'shared_fileset'"
            )

        return ManifestResolverDTO(
            anchor=anchor,
            type=res_type,
            pud_fileset=self.req_str_or_dict(data, ["pud_fileset"], default={}),
            shared_fileset=self.req_str_or_dict(data, ["shared_fileset"], default={}),
        )

    def _ui_cfg(self, anchor: str, res_type: str) -> KBStateResolverDTO:
        return KBStateResolverDTO(
            anchor=anchor,
            type=res_type,
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

    def fileset_cfg(self, data: Any) -> FileSetDTO:
        return FileSetDTO(
            includes=self.req_list(data, ["includes"]),
            excludes=self.req_list(data, ["excludes"], default=[]),
        )

    def _req(self, data: Any, path: list[str], target_type: type | tuple[type, ...], default: Any = None) -> Any:
        curr = data
        path_str = " -> ".join(path)
        try:
            for k in path:
                curr = curr[k]
        except (KeyError, TypeError, IndexError):
            if default is not None:
                return default
            raise ConfigAssemblyFailure(f"Missing required config path: '{path_str}'")

        if not isinstance(curr, target_type) or (str in (target_type if isinstance(target_type, tuple) else (target_type,)) and isinstance(curr, bool)):
            expected_name = (
                " or ".join(t.__name__ for t in target_type)
                if isinstance(target_type, tuple)
                else target_type.__name__
            )
            raise ConfigAssemblyFailure(
                f"Type mismatch at path '{path_str}': expected {expected_name}, got {type(curr).__name__}"
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

    def req_int(self, data: Any, path: list[str], default: Any = None) -> int:
        return self._req(data, path, int, default)

    def req_str_or_dict(self, data: Any, path: list[str], default: Any = None) -> str | dict[str, Any]:
        return self._req(data, path, (str, dict), default)