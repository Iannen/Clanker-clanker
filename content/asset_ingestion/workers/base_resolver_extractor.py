from typing import Any
from app.models import File, Filelist, MultiDocResolver, TruncationSpec
from asset_ingestion.commons.error_collector import ErrorCollector
from asset_ingestion.commons.value_extractor import ValueExtractor


class BaseResolverExtractor:
    def __init__(self, cfg_dict: dict[str, Any], collector: ErrorCollector) -> None:
        self.cfg_dict = cfg_dict
        self.collector = collector
        self.extractor = ValueExtractor()

    def extract(self) -> MultiDocResolver | None:
        self.collector.push_path("base_resolvers")
        try:
            raw_resolvers = self.extractor.req_list(self.cfg_dict, ["base_resolvers"], default=[])
            extracted: list[MultiDocResolver] = []

            for r in raw_resolvers:
                res_type = self.extractor.req_str(r, ["type"])
                anchor = self.extractor.req_str(r, ["id"])

                if res_type != "multi-document-retrieval":
                    self.collector.add_complaint(
                        f"Expected 'multi-document-retrieval' resolver type in base_resolvers, got '{res_type}'"
                    )
                    continue

                if len(extracted) >= 1:
                    self.collector.add_complaint(
                        f"Extraneous base resolver '{anchor}' encountered; at most 1 base resolver expected"
                    )
                    continue

                raw_files = self.extractor.req_list(r, ["files"], default=[])
                file_objs = [self._build_file(f) for f in raw_files]
                extracted.append(MultiDocResolver(anchor=anchor, files=Filelist(files=file_objs)))

            return extracted[0] if extracted else None
        finally:
            self.collector.pop_path()

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