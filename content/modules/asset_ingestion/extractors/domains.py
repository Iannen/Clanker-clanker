from stdlib import dataclass
from core import Domain, ConfigAssembly
from ...asset_ingestion import ErrorCollector, ValueExtractor, Config, DomParser, NamedMap

@dataclass(eq=False)
class DomainExtractor(ValueExtractor):
    shr_doms = None
    collector: ErrorCollector

    def get_domains(self, clank_cfg, clank_fs, clank_fl, pud_cfg, pud_fs, pud_fl, base_res) -> tuple[list[Domain] | None, list[Domain] | None]:
        clank_doms = self._extract(clank_cfg, clank_fs, clank_fl, base_res) # clank must be satisfied from clank fl
        pud_doms = self._extract(pud_cfg, pud_fs, pud_fl, base_res) # put from unified
        return clank_doms, pud_doms

    def _extract(self, cfg: Config, fileset_map, filelist_map, base_res) -> list[Domain] | None:
        if not self.valid_args(locals()): return None
        try: doms_dict = self.req_dict(cfg.data, ["domains"])
        except ConfigAssembly: self.collector.add_critical_complaint("config dont got no doms son"); return None
        doms_list = [
            {"name": name, **domain_data}
            for name, domain_data in doms_dict.items()
        ]
        ret_val = [DomParser(self.collector).parse(d, fileset_map, filelist_map, base_res) for d in doms_list]
        map = NamedMap(self.collector, Domain)
        
        for dom in ret_val: map.set(dom.name, dom) 
        
        #return ret_val
        return map