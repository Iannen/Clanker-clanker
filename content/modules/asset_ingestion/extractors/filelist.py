from stdlib import Any, dataclass
from ...asset_ingestion import ErrorCollector, FilelistMap, ValueExtractor, FilelistParser


@dataclass
class FilelistExtractor:
    collector: ErrorCollector

    def extract(self, cfg: dict[str, Any]) -> FilelistMap:
        extractor = ValueExtractor()
        raw_filelists = extractor.req_dict(cfg, ["filelists"], default={})

        result = {}
        for k, v in raw_filelists.items():
            with self.collector.path(k):
                result[k] = FilelistParser(v, self.collector).parse()

        return FilelistMap(data=result, collector=self.collector)