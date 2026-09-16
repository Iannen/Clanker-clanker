# user in render_pipeline, asset_ingestion and ports_adapters
class PathTokens:
    PUD = "<PUD>"
    SHARED = "<SHARED>"
    CONTENT = "content"

# used in asset_ingestion only
class CfgFragments:
    PUD_CFG = PathTokens.PUD + "/.clanker/config.yaml"
    SYSTEM_CFG = PathTokens.SHARED + "/content/a_lib/shared-assets/config-fragments/system_cfg.yaml" 
    SHARED_CFG = PathTokens.SHARED + "/content/a_lib/shared-assets/config-fragments/shared_cfg.yaml" 
    TEMPLATE_CFG = PathTokens.SHARED + "/content/a_lib/templates/config.template"

class DocPaths:
    SHARED_TEMPLATES = PathTokens.SHARED + "/content/a_lib/templates/documentation"
    PUD_DOCS = PathTokens.PUD + "/.clanker/progress-documentation"
    TEMPL_EXT = ".template"
    DOC_EXT = ".cdoc"

class TemplatePaths:
    CFG_TEMPLATE = PathTokens.SHARED + "/content/a_lib/templates/config.template"
    README_TEMPLATE = PathTokens.SHARED + "/content/a_lib/templates/README.template"
    ARCH_TEMPLATE = PathTokens.SHARED + "/content/a_lib/templates/documentation/architecture.template"
    BACKLOG_TEMPLATE = PathTokens.SHARED + "/content/a_lib/templates/documentation/backlog.template"
    NORTH_STAR_TEMPLATE = PathTokens.SHARED + "/content/a_lib/templates/documentation/north-star.template"
    PROJECT_HISTORY_TEMPLATE = PathTokens.SHARED + "/content/a_lib/templates/documentation/project-history.template"

# used in render_pipeline only
class Layouts:
    UI = PathTokens.SHARED + "/content/a_lib/shared-assets/layouts/ui.layout"
    PROMPT = PathTokens.SHARED + "/content/a_lib/shared-assets/layouts/prompt.layout"
    BTN_ACTIVE = PathTokens.SHARED + "/content/a_lib/shared-assets/layouts/btn_active.layout"
    BTN_HL = PathTokens.SHARED + "/content/a_lib/shared-assets/layouts/btn_hl.layout"
    BTN_INACTIVE = PathTokens.SHARED + "/content/a_lib/shared-assets/layouts/btn_inactive.layout"