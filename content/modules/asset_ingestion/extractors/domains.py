from stdlib import Any, dataclass, field
from core import Domain, Prompt, Resolver, ConfigAssembly
from ...asset_ingestion import (ErrorCollector, FilesetMap, FilelistMap, ValueExtractor, Config,DomParser)

@dataclass(eq=False)
class DomainExtractor(ValueExtractor):
    shr_doms = None
    collector: ErrorCollector

    def extract_shared_doms(self, cfg: Config, fileset_map: FilesetMap, filelist_map: FilelistMap) -> list[Domain] | None:
        self.shr_doms = self._extract(cfg, fileset_map, filelist_map)
        return self.shr_doms, self

    def extract_and_return_both(self, cfg: Config, fileset_map: FilesetMap, filelist_map: FilelistMap, base_res: Resolver):
        pud_doms = self._extract(cfg, fileset_map, filelist_map)
        if pud_doms:
            for d in [d for doms in (self.shr_doms, pud_doms) if doms for d in doms if d is not None]:
                d.resolvers = base_res + d.resolvers
        return pud_doms, self.shr_doms

    def _extract(self, cfg: Config, fileset_map: FilesetMap, filelist_map: FilelistMap) -> list[Domain] | None:
        locs = locals()
        if not self.valid_args(locals()): return None
        try: return [DomParser(self.collector).parse(d, fileset_map, filelist_map) for d in self.req_list(cfg.data, ["domains"])]
        except ConfigAssembly: self.collector.add_critical_complaint(f"{cfg.name}: does not have domains list!")