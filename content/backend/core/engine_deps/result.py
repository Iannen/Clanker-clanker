from backend.stdlib import dataclass, ABC, abstractmethod, Any, Field
from backend.core import entities as e

class Complaint(): pass
class Critical(Complaint): pass
class Soft(Complaint): pass


@dataclass
class Malformed(Critical):
    name: str; path: str; details: str

@dataclass
class Missing(Critical):
    name: str; paths: str | list[str]

@dataclass
class FilenameCollision(Soft):
    filename: str
    paths: list[str]
    chosen_path: str

@dataclass
class DomainOverflow(Soft):
    buttons: list["e.NewBtn"]
    discarded_domains: list["e.Domain"]

@dataclass
class UnsatisfiedFiles(Soft):
    files: list[e.File]

@dataclass
class UnsatisfiedFilesetSubjects(Soft):
    assetpack: Any
    subjects: list[str]

@dataclass
class MissingEntityFields(Soft):
    entity_cls: type
    missing_fields: list[Field]
    data: dict


@dataclass
class PromptRenderOutput:
    text: str
    lines: int
    chars: int


@dataclass
class BootResult:
    shared_domains: list[e.SharedDomain]
    pud_domains: list[e.PudDomain]


class Report(ABC):
    @abstractmethod
    def get_all_complaints(self) -> list[Soft]: ...
    @abstractmethod
    def get_critical_complaints(self) -> list[str]: ...


class Command: pass

@dataclass
class StartCmd(Command):
    kb: "e.Keyboard"


class Result: pass


@dataclass
class IngestApplyResult(Result):
    created: list[str]
    updated: list[str]
    deleted: list[str]
    missing_paths: list[str]
    unexpected_paths: list[str]
    parse_errors: list[str]


@dataclass
class IngestionResult(Result): report: Report

@dataclass
class StartResult(IngestionResult):
    kb: e.Keyboard

@dataclass
class ClankerizeResult(IngestionResult): pass

@dataclass
class TerminateResult(IngestionResult): pass


class IngestionService(ABC):
    @abstractmethod
    def get_runtime_config(self) -> tuple[StartCmd | StartResult | ClankerizeResult | TerminateResult, BootResult | None]: ...
    @abstractmethod
    def initialize_workspace(self) -> tuple[StartCmd | StartResult | ClankerizeResult | TerminateResult, BootResult | None]: ...

class PromptService(ABC):
    @abstractmethod
    def render_from_entities(self, domain: e.Domain, prompt: e.Prompt) -> PromptRenderOutput: ...