from abc import ABC, abstractmethod

class ContentShaper(ABC):
    @abstractmethod
    def normalize_file_spec(self, item: str | dict) -> tuple[str, int | None]: ...

    @abstractmethod
    def apply_truncation(self, content: str, spec: TruncationSpec | None) -> str: ...

    @abstractmethod
    def hydrate(
        self, delim: str, template: str, replacements: dict[str, str]
    ) -> str: ...