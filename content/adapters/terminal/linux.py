import base64
import os
import sys
import termios
import tty
from core.engine_deps import TerminalPort, IOControl, TerminalFailure

class LinuxTerminalAdapter(TerminalPort):
    def to_clipboard(self, text_content: str) -> int:
        try:
            payload = base64.b64encode(text_content.encode("utf-8")).decode("utf-8")
            sys.stdout.write(f"\033]52;c;{payload}\007")
            sys.stdout.flush()
            return len(text_content.splitlines())
        except (OSError, UnicodeError) as ex:
            raise TerminalFailure from ex

    def write(self, text: str) -> None:
        res = os.system("clear")
        if res != 0:
            raise TerminalFailure from ValueError(f"'clear' failed with status code {res}")
        try:
            print(text, end="", flush=True)
        except (OSError, UnicodeError) as ex:
            raise TerminalFailure from ex

    def read_char(self) -> str:
        import termios
        import tty
        try:
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                ch = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            if not ch:
                raise TerminalFailure from ValueError("Unexpected empty read on stdin (EOF)")
            return ch
        except TerminalFailure:
            raise
        except (termios.error, OSError, EOFError) as ex:
            raise TerminalFailure from ex

    def get_acceptance(self, required_phrase: str | None) -> tuple[str, str]:
        try:
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
        except TerminalFailure:
            raise
        except (OSError, UnicodeError) as ex:
            raise TerminalFailure from ex