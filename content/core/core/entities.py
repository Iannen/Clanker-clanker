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
    selected_dom_btn: DomButton | None = None
    def get_btns(self, cls: Type[NewBtn] | None = None) -> list[NewBtn]:
        all_btns = [
            *self.shared_dom_btns.values(),
            *self.pud_dom_btns.values(),
            *self.prompt_btns.values(),
        ]
        if cls is None:
            return all_btns
        return [btn for btn in all_btns if isinstance(btn, cls)]
    def get(self, key: str, default: NewBtn | None = None) -> NewBtn | None:
        return (
            self.shared_dom_btns.get(key)
            or self.pud_dom_btns.get(key)
            or self.prompt_btns.get(key, default)
        )
    def set_selected_dom_btn(self, btn:DomButton):
        self.selected_dom_btn=btn

@dataclass
class AssetPack:
    name: str
    roots: list[str]
    paths: list[str]
@dataclass
class RepoItem: name: str; path: str
@dataclass
class Filereq(RepoItem): pass
@dataclass
class Config(RepoItem): data: dict