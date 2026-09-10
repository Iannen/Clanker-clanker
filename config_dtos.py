from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from models import (
    Domain,
    Prompt,
    Render,
    File,
    Filelist,
    FileSet,
    Resolver,
    MultiDocResolver,
    RepoContentResolver,
    ManifestResolver,
    KBStateResolver,
    TruncationSpec,
    ConfigAssemblyFailure,
    ErrorCollector,
)


@dataclass
class KbSpec:
    shared_domain_keys: str
    pud_domain_keys: str
    prompt_keys: str


class FilesetMap:
    def __init__(self, data: dict[str, FileSet], collector: ErrorCollector) -> None:
        self._data = data
        self._collector = collector

    def get(self, key: str) -> FileSet | None:
        if key not in self._data:
            #self._collector.add_complaint(f"Referenced fileset '{key}' does not exist")
            return None
        return self._data[key]

class ConfigTranslator:
    def __init__(self, extractor: ValueExtractor | None = None) -> None:
        self.extractor = extractor or ValueExtractor()
        self.collector: ErrorCollector = ErrorCollector()

    def set_collector(self, collector: ErrorCollector) -> None:
        self.collector = collector

    def get_collector(self) -> ErrorCollector:
        return self.collector

    def extract_filesets(
        self, doms_cfg_dict: dict[str, Any]
    ) -> dict[str, FileSet]:
        raw_filesets = self.extractor.req_dict(doms_cfg_dict, ["filesets"], default={})
        result = {}
        for k, v in raw_filesets.items():
            result[k] = self._build_fileset(v)
        return result

    def extract_domains(
        self,
        doms_cfg_dict: dict[str, Any],
        filesetmap: FilesetMapProtocol,
    ) -> list[Domain]:
        raw_domains = self.extractor.req_list(doms_cfg_dict, ["domains"])
        domains = []
        for d in raw_domains:
            name = self.extractor.req_str(d, ["name"])
            raw_resolvers = self.extractor.req_list(d, ["resolvers"])
            raw_prompts = self.extractor.req_list(d, ["prompts"])

            resolvers = [self._build_resolver(r, filesetmap, self.collector) for r in raw_resolvers]
            prompts = self._build_prompts(raw_prompts, filesetmap, self.collector)
            domains.append(Domain(name=name, prompts=prompts, resolvers=resolvers))
        return domains

    def process_sys_cfg(
        self, sys_cfg: dict[str, Any]
    ) -> tuple[Render, KbSpec]:
        kb_spec = KbSpec(
            shared_domain_keys=self.extractor.req_str(sys_cfg, ["button_rows", "shared_domains_row"]),
            pud_domain_keys=self.extractor.req_str(sys_cfg, ["button_rows", "pud_domains_row"]),
            prompt_keys=self.extractor.req_str(sys_cfg, ["button_rows", "prompts_row"]),
        )
        ui_render_data = self.extractor.req_dict(sys_cfg, ["ui_render"])
        ui_render = self._build_render(ui_render_data, FilesetMap({}, self.collector), self.collector)
        return ui_render, kb_spec

    def get_resolvers(
        self,
        raw_resolvers: list[dict[str, Any]],
        filesetmap: FilesetMapProtocol,
    ) -> list[Resolver]:
        return [self._build_resolver(r, filesetmap, self.collector) for r in raw_resolvers]

    def _build_prompts(
        self,
        dicts: list[dict[str, Any]],
        filesetmap: FilesetMapProtocol,
        collector: ErrorCollector,
    ) -> list[Prompt]:
        prompts = []
        for d in dicts:
            name = self.extractor.req_str(d, ["name"])
            render_dict = self.extractor.req_dict(d, ["render"], default={})
            render = self._build_render(render_dict, filesetmap, collector)
            prompts.append(Prompt(name=name, render=render))
        return prompts

    def _build_render(
        self,
        render_dict: dict[str, Any],
        filesetmap: FilesetMapProtocol,
        collector: ErrorCollector,
    ) -> Render:
        template = self.extractor.req_str(render_dict, ["template"], Render.template)
        inherit_base = self.extractor.req_bool(render_dict, ["inherit_base"], Render.inherit_base)
        inherit_domain = self.extractor.req_bool(render_dict, ["inherit_domain"], Render.inherit_domain)
        raw_resolvers = self.extractor.req_list(render_dict, ["resolvers"])
        resolvers = [self._build_resolver(r, filesetmap, collector) for r in raw_resolvers]
        return Render(
            template=template,
            resolvers=resolvers,
            inherit_base=inherit_base,
            inherit_domain=inherit_domain,
        )

    def _build_fileset(self, raw_data: Any) -> FileSet:
        includes = self.extractor.req_list(raw_data, ["includes"])
        excludes = self.extractor.req_list(raw_data, ["excludes"], default=[])
        return FileSet(includes=includes, excludes=excludes)

    def _build_file(self, data: Any) -> File:
        if isinstance(data, dict):
            filename = self.extractor.req_str(data, ["file"])
            if "tail_lines" in data:
                tail_lines = self.extractor.req_int(data, ["tail_lines"], default=None)
                trunc_spec = TruncationSpec(tail_lines=tail_lines) if tail_lines is not None else None
            else:
                trunc_spec = None
            return File(name=filename, truncation_spec=trunc_spec)
        return File(name=self.extractor.req_str({"file": data}, ["file"]))

    def _build_resolver(
        self,
        data: dict[str, Any],
        filesetmap: FilesetMapProtocol,
        collector: ErrorCollector,
    ) -> Resolver:
        res_type = self.extractor.req_str(data, ["type"])
        anchor = self.extractor.req_str(data, ["id"])

        if res_type == "multi-document-retrieval":
            raw_files = self.extractor.req_list(data, ["files"], default=[])
            file_objs = [self._build_file(f) for f in raw_files]
            return MultiDocResolver(anchor=anchor, files=Filelist(files=file_objs))

        if res_type == "repo_content":
            if "fileset" in data:
                fileset_val = self.extractor.req_str_or_dict(data, ["fileset"])
            else:
                fileset_val = {
                    "includes": self.extractor.req_list(data, ["includes"]),
                    "excludes": self.extractor.req_list(data, ["excludes"], default=[]),
                }

            if isinstance(fileset_val, str):
                fileset_obj = filesetmap.get(fileset_val)
            else:
                fileset_obj = self._build_fileset(fileset_val)
            return RepoContentResolver(anchor=anchor, fileset=fileset_obj or FileSet(includes=[], excludes=[]))

        if res_type == "repo-manifest":
            if "pud_fileset" not in data and "shared_fileset" not in data:
                raise ConfigAssemblyFailure(
                    f"Manifest resolver '{anchor}' must specify at least 'pud_fileset' or 'shared_fileset'"
                )

            pud_val = self.extractor.req_str_or_dict(data, ["pud_fileset"], default={})
            shared_val = self.extractor.req_str_or_dict(data, ["shared_fileset"], default={})

            if isinstance(pud_val, str):
                pud_fileset_obj = filesetmap.get(pud_val)
            else:
                pud_fileset_obj = self._build_fileset(pud_val) if pud_val else None

            if isinstance(shared_val, str):
                shared_fileset_obj = filesetmap.get(shared_val)
            elif isinstance(shared_val, dict) and shared_val:
                shared_fileset_obj = self._build_fileset(shared_val)
            else:
                shared_fileset_obj = None

            return ManifestResolver(
                anchor=anchor,
                pud_fileset=pud_fileset_obj or FileSet(includes=[], excludes=[]),
                shared_fileset=shared_fileset_obj,
            )

        if res_type in ("kb_info", "kb_state"):
            return KBStateResolver(anchor=anchor)

        raise ConfigAssemblyFailure(f"Unsupported resolver type: '{res_type}'")

class ValueExtractor:
    def _req(
        self, data: Any, path: list[str], target_type: type | tuple[type, ...], default: Any = None
    ) -> Any:
        curr = data
        path_str = " -> ".join(path)
        try:
            for k in path:
                curr = curr[k]
        except (KeyError, TypeError, IndexError):
            if default is not None:
                return default
            raise ConfigAssemblyFailure(f"Missing required config path: '{path_str}'")

        if not isinstance(curr, target_type) or (
            str in (target_type if isinstance(target_type, tuple) else (target_type,))
            and isinstance(curr, bool)
        ):
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