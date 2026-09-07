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
class MultiDocResolverDTO(ResolverDTO):
    files: list[Any] = field(default_factory=list)

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

    def _mdr_cfg(self, data: dict[str, Any], anchor: str, res_type: str) -> MultiDocResolverDTO:
        files = self.req_list(data, ["files"], default=[])
        return MultiDocResolverDTO(
            anchor=anchor,
            type=res_type,
            files=files,
        )

    def _repo_cfg(self, data: dict[str, Any], anchor: str, res_type: str) -> RepoContentResolverDTO:
        if "fileset" in data:
            fileset_val = data["fileset"]
            if not isinstance(fileset_val, (str, dict)):
                raise ConfigAssemblyFailure(
                    f"Type mismatch at path 'fileset': expected str or dict, got {type(fileset_val).__name__}"
                )
        else:
            fileset_val = {
                "includes": self.req_list(data, ["includes"], default=[]),
                "excludes": self.req_list(data, ["excludes"], default=[]),
            }
        return RepoContentResolverDTO(
            anchor=anchor,
            type=res_type,
            fileset=fileset_val,
        )

    def _manif_cfg(self, data: dict[str, Any], anchor: str, res_type: str) -> ManifestResolverDTO:
        pud_fileset = data.get("pud_fileset", {})
        if not isinstance(pud_fileset, (str, dict)):
            raise ConfigAssemblyFailure(
                f"Type mismatch at path 'pud_fileset': expected str or dict, got {type(pud_fileset).__name__}"
            )
        shared_fileset = data.get("shared_fileset")
        if shared_fileset is not None and not isinstance(shared_fileset, (str, dict)):
            raise ConfigAssemblyFailure(
                f"Type mismatch at path 'shared_fileset': expected str or dict, got {type(shared_fileset).__name__}"
            )
        return ManifestResolverDTO(
            anchor=anchor,
            type=res_type,
            pud_fileset=pud_fileset,
            shared_fileset=shared_fileset,
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