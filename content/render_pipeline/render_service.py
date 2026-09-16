from app.entities import MultiDocResolver, RepoContentResolver, ManifestResolver, KBStateResolver, Button, Domain, Keyboard, Resolver, Render
from app.deps.render import RenderService
from render_pipeline.content_shaper import ContentShaper
from app.constants import Layouts, PathTokens
from ports_adapters.ports import NoSuchFile
   
from app.presentation import ActionResult

class RenderServiceImpl(RenderService):
    def __init__(self, files: FileBridgePort) -> None:
        self.files = files
        self.shaper = ContentShaper()
        self._ui_render: Render | None = None

    def set_ui_render(self, ui_render: Render) -> None:
        self._ui_render = ui_render

    def render_ui(self, keyboard: Keyboard, msg: ActionResult | None) -> str:
        if self._ui_render is None:
            raise CorruptClanker("UI render spec has not been configured.")
        template = self.get_template(self._ui_render)
        repl_map = self._res_ui(keyboard)
        repl_map["msg"] = msg.get_msg() if msg is not None else ""
        return self.hydrate(template, repl_map)

    def render_prompt(self, ctx: RenderContext) -> str:
        template = self.get_template(ctx.render)
        repl_map = self.get_repl_map(ctx.keyboard, ctx.base_resolvers, ctx.render)
        return self.hydrate(template, repl_map)

    def hydrate(self, template: str, replacements: dict[str, str]) -> str:
        return self.shaper.hydrate(template, replacements)

    def get_template(self, render: Render) -> str:
        try:
            match render.template:
                case "prompt_template":
                    return self.files.read_asset(Layouts.PROMPT)
                case "ui_template":
                    return self.files.read_asset(Layouts.UI)
        except NoSuchFile as ex:
            raise CorruptClanker(f"Error loading template for '{render.template}': {ex}") from ex

    def get_repl_map(self, keyboard: Keyboard, base_resolvers: list[Resolver], render: Render) -> dict[str, str]:
        active_resolvers: list[Resolver] = []
        if render.inherit_base:
            active_resolvers.extend(base_resolvers)
        if render.inherit_domain:
            active_btn = keyboard.button_map.get(keyboard.selected_key)
            if active_btn and isinstance(active_btn.inhabitant, Domain):
                active_resolvers.extend(active_btn.inhabitant.resolvers)
        active_resolvers.extend(render.resolvers)
        replacements: dict[str, str] = {}
        for resolver in active_resolvers:
            match resolver:
                case MultiDocResolver():
                    replacements.update(self._res_multi_doc(resolver))
                case RepoContentResolver():
                    replacements.update(self._res_repo_content(resolver))
                case ManifestResolver():
                    replacements.update(self._res_manifest(resolver))
                case KBStateResolver():
                    replacements.update(self._res_ui(keyboard))
        return replacements

    def _res_multi_doc(self, resolver: MultiDocResolver) -> dict[str, str]:
        filenames = [f.name for f in resolver.files.files]
        contents_map = self.files.get_contents_with_pud_fallback(filenames)

        fragments = []
        for file_obj in resolver.files.files:
            filename = file_obj.name

            basename = filename.rsplit('/', 1)[-1]
            raw_content = contents_map.get(filename)
            if raw_content is not None:
                content = self.shaper.apply_truncation(raw_content, file_obj.truncation_spec)
            else:
                content = f"[{resolver.anchor}: No content found at '{filename}']"
            tag_name = basename

            fragments.append(f"<{tag_name}>\n{content}\n</{tag_name}>")

        return {resolver.anchor: "\n\n".join(fragments)}

    def _res_repo_content(self, resolver: RepoContentResolver) -> dict[str, str]:
        paths = sorted(
            self.files.get_files(PathTokens.PUD, resolver.fileset.includes, missing_ok=False) -
            self.files.get_files(PathTokens.PUD, resolver.fileset.excludes, missing_ok=True)
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
            self.files.get_files(basepath_token, fileset.includes, missing_ok=False) -
            self.files.get_files(basepath_token, fileset.excludes, missing_ok=True)
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

    def _res_ui(self, keyboard: Keyboard) -> dict[str, str]:
        if keyboard is None:
            return {}

        btn_hl = self.files.read_asset(Layouts.BTN_HL)
        btn_active = self.files.read_asset(Layouts.BTN_ACTIVE)
        btn_inactive = self.files.read_asset(Layouts.BTN_INACTIVE)

        repl_map = {}
        for btn in keyboard.get_unique_buttons():
            label = ""
            template = btn_inactive
            if btn.type == Button.TYPE_DOMAIN:
                if btn.key == keyboard.selected_key:
                    template = btn_hl
                    label = btn.inhabitant.name if btn.inhabitant else ""
                elif btn.inhabitant:
                    template = btn_active
                    label = btn.inhabitant.name

            elif btn.type == Button.TYPE_PROMPT:
                if btn.inhabitant:
                    template = btn_active
                    label = btn.inhabitant.name

            repl_map |= self.shaper.shape_button_replacements(btn, label, template)
        return repl_map