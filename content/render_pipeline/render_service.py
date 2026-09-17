from app.entities import MultiDocResolver, RepoContentResolver, ManifestResolver, KBStateResolver, Button, Domain, Resolver, Render
from app.deps.render import RenderService
from app.exceptions import CorruptClanker, IllegalDuplicateFile
from render_pipeline.content_shaper import ContentShaper
from app.constants import Layouts
from ports_adapters.ports import PathTokens, NoSuchFile, DiskPort
    
from app.presentation import ActionResult
    
from app.presentation import ActionResult

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
        repl_map = self._res_ui(ctx.btn_map, ctx.selected_key)
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
                    return self.files.read_asset(Layouts.PROMPT)
                case "ui_template":
                    return self.files.read_asset(Layouts.UI)
        except NoSuchFile as ex:
            raise CorruptClanker(f"Error loading template for '{render.template}': {ex}") from ex

    def _get_repl_map(self, ctx: RenderContext) -> dict[str, str]:
        active_resolvers: list[Resolver] = []
        if ctx.render.inherit_base:
            active_resolvers.extend(ctx.base_resolvers)
        if ctx.render.inherit_domain and ctx.selected_key:
            active_btn = ctx.btn_map.get(ctx.selected_key)
            if active_btn and isinstance(active_btn.inhabitant, Domain):
                active_resolvers.extend(active_btn.inhabitant.resolvers)
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
                case KBStateResolver():
                    replacements.update(self._res_ui(ctx.btn_map, ctx.selected_key))
        return replacements

    def _res_multi_doc(self, resolver: MultiDocResolver) -> dict[str, str]:
        target_filenames = {f.name for f in resolver.files.files}

        def _is_test_path(rel_p_str: str) -> bool:
            parts = rel_p_str.split('/')
            return parts[0] == "test" or (len(parts) > 1 and parts[0] == "content" and parts[1] == "test")

        shared_files = self.files.get_files(PathTokens.SHARED, ["."], missing_ok=True)
        shared_map: dict[str, str] = {}
        for p in shared_files:
            parts = p.split('/')
            if any(part.startswith('.') for part in parts) or _is_test_path(p):
                continue
            name = parts[-1]
            if name in target_filenames:
                if name in shared_map:
                    raise IllegalDuplicateFile
                shared_map[name] = f"{PathTokens.SHARED}/{p}"

        pud_files = self.files.get_files(PathTokens.PUD, ["."], missing_ok=True)
        pud_map: dict[str, str] = {}
        for p in pud_files:
            if _is_test_path(p):
                continue
            name = p.rsplit('/', 1)[-1]
            if name in target_filenames:
                if name in pud_map:
                    raise IllegalDuplicateFile
                pud_map[name] = f"{PathTokens.PUD}/{p}"

        resolved_token_paths = {**shared_map, **pud_map}

        fragments = []
        for file_obj in resolver.files.files:
            filename = file_obj.name
            basename = filename.rsplit('/', 1)[-1]
            token_path = resolved_token_paths.get(filename)

            if token_path:
                try:
                    raw_content = self.files.read_asset(token_path)
                    content = self.shaper.apply_truncation(raw_content, file_obj.truncation_spec)
                except NoSuchFile:
                    content = f"[{resolver.anchor}: No content found at '{filename}']"
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

    def _res_ui(self, btn_map: dict[str, Button], selected_key: str | None) -> dict[str, str]:
        if not btn_map:
            return {}

        btn_hl = self.files.read_asset(Layouts.BTN_HL)
        btn_active = self.files.read_asset(Layouts.BTN_ACTIVE)
        btn_inactive = self.files.read_asset(Layouts.BTN_INACTIVE)

        repl_map = {}
        unique_buttons = {btn.key: btn for btn in btn_map.values()}.values()
        for btn in unique_buttons:
            label = ""
            template = btn_inactive
            if btn.type == Button.TYPE_DOMAIN:
                if btn.key == selected_key:
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