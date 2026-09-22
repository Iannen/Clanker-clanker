from stdlib import json, os
from core.engine_deps import TerminalPort, IOControl, TerminalFailure
from core import TestSequenceEnded

class ScriptedTeminalAdapter(TerminalPort):
    def __init__(self, input_sequence: list[str], report_path: str):
        self.input_sequence = self._flatten_sequence(input_sequence)
        self.report_path = report_path
        self.input_index = 0
        self.frames = []
        self.clipboards = []

    def _flatten_sequence(self, input_sequence: list[str]) -> list[str]:
        flattened = []
        for item in input_sequence:
            if isinstance(item, str):
                if len(item) > 1 and not item.startswith("\x1b") and not item.startswith("\033"):
                    flattened.extend(list(item))
                else:
                    flattened.append(item)
            else:
                flattened.append(item)
        return flattened

    def to_clipboard(self, text_content: str) -> int:
        self.clipboards.append(text_content)
        return len(text_content.splitlines())

    def write(self, text: str) -> None:
        self.frames.append(text)
        self._flush_report()

    def read_char(self) -> str:
        if self.input_index >= len(self.input_sequence):
            raise TestSequenceEnded
        
        try:
            ch = self.input_sequence[self.input_index]
            self.input_index += 1
            return ch
        except Exception as ex:
            raise TerminalFailure from ex

    def get_acceptance(self, required_phrase: str | None) -> tuple[str, str]:

        if required_phrase is None:
            while True:
                ch = self.read_char()
                if ch in IOControl.ABORT_KEYS:
                    return (IOControl.DECLINED, "")
                if ch == IOControl.ACCEPT_KEY:
                    return (IOControl.ACCEPTED, "")

        buffer = ""
        while True:
            ch = self.read_char()
            if ch in IOControl.ABORT_KEYS:
                return (IOControl.DECLINED, "")
            if ch == IOControl.ACCEPT_KEY:
                if buffer == required_phrase:
                    return (IOControl.ACCEPTED, "")
                return (IOControl.INVALID, buffer)
            if ch in IOControl.BACKSPACE_KEYS:
                if len(buffer) > 0:
                    buffer = buffer[:-1]
            elif ch.isprintable():
                buffer += ch

    def _flush_report(self) -> None:
        try:
            report = {
                "frames": self.frames,
                "clipboards": self.clipboards,
                "inputs_consumed": self.input_index
            }
            os.makedirs(os.path.dirname(os.path.abspath(self.report_path)), exist_ok=True)
            with open(self.report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
        except (OSError, UnicodeError, TypeError) as ex:
            raise TerminalFailure from ex