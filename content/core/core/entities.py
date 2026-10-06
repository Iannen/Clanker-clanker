from stdlib import dataclass, ClassVar, Type, re

class classproperty:
    def __init__(self, func):
        self.func = func
    def __get__(self, obj, owner):
        return self.func(owner)

class Entity:
    @classproperty
    def key_name(cls) -> str:
        if hasattr(cls, "_key_name"):
            return cls._key_name

        name = re.sub(r'(?<!^)(?=[A-Z][a-z])|(?<=[a-z0-9])(?=[A-Z])', '_', cls.__name__)
        return name.lower()

    @classproperty
    def plural_key(cls) -> str:
        return getattr(cls, "_plural_key", f"{cls.key_name}s")

@dataclass
class TruncationSpec(Entity):
    TYPE_TAIL: ClassVar[str] = "tail"
    TYPE_REGEX_RANGE: ClassVar[str] = "regex_range"
    type: str
    tail_lines: int | None = None
    from_line: str | None = None
    up_to: str | None = None

@dataclass
class File(Entity):
    name: str
    truncation_spec: TruncationSpec | None = None
    path: str | None = None

@dataclass
class Filelist(Entity):
    files: list[File] 

@dataclass
class Fileset(Entity):
    includes: list[str]
    excludes: list[str] | None

@dataclass
class Resolver(Entity):
    anchor: str

@dataclass
class MultiDocResolver(Resolver):
    files: Filelist 

@dataclass
class RepoContentResolver(Resolver):
    fileset: Fileset 

@dataclass
class ManifestResolver(Resolver):
    pud_fileset: Fileset 
    shared_fileset: Fileset | None = None

@dataclass
class KBStateResolver(Resolver):
    anchor: str = "kb_info"

@dataclass
class Render(Entity):
    resolvers: list[Resolver] 
    template: str = "prompt_template"
    inherit_base: bool = True
    inherit_domain: bool = True

@dataclass 
class UIRender(Entity):
    resolvers: list[Resolver] 
    template: str = "prompt_template"
    inherit_base: bool = False
    inherit_domain: bool = False

@dataclass
class Prompt(Entity):
    name: str
    render: Render

@dataclass
class Domain(Entity):
    name: str
    prompts: list[Prompt]
    resolvers: list[Resolver]

@dataclass 
class NewBtn: key: str
@dataclass
class PromptButton(NewBtn): inhabitant: Prompt | None = None
@dataclass
class DomButton(NewBtn): inhabitant: Domain | None = None
@dataclass
class SharedDomButton(DomButton): pass
@dataclass
class PudDomButton(DomButton): pass

@dataclass
class Keyboard(Entity):
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
class RepoItem: name: str; path: str
@dataclass
class Filereq(RepoItem): content: str
@dataclass
class Config(RepoItem): data: dict

@dataclass
class AssetPack(RepoItem):
    name: str
    roots: list[str]
    paths: list[str]
