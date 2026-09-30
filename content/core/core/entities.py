from stdlib import dataclass, field, ClassVar, Callable

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

@dataclass 
class NewBtn: key: str
@dataclass
class PromptButton(NewBtn): inhabitant: Prompt | None = None
@dataclass
class DomButton(NewBtn): inhabitant: Domain
@dataclass
class SharedDomButton(DomButton): pass
@dataclass
class PudDomButton(DomButton): pass

@dataclass
class Keyboard:
    shared_dom_btns: dict[str, SharedDomButton]
    pud_dom_btns: dict[str, PudDomButton]
    prompt_btns: dict[str, PromptButton]
    selected_dom: Domain | None = None

@dataclass
class BaseCfg: name: str; path: str
@dataclass
class MissingConfig(BaseCfg): pass
@dataclass
class MalformedConfig(BaseCfg): details: str
@dataclass
class Config(BaseCfg): data: dict

@dataclass
class BaseAssetPack:
    name: str
    roots: list[str]
@dataclass
class AssetPack(BaseAssetPack):
    paths: list[str] | None = None
@dataclass
class MissingAssetPack(BaseAssetPack): pass
