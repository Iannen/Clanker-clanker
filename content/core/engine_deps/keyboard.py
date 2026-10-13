from stdlib import ABC, abstractmethod, dataclass
from core import Render, ActionResult, Keyboard
from core.engine_deps import Result, Command

class KBService(ABC):
    @abstractmethod
    def setup(self, kb: Keyboard) -> None: ...
    @abstractmethod
    def handle_cmd(self, cmd: Command) -> Result: ...
    @abstractmethod
    def get_ui_context(self) -> UIRenderContext: ...

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