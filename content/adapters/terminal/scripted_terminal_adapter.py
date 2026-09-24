from dataclasses import dataclass, field, asdict
from typing import Optional
from pathlib import Path
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

    def __init__(self, input_sequence: list[str], framedump_path: Path):
        self.sandbox_dir = os.getcwd()
        self.framedump_path = framedump_path
        self.input_sequence = self._flatten_sequence(input_sequence)
        self.frames = []
        self.input_index = 0
        self.last_write = None
        self.last_cp = None

    def _flatten_sequence(self, input_sequence: list[str]) -> list[str]:
        flattened = [self.START_APP_EVENT]
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
        self.last_cp = text_content
        return len(text_content.splitlines())

    def write(self, text: str) -> None:
        self.last_write = text

    def read_char(self) -> str:
        self.frames.append(ExecutionFrame(
            latest_input=self.input_sequence[self.input_index],
            latest_write=self.last_write,
            latest_clipboard=self.last_cp,
            disk_paths=self._get_disk_paths()
        ))
        self.last_cp = self.last_write = None
        if self.input_index + 1 >= len(self.input_sequence):
            raise TestSequenceEnded
        try:
            self.input_index += 1
            return self.input_sequence[self.input_index]
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

    def flush_report(
        self, 
        exit_code: Optional[int] = None, 
        stdout: Optional[str] = None, 
        stderr: Optional[str] = None
    ) -> None:
        try:
            self.frames.append(ExecutionFrame(
                latest_input=self.END_APP_EVENT,
                latest_write=self.last_write,
                latest_clipboard=self.last_cp,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                disk_paths=self._get_disk_paths()
            ))
            self.last_write = self.last_cp = None

            report = {
                "records": [asdict(r) for r in self.frames]
            }

            self.framedump_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.framedump_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
        except (OSError, UnicodeError, TypeError) as ex:
            raise TerminalFailure from ex

    def _get_disk_paths(self) -> list[str]:
        if not self.sandbox_dir or not os.path.isdir(self.sandbox_dir):
            return []

        root = Path(self.sandbox_dir)
        paths = [
            str(p.relative_to(root))
            for p in root.rglob("*")
            if p.relative_to(root).parts[0] != "framedumps"
        ]
        return sorted(paths)