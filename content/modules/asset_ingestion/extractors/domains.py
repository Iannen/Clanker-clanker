from stdlib import Any, dataclass, field
from core import Domain, Prompt, Resolver, ConfigAssembly
from ...asset_ingestion import ErrorCollector, ValueExtractor, Config, DomParser, NotFound

@dataclass(eq=False)
class DomainExtractor(ValueExtractor):
    shr_doms = None
    collector: ErrorCollector

    def get_domains(self, clank_cfg, clank_fs, clank_fl, pud_cfg, pud_fs, pud_fl, base_res):
        clank_doms = self._extract(clank_cfg, clank_fs, clank_fl, base_res)
        pud_doms = self._extract(pud_cfg, pud_fs, pud_fl, base_res)
        return clank_doms, pud_doms

    def _extract(self, cfg: Config, fileset_map, filelist_map, base_res) -> list[Domain] | None:
        if not self.valid_args(locals()): return None
        try: return [DomParser(self.collector).parse(d, fileset_map, filelist_map, base_res) for d in self.req_list(cfg.data, ["domains"])]
        except ConfigAssembly: self.collector.add_critical_complaint(f"{cfg.name}: does not have domains list!")