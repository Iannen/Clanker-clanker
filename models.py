from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, ClassVar, Protocol

class IOBridgePort(Protocol):
    def to_clipboard(self, text_content: str) -> int: ...
    def write(self, text: str) -> None: ...
    def read_char(self) -> str: ...
    def get_acceptance(self, required_phrase: str | None) -> tuple[str, str]: ...


class FileBridgePort(Protocol):
    def get_file_contents(self, tokenized_path: str) -> str: ...
    def write_default_documents(
        self, doc_templ_dir: str, pud_doc_dir: str, templ_ext: str, doc_ext: str
    ) -> None: ...
    def is_cwd_script_dir(self) -> bool: ...
    def write_yaml(self, tokenized_path: str, data: dict) -> None: ...
    def read_asset(self, tokenized_path: str | Path) -> str: ...
    def get_files(
        self,
        basepath_token: str,
        rel_roots: list[str | Path],
        missing_ok: bool = False
    ) -> set[Path]: ...
    def get_contents_with_pud_fallback(
        self, file_names: list[str]
    ) -> dict[str, str | None]: ...


class ContentShaper(Protocol):
    def normalize_file_spec(self, item: str | dict) -> tuple[str, int | None]: ...
    def trim_to_tail(self, content: str, tail_lines: int | None) -> str: ...
    def hydrate(
        self, delim: str, template: str, replacements: dict[str, str]
    ) -> str: ...


class ConfigValidatorProtocol(Protocol):
    def assert_no_quotes(self, raw_text: str, filepath: str = "") -> None: ...
    def get_as_dict(self, raw_text: str) -> dict: ...
    def assert_filesets_not_neglected(
        self, cfg_frag: dict, filepath: str = ""
    ) -> None: ...


class RuntimeConfigAssemblerProtocol(Protocol):
    def assemble(
        self,
        config_data: dict,
        kb_def_data: dict,
        shared_domains_data: dict
    ) -> RuntimeConfig: ...


class BaseEx(ABC, Exception):
    @property
    @abstractmethod
    def leaf_ex(self) -> bool:pass

class Failure(BaseEx): pass
class ControlNotice(BaseEx): pass
class UserNotice(BaseEx): pass

class MissedNotice(Failure): leaf_ex = True
class BaseExInstantiation(Failure): leaf_ex = True
class NoticeArgs(Failure): leaf_ex = True
class BridgeLeakage(Failure): leaf_ex = True
class BadFile(Failure): leaf_ex = True
class NotImplemented(Failure): leaf_ex = True
class MissedAdoptedNotice(Failure): leaf_ex = True
class UnexpectedEx(Failure): leaf_ex = True
class CorruptClanker(Failure): leaf_ex = True
class ConfigAssemblyFailure(Failure): leaf_ex = True
class IllegalDuplicateFile(Failure): leaf_ex = True
class UserTask(Failure): leaf_ex = True

class UserDecline(ControlNotice): leaf_ex = True
class ProgramExit(ControlNotice): 
    leaf_ex = True
    def get_compliance_msg(self) -> str:
        return "Program exited"

class NoConfig(ControlNotice): leaf_ex = True
class ConfigViolations(UserNotice): leaf_ex = True

class SystemKeys:
    DELIM = "§"

@dataclass
class Config:
    DEFAULT_REL_PATH: ClassVar[str] = "/.clanker/config.yaml"
    DEFAULT_ASSETS_DIR: ClassVar[Path] = Path(".clanker/assets")
    layout: str
    domains: list[str]

@dataclass
class TruncationSpec:
    tail_lines: int | None = None

@dataclass
class File:
    name: str
    full_path_from_pud: bool = False
    truncation_spec: TruncationSpec | None = None

@dataclass
class Filelist:
    files: list[File] = field(default_factory=list)

@dataclass
class FileSet:
    includes: list[str] = field(default_factory=list)
    excludes: list[str] = field(default_factory=list)

@dataclass
class Resolver:
    anchor: str

@dataclass
class MultiDocResolver(Resolver):
    files: Filelist = field(default_factory=Filelist)

@dataclass
class RepoContentResolver(Resolver):
    fileset: FileSet = field(default_factory=FileSet)

@dataclass
class ManifestResolver(Resolver):
    pud_fileset: FileSet = field(default_factory=FileSet)
    shared_fileset: FileSet | None = None

@dataclass
class KBStateResolver(Resolver):
    anchor: str = "kb_info"

@dataclass
class Render:
    template: str = "prompt_template"
    resolvers: list[Resolver] = field(default_factory=list)
    inherit_base: bool = True
    inherit_domain: bool = True

@dataclass
class Prompt:
    name: str
    render: Render

@dataclass
class Domain:
    name: str
    prompts: list[Prompt]
    resolvers: list[Resolver]

@dataclass
class Button:
    type: str
    key: str
    inhabitant: Domain | Prompt | None = None
    action: Callable | None = None

    def get_repl_map(self, label: str, template: str) -> dict[str, str]:
        lines = template.strip("\n").splitlines()
        norm_label = label[:6].ljust(6)
        mapped_lines = [
            lines[0],
            lines[1],
            lines[2].replace(SystemKeys.DELIM, self.key, 1),
            lines[3],
            lines[4].replace(SystemKeys.DELIM * 6, norm_label, 1),
        ]
        return {f"{self.key}{idx}": line for idx, line in enumerate(mapped_lines)}

@dataclass
class RuntimeConfig:
    keyboard: Keyboard
    ui_render: Render
    base_resolvers: list[Resolver]

@dataclass
class Keyboard:
    button_map: dict[str, Button]
    selected_key: str | None = None

    def get_unique_buttons(self, btn_type: str | None = None) -> list[Button]:
        unique = {btn.key: btn for btn in self.button_map.values()}.values()
        if btn_type is None:
            return list(unique)
        return [btn for btn in unique if btn.type == btn_type]

    def handle_key(self, key: str) -> ActionResult | None:
        btn = self.button_map.get(key)
        if btn is None:
            return None
        if callable(btn.action):
            return btn.action(key)
        return ActionResult(f"No action bound to key '{key}'")

class BasePathTokens:
    PUD = "<PUD>"
    SHARED = "<SHARED>"

class IOControl:
    ACCEPTED = "accepted"
    DECLINED = "declined"
    INVALID = "invalid"
    ABORT_KEYS = ("\x1b", "\x03")
    ACCEPT_KEY = "\x04"
    BACKSPACE_KEYS = ("\x7f", "\x08")

class CfgFragments:
    PUD_CFG = "/.clanker/config.yaml" #domains, prompts, filesets , filelists & such
    SYSTEM_CFG = "/.clanker/shared-assets/config-fragments/system_cfg.yaml" #ui render & rows for button instantiation
    SHARED_CFG = "/.clanker/shared-assets/config-fragments/shared_cfg.yaml" #domains, prompts, filesets , filelists & such
    TEMPLATE_CFG = "/.clanker/templates/config.template"
    
class DocPaths:
    SHARED_TEMPLATES = "/.clanker/templates/documentation"
    PUD_DOCS = "/.clanker/progress-documentation"
    TEMPL_EXT = ".template"
    DOC_EXT = ".cdoc"

class Layout:
    UI = "/.clanker/shared-assets/layouts/ui.layout"
    PROMPT = "/.clanker/shared-assets/layouts/prompt.layout"
    BTN_ACTIVE = "/.clanker/shared-assets/layouts/btn_active.layout"
    BTN_HL = "/.clanker/shared-assets/layouts/btn_hl.layout"
    BTN_INACTIVE = "/.clanker/shared-assets/layouts/btn_inactive.layout"

class ActionResult:
    def __init__(self, message: str):
        self.message = message

    def get_msg(self) -> str:
        width = 117
        return f"{self.message:<{width}}"[:width]