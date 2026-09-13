from typing import Any
from app.models import FileSet
from asset_ingestion.commons.error_collector import ErrorCollector
from asset_ingestion.commons.fileset_map import FilesetMap
from asset_ingestion.commons.value_extractor import ValueExtractor

class FilesetExtractor:
    def __init__(self, doms_cfg_dict: dict[str, Any], collector: ErrorCollector) -> None:
        self.doms_cfg_dict = doms_cfg_dict
        self.collector = collector
        self.extractor = ValueExtractor()

    def extract(self) -> FilesetMap:
        raw_filesets = self.extractor.req_dict(self.doms_cfg_dict, ["filesets"], default={})
        result = {}
        for k, v in raw_filesets.items():
            result[k] = self._build_fileset(v)
        return FilesetMap(data=result, collector=self.collector)

    def _build_fileset(self, raw_data: Any) -> FileSet:
        includes = self.extractor.req_list(raw_data, ["includes"])
        excludes = self.extractor.req_list(raw_data, ["excludes"], default=[])
        return FileSet(includes=includes, excludes=excludes)