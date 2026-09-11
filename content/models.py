from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, ClassVar, Protocol
    
class BaseEx(ABC, Exception):
    @property
    @abstractmethod
    def leaf_ex(self) -> bool:pass

class Fatal(BaseEx): pass
class Notice(BaseEx): pass

class MissedNotice(Fatal): leaf_ex = True
class NoticeArgs(Fatal):
    leaf_ex = True
    def __init__(self, cls_name: str, args: tuple, kwargs: dict):
        super().__init__(f"Notice '{cls_name}' illegal args: args={args!r}, kwargs={kwargs!r}")
class BridgeLeakage(Fatal): leaf_ex = True
class UnexpectedEx(Fatal): leaf_ex = True
class CorruptClanker(Fatal): leaf_ex = True
class ConfigAssemblyFailure(Fatal): leaf_ex = True
class IllegalDuplicateFile(Fatal): leaf_ex = True
class UserTask(Fatal): leaf_ex = True

class UserDecline(Notice): leaf_ex = True
class ProgramExit(Notice): 
    leaf_ex = True
    def get_compliance_msg(self) -> str:
        return "Program exited"

class NoConfig(Notice): leaf_ex = True

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
    TYPE_TAIL: ClassVar[str] = "tail"
    TYPE_REGEX_RANGE: ClassVar[str] = "regex_range"

    type: str
    tail_lines: int | None = None
    from_line: str | None = None
    up_to: str | None = None

@dataclass
class File:
    name: str
    truncation_spec: TruncationSpec | None = None

@dataclass
class Filelist:
    files: list[File] = field(default_factory=list)

@dataclass
class FileSet:
    includes: list[str]
    excludes: list[str]

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
    TYPE_DOMAIN: ClassVar[str] = "domain"
    TYPE_PROMPT: ClassVar[str] = "prompt"

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