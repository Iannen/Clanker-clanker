# used in asset_ingestion only
class CfgFragments:
    PUD_CFG = "/.clanker/config.yaml"
    SYSTEM_CFG = "/.clanker/shared-assets/config-fragments/system_cfg.yaml" 
    SHARED_CFG = "/.clanker/shared-assets/config-fragments/shared_cfg.yaml" 
    TEMPLATE_CFG = "/.clanker/templates/config.template"

class DocPaths: # this one needs special attention, cuz adapter hardcodes stuff as str. no concat Pathtokens here yet. this turns into adapterrazzia later
    SHARED_TEMPLATES = "/.clanker/templates/documentation"
    PUD_DOCS = "/.clanker/progress-documentation"
    TEMPL_EXT = ".template"
    DOC_EXT = ".cdoc"

# used in render_pipeline only only
class Layout:
    UI = "/.clanker/shared-assets/layouts/ui.layout"
    PROMPT = "/.clanker/shared-assets/layouts/prompt.layout"
    BTN_ACTIVE = "/.clanker/shared-assets/layouts/btn_active.layout"
    BTN_HL = "/.clanker/shared-assets/layouts/btn_hl.layout"
    BTN_INACTIVE = "/.clanker/shared-assets/layouts/btn_inactive.layout"

# user in render_pipeline, asset_ingestion and ports_adapters
class BasePathTokens:
    PUD = "<PUD>"
    SHARED = "<SHARED>"
    CONTENT = "content"