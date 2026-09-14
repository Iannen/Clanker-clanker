from app.deps.ingestion import Report
from contextlib import contextmanager
from typing import Generator

class ErrorCollector(Report):
    def __init__(self) -> None:
        self._path_stack: list[str] = []
        self._complaints: list[str] = []
        self._domain_overflows: list[Any] = []

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

    def add_complaint(self, message: str) -> None:
        active_path = " -> ".join(self._path_stack)
        if active_path:
            self._complaints.append(f"[{active_path}] {message}")
        else:
            self._complaints.append(message)
    
    def get_complaints(self) -> list[str]:
        return self._complaints

    def record_domain_overflow(self, overflow: Any) -> None:
        self._domain_overflows.append(overflow)

    def get_domain_overflow_report(self) -> str | None:
        if not self._domain_overflows:
            return None
        return "\n".join(dof.get_msg() for dof in self._domain_overflows)