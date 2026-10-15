from stdlib import dataclass, ABC, abstractmethod, Any, Field
from core import Render, ActionResult, Keyboard, File

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
    def render_prompt(self, ctx: RenderContext) -> ActionResult: ...

class KBService(ABC):
    @abstractmethod
    def setup(self, start_res: StartResult) -> None: ...
    @abstractmethod
    def handle_cmd(self, cmd: Command) -> Result: ...
    @abstractmethod
    def get_ui_context(self) -> UIRenderContext: ...

# their results


class Result:
    @property
    def type(self) -> type: return type(self)

    @property
    def types(self) -> tuple[type, ...]: return type(self).__mro__

@dataclass
class Command(Result): char: str

@dataclass
class CommandResult(Result):
    ctx: UIRenderContext
    msg: ActionResult


class ExitCommand: exit_msg: str = ""
class UserDeclinedStart(ExitCommand): exit_msg = "Bootstrap declined by user"
class UserDeclinedClankerize(ExitCommand): exit_msg = "User declined to clankerize project"
class StartupFailed(ExitCommand): exit_msg = "Program could not start"
class UserAborted(ExitCommand): exit_msg = "Program exited"

@dataclass 
class NullCommandResult(Result): message: ActionResult
@dataclass 
class DomainSelectedResult(Result): message: ActionResult
@dataclass 
class UninhabitatedDomainResult(Result): message: ActionResult

@dataclass
class UninhabitatedPromptResult(Result): message: ActionResult

@dataclass
class PromptRenderResult(Result): ctx: RenderContext

@dataclass
class IngestionResult(Result): report: Report
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
    render: Render

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