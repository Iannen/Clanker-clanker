from stdlib import ABC, abstractmethod
from core import Button, Render, Resolver, ActionResult

class Report(ABC):
    @abstractmethod
    def get_complaints(self) -> list[str]: ...

    @abstractmethod
    def get_critical_complaints(self) -> list[str]: ...

class IngestionService(ABC): 
    @abstractmethod
    def get_runtime_config(self) -> tuple[ActionResult, Report, dict[str, Button], Render, list[Resolver]]: ...
    @abstractmethod
    def initialize_workspace(self) -> None: ...