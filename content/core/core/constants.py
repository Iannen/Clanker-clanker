from stdlib import StrEnum


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