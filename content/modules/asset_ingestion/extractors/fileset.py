from dataclasses import dataclass
from ...asset_ingestion import ErrorCollector, FilesetMap, ValueExtractor, FilesetParser, Config

@dataclass
class FilesetExtractor(ValueExtractor):
    collector: ErrorCollector

    def get_filesets(self, clank_cfg, pud_cfg) -> tuple[FilesetMap | None, FilesetMap | None]:
        clank_fs = self._extract(clank_cfg)
        pud_fs = self._extract(pud_cfg, clank_fs)
        return clank_fs, pud_fs

    def _extract(self, cfg: Config, existing: Optional[FilesetMap] = None) -> FilesetMap | None:
        if not cfg: return None
        raw_filesets = self.opt_dict(cfg.data, ["filesets"], default={})

        result = dict(existing._data) if existing is not None else {}

        for k, v in raw_filesets.items():
            result[k] = FilesetParser(v, self.collector).parse()

        new_map = FilesetMap(data=result, collector=self.collector)
        return existing.merge(new_map) if existing is not None else new_map