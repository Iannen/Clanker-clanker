from abc import ABC, abstractmethod
from app.exceptions import Notice, Fatal

class TerminalPort(ABC):
    @abstractmethod
    def to_clipboard(self, text_content: str) -> int: ...

    @abstractmethod
    def write(self, text: str) -> None: ...

    @abstractmethod
    def read_char(self) -> str: ...

    @abstractmethod
    def get_acceptance(self, required_phrase: str | None) -> tuple[str, str]: ...


class NoSuchFile(Notice): leaf_ex = True
class FileAccessError(Fatal): leaf_ex = True

class DiskPort(ABC):
    @abstractmethod
    def get_file_contents(self, tokenized_path: str) -> str: ...

    @abstractmethod
    def assert_dir_absent(self, tokenized_path: str) -> None: ...

    @abstractmethod
    def assert_file_absent(self, tokenized_path: str) -> None: ...

    @abstractmethod
    def copy_file(
        self, from_path: str, to_dir: str, from_ext: str = "", to_ext: str = ""
    ) -> None: ...

    @abstractmethod
    def is_cwd_script_dir(self) -> bool: ...

    @abstractmethod
    def read_asset(self, tokenized_path: str) -> str: ...

    @abstractmethod
    def get_files(
        self,
        basepath_token: str,
        rel_roots: list[str],
        missing_ok: bool = False
    ) -> set[str]: ...

    @abstractmethod
    def get_contents_with_pud_fallback(
        self, file_names: list[str]
    ) -> dict[str, str | None]: ...

class ConfigParserPort(ABC):
    @abstractmethod
    def get_as_dict(self, raw_text: str) -> dict: ...