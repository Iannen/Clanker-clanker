from dataclasses import dataclass
from typing import overload, Optional
from ...asset_ingestion import ErrorCollector, FilesetMap, ValueExtractor, FilesetParser, Config


@dataclass
class FilesetExtractor:
    collector: ErrorCollector

    @overload
    def extract(self, cfg: Config) -> FilesetMap: ...

    @overload
    def extract(self, cfg: Config, existing: FilesetMap) -> FilesetMap: ...

    def extract(self, cfg: Config, existing: Optional[FilesetMap] = None) -> FilesetMap:
        extractor = ValueExtractor()
        raw_filesets = extractor.opt_dict(cfg.data, ["filesets"], default={})

        result = dict(existing._data) if existing is not None else {}

        for k, v in raw_filesets.items():
            result[k] = FilesetParser(v, self.collector).parse()

        new_map = FilesetMap(data=result, collector=self.collector)
        return existing.merge(new_map) if existing is not None else new_map