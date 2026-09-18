from typing import Any
from app.entities import File, Filelist, TruncationSpec
from asset_ingestion.commons.error_collector import ErrorCollector
from asset_ingestion.commons.fileset_map import FilelistMap
from asset_ingestion.commons.value_extractor import ValueExtractor


class FilelistParser:
    def __init__(
        self,
        filelist_cfg: Any,
        collector: ErrorCollector,
        filelist_map: FilelistMap | None = None,
    ) -> None:
        self.filelist_cfg = filelist_cfg
        self.collector = collector
        self.filelist_map = filelist_map
        self.extractor = ValueExtractor()

    def parse(self) -> Filelist:
        if isinstance(self.filelist_cfg, str):
            if self.filelist_map is not None:
                filelist_obj = self.filelist_map.get(self.filelist_cfg)
                if filelist_obj is not None:
                    return filelist_obj
            return Filelist(files=[])

        if isinstance(self.filelist_cfg, list):
            file_objs = [self._build_file(f) for f in self.filelist_cfg]
            return Filelist(files=file_objs)

        return Filelist(files=[])

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