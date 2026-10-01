from stdlib import Self, dataclass
from core import Domain, File, MultiDocResolver, PathTokens, AssetPack

@dataclass
class FilelistValidator:
    pud_assets: AssetPack
    shared_assets: AssetPack

    def validate(
        self,
        config: Config,
        doms: list[Domain],
        collector,
    ) -> Self:
        if doms and self.pud_assets and self.shared_assets: self._detect_unbacked_filerefs(config, doms, collector)
        return self

    def _detect_unbacked_filerefs(
        self,
        config: Config,
        doms: list[Domain],
        collector,
    ) -> None:
        reqs = self._extract_existencereqs(doms)
        pud_map = {p.rsplit("/", 1)[-1]: f"{PathTokens.PUD}/{p}" for p in self.pud_assets.paths}
        shared_map = {p.rsplit("/", 1)[-1]: f"{PathTokens.SHARED}/{p}" for p in self.shared_assets.paths}

        for file_item, context_path in reqs:
            target_path = pud_map.get(file_item.name) or shared_map.get(file_item.name)
            if target_path:
                file_item.path = target_path
            else:
                self._handle_unbacked_file(collector, doms, file_item.name, config, context_path)

    def _handle_unbacked_file(
        self,
        collector,
        targets: list[Domain],
        filename: str,
        config: Config,
        context_path: str,
    ) -> None:
        with collector.path(config.name):
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
            for resolver in getattr(dom, "resolvers", []):
                if isinstance(resolver, MultiDocResolver):
                    for file_item in resolver.files.files:
                        context = f"domain={dom.name}, resolver=MultiDocResolver, fileset=files, file={file_item.name}"
                        reqs.append((file_item, context))

            for prompt in getattr(dom, "prompts", []):
                for resolver in prompt.render.resolvers:
                    if isinstance(resolver, MultiDocResolver):
                        for file_item in resolver.files.files:
                            context = f"domain={dom.name}, prompt={prompt.name}, resolver=MultiDocResolver, fileset=files, file={file_item.name}"
                            reqs.append((file_item, context))
        return reqs