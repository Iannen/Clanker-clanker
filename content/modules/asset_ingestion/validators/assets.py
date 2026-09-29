from core import Domain, ManifestResolver, RepoContentResolver, AssetPack
from stdlib import dataclass, Self

@dataclass
class FilesetValidator:
    pud_assets: AssetPack
    shared_assets: AssetPack

    def validate(
        self,
        config_name: str,
        doms: list[Domain],
        collector,
    ) -> Self:
        self._detect_unbacked_includes(config_name, doms, collector)
        return self

    def _detect_unbacked_includes(
        self,
        config_name: str,
        doms: list[Domain],
        collector,
    ) -> None:
        pud_reqs = self._extract_filesets_that_target_pud(doms)
        for include_path, context in pud_reqs:
            has_match = any(
                self._is_parent_or_equal(asset_path, include_path)
                for asset_path in self.pud_assets.paths
            )
            if not has_match:
                self._report_unbacked_include(
                    collector, config_name, "pud", include_path, context
                )

        shared_reqs = self._extract_filesets_that_target_shared(doms)
        for include_path, context in shared_reqs:
            has_match = any(
                self._is_parent_or_equal(asset_path, include_path)
                for asset_path in self.shared_assets.paths
            )
            if not has_match:
                self._report_unbacked_include(
                    collector, config_name, "shared", include_path, context
                )

    def _report_unbacked_include(
        self,
        collector,
        config_name: str,
        target_name: str,
        include_path: str,
        context: str,
    ) -> None:
        with collector.path(config_name):
            collector.add_complaint(
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