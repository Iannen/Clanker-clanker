from stdlib import Any, dataclass, field
from core import Domain, Prompt, Resolver, PudAssets, ClankerAssets
from ...asset_ingestion import (
    ErrorCollector,
    FilesetMap,
    FilelistMap,
    ValueExtractor,
    ResolverParser,
    RenderParser,
    Config
)

@dataclass(slots=True, eq=False)
class DomainExtractor:
    collector: ErrorCollector
    fileset_map: FilesetMap
    filelist_map: FilelistMap
    extractor: ValueExtractor = field(default_factory=ValueExtractor)

    def extract(self, cfg: dict[str, Any]) -> list[Domain]:
        domains = []
        for d in self.extractor.req_list(cfg, ["domains"]):
            name = self.extractor.req_str(d, ["name"])
            with self.collector.path(name):
                raw_resolvers = self.extractor.req_list(d, ["resolvers"])
                raw_prompts = self.extractor.req_list(d, ["prompts"])

                resolvers = [
                    ResolverParser(
                        r, self.collector, self.fileset_map, self.filelist_map
                    ).parse()
                    for r in raw_resolvers
                ]
                prompts = self._build_prompts(raw_prompts)
                domains.append(Domain(name=name, prompts=prompts, resolvers=resolvers))
        return domains

    def _build_prompts(self, dicts: list[dict[str, Any]]) -> list[Prompt]:
        prompts = []
        for d in dicts:
            name = self.extractor.req_str(d, ["name"])
            with self.collector.path(name):
                #render_dict = self.extractor.req_dict(d, ["render"], default={})
                render_dict = self.extractor.opt_dict(d, ["render"], default={})
                render = RenderParser(
                    render_dict, self.collector, self.fileset_map, self.filelist_map
                ).extract()
                prompts.append(Prompt(name=name, render=render))
        return prompts

@dataclass(slots=True, eq=False)
class NewDomainExtractor:
    collector: ErrorCollector
    fileset_map: FilesetMap
    filelist_map: FilelistMap
    extractor: ValueExtractor = field(default_factory=ValueExtractor)

    def extract(self, cfg: Config) -> list[Domain]:
        domains = []
        for d in self.extractor.req_list(cfg.data, ["domains"]):
            name = self.extractor.req_str(d, ["name"])
            with self.collector.path(name):
                raw_resolvers = self.extractor.req_list(d, ["resolvers"])
                raw_prompts = self.extractor.req_list(d, ["prompts"])

                resolvers = [
                    ResolverParser(
                        r, self.collector, self.fileset_map, self.filelist_map
                    ).parse()
                    for r in raw_resolvers
                ]
                prompts = self._build_prompts(raw_prompts)
                domains.append(Domain(name=name, prompts=prompts, resolvers=resolvers))
        return domains

    def _build_prompts(self, dicts: list[dict[str, Any]]) -> list[Prompt]:
        prompts = []
        for d in dicts:
            name = self.extractor.req_str(d, ["name"])
            with self.collector.path(name):
                #render_dict = self.extractor.req_dict(d, ["render"], default={})
                render_dict = self.extractor.opt_dict(d, ["render"], default={})
                render = RenderParser(
                    render_dict, self.collector, self.fileset_map, self.filelist_map
                ).extract()
                prompts.append(Prompt(name=name, render=render))
        return prompts