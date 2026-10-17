import base64
import os
import sys
import termios
import tty
from core.engine_deps import TerminalPort, IOControl, TerminalFailure, Proposition

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

    def get_acceptance(self, proposition: Proposition) -> bool:
        try:
            msg = f"{proposition.subject}\n{proposition.statement}" if proposition.subject else proposition.statement
            
            if proposition.required_phrase is None:
                instructions = "Press [Ctrl+D] to proceed, or [ESC/Ctrl+C] to decline.\n> "
                base_msg = f"\n{msg}\n{instructions}"
                self.write(base_msg)
                while True:
                    ch = self.read_char()
                    if ch in IOControl.ABORT_KEYS:
                        return False
                    if ch == IOControl.ACCEPT_KEY:
                        return True

            instructions = f"Type '{proposition.required_phrase}' and press [Ctrl+D] to confirm, or [ESC/Ctrl+C] to cancel.\n> "
            base_msg = f"\n{msg}\n{instructions}"
            self.write(base_msg)

            while True:
                buffer = ""
                while True:
                    ch = self.read_char()
                    if ch in IOControl.ABORT_KEYS:
                        return False
                    if ch == IOControl.ACCEPT_KEY:
                        if buffer == proposition.required_phrase:
                            sys.stdout.write("\n")
                            sys.stdout.flush()
                            return True
                        break
                    if ch in IOControl.BACKSPACE_KEYS:
                        if len(buffer) > 0:
                            buffer = buffer[:-1]
                            sys.stdout.write("\b \b")
                            sys.stdout.flush()
                    elif ch.isprintable():
                        buffer += ch
                        sys.stdout.write(ch)
                        sys.stdout.flush()
                
                err = f"Invalid confirmation. Expected '{proposition.required_phrase}', got '{buffer}'. Try again.\n"
                self.write(f"{base_msg}{err}> ")
        except TerminalFailure:
            raise
        except (OSError, UnicodeError) as ex:
            raise TerminalFailure from ex