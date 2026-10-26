from stdlib import dataclass
from core import File, AssetPack
from core.engine_deps import UnsatisfiedFiles, FilenameCollision
from ...asset_ingestion import ErrorCollector, Numap

@dataclass
class FilelistValidator2:
    ec: ErrorCollector
    clank_doc_assets: AssetPack
    pud_doc_assets: AssetPack
    numap: Numap

    def validate(self):
        if not (self.clank_doc_assets and self.pud_doc_assets): return

        clank_map = self._resolve_and_collect_collisions(self.clank_doc_assets)
        pud_map = self._resolve_and_collect_collisions(self.pud_doc_assets)

        combined_map = pud_map | clank_map
        files = self.numap.get_entities(File)

        unsatisfied_files: list[File] = []

        for file_item in files:
            target_path = combined_map.get(file_item.name)
            if target_path:
                file_item.path = target_path
            else:
                unsatisfied_files.append(file_item)

        if unsatisfied_files:
            self.ec.accept(UnsatisfiedFiles(unsatisfied_files))
            self.numap.prune(unsatisfied_files)

    def _resolve_and_collect_collisions(self, pack: AssetPack) -> dict[str, str]:
        filename_to_paths: dict[str, list[str]] = {}
        for path_str in pack.paths:
            filename = path_str.rsplit("/", 1)[-1]
            full_path = f"{pack.token}/{path_str}"
            filename_to_paths.setdefault(filename, []).append(full_path)

        resolved_map: dict[str, str] = {}
        for filename, full_paths in filename_to_paths.items():
            winner_path = sorted(full_paths, key=lambda p: (p.count("/"), p))[0]
            resolved_map[filename] = winner_path
            if len(full_paths) > 1:
                self.ec.accept(FilenameCollision(filename, full_paths, winner_path))

        return resolved_map
