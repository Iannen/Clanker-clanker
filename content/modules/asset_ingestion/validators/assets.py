from core import ManifestResolver, RepoContentResolver, Domain

class FilesetValidator:
    def validate(
        self,
        pud_assets: set[str],
        pud_doms: list[Domain],
        shared_assets: set[str],
        shared_doms: list[Domain],
        collector,
    ) -> None:
        pud_cfg_name = "pud"
        shared_cfg_name = "shared"
        self._detect_unbacked_includes(pud_cfg_name, pud_assets, shared_assets, pud_doms, collector)
        self._detect_unbacked_includes(shared_cfg_name, pud_assets, shared_assets, shared_doms, collector)

    def _detect_unbacked_includes(
        self,
        config_name: str,
        pud_assets: set[str],
        shared_assets: set[str],
        doms: list[Domain],
        collector,
    ) -> None:
        pud_reqs = self._extract_filesets_that_target_pud(doms)
        for include_path, context in pud_reqs:
            has_match = any(
                self._is_parent_or_equal(asset_path, include_path)
                for asset_path in pud_assets
            )
            if not has_match:
                self._report_unbacked_include(
                    collector, config_name, "pud", include_path, context
                )
        shared_reqs = self._extract_filesets_that_target_shared(doms)
        for include_path, context in shared_reqs:
            has_match = any(
                self._is_parent_or_equal(asset_path, include_path)
                for asset_path in shared_assets
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
            for resolver in dom.resolvers:
                if isinstance(resolver, RepoContentResolver):
                    for inc in resolver.fileset.includes:
                        context = f"domain={dom.name}, resolver=RepoContentResolver, include={inc}"
                        reqs.append((inc, context))
                elif isinstance(resolver, ManifestResolver):
                    for inc in resolver.pud_fileset.includes:
                        context = f"domain={dom.name}, resolver=ManifestResolver, fileset=pud_fileset, include={inc}"
                        reqs.append((inc, context))

            for prompt in dom.prompts:
                for resolver in prompt.render.resolvers:
                    if isinstance(resolver, RepoContentResolver):
                        for inc in resolver.fileset.includes:
                            context = f"domain={dom.name}, prompt={prompt.name}, resolver=RepoContentResolver, include={inc}"
                            reqs.append((inc, context))
                    elif isinstance(resolver, ManifestResolver):
                        for inc in resolver.pud_fileset.includes:
                            context = f"domain={dom.name}, prompt={prompt.name}, resolver=ManifestResolver, fileset=pud_fileset, include={inc}"
                            reqs.append((inc, context))

        return reqs

    def _extract_filesets_that_target_shared(self, doms: list[Domain]) -> list[tuple[str, str]]:
        reqs: list[tuple[str, str]] = []

        for dom in doms:
            for resolver in dom.resolvers:
                if isinstance(resolver, ManifestResolver) and resolver.shared_fileset is not None:
                    for inc in resolver.shared_fileset.includes:
                        context = f"domain={dom.name}, resolver=ManifestResolver, fileset=shared_fileset, include={inc}"
                        reqs.append((inc, context))

            for prompt in dom.prompts:
                for resolver in prompt.render.resolvers:
                    if isinstance(resolver, ManifestResolver) and resolver.shared_fileset is not None:
                        for inc in resolver.shared_fileset.includes:
                            context = f"domain={dom.name}, prompt={prompt.name}, resolver=ManifestResolver, fileset=shared_fileset, include={inc}"
                            reqs.append((inc, context))

        return reqs

