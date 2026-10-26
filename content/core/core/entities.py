from stdlib import dataclass, Type, re, Any, StrEnum

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


class PathTokens:
    PUD = "<PUD>"
    SHARED = "<SHARED>"

PUD = PathTokens.PUD
SHR = PathTokens.SHARED

SHR_CFG_FRAGS = SHR + "/content/a_lib/shared-assets/config-fragments/"
SHR_TEMPL = SHR + "/content/a_lib/templates/"
SHR_DOC_TEMPL = SHR_TEMPL + "documentation/"
SHR_LAYOUTS = SHR + "/content/a_lib/shared-assets/layouts/"
PROG_DOCS = PUD + "/.clanker/progress-documentation/"



class ClankerAssets:
    class Configs(StrEnum):
        sys_cfg = SHR_CFG_FRAGS + "system_cfg.yaml"
        shared_cfg = SHR_CFG_FRAGS + "shared_cfg.yaml"

    class templates(StrEnum):
        CFG = SHR_TEMPL + "config.template"
        README = SHR_TEMPL + "README.template"
        DOC_ARCHITECTURE = SHR_DOC_TEMPL + "architecture.template"
        DOC_NORTH_STAR = SHR_DOC_TEMPL + "north-star.template"
        DOC_BACKLOG = SHR_DOC_TEMPL + "backlog.template"
        DOC_PROJECT_HISTORY = SHR_DOC_TEMPL + "project-history.template"

    class layouts(StrEnum):
        UI = SHR_LAYOUTS + "ui.layout"
        PROMPT = SHR_LAYOUTS + "prompt.layout"
        BTN_ACTIVE = SHR_LAYOUTS + "btn_active.layout"
        BTN_HL = SHR_LAYOUTS + "btn_hl.layout"
        BTN_INACTIVE = SHR_LAYOUTS + "btn_inactive.layout"

class PudAssets:
    class Configs(StrEnum):
        configuration_file = PUD + "/.clanker/config.yaml"

    class Directories(StrEnum):
        CONTENTS = PUD + "/content"

    class Files(StrEnum):
        README = PUD + "/README.md"

    class Documentation(StrEnum):
        ARCHITECTURE = PROG_DOCS + "architecture.cdoc"
        NORTH_STAR = PROG_DOCS + "north-star.cdoc"
        BACKLOG = PROG_DOCS + "backlog.backlog"
        PROJECT_HISTORY = PROG_DOCS + "project-history.history"

class RepoContract:
    DIRS_TO_CREATE = [
        PudAssets.Directories.CONTENTS,
    ]

    MAPPINGS = [
        (ClankerAssets.templates.CFG, PudAssets.Configs.configuration_file),
        (ClankerAssets.templates.README, PudAssets.Files.README),
        (ClankerAssets.templates.DOC_ARCHITECTURE, PudAssets.Documentation.ARCHITECTURE),
        (ClankerAssets.templates.DOC_NORTH_STAR, PudAssets.Documentation.NORTH_STAR),
        (ClankerAssets.templates.DOC_BACKLOG, PudAssets.Documentation.BACKLOG),
        (ClankerAssets.templates.DOC_PROJECT_HISTORY, PudAssets.Documentation.PROJECT_HISTORY),
    ]

    @classmethod
    def get_all_target_paths(cls) -> set[str]:
        target_paths = set(cls.DIRS_TO_CREATE)
        for _, to_path in cls.MAPPINGS:
            target_paths.add(to_path)
        return target_paths