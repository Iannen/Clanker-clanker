from stdlib import StrEnum
class PathTokens:
    PUD = "<PUD>"
    SHARED = "<SHARED>"

class ClankerAssets:
    class States(StrEnum):
        OK = "co"     
        BAD = "cb"     

    class Configs(StrEnum):
        sys_cfg = PathTokens.SHARED + "/content/a_lib/shared-assets/config-fragments/system_cfg.yaml"
        shared_cfg = PathTokens.SHARED + "/content/a_lib/shared-assets/config-fragments/shared_cfg.yaml"

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
    class States(StrEnum):
        OK = "po"     
        EMPTY = "pe"   
        BAD = "pb"     
        
    class Configs(StrEnum):
        configuration_file = PathTokens.PUD + "/.clanker/config.yaml"

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
        (ClankerAssets.Templates.CFG, PudAssets.Configs.configuration_file),
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
