from app.models import *
from app.deps.render import RenderService
from render_pipeline.code import DefaultContentShaper
from app.constants import Layout, BasePathTokens
from ports_adapters.ports import NoSuchFile

class SystemKeys:
    DELIM = "§"
    
class RenderServiceImpl(RenderService):
    def __init__(self, files: FileBridgePort) -> None:
        self.files = files
        self.shaper = DefaultContentShaper()

    def hydrate(self, template: str, replacements: dict[str, str]) -> str:
        return self.shaper.hydrate(SystemKeys.DELIM, template, replacements)

    def get_template(self, render: Render) -> str:
        try:
            match render.template:
                case "prompt_template":
                    return self.files.read_asset(BasePathTokens.SHARED + Layout.PROMPT)
                case "ui_template":
                    return self.files.read_asset(BasePathTokens.SHARED + Layout.UI)
        except NoSuchFile as ex:
            raise CorruptClanker(f"Error loading template for '{render.template}': {ex}") from ex

    def get_repl_map(self, cfg: RuntimeConfig, render: Render) -> dict[str, str]:
        active_resolvers: list[Resolver] = []
        if render.inherit_base:
            active_resolvers.extend(cfg.base_resolvers)
        if render.inherit_domain:
            active_btn = cfg.keyboard.button_map.get(cfg.keyboard.selected_key)
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
                    replacements.update(self._res_ui(cfg.keyboard))
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
            self.files.get_files(BasePathTokens.PUD, resolver.fileset.includes, missing_ok=False) -
            self.files.get_files(BasePathTokens.PUD, resolver.fileset.excludes, missing_ok=True)
        )

        tree_header = f"<tree>\n" + "\n".join(f"├── {p}" for p in paths) + "\n</tree>"

        file_blocks = []
        for p in paths:
            try:
                content = self.files.read_asset(f"<PUD>/{p}").rstrip()
                file_blocks.append(f"<{p}>\n{content}\n</{p}>")
            except UnicodeDecodeError:
                pass

        inner_content = tree_header + "\n" + "\n".join(file_blocks)
        return {resolver.anchor: f"<repo-content>\n{inner_content}\n</repo-content>"}

    def _res_manifest(self, resolver: ManifestResolver) -> dict[str, str]:
        manifest_blocks = [
            self._build_manifest("pud-manifest", "<PUD>", resolver.pud_fileset)
        ]

        if resolver.shared_fileset is not None:
            manifest_blocks.append(
                self._build_manifest("shared-manifest", "<SHARED>", resolver.shared_fileset)
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

        btn_hl = self.files.read_asset("<SHARED>/.clanker/shared-assets/layouts/btn_hl.layout")
        btn_active = self.files.read_asset("<SHARED>/.clanker/shared-assets/layouts/btn_active.layout")
        btn_inactive = self.files.read_asset("<SHARED>/.clanker/shared-assets/layouts/btn_inactive.layout")

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

            repl_map |= btn.get_repl_map(label, template)
        return repl_map