from stdlib import dataclass, ABC, abstractmethod, Any, Field
from core import Render, Keyboard, File, DomButton, PromptButton, Prompt

# services
class IngestionService(ABC): 
    @abstractmethod
    def get_runtime_config(self) -> StartResult | ClankerizeResult | TerminateResult: ...
    @abstractmethod
    def initialize_workspace(self) -> StartResult: ... 

class FrontendService(ABC):
    @abstractmethod
    def set_ui_render(self, ui_render: Render) -> None: ...
    @abstractmethod
    def exchange(self, command_result: CommandResult) -> Command | ExitCommand: ...
    @abstractmethod
    def run_bootstrap_result(self, bootstrap_res: IngestionResult) -> ExitCommand | ClankerizeResult | StartResult: ...

class PromptService(ABC):
    @abstractmethod
    def render_prompt(self, ctx: RenderContext): ...

class KBService(ABC):
    @abstractmethod
    def setup(self, start_res: StartResult) -> CommandResult: ...
    @abstractmethod
    def handle_cmd(self, cmd: Command) -> CommandResult: ...
    @abstractmethod
    def get_ui_context(self) -> UIRenderContext: ...

# their results

@dataclass(slots=True)
class Command:
    char: str

@dataclass(slots=True)
class CommandResult:
    ctx: UIRenderContext
    cmd: Command

@dataclass(slots=True)
class BootstrapSuccess(CommandResult): pass

@dataclass(slots=True)
class UnboundKeyResult(CommandResult): pass

@dataclass(slots=True)
class DomainSelectedResult(CommandResult): btn: DomButton

@dataclass(slots=True)
class UninhabitedDomainResult(CommandResult): btn: DomButton

@dataclass(slots=True)
class UninhabitedPromptResult(CommandResult): btn: PromptButton

@dataclass(slots=True)
class PromptRenderResult(CommandResult):
    btn: PromptButton
    lines: int
    chars: int


class ExitCommand: exit_msg: str = ""
class UserDeclinedStart(ExitCommand): exit_msg = "Bootstrap declined by user"
class UserDeclinedClankerize(ExitCommand): exit_msg = "User declined to clankerize project"
class StartupFailed(ExitCommand): exit_msg = "Program could not start"
class UserAborted(ExitCommand): exit_msg = "Program exited"

@dataclass
class IngestionResult: report: Report
@dataclass
class StartResult(IngestionResult):
    kb: Keyboard
    ui_render: Render
@dataclass
class ClankerizeResult(IngestionResult): pass
@dataclass
class TerminateResult(IngestionResult): pass

# the stuff the results may harbor, which are not entities

@dataclass
class RenderContext:
    kb: Keyboard

@dataclass(slots=True)
class StandardRenderContext(RenderContext):
    prompt: Prompt = None

@dataclass(slots=True)
class HotRenderContext(RenderContext):
    prompt: Prompt = None

@dataclass
class UIRenderContext:
    kb: Keyboard
    ui_render: Render

class Report(ABC):
    @abstractmethod
    def get_complaints(self) -> list[str]: ...
    @abstractmethod
    def get_all_complaints(self) -> list[Soft]: ...
    @abstractmethod
    def get_critical_complaints(self) -> list[str]: ...

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
    buttons: list["NewBtn"]
    discarded_domains: list["Domain"]

@dataclass
class UnsatisfiedFiles(Soft):
    files: list[File]

@dataclass
class UnsatisfiedFilesetSubjects(Soft):
    assetpack: Any
    subjects: list[str]

@dataclass
class MissingEntityFields(Soft):
    entity_cls: type
    missing_fields: list[Field]
    data: dict