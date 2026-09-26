from stdlib import Any, dataclass, field
from core import MultiDocResolver, Resolver
from ...asset_ingestion import ErrorCollector, ValueExtractor, ResolverParser


@dataclass(slots=True, eq=False)
class BaseResolverExtractor:
    collector: ErrorCollector
    fileset_map: FilesetMap
    filelist_map: FilelistMap
    extractor: ValueExtractor = field(default_factory=ValueExtractor)

    def extract(self, cfg: dict[str, Any]) -> list[Resolver]:
        with self.collector.path("base_resolvers"):
            raw_resolvers = self.extractor.req_list(cfg, ["base_resolvers"], default=[])
            extracted: list[MultiDocResolver] = []

            for r in raw_resolvers:
                res_type = self.extractor.req_str(r, ["type"])
                anchor = self.extractor.req_str(r, ["id"])

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

                resolver_obj = ResolverParser(r, self.collector, self.filelist_map, self.filelist_map).parse()
                if isinstance(resolver_obj, MultiDocResolver):
                    extracted.append(resolver_obj)

            if extracted:
                return [extracted[0]]

            self.collector.add_complaint("Missing required base resolver configuration")
            return []