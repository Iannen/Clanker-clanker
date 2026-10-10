from stdlib import contextmanager, Generator, ABC, abstractmethod, dataclass, defaultdict
from core.engine_deps import Report
from core import File

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
        self._path_stack: list[str] = []
        self._complaints: list[str] = []
        self._critical_complaints: list[str] = []

    def push_path(self, segment: str) -> None:
        self._path_stack.append(segment)

    def pop_path(self) -> None:
        if self._path_stack:
            self._path_stack.pop()

    @contextmanager
    def path(self, segment: str) -> Generator[None, None, None]:
        self.push_path(segment)
        try:
            yield
        finally:
            self.pop_path()

    def _format_message(self, message: str) -> str:
        active_path = " -> ".join(self._path_stack)
        return f"[{active_path}] {message}" if active_path else message

    def add_complaint(self, message: str) -> None:
        self._complaints.append(self._format_message(message))

    def add_critical_complaint(self, message: str) -> None:
        self._critical_complaints.append(self._format_message(message))

    def get_complaints(self) -> list[str]:
        return self._complaints

    def get_critical_complaints(self) -> list[str]:
        return self._critical_complaints

    def has_crits(self) -> bool:
        return len(self._critical_complaints) > 0

    def accept(self, compl: "Complaint") -> None:
        match compl:
            case Critical(): self.add_critical_complaint(compl.to_string())
            case Soft(): self.add_complaint(compl.to_string())

class Complaint(ABC):
    @abstractmethod
    def to_string(self) -> str: ...

class Critical(Complaint): pass
class Soft(Complaint): pass

@dataclass
class Malformed(Critical):
    name: str; path: str; details: str
    def to_string(self): return f"{self.__class__.__name__}: '{self.name}' at '{self.path}': \n{self.details}"

@dataclass
class Missing(Critical):
    name: str; paths: str | list[str]
    def to_string(self): return f"{self.__class__.__name__}: '{self.name}' not found at '{self.paths}'"

@dataclass(slots=True)
class FilenameCollision(Soft):
    filename: str
    paths: list[str]
    chosen_path: str

    def to_string(self) -> str:
        formatted_paths = ", ".join(f"'{p}'" for p in sorted(self.paths))
        return (
            f"Filename collision detected for '{self.filename}'. Coexisting paths: {formatted_paths}\n"
            f"\tDefaulted to using: '{self.chosen_path}'"
        )

@dataclass(slots=True)
class DomainOverflow(Soft):
    buttons: list["NewBtn"]
    discarded_domains: list["Domain"]

    def to_string(self) -> str:
        row_keys = [btn.key for btn in self.buttons if hasattr(btn, "key")]
        accepted_count = sum(len(btn.domains) for btn in self.buttons if hasattr(btn, "domains"))
        received_count = accepted_count + len(self.discarded_domains)
        msg = f"Domain overflow in row '{row_keys}': received {received_count} domains, but only {accepted_count} slots are available."
        for dom in self.discarded_domains:
            msg += f"\n\tDomain '{dom.name}' was discarded."
        return msg

@dataclass(slots=True)
class UnsatisfiedFiles(Soft):
    files: list[File]

    def to_string(self) -> str:
        files_str = "\n\t- ".join(f"'{f.name}'" for f in self.files)
        return (
            f"Removed {len(self.files)} file reference(s) "
            f"unsatisfied by asset packs:\n\t- {files_str}"
        )

@dataclass(slots=True)
class UnsatisfiedFilesetSubjects(Soft):
    assetpack_name: str
    subjects: list[str]

    def to_string(self) -> str:
        subjects_str = "\n\t- ".join(f"'{s}'" for s in self.subjects)
        return (
            f"Asset pack '{self.assetpack_name}': Removed {len(self.subjects)} unsatisfied subject(s):\n\t- {subjects_str}"
        )