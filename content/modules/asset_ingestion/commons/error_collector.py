from stdlib import dataclass, defaultdict
from core.engine_deps import Report, Complaint, Critical, Soft, FilenameCollision

class RepoItem: pass

@dataclass
class Filereq(RepoItem):
    name: str; path: str; content: str

@dataclass
class Config(RepoItem):
    name: str; path: str; data: dict

class AssetPack(RepoItem):
    def __init__(self, token: str, paths: list[str]):
        self.token = token
        self.paths = paths
        self.resolved_map: dict[str, str] = {}
        self.collisions: list[FilenameCollision] = []

        filename_to_paths: dict[str, list[str]] = defaultdict(list)
        for path_str in self.paths:
            filename = path_str.rsplit("/", 1)[-1]
            filename_to_paths[filename].append(path_str)

        for filename, raw_paths in filename_to_paths.items():
            full_paths = [f"{self.token}/{p}" for p in raw_paths]
            winner_path = sorted(full_paths, key=lambda p: (p.count("/"), p))[0]
            
            self.resolved_map[filename] = winner_path
            
            if len(full_paths) > 1:
                self.collisions.append(FilenameCollision(filename, full_paths, winner_path))

class ErrorCollector(Report):
    def __init__(self) -> None:
        self._soft_complaints: list[Soft] = []
        self._critical_complaints: list[Critical] = []

    def get_complaints(self) -> list[str]:
        return [c.to_string() for c in self._soft_complaints]

    def get_critical_complaints(self) -> list[str]:
        return [c.to_string() for c in self._critical_complaints]

    def has_crits(self) -> bool:
        return len(self._critical_complaints) > 0

    def accept(self, compl: Complaint) -> None:
        match compl:
            case Critical(): self._critical_complaints.append(compl)
            case Soft(): self._soft_complaints.append(compl)
