#from stdlib import dataclass
#from core.engine_deps import Report

#Actionresult is deprecated, and will be phased out

class ActionResult:
    BOOTSTRAP_SUCCESS = "Bootstrap completed successfully"
    NO_PROMPT_BOUND = "No prompt assigned to key '{key}'"
    UNBOUND_KEY = "No action bound to key '{key}'"
    DOMAIN_SELECTED = "Domain '{domain}' on key '{key}' selected"
    KEY_EMPTY = "Key '{key}' is empty"
    COPIED_TO_CLIPBOARD = "Copied {lines} lines ({chars} chars) to clipboard"

    MSG_DEFAULT: str = "Program exited"
    MSG_DECLINED_INIT: str = "Initialization declined by user"
    MSG_DECLINED_BOOTSTRAP: str = "Bootstrap declined by user"

    def __init__(self, message: str):
        self.message = message
        
"""
class Result:
    @property
    def type(self) -> type: return type(self)

@dataclass
class IngestionResult(Result): report = Report
@dataclass
class StartResult(IngestionResult):
    kb: Keyboard
    ui_render: Render
@dataclass
class ClankerizeResult(IngestionResult): pass
@dataclass
class TerminateResult(IngestionResult): pass
"""