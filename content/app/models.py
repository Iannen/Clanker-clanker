from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, ClassVar


""" 
Author understands below to be entities. 
He thinks they are suitable for a submodule of 'models' - 'entities'

In general he thinks none should supply default value.
    - an ingestion / validation responsibility
They should only be 'nonnable' *if that makes sense given the intended workings of the system.*

Any functionality of methods must be curated to not violate CA principles

Author notes that every class depends upon the values of ingested config, except for the RuntimeConfig and Keyboard classes.
These two classes are sort of container classes which the system otherwise uses to
    - assigning inhabitants and actions to the buttons
    - and then accessing the actions
Certainly they can be flattened into one class? 
If this is the way - does this class become a service in the system, receiving the buttonmap from the ingestion system?

Excluding the fact that presentation concerns leak in - are these all entities of the system?
""" 

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

""" 
the Ex machinery. 
Author thinks the baseclasses should remain 'center stage', while at least the leaf nodes migrate down closer to their usage modules.
""" 

class BaseEx(ABC, Exception):
    @property
    @abstractmethod
    def leaf_ex(self) -> bool:pass

class Fatal(BaseEx):
    def __str__(self) -> str:
        msg = super().__str__()
        return f": {msg}" if msg else ""

class Notice(BaseEx): pass

class MissedNotice(Fatal): leaf_ex = True
class NoticeArgs(Fatal):
    leaf_ex = True
    def __init__(self, cls_name: str, args: tuple, kwargs: dict):
        super().__init__(f"Notice '{cls_name}' illegal args: args={args!r}, kwargs={kwargs!r}")
class AdapterLeakage(Fatal):
    leaf_ex = True
    def __str__(self) -> str:
        if not self.args and self.__cause__:
            return f": [{type(self.__cause__).__name__}] {self.__cause__}"
        return super().__str__()
class UnexpectedEx(Fatal): leaf_ex = True
class CorruptClanker(Fatal): leaf_ex = True
class ConfigAssembly(Fatal): leaf_ex = True
class IllegalDuplicateFile(Fatal): leaf_ex = True
class UserTask(Fatal): leaf_ex = True

class UserDecline(Notice): leaf_ex = True
class ProgramExit(Notice): 
    leaf_ex = True
    MSG_DEFAULT: ClassVar[str] = "Program exited"
    MSG_DECLINED_INIT: ClassVar[str] = "Initialization declined by user"
    MSG_DECLINED_BOOTSTRAP: ClassVar[str] = "Bootstrap declined by user"
    
class NoConfig(Notice): leaf_ex = True

""" 
Author think these appear to be concerned with supplying paths and other statics to the rest of the system.
It is thought that it is good to keep this 'center stage', but perhaps in separate file?

'llm says: 
""" 
class SystemKeys:
    DELIM = "§"

class Config:
    DEFAULT_REL_PATH: ClassVar[str] = "/.clanker/config.yaml"

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
    PUD_CFG = "/.clanker/config.yaml"
    SYSTEM_CFG = "/.clanker/shared-assets/config-fragments/system_cfg.yaml" 
    SHARED_CFG = "/.clanker/shared-assets/config-fragments/shared_cfg.yaml" 
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

""" 
Author is not certain what to make of this one. right now its simple str, but soon it may become more complex:
    - yield some content to a header
    - other to  a sidebar
    - and so on

An llm said: this is a 'ViewModel', and belongs in a 'presentation layer' - but what does that boil down to concretely with regards to placement?
""" 

class ActionResult:
    def __init__(self, message: str):
        self.message = message

    def get_msg(self) -> str:
        width = 117
        return f"{self.message:<{width}}"[:width]
