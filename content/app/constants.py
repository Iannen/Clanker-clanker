class PathTokens:
    PUD = "<PUD>"
    SHARED = "<SHARED>"
    CONTENT = "content"

class CfgFragments:
    PUD_CFG = PathTokens.PUD + "/.clanker/config.yaml"
    SYSTEM_CFG = PathTokens.SHARED + "/content/a_lib/shared-assets/config-fragments/system_cfg.yaml" 
    SHARED_CFG = PathTokens.SHARED + "/content/a_lib/shared-assets/config-fragments/shared_cfg.yaml" 
    TEMPLATE_CFG = PathTokens.SHARED + "/content/a_lib/templates/config.template"

class Layouts:
    UI = PathTokens.SHARED + "/content/a_lib/shared-assets/layouts/ui.layout"
    PROMPT = PathTokens.SHARED + "/content/a_lib/shared-assets/layouts/prompt.layout"
    BTN_ACTIVE = PathTokens.SHARED + "/content/a_lib/shared-assets/layouts/btn_active.layout"
    BTN_HL = PathTokens.SHARED + "/content/a_lib/shared-assets/layouts/btn_hl.layout"
    BTN_INACTIVE = PathTokens.SHARED + "/content/a_lib/shared-assets/layouts/btn_inactive.layout"
    
class RepoContract:
    DIRS_TO_CREATE = [
        PathTokens.PUD + "/content",
    ]

    MAPPINGS = [
        (
            PathTokens.SHARED + "/content/a_lib/templates/config.template",
            PathTokens.PUD + "/.clanker/config.yaml",
        ),
        (
            PathTokens.SHARED + "/content/a_lib/templates/README.template",
            PathTokens.PUD + "/README.md",
        ),
        (
            PathTokens.SHARED + "/content/a_lib/templates/documentation/architecture.template",
            PathTokens.PUD + "/.clanker/progress-documentation/architecture.cdoc",
        ),
        (
            PathTokens.SHARED + "/content/a_lib/templates/documentation/north-star.template",
            PathTokens.PUD + "/.clanker/progress-documentation/north-star.cdoc",
        ),
        (
            PathTokens.SHARED + "/content/a_lib/templates/documentation/backlog.template",
            PathTokens.PUD + "/.clanker/progress-documentation/backlog.backlog",
        ),
        (
            PathTokens.SHARED + "/content/a_lib/templates/documentation/project-history.template",
            PathTokens.PUD + "/.clanker/progress-documentation/project-history.history",
        ),
    ]

    @classmethod
    def get_all_target_paths(cls) -> set[str]:
        target_paths = set(cls.DIRS_TO_CREATE)
        for _, to_path in cls.MAPPINGS:
            target_paths.add(to_path)
        return target_paths
