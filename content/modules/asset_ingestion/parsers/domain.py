from stdlib import dataclass
from ...asset_ingestion import ValueExtractor, ErrorCollector, ResolverParser, RenderParser
from core import Domain, Prompt
@dataclass
class DomParser(ValueExtractor):
    ec: ErrorCollector
    def parse(self, data: dict, fileset_map: FilesetMap, filelist_map: FilelistMap) -> Domain:
        name = self.req_str(data, ["name"])
        with self.ec.path(name):
            raw_resolvers = self.req_list(data, ["resolvers"])
            raw_prompts = self.req_list(data, ["prompts"])

            resolvers = [ResolverParser(r, self.ec, fileset_map, filelist_map).parse()for r in raw_resolvers]
            prompts = self._build_prompts(raw_prompts, fileset_map, filelist_map)
            return Domain(name=name, prompts=prompts, resolvers=resolvers)
    def _build_prompts(self, dicts: list[dict[str, Any]], fileset_map: FilesetMap, filelist_map: FilelistMap) -> list[Prompt]:
        prompts = []
        for d in dicts:
            name = self.req_str(d, ["name"])
            with self.ec.path(name):
                render_dict = self.opt_dict(d, ["render"], default={})
                render = RenderParser(
                    render_dict, self.ec, fileset_map, filelist_map
                ).extract()
                prompts.append(Prompt(name=name, render=render))
        return prompts