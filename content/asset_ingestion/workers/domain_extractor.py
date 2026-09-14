from typing import Any
from app.models import (
    Domain,
    Prompt,
)
from asset_ingestion.commons.error_collector import ErrorCollector
from asset_ingestion.commons.fileset_map import FilesetMap
from asset_ingestion.commons.value_extractor import ValueExtractor
from asset_ingestion.workers.resolver_worker import ResolverWorker
from asset_ingestion.workers.ui_render_extractor import RenderWorker

class DomainExtractor:
    def __init__(
        self,
        doms_cfg_dict: dict[str, Any],
        collector: ErrorCollector,
        fileset_map: FilesetMap,
    ) -> None:
        self.doms_cfg_dict = doms_cfg_dict
        self.collector = collector
        self.fileset_map = fileset_map
        self.extractor = ValueExtractor()

    def extract(self) -> list[Domain]:
        raw_domains = self.extractor.req_list(self.doms_cfg_dict, ["domains"])
        domains = []
        for d in raw_domains:
            name = self.extractor.req_str(d, ["name"])
            self.collector.push_path(name)
            try:
                raw_resolvers = self.extractor.req_list(d, ["resolvers"])
                raw_prompts = self.extractor.req_list(d, ["prompts"])

                resolvers = [ResolverWorker(r, self.collector, self.fileset_map).parse() for r in raw_resolvers]
                prompts = self._build_prompts(raw_prompts)
                domains.append(Domain(name=name, prompts=prompts, resolvers=resolvers))
            finally:
                self.collector.pop_path()
        return domains

    def _build_prompts(self, dicts: list[dict[str, Any]]) -> list[Prompt]:
        prompts = []
        for d in dicts:
            name = self.extractor.req_str(d, ["name"])
            self.collector.push_path(name)
            try:
                render_dict = self.extractor.req_dict(d, ["render"], default={})
                render = RenderWorker(render_dict, self.collector, self.fileset_map).extract()
                prompts.append(Prompt(name=name, render=render))
            finally:
                self.collector.pop_path()
        return prompts