from stdlib import dataclass, ABC, abstractmethod, Any, Field
from core import entities as e

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
class BootCmd(Command): pass

@dataclass(slots=True)
class StartCmd(Command):
    kb: "e.Keyboard"
    ui_render: "e.Render"

class ClankerizeCmd(Command): pass

@dataclass
class KbCmd(Command): char: str

class ExitCommand(Command): exit_msg: str
class UserDeclinedStart(ExitCommand): exit_msg = "Bootstrap declined by user"
class UserDeclinedClankerize(ExitCommand): exit_msg = "User declined to clankerize project"
class StartupFailed(ExitCommand): exit_msg = "Program could not start"
class UserAborted(ExitCommand): exit_msg = "Program exited"


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

@dataclass
class RenderHotPromptCmd(KbServiceEmission, Command):
    prompt: e.Prompt


@dataclass
class PromptRenderResult(KbServiceEmission, Result):
    text: str
    lines: int
    chars: int


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

class FrontendService(ABC):
    @abstractmethod
    def get_request(self) -> Command: ...
    @abstractmethod
    def post_response(self, command_result: Result) -> None: ...

class PromptService(ABC):
    @abstractmethod
    def render_prompt(self, cmd: RenderNormalPromptCmd | RenderHotPromptCmd) -> PromptRenderResult: ...

class KBService(ABC):
    @abstractmethod
    def handle_start(self, cmd: StartCmd) -> BootstrapSuccess: ...
    @abstractmethod
    def handle_key(self, cmd: KbCmd) -> KbServiceEmission: ...