from stdlib import Any, dataclass
from ...asset_ingestion import ErrorCollector, FilelistMap, ValueExtractor, FilelistParser, Config


@dataclass
class FilelistExtractor:
    collector: ErrorCollector

    def extract(self, cfg: dict[str, Any]) -> FilelistMap:
        extractor = ValueExtractor()
        #raw_filelists = extractor.req_dict(cfg, ["filelists"], default={})
        raw_filelists = extractor.opt_dict(cfg, ["filelists"], default={})

        result = {}
        for k, v in raw_filelists.items():
            with self.collector.path(k):
                result[k] = FilelistParser(v, self.collector).parse()

        return FilelistMap(data=result, collector=self.collector)

@dataclass
class NewFilelistExtractor:
    collector: ErrorCollector

    def extract(self, cfg: Config) -> FilelistMap:
        extractor = ValueExtractor()
        #raw_filelists = extractor.req_dict(cfg.data, ["filelists"], default={})
        raw_filelists = extractor.opt_dict(cfg.data, ["filelists"], default={})

        result = {}
        for k, v in raw_filelists.items():
            with self.collector.path(k):
                result[k] = FilelistParser(v, self.collector).parse()

        return FilelistMap(data=result, collector=self.collector)