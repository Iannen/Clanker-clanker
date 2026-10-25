from stdlib import dataclass, Type, re, Any, defaultdict

class classproperty:
    def __init__(self, func):
        self.func = func
    def __get__(self, obj, owner):
        return self.func(owner)

class Entity:
    def set_ancestor(self, ancestor: Any) -> None:
        self.ancestor = ancestor

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
    name: str | None
    files: list[File] 

@dataclass
class FilesetItem(Entity):
    value: str

@dataclass
class Fileset(Entity):
    name: str | None
    includes: list[FilesetItem]
    excludes: list[FilesetItem] | None

@dataclass
class PudFileset(Fileset): pass

@dataclass
class SharedFileset(Fileset): pass

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
    fileset: PudFileset 

@dataclass
class ManifestResolver(Resolver):
    type = "repo-manifest"
    pud_fileset: PudFileset 
    shared_fileset: SharedFileset | None

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
class NewBtn(Entity): key: str
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


class PathTokens:
    PUD = "<PUD>"
    SHARED = "<SHARED>"
SHR = PathTokens.SHARED

class RepoItem: pass

@dataclass
class Config(RepoItem):
    name: str; path: str; data: dict

@dataclass
class Filereq(RepoItem):
    name: str; path: str; content: str

class AssetPack(RepoItem):
    def __init__(self, token: str, paths: list[str]):
        self.token = token
        self.paths = paths
        self.resolved_map: dict[str, str] = {}
        self.collisions: list["FilenameCollision"] = []

        filename_to_paths: dict[str, list[str]] = defaultdict(list)
        for path_str in self.paths:
            filename = path_str.rsplit("/", 1)[-1]
            filename_to_paths[filename].append(path_str)

        for filename, raw_paths in filename_to_paths.items():
            full_paths = [f"{self.token}/{p}" for p in raw_paths]
            winner_path = sorted(full_paths, key=lambda p: (p.count("/"), p))[0]
            
            self.resolved_map[filename] = winner_path
            
            if len(full_paths) > 1: pass
                #self.collisions.append(FilenameCollision(filename, full_paths, winner_path))