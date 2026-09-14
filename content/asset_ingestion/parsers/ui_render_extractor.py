from typing import Any
from app.models import Render
from asset_ingestion.commons.error_collector import ErrorCollector
from asset_ingestion.commons.fileset_map import FilesetMap
from asset_ingestion.commons.value_extractor import ValueExtractor
from asset_ingestion.parsers.resolver_worker import ResolverWorker


class RenderWorker:
    def __init__(
        self,
        render_dict: dict[str, Any],
        collector: ErrorCollector,
        fileset_map: FilesetMap,
    ) -> None:
        self.render_dict = render_dict
        self.collector = collector
        self.fileset_map = fileset_map
        self.extractor = ValueExtractor()

    def extract(self) -> Render:
        template = self.extractor.req_str(self.render_dict, ["template"], Render.template)
        inherit_base = self.extractor.req_bool(self.render_dict, ["inherit_base"], Render.inherit_base)
        inherit_domain = self.extractor.req_bool(self.render_dict, ["inherit_domain"], Render.inherit_domain)
        raw_resolvers = self.extractor.req_list(self.render_dict, ["resolvers"])
        resolvers = [ResolverWorker(r, self.collector, self.fileset_map).parse() for r in raw_resolvers]
        return Render(
            template=template,
            resolvers=resolvers,
            inherit_base=inherit_base,
            inherit_domain=inherit_domain,
        )