from app import ActionResult, ProgramExit, UserDecline, UserQuestions
from app.deps import TUIService
from ports_adapters.ports import IOControl, TerminalPort

class TUIServiceImpl(TUIService):
    def __init__(self, io_bridge: TerminalPort) -> None:
        self.io_bridge = io_bridge

    def display(self, ui_string: str) -> None:
        self.io_bridge.write(f"{ui_string}\n")

    def to_clipboard(self, text_content: str) -> ActionResult:
        lines_count = self.io_bridge.to_clipboard(text_content)
        char_count = len(text_content)
        return ActionResult(ActionResult.COPIED_TO_CLIPBOARD.format(lines=lines_count, chars=char_count))

    def get_key(self) -> str:
        ch = self.io_bridge.read_char()
        if ch in IOControl.ABORT_KEYS:
            raise ProgramExit
        return ch.lower()

    def get_confirmation(self, prompt_msg: str, required_phrase: str) -> None:
        instructions = UserQuestions.CONFIRMATION_INSTRUCTIONS.format(required_phrase=required_phrase)
        base_msg = f"\n{prompt_msg}\n{instructions}"
        self.io_bridge.write(base_msg)
        while True:
            status, value = self.io_bridge.get_acceptance(required_phrase)
            if status == IOControl.ACCEPTED:
                return
            if status == IOControl.DECLINED:
                raise UserDecline
            if status == IOControl.INVALID:
                err = UserQuestions.CONFIRMATION_INVALID_ERR.format(required_phrase=required_phrase, value=value)
                self.io_bridge.write(base_msg + err + "> ")