#Actionresult is deprecated, and will be phased out

class ActionResult:
    BOOTSTRAP_SUCCESS = "Bootstrap completed successfully"
    UNBOUND_KEY = "No action bound to key '{key}'"
    DOMAIN_SELECTED = "Domain '{domain}' on key '{key}' selected"
    KEY_EMPTY = "Key '{key}' is empty"
    COPIED_TO_CLIPBOARD = "Copied {lines} lines ({chars} chars) to clipboard"

    MSG_DEFAULT: str = "Program exited"
    MSG_DECLINED_INIT: str = "User declined to clankerize project"
    MSG_DECLINED_BOOTSTRAP: str = "Bootstrap declined by user"

    def __init__(self, message: str):
        self.message = message
        
