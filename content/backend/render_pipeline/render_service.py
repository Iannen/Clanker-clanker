import re

from backend.core import entities as e
from backend.stdlib import dataclass
from backend.core import engine_deps as d
from . import PromptContentShaper


@dataclass
class PromptServiceImpl(d.PromptService):
    files: d.DiskPort

    def __post_init__(self) -> None:
        self.shaper: PromptContentShaper = PromptContentShaper()

    def render_prompt(self, cmd: d.RenderNormalPromptCmd | d.RenderHotPromptCmd) -> d.PromptRenderResult:
        try:
            template = self.files.read_asset(e.ClankerAssets.layouts.PROMPT)
        except d.NoSuchFile as ex:
            raise e.CorruptClanker(f"Error loading template for '{cmd.prompt.render.template}': {ex}") from ex

        # a. parse layout into ordered sections
        section_pattern = re.compile(r"§([^§]+)§")
        section_names = [m.group(1).strip() for m in section_pattern.finditer(template)]
        sections: dict[str, list[e.Resolver]] = {name: [] for name in section_names}

        # b. collect resolvers
        resolvers = self._collect_resolvers(cmd)

        # c. derive global type order (alphabetical by class name)
        order = sorted({type(r) for r in resolvers}, key=lambda t: t.__name__)

        # d. assign resolvers to sections by anchor
        for res in resolvers:
            if res.anchor not in sections:
                raise e.CorruptClanker(f"Resolver anchor '{res.anchor}' has no matching section in layout")
            sections[res.anchor].append(res)

        # e. evict empty sections
        sections = {k: v for k, v in sections.items() if v}

        # f. sort each section's list by type order
        for key in sections:
            sections[key].sort(key=lambda r: order.index(type(r)))

        # g-h. build render
        render_parts: list[str] = []
        for section_name, res_list in sections.items():
            header = f"¤¤ {section_name} ¤¤"
            fragments = [self._dispatch(res) for res in res_list]
            section_content = header + "\n\n" + "\n\n".join(fragments)
            render_parts.append(section_content)

        render = "\n\n\n".join(render_parts) + "\n"

        # i. return
        lines_count = len(render.splitlines())
        char_count = len(render)
        return d.PromptRenderResult(
            kb=cmd.kb,
            ui_render=cmd.ui_render,
            cmd=cmd,
            text=render,
            lines=lines_count,
            chars=char_count,
        )

    def _collect_resolvers(self, cmd: d.RenderNormalPromptCmd | d.RenderHotPromptCmd) -> list[e.Resolver]:
        match cmd:
            case d.RenderNormalPromptCmd():
                resolvers: list[e.Resolver] = []
                if cmd.prompt.render.inherit_domain:
                    resolvers.extend(cmd.domain.resolvers)
                resolvers.extend(cmd.prompt.render.resolvers)
                return resolvers

            case d.RenderHotPromptCmd():
                domain_resolvers = cmd.domain.resolvers
                prompt_resolvers = cmd.prompt.render.resolvers

                md_resolvers = [
                    r for r in (domain_resolvers + prompt_resolvers)
                    if isinstance(r, e.MultiDocResolver)
                ]

                instruction_files = [
                    f for r in md_resolvers
                    for f in r.files.files
                    if f.name.endswith(".mode_instruction")
                    or f.name.endswith(".output_instruction")
                    or f.name.endswith(".history")
                ]

                lone_resolver = e.MultiDocResolver(
                    anchor="prompt_fragments",
                    files=e.Filelist(None, files=instruction_files),
                )
                return [lone_resolver]

    def _dispatch(self, res: e.Resolver) -> str:
        match res:
            case e.MultiDocResolver():
                return self._res_multi_doc(res)[res.anchor]
            case e.RepoContentResolver():
                return self._res_repo_content(res)[res.anchor]
            case e.ManifestResolver():
                return self._res_manifest(res)[res.anchor]

    def _res_multi_doc(self, resolver: e.MultiDocResolver) -> dict[str, str]:
        fragments = []
        for file_obj in resolver.files.files:
            raw_content = self.files.read_asset(file_obj.path)
            content = self.shaper.apply_truncation(raw_content, file_obj.truncation_spec)
            fragments.append(f"¤ {file_obj.name} ¤\n{content}\n¤ {file_obj.name} ¤")

        return {resolver.anchor: "\n\n".join(fragments)}

    def _res_repo_content(self, resolver: e.RepoContentResolver) -> dict[str, str]:
        includes = self.files.get_file_paths(
            e.PathTokens.PUD,
            [include.value for include in resolver.fileset.includes],
            missing_ok=False,
        )
        excludes = (
            self.files.get_file_paths(
                e.PathTokens.PUD,
                [exclude.value for exclude in resolver.fileset.excludes],
                missing_ok=True,
            )
            if resolver.fileset.excludes
            else set()
        )
        paths = sorted(includes - excludes)

        file_blocks = []
        for p in paths:
            try:
                content = self.files.read_asset(f"{e.PathTokens.PUD}/{p}").rstrip()
                file_blocks.append(f"¤ {p} ¤\n{content}\n¤ {p} ¤")
            except UnicodeDecodeError:
                pass

        return {resolver.anchor: "\n\n".join(file_blocks)}

    def _res_manifest(self, resolver: e.ManifestResolver) -> dict[str, str]:
        manifest_blocks = [
            self._build_manifest("pud-manifest", e.PathTokens.PUD, resolver.pud_fileset),
        ]

        if resolver.shared_fileset is not None:
            manifest_blocks.append(
                self._build_manifest("shared-manifest", e.PathTokens.SHARED, resolver.shared_fileset),
            )

        return {resolver.anchor: "\n\n".join(manifest_blocks)}

    def _build_manifest(self, tag: str, basepath_token: str, fileset: e.Fileset) -> str:
        includes = self.files.get_file_paths(
            basepath_token,
            [include.value for include in fileset.includes],
            missing_ok=False,
        )
        excludes = (
            self.files.get_file_paths(
                basepath_token,
                [exclude.value for exclude in fileset.excludes],
                missing_ok=True,
            )
            if fileset.excludes
            else set()
        )
        paths = sorted(includes - excludes)
        lines = []
        for p in paths:
            try:
                content = self.files.read_asset(f"{basepath_token}/{p}")
                line_count = len(content.splitlines())
                lines.append(f"{p} : {line_count} lines")
            except UnicodeDecodeError:
                pass

        return f"¤ {tag} ¤\n" + "\n".join(lines) + f"\n¤ {tag} ¤"