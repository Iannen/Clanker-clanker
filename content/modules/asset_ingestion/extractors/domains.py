from stdlib import dataclass
from core import Domain, ConfigAssembly
from ...asset_ingestion import ErrorCollector, ValueExtractor, Config, NamedMap

@dataclass(eq=False)
class DomainExtractor(ValueExtractor):
    collector: ErrorCollector
    clank_cfg: Config
    pud_cfg: Config
    def get_domains(self, parse_cls: type, clank_args, pud_args) -> tuple[NamedMap[Domain] | None, NamedMap[Domain] | None, NamedMap[Domain] | None]:
        clank_doms = self._extract(parse_cls, self.clank_cfg, clank_args)
        pud_doms = self._extract(parse_cls, self.pud_cfg, pud_args)

        if clank_doms is None:
            return None, pud_doms, None

        unified_doms = clank_doms.clone()
        if pud_doms:
            for k, v in pud_doms.items():
                unified_doms.set(k, v)

        return clank_doms, pud_doms, unified_doms
    
    def _extract(self, parse_cls: type, cfg: Config, parser_args: tuple | None = None) -> NamedMap[Domain] | None:
        if not self.valid_args(locals()): return None
        try: doms_dict = self.req_dict(cfg.data, ["domains"])
        except ConfigAssembly: self.collector.add_critical_complaint("config dont got no doms son"); return None

        args = parser_args or ()
        domain_map = NamedMap(self.collector, Domain)

        for k, v in doms_dict.items():
            domain_map.set(k, parse_cls(self.collector).parse(k, v, *args))

        return domain_map
