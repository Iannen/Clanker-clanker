from stdlib import dataclass, defaultdict
from ...asset_ingestion import ErrorCollector, AssetPack, FilenameCollision
#TODO: consider, perhaps I make this part of the fielist validator. its after all relating to the same 'file' concept

@dataclass(slots=True, eq=False)
class CollisionDetector:
    collector: ErrorCollector

    def detect(self, asset_pack: AssetPack | None) -> None:
        if not asset_pack or not asset_pack.paths:
            return

        filename_to_paths: dict[str, list[str]] = defaultdict(list)
        for path_str in asset_pack.paths:
            filename = path_str.rsplit("/", 1)[-1]
            filename_to_paths[filename].append(path_str)

        resolved: dict[str, str] = {}

        for filename, paths in filename_to_paths.items():
            full_paths = [f"{asset_pack.token}/{p}" for p in paths]
            winner_path = sorted(full_paths, key=lambda p: (p.count("/"), p))[0]
            if len(full_paths) > 1:
                self.collector.accept(FilenameCollision(filename,full_paths,winner_path,))
            resolved[filename] = winner_path

        asset_pack.resolved_map = resolved