from abc import ABC, abstractmethod
from app.exceptions import Notice, Fatal

class IOControl:
    ACCEPTED = "accepted"
    DECLINED = "declined"
    INVALID = "invalid"
    ABORT_KEYS = ("\x1b", "\x03")
    ACCEPT_KEY = "\x04"
    BACKSPACE_KEYS = ("\x7f", "\x08")

class TerminalFailure(Fatal): leaf_ex = True

class TerminalPort(ABC):
    @abstractmethod
    def to_clipboard(self, text_content: str) -> int: ...  # raises: TerminalFailure

    @abstractmethod
    def write(self, text: str) -> None: ...  # raises: TerminalFailure

    @abstractmethod
    def read_char(self) -> str: ...  # raises: TerminalFailure

    @abstractmethod
    def get_acceptance(self, required_phrase: str | None) -> tuple[str, str]: ...  # raises: TerminalFailure


class NoSuchFile(Notice): leaf_ex = True
class FileAccessError(Fatal): leaf_ex = True
class InvalidPathToken(Fatal): leaf_ex = True

class PathTokens:
    PUD = "<PUD>"
    SHARED = "<SHARED>"
    CONTENT = "content"

class DiskPort(ABC):
    @abstractmethod
    def get_file_contents(self, tokenized_path: str) -> str: ...  # raises: InvalidPathToken, NoSuchFile, FileAccessError

    @abstractmethod
    def assert_dir_absent(self, tokenized_path: str) -> None: ...  # raises: InvalidPathToken, WorkspaceAlreadyInitialized

    @abstractmethod
    def assert_file_absent(self, tokenized_path: str) -> None: ...  # raises: InvalidPathToken, WorkspaceAlreadyInitialized

    @abstractmethod
    def copy_file(
        self, from_path: str, to_dir: str, from_ext: str = "", to_ext: str = ""
    ) -> None: ...  # raises: InvalidPathToken, NoSuchFile, FileAccessError

    @abstractmethod
    def is_cwd_script_dir(self) -> bool: ...

    @abstractmethod
    def read_asset(self, tokenized_path: str) -> str: ...  # raises: InvalidPathToken, NoSuchFile, FileAccessError

    @abstractmethod
    def get_files(
        self,
        basepath_token: str,
        rel_roots: list[str],
        missing_ok: bool = False
    ) -> set[str]: ...  # raises: InvalidPathToken, NoSuchFile, FileAccessError

    @abstractmethod
    def get_contents_with_pud_fallback(
        self, file_names: list[str]
    ) -> dict[str, str | None]: ...  # raises: IllegalDuplicateFile, NoSuchFile, FileAccessError

class ConfigParseError(Notice): leaf_ex = True
class ConfigParserPort(ABC):
    @abstractmethod
    def get_as_dict(self, raw_text: str) -> dict: ...  # raises: ConfigParseError