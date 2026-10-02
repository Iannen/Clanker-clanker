from stdlib import Any, dataclass
from core import File, Filelist, TruncationSpec
from ...asset_ingestion import ErrorCollector, ValueExtractor

@dataclass
class FilelistParser(ValueExtractor):
    data: list[str] | list[dict]
    collector: ErrorCollector
    entity_cls = Filelist

    def parse(self) -> Filelist:
        files = [self._build_file(f) for f in self.data]
        return Filelist(files=files)

    def _build_file(self, data: Any) -> File:
        if isinstance(data, dict):
            filename = self.req_str(data, ["file"])
            trunc_spec = self._build_truncation_spec(data)
            return File(name=filename, truncation_spec=trunc_spec)
        return File(name=self.req_str({"file": data}, ["file"]))

    def _build_truncation_spec(self, data: dict[str, Any]) -> TruncationSpec | None:
        tail_lines = self.opt_int(data, ["tail_lines"], [])
        from_line = self.opt_str(data, ["from_line"], [])
        up_to = self.opt_str(data, ["up_to"], [])

        if tail_lines and (from_line or up_to):
            self.collector.add_complaint("TruncationSpec conflict: tail_lines cannot be combined with from_line or up_to")
            return None

        if tail_lines: return TruncationSpec(TruncationSpec.TYPE_TAIL, tail_lines)
            

        if from_line or up_to:
            return TruncationSpec(
                type=TruncationSpec.TYPE_REGEX_RANGE,
                from_line=from_line,
                up_to=up_to,
            )