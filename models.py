from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, ClassVar

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