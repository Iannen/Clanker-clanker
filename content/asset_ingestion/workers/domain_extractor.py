from typing import Any
from app.models import (
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
    ConfigAssembly,
)
from asset_ingestion.commons.error_collector import ErrorCollector
from asset_ingestion.commons.fileset_map import FilesetMap
from asset_ingestion.commons.value_extractor import ValueExtractor
from asset_ingestion.workers.ui_render_extractor import RenderWorker

class DomainExtractor:
    def __init__(
        self,
        doms_cfg_dict: dict[str, Any],
        collector: ErrorCollector,
        fileset_map: FilesetMap,
    ) -> None:
        self.doms_cfg_dict = doms_cfg_dict
        self.collector = collector
        self.fileset_map = fileset_map
        self.extractor = ValueExtractor()

    def _build_fileset(self, raw_data: Any) -> FileSet:
        includes = self.extractor.req_list(raw_data, ["includes"])
        excludes = self.extractor.req_list(raw_data, ["excludes"], default=[])
        return FileSet(includes=includes, excludes=excludes)

    def extract(self) -> list[Domain]:
        raw_domains = self.extractor.req_list(self.doms_cfg_dict, ["domains"])
        domains = []
        for d in raw_domains:
            name = self.extractor.req_str(d, ["name"])
            self.collector.push_path(name)
            try:
                raw_resolvers = self.extractor.req_list(d, ["resolvers"])
                raw_prompts = self.extractor.req_list(d, ["prompts"])

                resolvers = [self._build_resolver(r) for r in raw_resolvers]
                prompts = self._build_prompts(raw_prompts)
                domains.append(Domain(name=name, prompts=prompts, resolvers=resolvers))
            finally:
                self.collector.pop_path()
        return domains

    def _build_prompts(self, dicts: list[dict[str, Any]]) -> list[Prompt]:
        prompts = []
        for d in dicts:
            name = self.extractor.req_str(d, ["name"])
            self.collector.push_path(name)
            try:
                render_dict = self.extractor.req_dict(d, ["render"], default={})
                render = RenderWorker(render_dict, self.collector, self.fileset_map).extract()
                prompts.append(Prompt(name=name, render=render))
            finally:
                self.collector.pop_path()
        return prompts

    def _build_file(self, data: Any) -> File:
        if isinstance(data, dict):
            filename = self.extractor.req_str(data, ["file"])
            trunc_spec = self._build_truncation_spec(data)
            return File(name=filename, truncation_spec=trunc_spec)
        return File(name=self.extractor.req_str({"file": data}, ["file"]))

    def _build_resolver(self, data: dict[str, Any]) -> Resolver:
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
                fileset_obj = self.fileset_map.get(fileset_val)
            else:
                fileset_obj = self._build_fileset(fileset_val)
            return RepoContentResolver(anchor=anchor, fileset=fileset_obj or FileSet(includes=[], excludes=[]))

        if res_type == "repo-manifest":
            if "pud_fileset" not in data and "shared_fileset" not in data:
                raise ConfigAssembly(
                    f"Manifest resolver '{anchor}' must specify at least 'pud_fileset' or 'shared_fileset'"
                )

            pud_val = self.extractor.req_str_or_dict(data, ["pud_fileset"], default={})
            shared_val = self.extractor.req_str_or_dict(data, ["shared_fileset"], default={})

            if isinstance(pud_val, str):
                pud_fileset_obj = self.fileset_map.get(pud_val)
            else:
                pud_fileset_obj = self._build_fileset(pud_val) if pud_val else None

            if isinstance(shared_val, str):
                shared_fileset_obj = self.fileset_map.get(shared_val)
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

        raise ConfigAssembly(f"Unsupported resolver type: '{res_type}'")