from dataclasses import dataclass
from typing import overload, Optional
from ...asset_ingestion import ErrorCollector, FilelistMap, ValueExtractor, FilelistParser, Config


@dataclass
class FilelistExtractor:
    collector: ErrorCollector

    @overload
    def extract(self, cfg: Config) -> FilelistMap: ...

    @overload
    def extract(self, cfg: Config, existing: FilelistMap) -> FilelistMap: ...

    def clank_fl(self, cfg: Config) -> FilelistMap | None:
        self.clank_fl = self.extract(cfg)
        return self.clank_fl, self

    def unified_fl(self, cfg:Config) -> FilelistMap | None:
        return self.extract(cfg, self.clank_fl) # Should I return fl if clank fl is none? validation can continue, i think so.
    
    def extract(self, cfg: Config, existing: Optional[FilelistMap] = None) -> FilelistMap:
        if not cfg: return None
        extractor = ValueExtractor()
        raw_filelists = extractor.opt_dict(cfg.data, ["filelists"], default={})

        result = dict(existing._data) if existing is not None else {}

        for k, v in raw_filelists.items():
            with self.collector.path(k):
                result[k] = FilelistParser(v, self.collector).parse()

        new_map = FilelistMap(data=result, collector=self.collector)
        return existing.merge(new_map) if existing is not None else new_map