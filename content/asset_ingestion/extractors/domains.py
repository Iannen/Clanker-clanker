from typing import Any
from app import Domain, Prompt, Resolver
from asset_ingestion import (
    ErrorCollector,
    FilesetMap,
    FilelistMap,
    ValueExtractor,
    ResolverParser,
    RenderParser,
)


class DomainsExtractor:
    def extract(
        self,
        pud_cfg: dict[str, Any],
        shared_cfg: dict[str, Any],
        collector: ErrorCollector,
        fileset_map: FilesetMap,
        base_resolvers: list[Resolver],
        filelist_map: FilelistMap | None = None,
    ) -> tuple[list[Domain], list[Domain]]:
        extractor = ValueExtractor()
        results = []

        for cfg_dict in (pud_cfg, shared_cfg):
            raw_domains = extractor.req_list(cfg_dict, ["domains"])
            domains = []
            for d in raw_domains:
                name = extractor.req_str(d, ["name"])
                with collector.path(name):
                    raw_resolvers = extractor.req_list(d, ["resolvers"])
                    raw_prompts = extractor.req_list(d, ["prompts"])

                    resolvers = list(base_resolvers) + [ResolverParser(r, collector, fileset_map, filelist_map).parse() for r in raw_resolvers]
                    prompts = self._build_prompts(raw_prompts, collector, fileset_map, filelist_map, extractor)
                    domains.append(Domain(name=name, prompts=prompts, resolvers=resolvers))
            results.append(domains)

        return results[0], results[1]

    def _build_prompts(
        self,
        dicts: list[dict[str, Any]],
        collector: ErrorCollector,
        fileset_map: FilesetMap,
        filelist_map: FilelistMap | None,
        extractor: ValueExtractor,
    ) -> list[Prompt]:
        prompts = []
        for d in dicts:
            name = extractor.req_str(d, ["name"])
            with collector.path(name):
                render_dict = extractor.req_dict(d, ["render"], default={})
                render = RenderParser(render_dict, collector, fileset_map, filelist_map).extract()
                prompts.append(Prompt(name=name, render=render))
        return prompts