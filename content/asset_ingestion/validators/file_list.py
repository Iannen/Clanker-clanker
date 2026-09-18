from collections import defaultdict
from app.entities import Domain, MultiDocResolver, Prompt, Resolver

class FilelistValidator:
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
        
        self._detect_collisions(pud_cfg_name, pud_assets, collector)
        self._detect_collisions(shared_cfg_name, shared_assets, collector)

        self._detect_unbacked_filerefs(pud_cfg_name, pud_assets, shared_assets, pud_doms, collector)
        self._detect_unbacked_filerefs(shared_cfg_name, pud_assets, shared_assets, shared_doms, collector)

    def _detect_collisions(self, repo_name: str, searchspace: set[str], error_collector) -> None:
        filename_to_paths: dict[str, list[str]] = defaultdict(list)

        for path_str in searchspace:
            filename = path_str.rsplit("/", 1)[-1]
            filename_to_paths[filename].append(path_str)

        with error_collector.path(repo_name):
            for filename, paths in filename_to_paths.items():
                if len(paths) > 1:
                    formatted_paths = ", ".join(f"'{p}'" for p in sorted(paths))
                    error_collector.add_complaint(
                        f"Filename collision detected for '{filename}'. Coexisting paths: {formatted_paths}"
                    )

    def _detect_unbacked_filerefs(
        self,
        config_name: str,
        pud_assets: set[str],
        shared_assets: set[str],
        doms: list[Domain],
        collector,
    ) -> None:
        reqs = self._extract_existencereqs(doms)
        available_filenames = {
            path_str.rsplit("/", 1)[-1] for path_str in (set(pud_assets) | set(shared_assets))
        }

        with collector.path(config_name):
            for filename, context_path in reqs:
                if filename not in available_filenames:
                    collector.add_complaint(
                        f"the file of <{context_path}> was not found in either pud or clanker"
                    )

    def _extract_existencereqs(self, doms: list[Domain]) -> list[tuple[str, str]]:
        reqs: list[tuple[str, str]] = []

        for dom in doms:
            for resolver in dom.resolvers:
                if isinstance(resolver, MultiDocResolver):
                    for file_item in resolver.files.files:
                        context = f"domain={dom.name}, resolver=MultiDocResolver, fileset=files, file={file_item.name}"
                        reqs.append((file_item.name, context))

            for prompt in dom.prompts:
                for resolver in prompt.render.resolvers:
                    if isinstance(resolver, MultiDocResolver):
                        for file_item in resolver.files.files:
                            context = f"domain={dom.name}, prompt={prompt.name}, resolver=MultiDocResolver, fileset=files, file={file_item.name}"
                            reqs.append((file_item.name, context))
        return reqs
