from stdlib import dataclass, field
from core import MultiDocResolver, Resolver, Config
from ...asset_ingestion import ErrorCollector, ValueExtractor, ResolverParser, FilesetMap, FilelistMap

@dataclass(eq=False)
class BaseResolverExtractor(ValueExtractor):
    collector: ErrorCollector
    filelist_map: FilelistMap

    def extract_from_clanker(self, cfg: Config, filelist_map: FilelistMap) -> Resolver:
        # if clanker doesnt have baseres, then make critical complaint
        self.clanker_baseres = self._extract(cfg, filelist_map)
        return self.clanker_baseres, self

    def get_proper_baseres(self, cfg: Config, filelist_map: FilelistMap): 
        pud_br = self._extract(cfg, filelist_map)
        return pud_br if pud_br else self.clanker_baseres

    def _extract(self, cfg: Config, filelist_map: FilelistMap) -> list[Resolver]:
        if not self.valid_args(locals()): return None
        with self.collector.path("base_resolvers"):
            raw_resolvers = self.opt_list(cfg.data, ["base_resolvers"], [])
            extracted: list[MultiDocResolver] = []

            for r in raw_resolvers:
                res_type = self.req_str(r, ["type"])
                anchor = self.req_str(r, ["id"])

                if res_type != "multi-document-retrieval":
                    self.collector.add_complaint(
                        f"Expected 'multi-document-retrieval' resolver type in base_resolvers, got '{res_type}'"
                    )
                    continue

                if len(extracted) >= 1:
                    self.collector.add_complaint(
                        f"Extraneous base resolver '{anchor}' encountered; at most 1 base resolver expected"
                    )
                    continue

                resolver_obj = ResolverParser(r, self.collector, filelist_map, filelist_map).parse()
                if isinstance(resolver_obj, MultiDocResolver):
                    extracted.append(resolver_obj)

            if extracted:
                return [extracted[0]]
            return None
