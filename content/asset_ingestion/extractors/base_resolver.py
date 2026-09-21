from typing import Any
from app import MultiDocResolver, Resolver
from asset_ingestion import ErrorCollector, ValueExtractor, ResolverParser


class BaseResolversExtractor:
    def extract(
        self,
        pud_cfg: dict[str, Any],
        shared_cfg: dict[str, Any],
        collector: ErrorCollector,
    ) -> list[Resolver]:
        extractor = ValueExtractor()
        res_map: dict[str, MultiDocResolver] = {}

        for source_name, cfg in (("shared", shared_cfg), ("pud", pud_cfg)):
            with collector.path("base_resolvers"):
                raw_resolvers = extractor.req_list(cfg, ["base_resolvers"], default=[])
                extracted: list[MultiDocResolver] = []

                for r in raw_resolvers:
                    res_type = extractor.req_str(r, ["type"])
                    anchor = extractor.req_str(r, ["id"])

                    if res_type != "multi-document-retrieval":
                        collector.add_complaint(
                            f"Expected 'multi-document-retrieval' resolver type in base_resolvers, got '{res_type}'"
                        )
                        continue

                    if len(extracted) >= 1:
                        collector.add_complaint(
                            f"Extraneous base resolver '{anchor}' encountered; at most 1 base resolver expected"
                        )
                        continue

                    resolver_obj = ResolverParser(r, collector).parse()
                    if isinstance(resolver_obj, MultiDocResolver):
                        extracted.append(resolver_obj)

                if extracted:
                    res_map[source_name] = extracted[0]

        if "pud" in res_map:
            return [res_map["pud"]]
        if "shared" in res_map:
            return [res_map["shared"]]

        collector.add_complaint("Missing required base resolver configuration")
        return []