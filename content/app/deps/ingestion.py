from app.models import RuntimeConfig
from abc import ABC, abstractmethod

class Report(ABC):
    @abstractmethod
    def get_domain_overflow_report(self) -> str | None: ...
    @abstractmethod
    def get_complaints(self) -> list[str]: ...

class IngestionService(ABC): 
    @abstractmethod
    def get_runtime_config(self) -> tuple[Report, RuntimeConfig]: ...
    @abstractmethod
    def initialize_workspace(self) -> None: ...