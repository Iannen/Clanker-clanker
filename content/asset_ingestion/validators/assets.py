from pathlib import Path
from app.models import (
    RuntimeConfig,
    MultiDocResolver,
    RepoContentResolver,
    ManifestResolver,
    Resolver,
)
from asset_ingestion.commons.error_collector import ErrorCollector

class AssetValidator:
    def validate(
        self,
        pud_pathlist: set[Path],
        shared_pathlist: set[Path],
        rtc: RuntimeConfig,
        collector: ErrorCollector,
    ) -> None:
        resolvers: list[Resolver] = []

        resolvers.extend(rtc.base_resolvers)
        resolvers.extend(rtc.ui_render.resolvers)

        for btn in rtc.keyboard.button_map.values():
            inhabitant = btn.inhabitant
            if inhabitant is None:
                continue
            if hasattr(inhabitant, "resolvers"):
                resolvers.extend(inhabitant.resolvers)
            if hasattr(inhabitant, "prompts"):
                for prompt in inhabitant.prompts:
                    if hasattr(prompt, "render") and hasattr(prompt.render, "resolvers"):
                        resolvers.extend(prompt.render.resolvers)

        # Track all resolved file paths across both PUD and SHARED
        referenced_pud_files: set[Path] = set()

        for resolver in resolvers:
            if isinstance(resolver, MultiDocResolver):
                for file_item in resolver.files.files:
                    file_name = file_item.name
                    pud_matches = {p for p in pud_pathlist if p.name == file_name}
                    shared_matches = {p for p in shared_pathlist if p.name == file_name}

                    if not (pud_matches or shared_matches):
                        collector.add_complaint(
                            f"MultiDocResolver asset '{file_name}' not found in PUD or SHARED filelists."
                        )
                    else:
                        referenced_pud_files.update(pud_matches)

            elif isinstance(resolver, RepoContentResolver):
                for inc in resolver.fileset.includes:
                    inc_path = Path(inc)
                    matches = {
                        p for p in pud_pathlist if p == inc_path or inc_path in p.parents
                    }
                    if not matches:
                        collector.add_complaint(
                            f"RepoContentResolver asset '{inc}' not found in PUD filelist."
                        )
                    else:
                        referenced_pud_files.update(matches)

            elif isinstance(resolver, ManifestResolver):
                for pud_inc in resolver.pud_fileset.includes:
                    pud_path = Path(pud_inc)
                    matches = {
                        p for p in pud_pathlist if p == pud_path or pud_path in p.parents
                    }
                    if not matches:
                        collector.add_complaint(
                            f"ManifestResolver pud asset '{pud_inc}' not found in PUD filelist."
                        )
                    else:
                        referenced_pud_files.update(matches)

                if resolver.shared_fileset is not None:
                    for shared_inc in resolver.shared_fileset.includes:
                        shared_path = Path(shared_inc)
                        shared_has_match = any(
                            p == shared_path or shared_path in p.parents for p in shared_pathlist
                        )
                        if not shared_has_match:
                            collector.add_complaint(
                                f"ManifestResolver shared asset '{shared_inc}' not found in SHARED filelist."
                            )

        # Reverse check: Complain about unreferenced files in .clanker/prompt-assets
        prompt_assets_prefix = Path(".clanker/prompt-assets")
        pud_prompt_assets = {
            p for p in pud_pathlist if prompt_assets_prefix in p.parents or p == prompt_assets_prefix
        }

        dangling_assets = pud_prompt_assets - referenced_pud_files
        for dangling in sorted(dangling_assets):
            collector.add_complaint(
                f"Dangling asset detected: '{dangling}' in '.clanker/prompt-assets' is not referenced by any resolver."
            )