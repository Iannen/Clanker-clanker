from stdlib import contextmanager, Generator, ABC, abstractmethod, dataclass
from core.engine_deps import Report
from core import Config, File

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
    cfg: Config
    files: list[File]

    def to_string(self) -> str:
        files_str = "\n\t- ".join(f"'{f.name}'" for f in self.files)
        return (
            f"Config '{self.cfg.name}': Removed {len(self.files)} file reference(s) "
            f"unsatisfied by asset packs:\n\t- {files_str}"
        )