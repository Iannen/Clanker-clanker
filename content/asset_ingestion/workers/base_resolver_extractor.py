from typing import Any
from app.models import MultiDocResolver
from asset_ingestion.commons.error_collector import ErrorCollector
from asset_ingestion.commons.value_extractor import ValueExtractor
from asset_ingestion.workers.resolver_worker import ResolverWorker


class BaseResolverExtractor:
    def __init__(self, cfg_dict: dict[str, Any], collector: ErrorCollector) -> None:
        self.cfg_dict = cfg_dict
        self.collector = collector
        self.extractor = ValueExtractor()

    def extract(self) -> MultiDocResolver | None:
        self.collector.push_path("base_resolvers")
        try:
            raw_resolvers = self.extractor.req_list(self.cfg_dict, ["base_resolvers"], default=[])
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

                resolver_obj = ResolverWorker(r, self.collector).parse()
                if isinstance(resolver_obj, MultiDocResolver):
                    extracted.append(resolver_obj)

            return extracted[0] if extracted else None
        finally:
            self.collector.pop_path()