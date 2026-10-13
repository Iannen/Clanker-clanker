from stdlib import ABC, abstractmethod, Any
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
    def get_confirmation(self, prompt_msg: str, required_phrase: str) -> None: ...
    @abstractmethod
    def confirm_start(self, report: Any) -> type[Affirmative] | type[Declined]: ...
    @abstractmethod
    def confirm_clankerize(self, report: Any) -> type[Affirmative] | type[Declined]: ...
    @abstractmethod
    def inform_termination(self, report: Any) -> str: ...

class ExitResult(Result): pass
class StartConfirmed(Result): pass
class StartDeclined(ExitResult): msg: str = "User declined program start"
class ClankerizeDeclined(ExitResult): msg: str = "User declined to clankerize project"
class ClankerizeConfirmed(Result): pass
class TerminationInfo(ExitResult): msg: str = "Program could not start"
