from stdlib import dataclass
from core import Render, UIRender
from ...asset_ingestion import ErrorCollector, ValueExtractor, ResolverParser, NamedMap

@dataclass
class RenderParser(ValueExtractor):
    collector: ErrorCollector
    entity_cls: type = Render

    def extract(self, name: str, data: dict, fileset_map: NamedMap, filelist_map: NamedMap) -> Render:
        template = self.opt_str(data, ["template"], Render.template)
        inherit_base = self.opt_bool(data, ["inherit_base"], Render.inherit_base)
        inherit_domain = self.opt_bool(data, ["inherit_domain"], Render.inherit_domain)
        res_dicts = self.req_list(data, ["resolvers"])
        resolvers = [ResolverParser(self.collector).parse("", data, fileset_map, filelist_map ) for data in res_dicts]
        return Render(
            template=template,
            resolvers=resolvers,
            inherit_base=inherit_base,
            inherit_domain=inherit_domain,
        )

@dataclass
class UIRenderParser(ValueExtractor): 
    collector: ErrorCollector
    entity_cls: type = UIRender
    
    def parse(self, name: str, data: dict, fileset_map: NamedMap, filelist_map: NamedMap) -> UIRender:
        template = self.opt_str(data, ["template"], UIRender.template)
        inherit_base = self.opt_bool(data, ["inherit_base"], UIRender.inherit_base)
        inherit_domain = self.opt_bool(data, ["inherit_domain"], UIRender.inherit_domain)
        res_dicts = self.req_list(data, ["resolvers"])
        resolvers = [ResolverParser(self.collector).parse("", data, fileset_map, filelist_map ) for data in res_dicts]
        return UIRender(
            template=template,
            resolvers=resolvers,
            inherit_base=inherit_base,
            inherit_domain=inherit_domain,
        )