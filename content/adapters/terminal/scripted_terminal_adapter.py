from dataclasses import dataclass, field, asdict
from typing import Optional
import json
import os
from core.engine_deps import TerminalPort, IOControl, TerminalFailure
from core import TestSequenceEnded

@dataclass
class ExecutionFrame:
    latest_input: Optional[str] = None
    latest_write: Optional[str] = None
    latest_clipboard: Optional[str] = None
    exit_code: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    disk_paths: list[str] = field(default_factory=list)

class ScriptedTerminalAdapter(TerminalPort):
    START_APP_EVENT = "__START_APP__"
    END_APP_EVENT = "__END_APP__"

    def __init__(self, input_sequence: list[str], sandbox_dir: Optional[str]):
        self.input_sequence = self._flatten_sequence(input_sequence)
        self.sandbox_dir = sandbox_dir
        self.input_index = 0
        self.records: list[ExecutionFrame] = [
            ExecutionFrame(latest_input=self.START_APP_EVENT)
        ]
        self.time = 0

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
        self.records[self.time].latest_clipboard = text_content
        self._flush_report()
        return len(text_content.splitlines())

    def write(self, text: str) -> None:
        self.records[self.time].latest_write = text
        self._flush_report()

    def read_char(self) -> str:
        self._flush_report()

        if self.input_index >= len(self.input_sequence):
            raise TestSequenceEnded
        
        try:
            ch = self.input_sequence[self.input_index]
            self.input_index += 1
            self.time += 1
            self.records.append(ExecutionFrame(latest_input=ch))
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
                "records": [asdict(r) for r in self.records]
            }
            os.makedirs(os.path.dirname(os.path.abspath(self.sandbox_dir)), exist_ok=True)
            with open(self.sandbox_dir, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
        except (OSError, UnicodeError, TypeError) as ex:
            raise TerminalFailure from ex