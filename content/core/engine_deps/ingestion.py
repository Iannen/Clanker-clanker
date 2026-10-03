from stdlib import ABC, abstractmethod, dataclass
from core import Render, Keyboard

class Report(ABC):
    @abstractmethod
    def get_complaints(self) -> list[str]: ...
    @abstractmethod
    def get_critical_complaints(self) -> list[str]: ...

@dataclass(slots=True, frozen=True)
class StartResult:
    report: Report
    kb: Keyboard
    ui_render: Render

@dataclass(slots=True, frozen=True)
class ClankerizeResult:
    report: Report

@dataclass(slots=True, frozen=True)
class TerminateResult:
    report: Report

class IngestionService(ABC): 
    @abstractmethod
    def get_runtime_config(self) -> StartResult | ClankerizeResult | TerminateResult: ...
    @abstractmethod
    def initialize_workspace(self) -> None: ...

