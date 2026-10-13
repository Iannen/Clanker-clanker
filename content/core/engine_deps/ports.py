from stdlib import ABC, abstractmethod, dataclass

class IOControl:
    ACCEPTED = "accepted"
    DECLINED = "declined"
    INVALID = "invalid"
    ABORT_KEYS = ("\x1b", "\x03")
    ACCEPT_KEY = "\x04"
    BACKSPACE_KEYS = ("\x7f", "\x08")

class TerminalFailure(Exception): pass

@dataclass
class Question:
    message: str
    required_phrase: str | None = None
    instructions: str = ""
    error_template: str | None = None

class TerminalPort(ABC):
    @abstractmethod
    def to_clipboard(self, text_content: str) -> int: ...  # raises: TerminalFailure

    @abstractmethod
    def write(self, text: str) -> None: ...  # raises: TerminalFailure

    @abstractmethod
    def read_char(self) -> str: ...  # raises: TerminalFailure

    @abstractmethod
    def get_acceptance(self, question: Question) -> bool: ...  # raises: TerminalFailure


class NoSuchFile(Exception): pass
class AssetExists(Exception): pass
class FileAccessError(Exception): pass
class InvalidPathToken(Exception): pass

class DiskPort(ABC):
    @abstractmethod
    def get_file_contents(self, tokenized_path: str) -> str: ...  # raises: InvalidPathToken, NoSuchFile, FileAccessError

    @abstractmethod
    def assert_absent(self, tokenized_path: str) -> None: ...  # raises: InvalidPathToken, AssetExists

    @abstractmethod
    def create_dir(
        self, tokenized_path: str
    ) -> None: ...  # raises: InvalidPathToken, FileAccessError

    @abstractmethod
    def copy_file(
        self, from_path: str, to_path: str
    ) -> None: ...  # raises: InvalidPathToken, NoSuchFile, FileAccessError

    @abstractmethod
    def is_cwd_script_dir(self) -> bool: ...

    @abstractmethod
    def read_asset(self, tokenized_path: str) -> str: ...  # raises: InvalidPathToken, NoSuchFile, FileAccessError

    @abstractmethod
    def get_file_paths(
        self,
        basepath_token: str,
        rel_roots: list[str],
        missing_ok: bool = False
    ) -> set[str]: ...  # raises: InvalidPathToken, NoSuchFile, FileAccessError

    @abstractmethod
    def get_dir_manifest(
        self,
        basepath_token: str,
        rel_roots: list[str]
    ) -> set[str]: ...  # raises: InvalidPathToken, NoSuchFile, FileAccessError

class ConfigParseError(Exception):pass
class ConfigParserPort(ABC):
    @abstractmethod
    def get_as_dict(self, raw_text: str) -> dict: ...  # raises: ConfigParseError