from stdlib import dataclass, ABC, abstractmethod, Any, Field
from core import Render, Keyboard, File, DomButton, PromptButton, Prompt

# Report and complaints only reference entities ( i think )
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

class Report(ABC):
    @abstractmethod
    def get_complaints(self) -> list[str]: ...
    @abstractmethod
    def get_all_complaints(self) -> list[Soft]: ...
    @abstractmethod
    def get_critical_complaints(self) -> list[str]: ...

# commands dont reference any of my types
class Command: pass
class BootCmd(Command): pass
class StartCmd(Command): pass
class ClankerizeCmd(Command): pass
@dataclass
class KbCmd(Command):char: str
class ExitCommand(Command): pass
class UserDeclinedStart(ExitCommand): exit_msg = "Bootstrap declined by user"
class UserDeclinedClankerize(ExitCommand): exit_msg = "User declined to clankerize project"
class StartupFailed(ExitCommand): exit_msg = "Program could not start"
class UserAborted(ExitCommand): exit_msg = "Program exited"

# results reference entities and python types
class Result: pass
@dataclass
class KbCmdResult(Result):
    kb: Keyboard
    ui_render: Render
    cmd: KbCmd
@dataclass
class BootstrapSuccess(KbCmdResult): pass
@dataclass
class UnboundKeyResult(KbCmdResult): pass
@dataclass
class DomainSelectedResult(KbCmdResult): btn: DomButton
@dataclass
class UninhabitedDomainResult(KbCmdResult): btn: DomButton
@dataclass
class UninhabitedPromptResult(KbCmdResult): btn: PromptButton
@dataclass
class PromptRenderResult(KbCmdResult):
    btn: PromptButton
    lines: int
    chars: int

class ExitResult(Result):  
    def __init__(self, cmd: ExitCommand): self.exit_msg= cmd.exit_msg

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

@dataclass(slots=True)
class StandardRenderContext(RenderContext):
    prompt: Prompt = None

@dataclass(slots=True)
class HotRenderContext(RenderContext):
    prompt: Prompt = None




# services reference results, and emit commands
class IngestionService(ABC): 
    @abstractmethod
    def get_runtime_config(self) -> StartResult | ClankerizeResult | TerminateResult: ...
    @abstractmethod
    def initialize_workspace(self) -> StartResult: ... 

class FrontendService(ABC):
    @abstractmethod
    def get_request(self) -> Command | ExitCommand: ...
    @abstractmethod
    def post_response(self, command_result: Result) -> None: ...

class PromptService(ABC):
    @abstractmethod
    def render_prompt(self, ctx: RenderContext): ...

class KBService(ABC):
    @abstractmethod
    def handle_cmd(self, Command): ...