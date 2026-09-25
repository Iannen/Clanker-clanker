from enum import StrEnum
class PathTokens:
    PUD = "<PUD>"
    SHARED = "<SHARED>"
"""
class ClankerAssets:
    SYSTEM_CFG = PathTokens.SHARED + "/content/a_lib/shared-assets/config-fragments/system_cfg.yaml"
    SHARED_CFG = PathTokens.SHARED + "/content/a_lib/shared-assets/config-fragments/shared_cfg.yaml"
    TEMPLATE_CFG = PathTokens.SHARED + "/content/a_lib/templates/config.template"
    README_TEMPLATE = PathTokens.SHARED + "/content/a_lib/templates/README.template"
    DOC_ARCHITECTURE_TEMPLATE = PathTokens.SHARED + "/content/a_lib/templates/documentation/architecture.template"
    DOC_NORTH_STAR_TEMPLATE = PathTokens.SHARED + "/content/a_lib/templates/documentation/north-star.template"
    DOC_BACKLOG_TEMPLATE = PathTokens.SHARED + "/content/a_lib/templates/documentation/backlog.template"
    DOC_PROJECT_HISTORY_TEMPLATE = PathTokens.SHARED + "/content/a_lib/templates/documentation/project-history.template"

    UI = PathTokens.SHARED + "/content/a_lib/shared-assets/layouts/ui.layout"
    PROMPT = PathTokens.SHARED + "/content/a_lib/shared-assets/layouts/prompt.layout"
    BTN_ACTIVE = PathTokens.SHARED + "/content/a_lib/shared-assets/layouts/btn_active.layout"
    BTN_HL = PathTokens.SHARED + "/content/a_lib/shared-assets/layouts/btn_hl.layout"
    BTN_INACTIVE = PathTokens.SHARED + "/content/a_lib/shared-assets/layouts/btn_inactive.layout"
"""
"""
class PudAssets:
    PUD_CFG = PathTokens.PUD + "/.clanker/config.yaml"
    README = PathTokens.PUD + "/README.md"
    CONTENTS_DIR = PathTokens.PUD + "/content"
    DOC_ARCHITECTURE = PathTokens.PUD + "/.clanker/progress-documentation/architecture.cdoc"
    DOC_NORTH_STAR = PathTokens.PUD + "/.clanker/progress-documentation/north-star.cdoc"
    DOC_BACKLOG = PathTokens.PUD + "/.clanker/progress-documentation/backlog.backlog"
    DOC_PROJECT_HISTORY = PathTokens.PUD + "/.clanker/progress-documentation/project-history.history"
"""
class ClankerAssets:
    class States(StrEnum):
        OK = "co"     
        EMPTY = "ce"   
        BAD = "cb"     

    class Configs(StrEnum):
        SYSTEM = PathTokens.SHARED + "/content/a_lib/shared-assets/config-fragments/system_cfg.yaml"
        SHARED = PathTokens.SHARED + "/content/a_lib/shared-assets/config-fragments/shared_cfg.yaml"

    class Templates(StrEnum):
        CFG = PathTokens.SHARED + "/content/a_lib/templates/config.template"
        README = PathTokens.SHARED + "/content/a_lib/templates/README.template"
        DOC_ARCHITECTURE = PathTokens.SHARED + "/content/a_lib/templates/documentation/architecture.template"
        DOC_NORTH_STAR = PathTokens.SHARED + "/content/a_lib/templates/documentation/north-star.template"
        DOC_BACKLOG = PathTokens.SHARED + "/content/a_lib/templates/documentation/backlog.template"
        DOC_PROJECT_HISTORY = PathTokens.SHARED + "/content/a_lib/templates/documentation/project-history.template"

    class Layouts(StrEnum):
        UI = PathTokens.SHARED + "/content/a_lib/shared-assets/layouts/ui.layout"
        PROMPT = PathTokens.SHARED + "/content/a_lib/shared-assets/layouts/prompt.layout"
        BTN_ACTIVE = PathTokens.SHARED + "/content/a_lib/shared-assets/layouts/btn_active.layout"
        BTN_HL = PathTokens.SHARED + "/content/a_lib/shared-assets/layouts/btn_hl.layout"
        BTN_INACTIVE = PathTokens.SHARED + "/content/a_lib/shared-assets/layouts/btn_inactive.layout"

class PudAssets:
    class Configs(StrEnum):
        PUD = PathTokens.PUD + "/.clanker/config.yaml"

    class Directories(StrEnum):
        CONTENTS = PathTokens.PUD + "/content"

    class Files(StrEnum):
        README = PathTokens.PUD + "/README.md"

    class Documentation(StrEnum):
        ARCHITECTURE = PathTokens.PUD + "/.clanker/progress-documentation/architecture.cdoc"
        NORTH_STAR = PathTokens.PUD + "/.clanker/progress-documentation/north-star.cdoc"
        BACKLOG = PathTokens.PUD + "/.clanker/progress-documentation/backlog.backlog"
        PROJECT_HISTORY = PathTokens.PUD + "/.clanker/progress-documentation/project-history.history"

class RepoContract:
    DIRS_TO_CREATE = [
        PudAssets.Directories.CONTENTS,
    ]

    MAPPINGS = [
        (ClankerAssets.Templates.CFG, PudAssets.Configs.PUD),
        (ClankerAssets.Templates.README, PudAssets.Files.README),
        (ClankerAssets.Templates.DOC_ARCHITECTURE, PudAssets.Documentation.ARCHITECTURE),
        (ClankerAssets.Templates.DOC_NORTH_STAR, PudAssets.Documentation.NORTH_STAR),
        (ClankerAssets.Templates.DOC_BACKLOG, PudAssets.Documentation.BACKLOG),
        (ClankerAssets.Templates.DOC_PROJECT_HISTORY, PudAssets.Documentation.PROJECT_HISTORY),
    ]

    @classmethod
    def get_all_target_paths(cls) -> set[str]:
        target_paths = set(cls.DIRS_TO_CREATE)
        for _, to_path in cls.MAPPINGS:
            target_paths.add(to_path)
        return target_paths
