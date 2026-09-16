class ActionResult:
    BOOTSTRAP_SUCCESS = "Bootstrap completed successfully"
    NO_PROMPT_BOUND = "No prompt assigned to key '{key}'"
    UNBOUND_KEY = "No action bound to key '{key}'"
    DOMAIN_SELECTED = "Domain '{domain}' on key '{key}' selected"
    KEY_EMPTY = "Key '{key}' is empty"
    COPIED_TO_CLIPBOARD = "Copied {lines} lines ({chars} chars) to clipboard"

    def __init__(self, message: str):
        self.message = message