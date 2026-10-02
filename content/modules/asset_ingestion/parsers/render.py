from stdlib import Any, dataclass
from core import Render
from ...asset_ingestion import ErrorCollector, ValueExtractor, ResolverParser

@dataclass
class RenderParser(ValueExtractor):
    render_dict: dict[str, Any]
    collector: ErrorCollector
    fileset_map: NamedMap
    filelist_map: NamedMap | None = None

    def extract(self) -> Render:
        template = self.opt_str(self.render_dict, ["template"], Render.template)
        inherit_base = self.opt_bool(self.render_dict, ["inherit_base"], Render.inherit_base)
        inherit_domain = self.opt_bool(self.render_dict, ["inherit_domain"], Render.inherit_domain)
        res_dicts = self.req_list(self.render_dict, ["resolvers"])
        resolvers = [ResolverParser(data, self.collector, self.fileset_map, self.filelist_map).parse() for data in res_dicts]
        return Render(
            template=template,
            resolvers=resolvers,
            inherit_base=inherit_base,
            inherit_domain=inherit_domain,
        )