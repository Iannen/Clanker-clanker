from dataclasses import dataclass, field
from typing import ClassVar, Callable

#eliminate all default assignments
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
    path: str | None = None

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
