from backend.stdlib import ABC, abstractmethod


class NoSuchFile(Exception): pass
class FileAccessError(Exception): pass
class InvalidPathToken(Exception): pass

class DiskPort(ABC):
    @abstractmethod
    def get_file_contents(self, tokenized_path: str) -> str: ...  # raises: InvalidPathToken, NoSuchFile, FileAccessError

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