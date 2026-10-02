from stdlib import dataclass, field
from core import MultiDocResolver, Resolver, Config
from ...asset_ingestion import ErrorCollector, ValueExtractor, ResolverParser

@dataclass(eq=False)
class BaseResolverExtractor(ValueExtractor):
    collector: ErrorCollector

    def get_base_res(self, clank_cfg, pud_cfg, clank_fl, pud_fl) -> Resolver | None:
        clank_br = self._extract(clank_cfg, clank_fl)
        # crit complain if no clank br
        pud_br = self._extract(pud_cfg, pud_fl)
        return pud_br if pud_br else clank_br

    def _extract(self, cfg: Config, filelist_map) -> Resolver | None:
        if not self.valid_args(locals()): return None

        raw_resolvers = self.opt_list(cfg.data, ["base_resolvers"], [])
        extracted = [res for r in raw_resolvers if (res := ResolverParser(r, self.collector, filelist_map, filelist_map).parse()) is not None]
        non_mds = [r for r in extracted if not isinstance(r, MultiDocResolver)]
        mds = [r for r in extracted if isinstance(r, MultiDocResolver)]

        md, overflow = (mds[0], mds[1:]) if mds else (None, [])
        with self.collector.path("base_resolvers"):
            for r in non_mds: self.collector.add_complaint(f"Expected 'multi-document-retrieval' resolver type in base_resolvers, got '{type(r).__name__}'")
            for _ in overflow: self.collector.add_complaint(f"Extraneous base resolver encountered in {cfg.name}; at most 1 base resolver expected")
        
        return md
