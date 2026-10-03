from stdlib import dataclass
from ...asset_ingestion import ValueExtractor, ErrorCollector, ResolverParser, RenderParser, NamedMap
from core import Domain, Prompt
@dataclass
class DomParser(ValueExtractor):
    ec: ErrorCollector
    def parse(self, data: dict, fileset_map: NamedMap, filelist_map: NamedMap, base_res) -> Domain:
        name = self.req_str(data, ["name"])
        with self.ec.path(name):
            raw_resolvers = self.req_list(data, ["resolvers"])
            raw_prompts = self.req_list(data, ["prompts"])

            resolvers = [ResolverParser(r, self.ec, fileset_map, filelist_map).parse()for r in raw_resolvers]
            if base_res: resolvers.append(base_res)
            prompts = self._build_prompts(raw_prompts, fileset_map, filelist_map)
            return Domain(name=name, prompts=prompts, resolvers=resolvers)
            
    def _build_prompts(self, dicts: list[dict], fileset_map, filelist_map) -> list[Prompt]:
        return [PromptParser(self.ec).parse(d, fileset_map, filelist_map) for d in dicts]

@dataclass
class PromptParser(ValueExtractor):
    ec: ErrorCollector
    def parse(self, data, fileset_map, filelist_map) -> Prompt: 
        return Prompt(self.req_str(data, ["name"]), RenderParser(self.req_dict(data, ["render"]), self.ec, fileset_map, filelist_map).extract())
        