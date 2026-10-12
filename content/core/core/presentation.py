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


class DoBootstrap(ActionResult):
    def __init__(self, message: str = ActionResult.BOOTSTRAP_SUCCESS):
        super().__init__(message)


class OfferBootstrapWithComplaints(ActionResult):
    def __init__(self, message: str = ActionResult.BOOTSTRAP_SUCCESS):
        super().__init__(message)


class OfferClankerize(ActionResult):
    def __init__(self, message: str = ActionResult.MSG_DECLINED_INIT):
        super().__init__(message)


class OfferClankerizeWithComplaints(ActionResult):
    def __init__(self, message: str = ActionResult.MSG_DECLINED_INIT):
        super().__init__(message)


class TerminateGracefully(ActionResult):
    def __init__(self, message: str = ActionResult.MSG_DEFAULT):
        super().__init__(message)
        
