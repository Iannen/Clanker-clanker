class ActionResult:
    BOOTSTRAP_SUCCESS = "Bootstrap completed successfully"
    NO_PROMPT_BOUND = "No prompt assigned to key '{key}'"
    UNBOUND_KEY = "No action bound to key '{key}'"
    DOMAIN_SELECTED = "Domain '{domain}' on key '{key}' selected"
    KEY_EMPTY = "Key '{key}' is empty"
    COPIED_TO_CLIPBOARD = "Copied {lines} lines ({chars} chars) to clipboard"

    def __init__(self, message: str):
        self.message = message

class ActionResult:
    BOOTSTRAP_SUCCESS = "Bootstrap completed successfully"
    NO_PROMPT_BOUND = "No prompt assigned to key '{key}'"
    UNBOUND_KEY = "No action bound to key '{key}'"
    DOMAIN_SELECTED = "Domain '{domain}' on key '{key}' selected"
    KEY_EMPTY = "Key '{key}' is empty"
    COPIED_TO_CLIPBOARD = "Copied {lines} lines ({chars} chars) to clipboard"

    def __init__(self, message: str):
        self.message = message


class UserQuestions:
    REQUIRED_PHRASE = "yes"
    INIT_REPO = "Directory not initialized as clank repo - clankerize?"

    @classmethod
    def overflow_proceed(cls, dof_report: str) -> str:
        return f"{dof_report}\nDo you wish to proceed with overflowed domains trimmed?"

    @classmethod
    def complaints_proceed(cls, complaints: list[str]) -> str:
        return f"{"\n".join(complaints)}\nProceed anyway?"