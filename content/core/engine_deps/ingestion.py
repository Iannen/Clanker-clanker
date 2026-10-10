from stdlib import ABC, abstractmethod, dataclass, Field
from core import Render, Keyboard, File

class Report(ABC):
    @abstractmethod
    def get_complaints(self) -> list[str]: ...
    @abstractmethod
    def get_critical_complaints(self) -> list[str]: ...

@dataclass(slots=True, frozen=True)
class StartResult:
    report: Report
    kb: Keyboard
    ui_render: Render

@dataclass(slots=True, frozen=True)
class ClankerizeResult:
    report: Report

@dataclass(slots=True, frozen=True)
class TerminateResult:
    report: Report

class IngestionService(ABC): 
    @abstractmethod
    def get_runtime_config(self) -> StartResult | ClankerizeResult | TerminateResult: ...
    @abstractmethod
    def initialize_workspace(self) -> None: ...

class Complaint(ABC):
    @abstractmethod
    def to_string(self) -> str: ...

class Critical(Complaint): pass
class Soft(Complaint): pass

@dataclass
class Malformed(Critical):
    name: str; path: str; details: str
    def to_string(self): return f"{self.__class__.__name__}: '{self.name}' at '{self.path}': \n{self.details}"

@dataclass
class Missing(Critical):
    name: str; paths: str | list[str]
    def to_string(self): return f"{self.__class__.__name__}: '{self.name}' not found at '{self.paths}'"

@dataclass(slots=True)
class FilenameCollision(Soft):
    filename: str
    paths: list[str]
    chosen_path: str

    def to_string(self) -> str:
        formatted_paths = ", ".join(f"'{p}'" for p in sorted(self.paths))
        return (
            f"Filename collision detected for '{self.filename}'. Coexisting paths: {formatted_paths}\n"
            f"\tDefaulted to using: '{self.chosen_path}'"
        )

@dataclass(slots=True)
class DomainOverflow(Soft):
    buttons: list["NewBtn"]
    discarded_domains: list["Domain"]

    def to_string(self) -> str:
        row_keys = [btn.key for btn in self.buttons if hasattr(btn, "key")]
        accepted_count = sum(len(btn.domains) for btn in self.buttons if hasattr(btn, "domains"))
        received_count = accepted_count + len(self.discarded_domains)
        msg = f"Domain overflow in row '{row_keys}': received {received_count} domains, but only {accepted_count} slots are available."
        for dom in self.discarded_domains:
            msg += f"\n\tDomain '{dom.name}' was discarded."
        return msg

@dataclass(slots=True)
class UnsatisfiedFiles(Soft):
    files: list[File]

    def to_string(self) -> str:
        files_str = "\n\t- ".join(f"'{f.name}'" for f in self.files)
        return (
            f"Removed {len(self.files)} file reference(s) "
            f"unsatisfied by asset packs:\n\t- {files_str}"
        )

@dataclass(slots=True)
class UnsatisfiedFilesetSubjects(Soft):
    assetpack_name: str
    subjects: list[str]

    def to_string(self) -> str:
        subjects_str = "\n\t- ".join(f"'{s}'" for s in self.subjects)
        return (
            f"Asset pack '{self.assetpack_name}': Removed {len(self.subjects)} unsatisfied subject(s):\n\t- {subjects_str}"
        )

@dataclass(slots=True)
class MissingEntityFields(Soft):
    entity_cls: type
    missing_fields: list[Field]
    data: dict

    def to_string(self) -> str:
        fields_str = ", ".join(f"'{f.name}'" for f in self.missing_fields)
        return (
            f"Failed to instantiate '{self.entity_cls.__name__}' due to missing required field(s): {fields_str}\n"
            f"\tReceived data: {self.data}"
        )

