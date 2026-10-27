from core import (
    Fileset,
    CorruptClanker,
    ClankerAssets,
    ManifestResolver,
    MultiDocResolver,
    PathTokens,
    RepoContentResolver,
    Resolver,
    ConfigAssembly,
    Filelist,
)
from stdlib import dataclass
from core.engine_deps import PromptService, RenderContext, DiskPort, TerminalPort, NoSuchFile, StandardRenderContext, HotRenderContext
from . import PromptContentShaper

@dataclass(slots=True)
class PromptServiceImpl(PromptService):
    files: DiskPort
    io_bridge: TerminalPort

    def __post_init__(self) -> None:
        self.shaper: PromptContentShaper = PromptContentShaper()

    def render_prompt(self, ctx: RenderContext) -> tuple[int, int]:
        template = self._get_template(ctx)
        repl_map = self._get_repl_map(ctx)
        text_content = self._hydrate(template, repl_map)
        lines_count = self.io_bridge.to_clipboard(text_content)
        char_count = len(text_content)
        return lines_count, char_count

    def _hydrate(self, template: str, replacements: dict[str, str]) -> str:
        return self.shaper.hydrate(template, replacements)

    def _get_template(self, ctx: RenderContext) -> str:
        match ctx:
            case StandardRenderContext() | HotRenderContext():
                template_name = ctx.prompt.render.template
            case _:
                template_name = ctx.render.template

        try:
            match template_name:
                case "prompt_template":
                    return self.files.read_asset(ClankerAssets.layouts.PROMPT)
        except NoSuchFile as ex:
            raise CorruptClanker(f"Error loading template for '{template_name}': {ex}") from ex

    def _get_repl_map(self, ctx: RenderContext) -> dict[str, str]:
        active_resolvers: list[Resolver] = []
        match ctx:
            case StandardRenderContext():
                if ctx.prompt.render.inherit_domain and ctx.kb.selected_dom_btn:
                    active_resolvers.extend(ctx.kb.selected_dom_btn.inhabitant.resolvers)
                active_resolvers.extend(ctx.prompt.render.resolvers)
            case HotRenderContext():
                domain_resolvers = ctx.kb.selected_dom_btn.inhabitant.resolvers if ctx.kb.selected_dom_btn else []
                prompt_resolvers = ctx.prompt.render.resolvers

                md_resolvers = [
                    r for r in (domain_resolvers + prompt_resolvers)
                    if isinstance(r, MultiDocResolver)
                ]

                instruction_files = [
                    f for r in md_resolvers
                    for f in r.files.files
                    if f.name.endswith(".mode_instruction") or f.name.endswith(".output_instruction") or f.name.endswith(".history")
                ]

                lone_resolver = MultiDocResolver(
                    anchor="prompt_fragments",
                    files=Filelist(None, files=instruction_files)
                )
                active_resolvers.append(lone_resolver)
            case _:
                if ctx.render.inherit_domain and ctx.kb.selected_dom_btn:
                    active_resolvers.extend(ctx.kb.selected_dom_btn.inhabitant.resolvers)
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

        file_blocks = ["¤¤ Repository Contents ¤¤"]
        for p in paths:
            try:
                content = self.files.read_asset(f"{PathTokens.PUD}/{p}").rstrip()
                file_blocks.append(f'¤filepath="{p}"¤\n{content}')
            except UnicodeDecodeError:
                pass

        return {resolver.anchor: "\n\n".join(file_blocks)}

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