from stdlib import defaultdict, Self, dataclass
from core import Domain, File, MultiDocResolver, PathTokens
from ...asset_ingestion import AssetPack

class FilelistValidator:
    def validate(
        self,
        config_name: str,
        doms: list[Domain],
        pud_assets: set[str],
        shared_assets: set[str],
        collector,
    ) -> None:
        """Validates file references across domains against available pud and shared assets."""
        self._detect_unbacked_filerefs(config_name, pud_assets, shared_assets, doms, collector)

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

@dataclass
class FilelistValidatorNew:
    pud_assets: set[str]
    shared_assets: set[str]

    def validate(
        self,
        config_name: str,
        doms: list[Domain],
        collector,
    ) -> Self:
        self._detect_unbacked_filerefs(config_name, doms, collector)
        return self

    def _detect_unbacked_filerefs(
        self,
        config_name: str,
        doms: list[Domain],
        collector,
    ) -> None:
        reqs = self._extract_existencereqs(doms)
        pud_map = {p.rsplit("/", 1)[-1]: f"{PathTokens.PUD}/{p}" for p in self.pud_assets}
        shared_map = {p.rsplit("/", 1)[-1]: f"{PathTokens.SHARED}/{p}" for p in self.shared_assets}

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

@dataclass
class FilelistValidatorNew2:
    pud_assets: AssetPack
    shared_assets: AssetPack

    def validate(
        self,
        config_name: str,
        doms: list[Domain],
        collector,
    ) -> Self:
        self._detect_unbacked_filerefs(config_name, doms, collector)
        return self

    def _detect_unbacked_filerefs(
        self,
        config_name: str,
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