import base64
import os
import sys
import termios
import tty
from pathlib import Path
from ruamel.yaml import YAML
from ports_adapters.ports import IOBridgePort, FileBridgePort, ConfigIngestorPort, NoSuchFile, FileAccessError
from app.constants import PathTokens

from tui.tui_service import IOControl
class IOBridge(IOBridgePort):
    def to_clipboard(self, text_content: str) -> int:
        payload = base64.b64encode(text_content.encode("utf-8")).decode("utf-8")
        sys.stdout.write(f"\033]52;c;{payload}\007")
        sys.stdout.flush()
        return len(text_content.splitlines())

    def write(self, text: str) -> None:
        os.system("clear")
        print(text, end="", flush=True)

    def read_char(self) -> str:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

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
                    sys.stdout.write("\n")
                    sys.stdout.flush()
                    return (IOControl.ACCEPTED, "")
                return (IOControl.INVALID, buffer)
            if ch in IOControl.BACKSPACE_KEYS:
                if len(buffer) > 0:
                    buffer = buffer[:-1]
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
            elif ch.isprintable():
                buffer += ch
                sys.stdout.write(ch)
                sys.stdout.flush()

class ConfigIngestor(ConfigIngestorPort):
    def __init__(self) -> None:
        self.yaml = YAML()
    def get_as_dict(self, raw_text: str) -> dict:
        return self.yaml.load(raw_text)