from stdlib import dataclass
from core import Domain, ConfigAssembly
from ...asset_ingestion import ErrorCollector, ValueExtractor, Config, DomParser, NamedMap

@dataclass(eq=False)
class DomainExtractor(ValueExtractor):
    collector: ErrorCollector
    clank_cfg: Config
    pud_cfg: Config
    def get_domains(self, clank_args, pud_args) -> tuple[NamedMap[Domain] | None, NamedMap[Domain] | None, NamedMap[Domain] | None]:
        #clank_args = (clank_fs, clank_fl, base_res)
        #pud_args = (unified_fs, unified_fl, base_res)
        clank_doms = self._extract(self.clank_cfg, clank_args)
        pud_doms = self._extract(self.pud_cfg, pud_args)

        if clank_doms is None:
            return None, pud_doms, None

        unified_doms = clank_doms.clone()
        if pud_doms:
            for k, v in pud_doms.items():
                unified_doms.set(k, v)

        return clank_doms, pud_doms, unified_doms
    
    def _extract(self, cfg: Config, parser_args: tuple | None = None) -> NamedMap[Domain] | None:
        if not self.valid_args(locals()): return None
        try: doms_dict = self.req_dict(cfg.data, ["domains"])
        except ConfigAssembly: self.collector.add_critical_complaint("config dont got no doms son"); return None

        args = parser_args or ()
        domain_map = NamedMap(self.collector, Domain)

        for k, v in doms_dict.items():
            domain_map.set(k, DomParser(self.collector).parse(k, v, *args))

        return domain_map
    """
    def _extract(self, cfg: Config, parser_args) -> NamedMap[Domain] | None:
        if not self.valid_args(locals()): return None
        try: doms_dict = self.req_dict(cfg.data, ["domains"])
        except ConfigAssembly: self.collector.add_critical_complaint("config dont got no doms son"); return None

        doms_list = [{"name": name, **domain_data} for name, domain_data in doms_dict.items()]
        ret_val = [DomParser(self.collector).parse(d, *parser_args) for d in doms_list]
        
        domain_map = NamedMap(self.collector, Domain)
        for dom in ret_val: 
            domain_map.set(dom.name, dom) 

        return domain_map
    """
"""
@dataclass(eq=False)
class DomainExtractor(ValueExtractor):
    shr_doms = None
    collector: ErrorCollector

    def get_domains(self, clank_cfg, clank_fs, clank_fl, pud_cfg, pud_fs, pud_fl, base_res) -> tuple[list[Domain] | None, list[Domain] | None]:
        clank_doms = self._extract(clank_cfg, clank_fs, clank_fl, base_res) # clank must be satisfied from clank fl
        pud_doms = self._extract(pud_cfg, pud_fs, pud_fl, base_res) # put from unified
        unified_doms = None
        return clank_doms, pud_doms, unified_doms

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
"""