from core import (
    FileSet,
    ActionResult,
    CorruptClanker,
    Domain,
    KBStateResolver,
    ClankerAssets,
    ManifestResolver,
    MultiDocResolver,
    PathTokens,
    Render,
    RepoContentResolver,
    Resolver,
    ConfigAssembly,
    Keyboard,
    DomButton,
    PromptButton,
)
from core.engine_deps import RenderService, RenderContext, UIRenderContext, DiskPort, NoSuchFile
from . import ContentShaper

class RenderServiceImpl(RenderService):
    def __init__(self, files: DiskPort) -> None:
        self.files: DiskPort = files
        self.shaper: ContentShaper = ContentShaper()
        self._ui_render: Render | None = None

    def set_ui_render(self, ui_render: Render) -> None:
        self._ui_render = ui_render

    def render_ui(self, ctx: UIRenderContext, msg: ActionResult) -> str:
        if self._ui_render is None:
            raise CorruptClanker("UI render spec has not been configured.")
        template = self._get_template(self._ui_render)
        repl_map = self._res_ui(ctx.kb)
        repl_map["msg"] = self.shaper.shape_action_result(msg.message)
        return self._hydrate(template, repl_map)

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
                    return self.files.read_asset(ClankerAssets.Layouts.PROMPT)
                case "ui_template":
                    return self.files.read_asset(ClankerAssets.Layouts.UI)
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
        paths = sorted(
            self.files.get_file_paths(PathTokens.PUD, resolver.fileset.includes, missing_ok=False) -
            self.files.get_file_paths(PathTokens.PUD, resolver.fileset.excludes, missing_ok=True)
        )

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

    def _res_manifest(self, resolver: ManifestResolver) -> dict[str, str]:
        manifest_blocks = [
            self._build_manifest("pud-manifest", PathTokens.PUD, resolver.pud_fileset)
        ]

        if resolver.shared_fileset is not None:
            manifest_blocks.append(
                self._build_manifest("shared-manifest", PathTokens.SHARED, resolver.shared_fileset)
            )

        return {resolver.anchor: "\n".join(manifest_blocks)}

    def _build_manifest(self, tag: str, basepath_token: str, fileset: FileSet) -> str:
        paths = sorted(
            self.files.get_file_paths(basepath_token, fileset.includes, missing_ok=False) -
            self.files.get_file_paths(basepath_token, fileset.excludes, missing_ok=True)
        )

        lines = []
        for p in paths:
            try:
                content = self.files.read_asset(f"{basepath_token}/{p}")
                line_count = len(content.splitlines())
                lines.append(f"{p} : {line_count} lines")
            except UnicodeDecodeError:
                pass

        return f"<{tag}>\n" + "\n".join(lines) + "\n</" + tag + ">"

    def _res_ui(self, kb: Keyboard) -> dict[str, str]:
        btn_hl = self.files.read_asset(ClankerAssets.Layouts.BTN_HL)
        btn_active = self.files.read_asset(ClankerAssets.Layouts.BTN_ACTIVE)
        btn_inactive = self.files.read_asset(ClankerAssets.Layouts.BTN_INACTIVE)

        repl_map = {}
        for btn in kb.get_btns(DomButton):
            template = btn_inactive
            label = btn.inhabitant.name if btn.inhabitant else ""
            if btn==kb.selected_dom_btn: template = btn_hl
            elif btn.inhabitant: template = btn_active
            repl_map |= self.shaper.shape_button_replacements(btn, label, template)
        for btn in kb.get_btns(PromptButton):
            label = btn.inhabitant.name if btn.inhabitant else ""
            template = btn_active if btn.inhabitant else btn_inactive  
            repl_map |= self.shaper.shape_button_replacements(btn, label, template)
            
        return repl_map