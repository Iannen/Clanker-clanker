from abc import ABC, abstractmethod
from pathlib import Path

class IOBridgePort(ABC):
    @abstractmethod
    def to_clipboard(self, text_content: str) -> int: ...

    @abstractmethod
    def write(self, text: str) -> None: ...

    @abstractmethod
    def read_char(self) -> str: ...

    @abstractmethod
    def get_acceptance(self, required_phrase: str | None) -> tuple[str, str]: ...


class FileBridgePort(ABC):
    @abstractmethod
    def get_file_contents(self, tokenized_path: str) -> str: ...

    @abstractmethod
    def write_default_documents(
        self, doc_templ_dir: str, pud_doc_dir: str, templ_ext: str, doc_ext: str
    ) -> None: ...

    @abstractmethod
    def is_cwd_script_dir(self) -> bool: ...

    @abstractmethod
    def write_yaml(self, tokenized_path: str, data: dict) -> None: ...

    @abstractmethod
    def read_asset(self, tokenized_path: str | Path) -> str: ...

    @abstractmethod
    def get_files(
        self,
        basepath_token: str,
        rel_roots: list[str | Path],
        missing_ok: bool = False
    ) -> set[Path]: ...

    @abstractmethod
    def get_contents_with_pud_fallback(
        self, file_names: list[str]
    ) -> dict[str, str | None]: ...


class ConfigIngestorPort(ABC):
    @abstractmethod
    def get_as_dict(self, raw_text: str) -> dict: ...