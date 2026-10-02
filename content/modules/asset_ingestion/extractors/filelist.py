from dataclasses import dataclass
from ...asset_ingestion import ErrorCollector, NamedMap, ValueExtractor, FilelistParser, Config
from core import Filelist

@dataclass
class FilelistExtractor(ValueExtractor):
    ec: ErrorCollector

    def get_filelists(self, clank_cfg, pud_cfg) -> tuple[NamedMap[Filelist] | None, NamedMap[Filelist] | None]:
        clank_fl = self._extract(clank_cfg)
        pud_fl = self._extract(pud_cfg, clank_fl)
        return clank_fl, pud_fl

    def _extract(self, cfg: Config | None, existing: Optional[NamedMap[Filelist]] = None) -> NamedMap[Filelist] | None:
        if not cfg: return None
        raw_filelists = self.opt_dict(cfg.data, ["filelists"], default={})

        flm = existing if existing is not None else NamedMap(self.ec, Filelist)

        for k, v in raw_filelists.items():
            flm.set(k, FilelistParser(v, self.ec).parse())

        return flm