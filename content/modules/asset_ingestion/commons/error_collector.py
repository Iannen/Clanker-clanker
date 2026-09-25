from stdlib import contextmanager, Generator
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