from core import Domain, ManifestResolver, RepoContentResolver, AssetPack, Config, SharedDomain, PudDomain, Prompt
from stdlib import dataclass
from ...asset_ingestion import ErrorCollector, Numap
@dataclass
class FilesetValidator2:
    collector: ErrorCollector

    def validate_clank(self, numap: Numap, shared_assets: AssetPack | None, cfg: Config | None): 
        self.clank_cfg = cfg
        self.clank_doms = numap.get_entities(SharedDomain)
        self.clank_assets = shared_assets
        return self

    def validate_pud(self, numap: Numap, pud_assets: AssetPack | None, cfg: Config | None):
        doms = numap.get_entities(PudDomain)
        if not (getattr(self, "clank_assets", None) and getattr(self, "clank_doms", None) and getattr(self, "clank_cfg", None) and doms and pud_assets and cfg):
            return
        pud_reqs = self._extract_filesets_that_target_pud(doms)
        for include_path, context in pud_reqs:
            has_match = any(
                self._is_parent_or_equal(asset_path, include_path)
                for asset_path in pud_assets.paths
            )
            if not has_match:
                self._report_unbacked_include(
                    cfg.name, cfg.name, include_path, context
                )

        shared_reqs = self._extract_filesets_that_target_shared(self.clank_doms)
        for include_path, context in shared_reqs:
            has_match = any(
                self._is_parent_or_equal(asset_path, include_path)
                for asset_path in self.clank_assets.paths
            )
            if not has_match:
                self._report_unbacked_include(
                    cfg.name, self.clank_cfg.name, include_path, context
                )

    def _report_unbacked_include(self,config_name: str,target_name: str,include_path: str,context: str,) -> None:
        with self.collector.path(config_name):
            self.collector.add_complaint(
                f"asset include '{include_path}' (<{context}>) was not found in {target_name}"
            )

    def _is_parent_or_equal(self, asset_path: str, include_path: str) -> bool:
        if asset_path == include_path:
            return True
        prefix = include_path if include_path.endswith("/") else f"{include_path}/"
        return asset_path.startswith(prefix)

    def _extract_filesets_that_target_pud(self, doms: list[Domain]) -> list[tuple[str, str]]:
        reqs: list[tuple[str, str]] = []

        for dom in doms:
            for resolver in getattr(dom, "resolvers", []):
                if isinstance(resolver, RepoContentResolver):
                    for inc in getattr(resolver.fileset, "includes", []):
                        context = f"domain={dom.name}, resolver=RepoContentResolver, include={inc}"
                        reqs.append((inc, context))
                elif isinstance(resolver, ManifestResolver):
                    for inc in getattr(resolver.pud_fileset, "includes", []):
                        context = f"domain={dom.name}, resolver=ManifestResolver, fileset=pud_fileset, include={inc}"
                        reqs.append((inc, context))

            for prompt in getattr(dom, "prompts", []):
                for resolver in getattr(prompt.render, "resolvers", []):
                    if isinstance(resolver, RepoContentResolver):
                        for inc in getattr(resolver.fileset, "includes", []):
                            context = f"domain={dom.name}, prompt={prompt.name}, resolver=RepoContentResolver, include={inc}"
                            reqs.append((inc, context))
                    elif isinstance(resolver, ManifestResolver):
                        for inc in getattr(resolver.pud_fileset, "includes", []):
                            context = f"domain={dom.name}, prompt={prompt.name}, resolver=ManifestResolver, fileset=pud_fileset, include={inc}"
                            reqs.append((inc, context))

        return reqs

    def _extract_filesets_that_target_shared(self, doms: list[Domain]) -> list[tuple[str, str]]:
        reqs: list[tuple[str, str]] = []

        for dom in doms:
            for resolver in getattr(dom, "resolvers", []):
                if isinstance(resolver, ManifestResolver) and getattr(resolver, "shared_fileset", None) is not None:
                    for inc in getattr(resolver.shared_fileset, "includes", []):
                        context = f"domain={dom.name}, resolver=ManifestResolver, fileset=shared_fileset, include={inc}"
                        reqs.append((inc, context))

            for prompt in getattr(dom, "prompts", []):
                for resolver in getattr(prompt.render, "resolvers", []):
                    if isinstance(resolver, ManifestResolver) and getattr(resolver, "shared_fileset", None) is not None:
                        for inc in getattr(resolver.shared_fileset, "includes", []):
                            context = f"domain={dom.name}, prompt={prompt.name}, resolver=ManifestResolver, fileset=shared_fileset, include={inc}"
                            reqs.append((inc, context))

        return reqs

    def _get_reqs(self, doms: list[Domain]):
        for dom in doms:
            for manres in [p for p in dom.resolvers if isinstance(p, (ManifestResolver))]:
                i = 2
            for repores in [p for p in dom.resolvers if isinstance(p, (RepoContentResolver))]:
                i = 2
            for prompt in dom.prompts:
                for manres in [p for p in prompt.render.resolvers if isinstance(p, (ManifestResolver))]:
                    i = 2
                for repores in [p for p in prompt.render.resolvers if isinstance(p, (RepoContentResolver))]:
                    i = 2



@dataclass
class FSReq:
    cfg: Config
    dom: Domain
    include: str

@dataclass 
class MReq(FSReq): 
    mdr: ManifestResolver
    prompt: Prompt | None = None

@dataclass 
class CReq(FSReq): 
    mdr: RepoContentResolver
    prompt: Prompt | None = None