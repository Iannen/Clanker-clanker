from app.entities import MultiDocResolver, RepoContentResolver, ManifestResolver
from asset_ingestion.commons.error_collector import ErrorCollector
# big 'ol slopburger - but free
class AssetValidator:
    def validate(
        self,
        pud_pathlist: set[str],
        shared_pathlist: set[str],
        keyboard: Keyboard,
        ui_render: Render,
        base_resolvers: list[Resolver],
        collector: ErrorCollector,
    ) -> None:
        resolvers: list[Resolver] = []

        resolvers.extend(base_resolvers)
        resolvers.extend(ui_render.resolvers)

        for btn in keyboard.button_map.values():
            inhabitant = btn.inhabitant
            if inhabitant is None:
                continue
            if hasattr(inhabitant, "resolvers"):
                resolvers.extend(inhabitant.resolvers)
            if hasattr(inhabitant, "prompts"):
                for prompt in inhabitant.prompts:
                    if hasattr(prompt, "render") and hasattr(prompt.render, "resolvers"):
                        resolvers.extend(prompt.render.resolvers)

        referenced_pud_files: set[str] = set()

        def _is_parent_or_equal(path_str: str, prefix_str: str) -> bool:
            norm_p = path_str.strip("/")
            norm_pref = prefix_str.strip("/")

            if norm_pref in ("", "."):
                return not norm_p.startswith(".clanker/prompt-assets")

            return norm_p == norm_pref or norm_p.startswith(norm_pref + "/")

        def _get_basename(path_str: str) -> str:
            return path_str.rsplit("/", 1)[-1]

        for resolver in resolvers:
            if isinstance(resolver, MultiDocResolver):
                for file_item in resolver.files.files:
                    file_name = file_item.name
                    pud_matches = {p for p in pud_pathlist if _get_basename(p) == file_name}
                    shared_matches = {p for p in shared_pathlist if _get_basename(p) == file_name}

                    if not (pud_matches or shared_matches):
                        collector.add_complaint(
                            f"MultiDocResolver asset '{file_name}' not found in PUD or SHARED filelists."
                        )
                    else:
                        referenced_pud_files.update(pud_matches)

            elif isinstance(resolver, RepoContentResolver):
                for inc in resolver.fileset.includes:
                    matches = {
                        p for p in pud_pathlist if _is_parent_or_equal(p, inc)
                    }
                    if not matches:
                        collector.add_complaint(
                            f"RepoContentResolver asset '{inc}' not found in PUD filelist."
                        )
                    else:
                        referenced_pud_files.update(matches)

            elif isinstance(resolver, ManifestResolver):
                for pud_inc in resolver.pud_fileset.includes:
                    matches = {
                        p for p in pud_pathlist if _is_parent_or_equal(p, pud_inc)
                    }
                    if not matches:
                        collector.add_complaint(
                            f"ManifestResolver pud asset '{pud_inc}' not found in PUD filelist."
                        )
                    else:
                        referenced_pud_files.update(matches)

                if resolver.shared_fileset is not None:
                    for shared_inc in resolver.shared_fileset.includes:
                        shared_has_match = any(
                            _is_parent_or_equal(p, shared_inc) for p in shared_pathlist
                        )
                        if not shared_has_match:
                            collector.add_complaint(
                                f"ManifestResolver shared asset '{shared_inc}' not found in SHARED filelist."
                            )

        prompt_assets_prefix = ".clanker/prompt-assets"
        pud_prompt_assets = {
            p for p in pud_pathlist if _is_parent_or_equal(p, prompt_assets_prefix)
        }

        dangling_assets = pud_prompt_assets - referenced_pud_files
        for dangling in sorted(dangling_assets):
            collector.add_complaint(
                f"Dangling asset detected: '{dangling}' in '.clanker/prompt-assets' is not referenced by any resolver."
            )