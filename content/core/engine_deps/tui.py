from stdlib import ABC, abstractmethod, Any, dataclass
from core.engine_deps import Result
from core import ActionResult

class Affirmative: pass
class Declined: pass

class TUIService(ABC):
    @abstractmethod
    def display(self, ui_string: str) -> None: ...
    @abstractmethod
    def to_clipboard(self, text_content: str) -> ActionResult: ...
    @abstractmethod
    def get_key(self) -> str: ...
    @abstractmethod
    def confirm_start(self, report: Any) -> "StartConfirmed | StartDeclined": ...
    @abstractmethod
    def confirm_clankerize(self, report: Any) -> "ClankerizeConfirmed | ClankerizeDeclined": ...
    @abstractmethod
    def inform_termination(self, report: Any) -> "TerminationInfo": ...

@dataclass
class ExitResult(Result): exit_msg: str
class StartConfirmed(Result): pass
class ClankerizeConfirmed(Result): pass

