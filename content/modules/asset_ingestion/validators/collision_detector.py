from stdlib import Any, dataclass, field, defaultdict
from ...asset_ingestion import ErrorCollector

@dataclass(slots=True, eq=False)
class CollisionDetector:
    collector: ErrorCollector

    def detect(self, file_paths: set[str] | list[str]) -> None:
        filename_to_paths: dict[str, list[str]] = defaultdict(list)

        for path_str in file_paths:
            filename = path_str.rsplit("/", 1)[-1]
            filename_to_paths[filename].append(path_str)

        with self.collector.path(""):
            for filename, paths in filename_to_paths.items():
                if len(paths) > 1:
                    formatted_paths = ", ".join(f"'{p}'" for p in sorted(paths))
                    self.collector.add_complaint(
                        f"Filename collision detected for '{filename}'. Coexisting paths: {formatted_paths}"
                    )