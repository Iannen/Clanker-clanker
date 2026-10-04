from stdlib import dataclass
from ...asset_ingestion import ValueExtractor, ErrorCollector, ResolverParser, RenderParser, NamedMap
from core import Domain, Prompt
@dataclass
class DomParser(ValueExtractor):
    ec: ErrorCollector
    entity_cls = Domain
    def parse(self, name: str, data: dict, fileset_map: NamedMap, filelist_map: NamedMap) -> Domain:
        with self.ec.path(name):
            raw_resolvers = self.req_list(data, ["resolvers"])
            raw_prompts = self.req_list(data, ["prompts"])
            resolvers = [ResolverParser(self.ec).parse("", r, fileset_map, filelist_map)for r in raw_resolvers]
            prompts = self._build_prompts(raw_prompts, fileset_map, filelist_map)
            return Domain(name=name, prompts=prompts, resolvers=resolvers) #name=name, 
            
    def _build_prompts(self, dicts: list[dict], fileset_map, filelist_map) -> list[Prompt]:
        return [PromptParser(self.ec).parse(d, fileset_map, filelist_map) for d in dicts]

@dataclass
class PromptParser(ValueExtractor):
    ec: ErrorCollector
    def parse(self, data, fileset_map, filelist_map) -> Prompt: 
        return Prompt(self.req_str(data, ["name"]), RenderParser(self.ec).parse("", self.req_dict(data, ["render"]), fileset_map, filelist_map))
        