from dataclasses import dataclass
from typing import overload, Optional
from ...asset_ingestion import ErrorCollector, FilelistMap, ValueExtractor, FilelistParser, Config


@dataclass
class FilelistExtractor(ValueExtractor):
    collector: ErrorCollector

    def get_filelists(self, clank_cfg, pud_cfg) -> tuple[FilelistMap | None, FilelistMap | None]:
        clank_fl = self._extract(clank_cfg)
        pud_fl = self._extract(pud_cfg, clank_fl)
        return clank_fl, pud_fl

    def clank_fl(self, cfg: Config) -> FilelistMap | None:
        self.clank_fl = self._extract(cfg)
        return self.clank_fl, self

    def unified_fl(self, cfg:Config) -> FilelistMap | None:
        return self._extract(cfg, self.clank_fl) # Should I return fl if clank fl is none? validation can continue, i think so.
    
    def _extract(self, cfg: Config, existing: Optional[FilelistMap] = None) -> FilelistMap:
        if not cfg: return None
        raw_filelists = self.opt_dict(cfg.data, ["filelists"], default={})

        result = dict(existing._data) if existing is not None else {}

        for k, v in raw_filelists.items():
            with self.collector.path(k):
                result[k] = FilelistParser(v, self.collector).parse()

        new_map = FilelistMap(data=result, collector=self.collector)
        return existing.merge(new_map) if existing is not None else new_map