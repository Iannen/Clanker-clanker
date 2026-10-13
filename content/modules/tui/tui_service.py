from core import ActionResult
from core.engine_deps import (
    TUIService,
    IOControl,
    TerminalPort,
    ExitResult,
    StartConfirmed,
    ClankerizeConfirmed,
    Command,
    Report,
)
from ..tui import TUIQuestions

class TUIServiceImpl(TUIService):
    def __init__(self, io_bridge: TerminalPort) -> None:
        self.io_bridge = io_bridge

    def display(self, ui_string: str) -> None:
        self.io_bridge.write(f"{ui_string}\n")

    def confirm_start(self, report: Report) -> StartConfirmed | ExitResult:
        if not report.get_all_complaints(): return StartConfirmed()
        question = TUIQuestions.start_confirmation(report)
        if self.io_bridge.get_acceptance(question):
            return StartConfirmed()
        return ExitResult("User declined program start")

    def confirm_clankerize(self, report: Report) -> ClankerizeConfirmed | ExitResult:
        question = TUIQuestions.clankerize_confirmation(report)
        if self.io_bridge.get_acceptance(question):
            return ClankerizeConfirmed()
        return ExitResult("User declined to clankerize project")

    def inform_termination(self, report: Report) -> ExitResult:
        question = TUIQuestions.termination_acknowledgment(report)
        self.io_bridge.get_acceptance(question)
        return ExitResult("Program could not start")

    def to_clipboard(self, text_content: str) -> ActionResult: # this goes to Renderservice, which becomes promptservice
        lines_count = self.io_bridge.to_clipboard(text_content)
        char_count = len(text_content)
        return ActionResult(ActionResult.COPIED_TO_CLIPBOARD.format(lines=lines_count, chars=char_count))

    def get_cmd(self) -> Command | ExitResult:
        ch = self.io_bridge.read_char()
        if ch in IOControl.ABORT_KEYS:
            return ExitResult(ActionResult.MSG_DEFAULT)
        return Command(char=ch.lower())