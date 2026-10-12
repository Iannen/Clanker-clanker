from stdlib import ABC, abstractmethod, dataclass, Field, Any
from core import Render, Keyboard, File

class Report(ABC):
    @abstractmethod
    def get_complaints(self) -> list[str]: ...
    @abstractmethod
    def get_all_complaints(self) -> list[Soft]: ...
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

class Complaint(): pass 
class Critical(Complaint): pass
class Soft(Complaint): pass
@dataclass
class Malformed(Critical):
    name: str; path: str; details: str

@dataclass
class Missing(Critical):
    name: str; paths: str | list[str]

@dataclass(slots=True)
class FilenameCollision(Soft):
    filename: str
    paths: list[str]
    chosen_path: str

@dataclass(slots=True)
class DomainOverflow(Soft):
    buttons: list["NewBtn"]
    discarded_domains: list["Domain"]

@dataclass(slots=True)
class UnsatisfiedFiles(Soft):
    files: list[File]

@dataclass(slots=True)
class UnsatisfiedFilesetSubjects(Soft):
    assetpack: Any
    subjects: list[str]

@dataclass(slots=True)
class MissingEntityFields(Soft):
    entity_cls: type
    missing_fields: list[Field]
    data: dict