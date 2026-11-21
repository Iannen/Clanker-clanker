
import re

from backend.core import entities as e
from backend.stdlib import dataclass
from backend.core import engine_deps as d
from . import PromptContentShaper

TYPE_ORDER: list[type] = [
    e.RepoContentResolver,
    e.MultiDocResolver,
]


def _resolver_rank(r: e.Resolver) -> int:
    for i, cls in enumerate(TYPE_ORDER):
        if isinstance(r, cls):
            return i
    return len(TYPE_ORDER)


@dataclass
class PromptServiceImpl(d.PromptService):
    files: d.DiskPort

    def __post_init__(self) -> None:
        self.shaper: PromptContentShaper = PromptContentShaper()

    def render_from_entities(self, domain: e.Domain, prompt: e.Prompt) -> d.PromptRenderOutput:
        try:
            template = self.files.get_file_contents(e.ClankerAssets.layouts.PROMPT)
        except d.NoSuchFile as ex:
            raise e.CorruptClanker(f"Error loading template for '{prompt.render.template}': {ex}") from ex

        resolvers = self._collect_resolvers_from(domain, prompt)
        text, lines, chars = self._assemble_render(
            template,
            resolvers,
            prompt.expanded_paths,
        )
        return d.PromptRenderOutput(text=text, lines=lines, chars=chars)

    def _collect_resolvers_from(self, domain: e.Domain, prompt: e.Prompt) -> list[e.Resolver]:
        resolvers: list[e.Resolver] = []
        if prompt.render.inherit_domain:
            resolvers.extend(domain.resolvers)
        resolvers.extend(prompt.render.resolvers)
        return resolvers

    def _assemble_render(
        self,
        template: str,
        resolvers: list[e.Resolver],
        expanded_paths: list[str],
    ) -> tuple[str, int, int]:
        section_pattern = re.compile(r"§([^§]+)§")
        section_names = [m.group(1).strip() for m in section_pattern.finditer(template)]
        sections: dict[str, list[e.Resolver]] = {name: [] for name in section_names}

        for res in resolvers:
            if res.anchor not in sections:
                raise e.CorruptClanker(f"Resolver anchor '{res.anchor}' has no matching section in layout")
            sections[res.anchor].append(res)

        sections = {k: v for k, v in sections.items() if v}

        for key in sections:
            sections[key].sort(key=_resolver_rank)

        render_parts: list[str] = []
        for section_name, res_list in sections.items():
            header = f"{e.Delims.PROMPT_OPEN[1]}{section_name}{e.Delims.PROMPT_CLOSE[1]}"
            fragments = [
                self._dispatch(res, expanded_paths)
                for res in res_list
            ]
            section_content = header + "\n\n" + "\n\n".join(fragments)
            render_parts.append(section_content)

        render = "\n\n\n".join(render_parts) + "\n"
        return render, len(render.splitlines()), len(render)

    def _dispatch(self, res: e.Resolver, expanded_paths: list[str]) -> str:
        match res:
            case e.MultiDocResolver():
                return self._res_multi_doc(res)[res.anchor]
            case e.RepoContentResolver():
                return self._res_repo_content(res, expanded_paths)[res.anchor]

    def _res_multi_doc(self, resolver: e.MultiDocResolver) -> dict[str, str]:
        fragments = []
        for file_obj in resolver.files.files:
            raw_content = self.files.get_file_contents(file_obj.path)
            content = self.shaper.process(raw_content, file_obj)
            fragments.append(
                f"{e.Delims.FILELIST_START_OPEN[1]}{file_obj.name}{e.Delims.FILELIST_START_CLOSE[1]}\n"
                f"{content}\n"
                f"{e.Delims.FILELIST_END_OPEN[1]}{file_obj.name}{e.Delims.FILELIST_END_CLOSE[1]}"
            )

        return {resolver.anchor: "\n\n".join(fragments)}

    def _res_repo_content(
        self,
        resolver: e.RepoContentResolver,
        expanded_paths: list[str],
    ) -> dict[str, str]:
        content_blocks: list[str] = []
        content_paths: set[str] = set()
        expanded_path_set = set(expanded_paths)

        if resolver.content_fileset:
            includes = self.files.get_file_paths(
                e.PathTokens.PUD,
                [include.value for include in resolver.content_fileset.includes],
                missing_ok=False,
            )
            excludes = (
                self.files.get_file_paths(
                    e.PathTokens.PUD,
                    [exclude.value for exclude in resolver.content_fileset.excludes],
                    missing_ok=True,
                )
                if resolver.content_fileset.excludes
                else set()
            )
            content_paths = set(includes - excludes)
            for p in sorted(content_paths):
                try:
                    content = self.files.get_file_contents(f"{e.PathTokens.PUD}/{p}").rstrip()
                    content_blocks.append(
                        f"{e.Delims.READ_FILESET_UL[1]}{p}{e.Delims.FILESET_OPEN_END_TAG[1]}\n"
                        f"{content}\n"
                        f"{e.Delims.READ_FILESET_BL[1]}{p}{e.Delims.FILESET_OPEN_END_TAG[1]}"
                    )
                except UnicodeDecodeError:
                    pass

        meta_blocks: list[str] = []
        if resolver.meta_fileset:
            meta_includes = self.files.get_file_paths(
                e.PathTokens.PUD,
                [include.value for include in resolver.meta_fileset.includes],
                missing_ok=False,
            )
            meta_excludes = (
                self.files.get_file_paths(
                    e.PathTokens.PUD,
                    [exclude.value for exclude in resolver.meta_fileset.excludes],
                    missing_ok=True,
                )
                if resolver.meta_fileset.excludes
                else set()
            )
            meta_paths = sorted(meta_includes - meta_excludes - content_paths)
            for p in meta_paths:
                try:
                    if p in expanded_path_set:
                        content = self.files.get_file_contents(
                            f"{e.PathTokens.PUD}/{p}"
                        ).rstrip()
                        meta_blocks.append(
                            f"{e.Delims.READ_FILESET_UL[1]}{p}{e.Delims.FILESET_OPEN_END_TAG[1]}\n"
                            f"{content}\n"
                            f"{e.Delims.READ_FILESET_BL[1]}{p}{e.Delims.FILESET_OPEN_END_TAG[1]}"
                        )
                    else:
                        content = self.files.get_file_contents(f"{e.PathTokens.PUD}/{p}")
                        line_count = len(content.splitlines())
                        meta_blocks.append(
                            f"{e.Delims.FILE_META_UL[1]}{p} loc={line_count}{e.Delims.FILE_META_CLOSE[1]}"
                        )
                except UnicodeDecodeError:
                    pass

        all_blocks = content_blocks + meta_blocks
        return {resolver.anchor: "\n\n".join(all_blocks)}
