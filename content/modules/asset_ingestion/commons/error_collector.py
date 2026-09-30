from stdlib import contextmanager, Generator, ABC, abstractmethod, dataclass
from core.engine_deps import Report

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

    def set_complaints(self, complaints: list[str]) -> None:
        self._complaints = complaints

    def set_critical_complaints(self, critical_complaints: list[str]) -> None:
        self._critical_complaints = critical_complaints

    def get_complaints(self) -> list[str]:
        return self._complaints

    def get_critical_complaints(self) -> list[str]:
        return self._critical_complaints

    def has_crits(self) -> bool:
        return len(self._critical_complaints) > 0

    def merge(self, other: ErrorCollector) -> None:
        merged_collector = ErrorCollector()
        merged_collector.set_complaints(self.get_complaints() + other.get_complaints())
        merged_collector.set_critical_complaints(self.get_critical_complaints() + other.get_critical_complaints())
        return merged_collector

    def accept(self, compl: Complaint):
        match(compl):
            case(Critical()): self.add_critical_complaint(compl.to_string())
            case(Soft): self.add_complaint(compl.to_string())

class Complaint(ABC):
    @abstractmethod
    def to_string(self): ...

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