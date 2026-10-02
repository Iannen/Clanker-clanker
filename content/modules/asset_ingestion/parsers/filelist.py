from stdlib import Any, dataclass
from core import File, Filelist, TruncationSpec
from ...asset_ingestion import ErrorCollector, ValueExtractor

@dataclass
class FilelistParser(ValueExtractor):
    filelist_cfg: Any
    collector: ErrorCollector
    entity_cls = Filelist

    def parse(self) -> Filelist:
        file_objs = [self._build_file(f) for f in self.filelist_cfg]
        return Filelist(files=file_objs)

    def _build_file(self, data: Any) -> File:
        if isinstance(data, dict):
            filename = self.req_str(data, ["file"])
            trunc_spec = self._build_truncation_spec(data)
            return File(name=filename, truncation_spec=trunc_spec)
        return File(name=self.req_str({"file": data}, ["file"]))

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
            tail_lines = self.req_int(data, ["tail_lines"])
            if tail_lines is None:
                self.collector.add_complaint("TruncationSpec error: tail_lines must be an integer")
                return None
            return TruncationSpec(type=TruncationSpec.TYPE_TAIL, tail_lines=tail_lines)

        if has_from or has_upto:
            from_line = self.req_str(data, ["from_line"]) if has_from else None
            up_to = self.req_str(data, ["up_to"]) if has_upto else None
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