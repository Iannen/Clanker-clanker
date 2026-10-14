from core import (
    Fileset,
    CorruptClanker,
    ClankerAssets,
    ManifestResolver,
    MultiDocResolver,
    PathTokens,
    Render,
    RepoContentResolver,
    Resolver,
    ConfigAssembly,
)
from core.engine_deps import RenderService, RenderContext, DiskPort, NoSuchFile
from . import ContentShaper

class RenderServiceImpl(RenderService):
    def __init__(self, files: DiskPort) -> None:
        self.files: DiskPort = files
        self.shaper: ContentShaper = ContentShaper()

    def render_prompt(self, ctx: RenderContext) -> str:
        template = self._get_template(ctx.render)
        repl_map = self._get_repl_map(ctx)
        return self._hydrate(template, repl_map)

    def _hydrate(self, template: str, replacements: dict[str, str]) -> str:
        return self.shaper.hydrate(template, replacements)

    def _get_template(self, render: Render) -> str:
        try:
            match render.template:
                case "prompt_template":
                    return self.files.read_asset(ClankerAssets.layouts.PROMPT)
        except NoSuchFile as ex:
            raise CorruptClanker(f"Error loading template for '{render.template}': {ex}") from ex

    def _get_repl_map(self, ctx: RenderContext) -> dict[str, str]:
        active_resolvers: list[Resolver] = []
        if ctx.render.inherit_domain:
            if ctx.kb.selected_dom_btn: active_resolvers.extend(ctx.kb.selected_dom_btn.inhabitant.resolvers)
        active_resolvers.extend(ctx.render.resolvers)
        replacements: dict[str, str] = {}
        for resolver in active_resolvers:
            match resolver:
                case MultiDocResolver():
                    replacements.update(self._res_multi_doc(resolver))
                case RepoContentResolver():
                    replacements.update(self._res_repo_content(resolver))
                case ManifestResolver():
                    replacements.update(self._res_manifest(resolver))
        return replacements

    def _res_multi_doc(self, resolver: MultiDocResolver) -> dict[str, str]:
        fragments = []
        for file_obj in resolver.files.files:
            try:
                raw_content = self.files.read_asset(file_obj.path)
            except NoSuchFile as ex:
                raise ConfigAssembly from ex

            content = self.shaper.apply_truncation(raw_content, file_obj.truncation_spec)
            fragments.append(f"<{file_obj.name}>\n{content}\n</{file_obj.name}>")

        return {resolver.anchor: "\n\n".join(fragments)}

    def _res_repo_content(self, resolver: RepoContentResolver) -> dict[str, str]:
        includes = self.files.get_file_paths(PathTokens.PUD, [include.value for include in resolver.fileset.includes], missing_ok=False)
        excludes = self.files.get_file_paths(PathTokens.PUD, [exclude.value for exclude in resolver.fileset.excludes], missing_ok=True) if resolver.fileset.excludes else set()
        paths = sorted(includes - excludes)

        tree_header = f"<tree>\n" + "\n".join(f"├── {p}" for p in paths) + "\n</tree>"

        file_blocks = []
        for p in paths:
            try:
                content = self.files.read_asset(f"{PathTokens.PUD}/{p}").rstrip()
                file_blocks.append(f"<{p}>\n{content}\n</{p}>")
            except UnicodeDecodeError:
                pass

        inner_content = tree_header + "\n" + "\n".join(file_blocks)
        return {resolver.anchor: f"<repo-content>\n{inner_content}\n</repo-content>"}

    def _res_manifest(self, resolver: ManifestResolver) -> str:
        manifest_blocks = [
            self._build_manifest("pud-manifest", PathTokens.PUD, resolver.pud_fileset)
        ]

        if resolver.shared_fileset is not None:
            manifest_blocks.append(
                self._build_manifest("shared-manifest", PathTokens.SHARED, resolver.shared_fileset)
            )

        return {resolver.anchor: "\n".join(manifest_blocks)}

    def _build_manifest(self, tag: str, basepath_token: str, fileset: Fileset) -> str:
        includes = self.files.get_file_paths(basepath_token, [include.value for include in fileset.includes], missing_ok=False)
        excludes = self.files.get_file_paths(basepath_token, [exclude.value for exclude in fileset.excludes], missing_ok=True) if fileset.excludes else set()
        paths = sorted(includes - excludes)
        lines = []
        for p in paths:
            try:
                content = self.files.read_asset(f"{basepath_token}/{p}")
                line_count = len(content.splitlines())
                lines.append(f"{p} : {line_count} lines")
            except UnicodeDecodeError:
                pass

        return f"<{tag}>\n" + "\n".join(lines) + "\n</" + tag + ">"