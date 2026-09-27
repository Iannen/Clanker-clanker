from stdlib import dataclass
from ...asset_ingestion import ErrorCollector, FilesetMap, ValueExtractor, FilesetParser, Config

@dataclass
class FilesetExtractor:
    collector: ErrorCollector

    def extract(self, cfg: Config) -> FilesetMap:
        extractor = ValueExtractor()
        raw_filesets = extractor.opt_dict(cfg.data, ["filesets"], default= {})
        result = {}
        for k, v in raw_filesets.items():
            result[k] = FilesetParser(v, self.collector).parse()

        return FilesetMap(data=result, collector=self.collector)