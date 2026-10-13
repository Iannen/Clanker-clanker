from core import ActionResult, ProgramExit
from core.engine_deps import (
    TUIService,
    IOControl,
    TerminalPort,
    ExitResult,
    StartConfirmed,
    ClankerizeConfirmed,
    Report,
)
from ..tui import TUIQuestions, UserQuestions

class TUIServiceImpl(TUIService):
    def __init__(self, io_bridge: TerminalPort) -> None:
        self.io_bridge = io_bridge

    def display(self, ui_string: str) -> None:
        self.io_bridge.write(f"{ui_string}\n")

    def confirm_start(self, report: Report) -> StartConfirmed | ExitResult:
        if not report.get_all_complaints(): return StartConfirmed
        prompt_msg = TUIQuestions.start_confirmation(report)
        instructions = "Press [Ctrl+D] to proceed, or [ESC/Ctrl+C] to decline.\n> "
        base_msg = f"\n{prompt_msg}\n{instructions}"
        self.io_bridge.write(base_msg)
        status, value = self.io_bridge.get_acceptance(None)
        if status == IOControl.ACCEPTED:
            return StartConfirmed()
        if status == IOControl.DECLINED:
            return ExitResult("User declined program start")

    def confirm_clankerize(self, report: Report) -> ClankerizeConfirmed | ExitResult:
        prompt_msg = TUIQuestions.clankerize_confirmation(report)
        instructions = UserQuestions.CONFIRMATION_INSTRUCTIONS.format(required_phrase=UserQuestions.REQUIRED_PHRASE)
        base_msg = f"\n{prompt_msg}\n{instructions}"
        self.io_bridge.write(base_msg)
        while True:
            status, value = self.io_bridge.get_acceptance(UserQuestions.REQUIRED_PHRASE)
            if status == IOControl.ACCEPTED:
                return ClankerizeConfirmed()
            if status == IOControl.DECLINED:
                return ExitResult("User declined to clankerize project")
            if status == IOControl.INVALID:
                err = UserQuestions.CONFIRMATION_INVALID_ERR.format(required_phrase=UserQuestions.REQUIRED_PHRASE, value=value)
                self.io_bridge.write(base_msg + err + "> ")

    def inform_termination(self, report: Report) -> ExitResult:
        all_crits = report.get_critical_complaints()
        all_softs = report.get_complaints()
        msg = "Critical errors:\n" + "\n".join(all_crits)
        if all_softs:
            msg += "\nSoft complaints:\n" + "\n".join(all_softs)
        self.display(msg)
        return ExitResult("Program could not start")

    def to_clipboard(self, text_content: str) -> ActionResult:
        lines_count = self.io_bridge.to_clipboard(text_content)
        char_count = len(text_content)
        return ActionResult(ActionResult.COPIED_TO_CLIPBOARD.format(lines=lines_count, chars=char_count))

    def get_key(self) -> str:
        ch = self.io_bridge.read_char()
        if ch in IOControl.ABORT_KEYS:
            raise ProgramExit
        return ch.lower()