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


class Report(ABC):
    @abstractmethod
    def get_all_complaints(self) -> list[Soft]: ...
    @abstractmethod
    def get_critical_complaints(self) -> list[str]: ...


class Command: pass

@dataclass
class StartCmd(Command):
    kb: "e.Keyboard"
    ui_render: "e.Render"

@dataclass
class KbCmd(Command): char: str


class Result: pass


@dataclass
class KbServiceEmission:
    kb: e.Keyboard
    ui_render: e.Render
    cmd: Command


@dataclass
class BootstrapSuccess(KbServiceEmission, Result): pass

@dataclass
class UnboundKeyResult(KbServiceEmission, Result): pass

@dataclass
class DomainSelectedResult(KbServiceEmission, Result): btn: e.DomButton

@dataclass
class UninhabitedDomainResult(KbServiceEmission, Result): btn: e.DomButton

@dataclass
class UninhabitedPromptResult(KbServiceEmission, Result): btn: e.PromptButton


@dataclass
class RenderNormalPromptCmd(KbServiceEmission, Command):
    prompt: e.Prompt
    domain: e.Domain

@dataclass
class RenderHotPromptCmd(KbServiceEmission, Command):
    prompt: e.Prompt
    domain: e.Domain


@dataclass
class PromptRenderResult(KbServiceEmission, Result):
    text: str
    lines: int
    chars: int


@dataclass
class IngestApplyResult(Result):
    written: list[str]
    deleted: list[str]
    errors: list[str]

@dataclass
class IngestionResult(Result): report: Report

@dataclass
class StartResult(IngestionResult):
    kb: e.Keyboard
    ui_render: e.Render

@dataclass
class ClankerizeResult(IngestionResult): pass

@dataclass
class TerminateResult(IngestionResult): pass


class IngestionService(ABC):
    @abstractmethod
    def get_runtime_config(self) -> StartCmd | StartResult | ClankerizeResult | TerminateResult: ...
    @abstractmethod
    def initialize_workspace(self) -> StartCmd | StartResult | ClankerizeResult | TerminateResult: ...

class PromptService(ABC):
    @abstractmethod
    def render_prompt(self, cmd: RenderNormalPromptCmd | RenderHotPromptCmd) -> PromptRenderResult: ...

class KBService(ABC):
    @abstractmethod
    def handle_start(self, cmd: StartCmd) -> BootstrapSuccess: ...
    @abstractmethod
    def handle_key(self, cmd: KbCmd) -> KbServiceEmission: ...