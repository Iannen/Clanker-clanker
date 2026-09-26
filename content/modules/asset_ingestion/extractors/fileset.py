from stdlib import Any, dataclass
from ...asset_ingestion import ErrorCollector, FilesetMap, ValueExtractor, FilesetParser

@dataclass
class FilesetExtractor:
    collector: ErrorCollector

    def extract(self, cfg: dict[str, Any]) -> FilesetMap:
        extractor = ValueExtractor()
        raw_filesets = extractor.req_dict(cfg, ["filesets"], default={})

        result = {}
        for k, v in raw_filesets.items():
            result[k] = FilesetParser(v, self.collector).parse()

        return FilesetMap(data=result, collector=self.collector)