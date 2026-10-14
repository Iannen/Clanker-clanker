from stdlib import dataclass, ABC, abstractmethod, Any, Field
from core import Render, ActionResult, Keyboard, File

# services
class IngestionService(ABC): 
    @abstractmethod
    def get_runtime_config(self) -> StartResult | ClankerizeResult | TerminateResult: ...
    @abstractmethod
    def initialize_workspace(self) -> None: ... 

class TUIService(ABC):
    @abstractmethod
    def set_ui_render(self, ui_render: Render) -> None: ...
    @abstractmethod
    def display(self, ctx: UIRenderContext, msg: ActionResult) -> None: ...
    @abstractmethod
    def to_clipboard(self, text_content: str) -> ActionResult: ...
    @abstractmethod
    def get_cmd(self) -> Command | ExitResult: ...
    @abstractmethod
    def confirm_start(self, report: Report) -> StartConfirmed | ExitResult: ...
    @abstractmethod
    def confirm_clankerize(self, report: Report) -> ClankerizeConfirmed | ExitResult: ...
    @abstractmethod
    def inform_termination(self, report: Report) -> ExitResult: ...

class RenderService(ABC):
    @abstractmethod
    def render_prompt(self, ctx: RenderContext) -> str: ...

class KBService(ABC):
    @abstractmethod
    def setup(self, kb: Keyboard) -> None: ...
    @abstractmethod
    def handle_cmd(self, cmd: Command) -> Result: ...
    @abstractmethod
    def get_ui_context(self) -> UIRenderContext: ...

# their results

class Result:
    @property
    def type(self) -> type: return type(self)

@dataclass
class ExitResult(Result): exit_msg: str
class StartConfirmed(Result): pass
class ClankerizeConfirmed(Result): pass
@dataclass
class Command(Result): char: str

class Affirmative(Result): pass
class Declined(Result): pass

@dataclass
class RenderContext:
    kb: Keyboard
    render: Render

@dataclass
class UIRenderContext: kb: Keyboard

@dataclass
class ActionFeedbackResult(Result): message: ActionResult

@dataclass 
class NullCommandResult(Result): message: ActionResult
@dataclass 
class DomainSelectedResult(Result): message: ActionResult
@dataclass 
class UninhabitatedDomainResult(Result): message: ActionResult

@dataclass
class PromptRenderResult(Result): ctx: RenderContext
@dataclass
class UninhabitatedPromptResult(Result): message: ActionResult

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

# the stuff the results may harbour, which are not entities

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