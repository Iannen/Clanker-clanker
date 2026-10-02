from dataclasses import dataclass
from ...asset_ingestion import ErrorCollector, NamedMap, ValueExtractor, FilesetParser, Config
from core import FileSet

@dataclass
class FilesetExtractor(ValueExtractor):
    ec: ErrorCollector

    def get_filesets(self, clank_cfg, pud_cfg) -> tuple[NamedMap[FileSet] | None, NamedMap[FileSet] | None]:
        clank_fs = self._extract(clank_cfg)
        pud_fs = self._extract(pud_cfg, clank_fs)
        return clank_fs, pud_fs

    def _extract(self, cfg: Config, existing: Optional[NamedMap[FileSet]] = None) -> NamedMap[FileSet] | None:
        if not cfg: return None
        raw_filesets = self.opt_dict(cfg.data, ["filesets"], default={})

        res_map = existing if existing is not None else NamedMap(self.ec, FileSet)

        for k, v in raw_filesets.items():
            res_map.set(k, FilesetParser(v, self.ec).parse())

        return res_map