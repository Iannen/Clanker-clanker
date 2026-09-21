from typing import Any
from asset_ingestion import ErrorCollector, FilelistMap, ValueExtractor, FilelistParser


class FilelistExtractor:
    def extract(
        self,
        pud_cfg: dict[str, Any],
        shared_cfg: dict[str, Any],
        collector: ErrorCollector,
    ) -> FilelistMap:
        extractor = ValueExtractor()

        with collector.path("shared"):
            raw_shared = extractor.req_dict(shared_cfg, ["filelists"], default={})
            shared_result = {}
            for k, v in raw_shared.items():
                with collector.path(k):
                    shared_result[k] = FilelistParser(v, collector).parse()
            shared_flm = FilelistMap(data=shared_result, collector=collector)

        with collector.path("pud"):
            raw_pud = extractor.req_dict(pud_cfg, ["filelists"], default={})
            pud_result = {}
            for k, v in raw_pud.items():
                with collector.path(k):
                    pud_result[k] = FilelistParser(v, collector).parse()
            pud_flm = FilelistMap(data=pud_result, collector=collector)

        return shared_flm.merge(pud_flm)