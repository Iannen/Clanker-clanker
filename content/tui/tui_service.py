from app.deps.tui import TUIService
from ports_adapters.ports import IOBridgePort
from app.exceptions import ProgramExit, UserDecline
from app.presentation import ActionResult

class IOControl:
    ACCEPTED = "accepted"
    DECLINED = "declined"
    INVALID = "invalid"
    ABORT_KEYS = ("\x1b", "\x03")
    ACCEPT_KEY = "\x04"
    BACKSPACE_KEYS = ("\x7f", "\x08")

class TUIServiceImpl(TUIService):
    def __init__(self, io_bridge: IOBridgePort) -> None:
        self.io_bridge = io_bridge

    def display(self, ui_string: str) -> None:
        self.io_bridge.write(f"{ui_string}\n")

    def to_clipboard(self, text_content: str) -> ActionResult:
        lines_count = self.io_bridge.to_clipboard(text_content)
        char_count = len(text_content)
        return ActionResult(f"Copied {lines_count} lines ({char_count} chars) to clipboard")

    def get_key(self) -> str:
        ch = self.io_bridge.read_char()
        if ch in IOControl.ABORT_KEYS:
            raise ProgramExit
        return ch.lower()

    def get_confirmation(self, prompt_msg: str, required_phrase: str | None = None) -> None:
        instructions = f"Type '{required_phrase}' and press [Ctrl+D] to confirm, or [ESC/Ctrl+C] to cancel.\n> "
        if required_phrase is None:
            instructions = "Press [Ctrl+D] to confirm, or [ESC/Ctrl+C] to cancel.\n"            
        base_msg = f"\n{prompt_msg}\n{instructions}"
        self.io_bridge.write(base_msg)
        while True:
            status, value = self.io_bridge.get_acceptance(required_phrase)
            if status == IOControl.ACCEPTED:
                return
            if status == IOControl.DECLINED:
                raise UserDecline
            if status == IOControl.INVALID:
                err = f"Invalid confirmation. Expected '{required_phrase}', got '{value}'. Try again.\n"
                self.io_bridge.write(base_msg + err + "> ")