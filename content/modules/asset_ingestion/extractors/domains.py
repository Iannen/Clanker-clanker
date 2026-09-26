from stdlib import Any, dataclass, field
from core import Domain, Prompt, Resolver, PudAssets, ClankerAssets
from ...asset_ingestion import (
    ErrorCollector,
    FilesetMap,
    FilelistMap,
    ValueExtractor,
    ResolverParser,
    RenderParser,
)

@dataclass(slots=True, eq=False)
class DomainsExtractor:
    collector: ErrorCollector
    fileset_map: FilesetMap
    base_resolvers: list[Resolver]
    filelist_map: FilelistMap
    extractor: ValueExtractor = field(default_factory=ValueExtractor)

    def extract(self, configs: dict[str, Any]) -> tuple[list[Domain], list[Domain]]:
        pud_doms = self._extract_domains(configs.get(PudAssets.Configs.PUD.name))
        shared_doms = self._extract_domains(
            configs.get(ClankerAssets.Configs.shared_cfg.name)
        )
        return pud_doms, shared_doms

    def _extract_domains(self, cfg_dict: dict[str, Any] | None) -> list[Domain]:
        if cfg_dict is None:
            return []

        domains = []
        for d in self.extractor.req_list(cfg_dict, ["domains"]):
            name = self.extractor.req_str(d, ["name"])
            with self.collector.path(name):
                raw_resolvers = self.extractor.req_list(d, ["resolvers"])
                raw_prompts = self.extractor.req_list(d, ["prompts"])

                resolvers = list(self.base_resolvers) + [
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
                render_dict = self.extractor.req_dict(d, ["render"], default={})
                render = RenderParser(
                    render_dict, self.collector, self.fileset_map, self.filelist_map
                ).extract()
                prompts.append(Prompt(name=name, render=render))
        return prompts