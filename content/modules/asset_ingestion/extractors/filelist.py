from dataclasses import dataclass
from ...asset_ingestion import ErrorCollector, FilelistMap, ValueExtractor, FilelistParser, Config

@dataclass
class FilelistExtractor(ValueExtractor):
    collector: ErrorCollector

    def get_filelists(self, clank_cfg, pud_cfg) -> tuple[FilelistMap | None, FilelistMap | None]:
        clank_fl = self._extract(clank_cfg)
        pud_fl = self._extract(pud_cfg, clank_fl)
        return clank_fl, pud_fl
    
    def _extract(self, cfg: Config | None, existing: FilelistMap | None = None) -> FilelistMap | None:
        if not cfg: return None
        raw_filelists = self.opt_dict(cfg.data, ["filelists"], default={})

        result = dict(existing._data) if existing is not None else {}

        for k, v in raw_filelists.items():
            result[k] = FilelistParser(v, self.collector).parse()

        new_map = FilelistMap(data=result, collector=self.collector)
        return existing.merge(new_map) if existing is not None else new_map