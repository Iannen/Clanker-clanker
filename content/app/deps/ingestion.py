from abc import ABC, abstractmethod
from app.entities import Button, Render, Resolver

class Report(ABC):
    @abstractmethod
    def get_domain_overflow_report(self) -> str | None: ...
    @abstractmethod
    def get_complaints(self) -> list[str]: ...

from app.presentation import ActionResult

class IngestionService(ABC): 
    @abstractmethod
    def get_runtime_config(self) -> tuple[ActionResult, Report, dict[str, Button], Render, list[Resolver]]: ...
    @abstractmethod
    def initialize_workspace(self) -> None: ...