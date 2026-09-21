from collections import defaultdict
from app.entities import Domain, File, MultiDocResolver
from app.constants import PathTokens

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

        self._handle_collisions(repo_name, filename_to_paths, error_collector)

    def _handle_collisions(self, repo_name: str, filename_to_paths: dict[str, list[str]], error_collector) -> None:
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
        pud_map = {p.rsplit("/", 1)[-1]: f"{PathTokens.PUD}/{p}" for p in pud_assets}
        shared_map = {p.rsplit("/", 1)[-1]: f"{PathTokens.SHARED}/{p}" for p in shared_assets}

        for file_item, context_path in reqs:
            target_path = pud_map.get(file_item.name) or shared_map.get(file_item.name)
            if target_path:
                file_item.path = target_path
            else:
                self._handle_unbacked_file(collector, doms, file_item.name, config_name, context_path)

    def _handle_unbacked_file(
        self,
        collector,
        targets: list[Domain],
        filename: str,
        config_name: str,
        context_path: str,
    ) -> None:
        with collector.path(config_name):
            collector.add_complaint(
                f"the file of <{context_path}> was not found in either pud or shared, so it was removed"
            )

        for target in targets:
            for resolver in getattr(target, "resolvers", []):
                if isinstance(resolver, MultiDocResolver):
                    resolver.files.files = [f for f in resolver.files.files if f.name != filename]

            for prompt in getattr(target, "prompts", []):
                for resolver in prompt.render.resolvers:
                    if isinstance(resolver, MultiDocResolver):
                        resolver.files.files = [f for f in resolver.files.files if f.name != filename]

    def _extract_existencereqs(self, doms: list[Domain]) -> list[tuple[File, str]]:
        reqs: list[tuple[File, str]] = []

        for dom in doms:
            for resolver in dom.resolvers:
                if isinstance(resolver, MultiDocResolver):
                    for file_item in resolver.files.files:
                        context = f"domain={dom.name}, resolver=MultiDocResolver, fileset=files, file={file_item.name}"
                        reqs.append((file_item, context))

            for prompt in dom.prompts:
                for resolver in prompt.render.resolvers:
                    if isinstance(resolver, MultiDocResolver):
                        for file_item in resolver.files.files:
                            context = f"domain={dom.name}, prompt={prompt.name}, resolver=MultiDocResolver, fileset=files, file={file_item.name}"
                            reqs.append((file_item, context))
        return reqs