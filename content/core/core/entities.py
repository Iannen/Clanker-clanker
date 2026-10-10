from stdlib import dataclass, Type, re

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
    tail_lines: int | None
    from_line: str | None
    up_to: str | None

@dataclass
class File(Entity):
    name: str
    truncation_spec: TruncationSpec | None
    path: str | None

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
    type = "multi-document-retrieval"
    files: Filelist 

@dataclass
class SharedBaseResolver(MultiDocResolver): pass
@dataclass
class PudBaseResolver(MultiDocResolver): pass

@dataclass
class RepoContentResolver(Resolver):
    type = "repo-content"
    fileset: Fileset 

@dataclass
class ManifestResolver(Resolver):
    type = "repo-manifest"
    pud_fileset: Fileset 
    shared_fileset: Fileset | None

@dataclass
class KBStateResolver(Resolver):
    type = "ui-resolver"
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
class SharedDomain(Domain): pass
@dataclass 
class PudDomain(Domain): pass

@dataclass 
class NewBtn: key: str
@dataclass
class PromptButton(NewBtn): inhabitant: Prompt | None
@dataclass
class DomButton(NewBtn): inhabitant: Domain | None
@dataclass
class SharedDomButton(DomButton): pass
@dataclass
class PudDomButton(DomButton): pass

@dataclass
class Keyboard(Entity):
    buttons: dict[str, NewBtn]
    selected_dom_btn: DomButton | None

    def get_btns(self, cls: Type[NewBtn] | None = None) -> list[NewBtn]:
        if cls is None:
            return list(self.buttons.values())
        return [btn for btn in self.buttons.values() if isinstance(btn, cls)]

    def get(self, key: str) -> NewBtn | None:
        return self.buttons.get(key)

    def set_selected_dom_btn(self, btn: DomButton):
        self.selected_dom_btn = btn
