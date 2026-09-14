from typing import Any
from asset_ingestion.commons.error_collector import ErrorCollector
from asset_ingestion.commons.fileset_map import FilesetMap
from asset_ingestion.commons.value_extractor import ValueExtractor
from asset_ingestion.parsers.fileset import FilesetParser

class FilesetExtractor:
    def extract(
        self,
        pud_cfg: dict[str, Any],
        shared_cfg: dict[str, Any],
        collector: ErrorCollector,
    ) -> FilesetMap:
        extractor = ValueExtractor()
        raw_shared = extractor.req_dict(shared_cfg, ["filesets"], default={})
        shared_result = {}
        for k, v in raw_shared.items():
            shared_result[k] = FilesetParser(v, collector).parse()
        shared_fsm = FilesetMap(data=shared_result, collector=collector)

        raw_pud = extractor.req_dict(pud_cfg, ["filesets"], default={})
        pud_result = {}
        for k, v in raw_pud.items():
            pud_result[k] = FilesetParser(v, collector).parse()
        pud_fsm = FilesetMap(data=pud_result, collector=collector)

        return shared_fsm.merge(pud_fsm)