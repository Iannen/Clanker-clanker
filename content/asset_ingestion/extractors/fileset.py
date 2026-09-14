from typing import Any
from asset_ingestion.commons.error_collector import ErrorCollector
from asset_ingestion.commons.fileset_map import FilesetMap
from asset_ingestion.commons.value_extractor import ValueExtractor
from asset_ingestion.parsers.fileset import FilesetParser

class FilesetExtractor:
    def __init__(self, doms_cfg_dict: dict[str, Any], collector: ErrorCollector) -> None:
        self.doms_cfg_dict = doms_cfg_dict
        self.collector = collector
        self.extractor = ValueExtractor()

    def extract(self) -> FilesetMap:
        raw_filesets = self.extractor.req_dict(self.doms_cfg_dict, ["filesets"], default={})
        result = {}
        for k, v in raw_filesets.items():
            result[k] = FilesetParser(v, self.collector).parse()
        return FilesetMap(data=result, collector=self.collector)