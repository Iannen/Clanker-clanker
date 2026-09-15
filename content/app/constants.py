class CfgFragments:
    PUD_CFG = "/.clanker/config.yaml"
    SYSTEM_CFG = "/.clanker/shared-assets/config-fragments/system_cfg.yaml" 
    SHARED_CFG = "/.clanker/shared-assets/config-fragments/shared_cfg.yaml" 
    TEMPLATE_CFG = "/.clanker/templates/config.template"

class Layout:
    UI = "/.clanker/shared-assets/layouts/ui.layout"
    PROMPT = "/.clanker/shared-assets/layouts/prompt.layout"
    BTN_ACTIVE = "/.clanker/shared-assets/layouts/btn_active.layout"
    BTN_HL = "/.clanker/shared-assets/layouts/btn_hl.layout"
    BTN_INACTIVE = "/.clanker/shared-assets/layouts/btn_inactive.layout"

class Config:
    DEFAULT_REL_PATH: ClassVar[str] = "/.clanker/config.yaml"

class BasePathTokens:
    PUD = "<PUD>"
    SHARED = "<SHARED>"
    CONTENT = "content"