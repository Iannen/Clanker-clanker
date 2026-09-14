from typing import Any
from app.models import (
    ConfigAssembly,
    File,
    Filelist,
    FileSet,
    KBStateResolver,
    ManifestResolver,
    MultiDocResolver,
    RepoContentResolver,
    Resolver,
    TruncationSpec,
)
from asset_ingestion.commons.error_collector import ErrorCollector
from asset_ingestion.commons.fileset_map import FilesetMap
from asset_ingestion.commons.value_extractor import ValueExtractor


class ResolverWorker:
    def __init__(
        self,
        resolver_cfg: dict[str, Any],
        collector: ErrorCollector,
        fileset_map: FilesetMap | None = None,
    ) -> None:
        self.resolver_cfg = resolver_cfg
        self.collector = collector
        self.fileset_map = fileset_map
        self.extractor = ValueExtractor()

    def parse(self) -> Resolver:
        res_type = self.extractor.req_str(self.resolver_cfg, ["type"])
        anchor = self.extractor.req_str(self.resolver_cfg, ["id"])

        if res_type == "multi-document-retrieval":
            raw_files = self.extractor.req_list(self.resolver_cfg, ["files"], default=[])
            file_objs = [self._build_file(f) for f in raw_files]
            return MultiDocResolver(anchor=anchor, files=Filelist(files=file_objs))

        if res_type == "repo_content":
            if "fileset" in self.resolver_cfg:
                fileset_val = self.extractor.req_str_or_dict(self.resolver_cfg, ["fileset"])
            else:
                fileset_val = {
                    "includes": self.extractor.req_list(self.resolver_cfg, ["includes"]),
                    "excludes": self.extractor.req_list(self.resolver_cfg, ["excludes"], default=[]),
                }

            if isinstance(fileset_val, str):
                fileset_obj = self.fileset_map.get(fileset_val) if self.fileset_map else None
            else:
                fileset_obj = self._build_fileset(fileset_val)
            return RepoContentResolver(anchor=anchor, fileset=fileset_obj or FileSet(includes=[], excludes=[]))

        if res_type == "repo-manifest":
            if "pud_fileset" not in self.resolver_cfg and "shared_fileset" not in self.resolver_cfg:
                raise ConfigAssembly(
                    f"Manifest resolver '{anchor}' must specify at least 'pud_fileset' or 'shared_fileset'"
                )

            pud_val = self.extractor.req_str_or_dict(self.resolver_cfg, ["pud_fileset"], default={})
            shared_val = self.extractor.req_str_or_dict(self.resolver_cfg, ["shared_fileset"], default={})

            if isinstance(pud_val, str):
                pud_fileset_obj = self.fileset_map.get(pud_val) if self.fileset_map else None
            else:
                pud_fileset_obj = self._build_fileset(pud_val) if pud_val else None

            if isinstance(shared_val, str):
                shared_fileset_obj = self.fileset_map.get(shared_val) if self.fileset_map else None
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

    def _build_fileset(self, raw_data: Any) -> FileSet:
        includes = self.extractor.req_list(raw_data, ["includes"])
        excludes = self.extractor.req_list(raw_data, ["excludes"], default=[])
        return FileSet(includes=includes, excludes=excludes)

    def _build_file(self, data: Any) -> File:
        if isinstance(data, dict):
            filename = self.extractor.req_str(data, ["file"])
            trunc_spec = self._build_truncation_spec(data)
            return File(name=filename, truncation_spec=trunc_spec)
        return File(name=self.extractor.req_str({"file": data}, ["file"]))

    def _build_truncation_spec(self, data: dict[str, Any]) -> TruncationSpec | None:
        has_tail = "tail_lines" in data
        has_from = "from_line" in data
        has_upto = "up_to" in data

        if has_tail and (has_from or has_upto):
            self.collector.add_complaint(
                "TruncationSpec conflict: tail_lines cannot be combined with from_line or up_to"
            )
            return None

        if has_tail:
            tail_lines = self.extractor.req_int(data, ["tail_lines"], default=None)
            if tail_lines is None:
                self.collector.add_complaint("TruncationSpec error: tail_lines must be an integer")
                return None
            return TruncationSpec(type=TruncationSpec.TYPE_TAIL, tail_lines=tail_lines)

        if has_from or has_upto:
            from_line = self.extractor.req_str(data, ["from_line"], default=None) if has_from else None
            up_to = self.extractor.req_str(data, ["up_to"], default=None) if has_upto else None
            return TruncationSpec(
                type=TruncationSpec.TYPE_REGEX_RANGE,
                from_line=from_line,
                up_to=up_to,
            )

        trunc_keys = {"tail_lines", "from_line", "up_to"}
        if any(k in data for k in trunc_keys):
            self.collector.add_complaint("TruncationSpec error: invalid truncation specification")
            return None

        return None