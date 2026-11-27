from backend.stdlib import dataclass, Type, re, Any, StrEnum
from dataclasses import field

class CorruptClanker(Exception): pass

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
    path: str = ""

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
    files: Filelist
    type: str = "multi-document-retrieval"

@dataclass
class SharedBaseResolver(MultiDocResolver): pass
@dataclass
class PudBaseResolver(MultiDocResolver): pass

@dataclass
class RepoContentResolver(Resolver):
    content_fileset: PudFileset | None
    meta_fileset: PudFileset | None
    user_selected_files: list[str] = field(default_factory=list)
    assistant_selected_files: list[str] = field(default_factory=list)
    meta_files: list[str] = field(default_factory=list)
    type: str = "repo-content"

@dataclass
class Render(Entity):
    resolvers: list[Resolver]
    template: str = "prompt_template"
    inherit_base: bool = True
    inherit_domain: bool = True

@dataclass
class Prompt(Entity):
    name: str
    render: Render
    expanded_paths: list[str] = field(default_factory=list)

@dataclass
class Domain(Entity):
    name: str
    prompts: list[Prompt]
    resolvers: list[Resolver]

@dataclass
class SharedDomain(Domain): pass
@dataclass
class PudDomain(Domain): pass

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

class Delims:
    FILELIST_START_OPEN = ("§llul§", "<")
    FILELIST_START_CLOSE = ("§llur§", ">")
    FILELIST_END_OPEN = ("§llel§", "</")
    FILELIST_END_CLOSE = ("§ller§", ">")
    MANIFEST_MEMBER = ("§mm§", "🗄️")

    PROMPT_OPEN = ("§po§", "#")
    PROMPT_CLOSE = ("§pc§", "")
    CREATE_FILESET_UL = ("§cfsul§", "<create path=\"")
    READ_FILESET_UL = ("§rfsul§", "<file path=\"")
    UPDATE_FILESET_UL = ("§ufsul§", "<update path=\"")
    DELETE_FILESET_UL = ("§dfsul§", "<delete path=\"")

    CREATE_FILESET_BL = ("§cfsbl§", "</create")
    READ_FILESET_BL = ("§rfsbl§", "</file")
    UPDATE_FILESET_BL = ("§ufsbl§", "</update")

    FILESET_OPEN_END_TAG = ("§fsoet§", "\">")
    FILESET_CLOSED_END_TAG = ("§fscet§", "\"/>")
    FILESET_OPEN_END_TAG_BR = ("§fsoetbr§", ">")

    FILE_META_UL = ("§fmul§", "<file_meta path=\"")
    FILE_META_CLOSE = ("§fmc§", "\"/>")

class PathTokens:
    PUD = "<PUD>"
    SHARED = "<SHARED>"

SHR_CFG_FRAGS = PathTokens.SHARED + "/content/a_lib/shared-assets/config-fragments/"
SHR_TEMPL = PathTokens.SHARED + "/content/a_lib/templates/"
SHR_DOC_TEMPL = SHR_TEMPL + "documentation/"
SHR_LAYOUTS = PathTokens.SHARED + "/content/a_lib/shared-assets/layouts/"
PROG_DOCS = PathTokens.PUD + "/.clanker/progress-documentation/"

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
        configuration_file = PathTokens.PUD + "/.clanker/config.yaml"

    class Directories(StrEnum):
        CONTENTS = PathTokens.PUD + "/content"

    class Files(StrEnum):
        README = PathTokens.PUD + "/README.md"

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