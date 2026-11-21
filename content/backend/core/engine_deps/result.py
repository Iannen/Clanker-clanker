
from backend.stdlib import dataclass, ABC, abstractmethod, Any, Field, StrEnum
from dataclasses import field
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


class Report(ABC):
    @abstractmethod
    def get_all_complaints(self) -> list[Soft]: ...
    @abstractmethod
    def get_critical_complaints(self) -> list[str]: ...


class BootResultType(StrEnum):
    START = "start"
    CLANKERIZE = "clankerize"
    TERMINATE = "terminate"


@dataclass
class BootResult:
    type: BootResultType
    shared_domains: list[e.SharedDomain]
    pud_domains: list[e.PudDomain]
    report: "Report"


@dataclass
class IngestApplyResult:
    created: list[str]
    updated: list[str]
    deleted: list[str]
    missing_paths: list[str]
    unexpected_paths: list[str]
    parse_errors: list[str]
    expanded: list[str] = field(default_factory=list)


class IngestionService(ABC):
    @abstractmethod
    def get_runtime_config(self) -> BootResult: ...
    @abstractmethod
    def initialize_workspace(self) -> BootResult: ...


class PromptService(ABC):
    @abstractmethod
    def render_from_entities(self, domain: e.Domain, prompt: e.Prompt) -> PromptRenderOutput: ...
