from dataclasses import dataclass
from typing import overload, Optional
from ...asset_ingestion import ErrorCollector, FilesetMap, ValueExtractor, FilesetParser, Config


@dataclass
class FilesetExtractor(ValueExtractor):
    collector: ErrorCollector

    def clank_fs(self, cfg: Config) -> FilesetMap | None:
        self.clank_fs = self._extract(cfg)
        return self.clank_fs, self

    def unified_fs(self, cfg:Config) -> FilesetMap | None:
        return self._extract(cfg, self.clank_fs) # Should I return fl if clank fl is none? validation can continue, i think so.

    def _extract(self, cfg: Config, existing: Optional[FilesetMap] = None) -> FilesetMap | None:
        self.valid_args(locals())
        if not cfg: return None
        raw_filesets = self.opt_dict(cfg.data, ["filesets"], default={})

        result = dict(existing._data) if existing is not None else {}

        for k, v in raw_filesets.items():
            result[k] = FilesetParser(v, self.collector).parse()

        new_map = FilesetMap(data=result, collector=self.collector)
        return existing.merge(new_map) if existing is not None else new_map