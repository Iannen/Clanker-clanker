from core.engine_deps import FrontendService, IOControl, TerminalPort, DiskPort, StartResult, UserDeclinedStart, UserDeclinedClankerize, StartupFailed, UserAborted, KbCmd, ClankerizeResult, TerminateResult, BootCmd, StartCmd, ClankerizeCmd, Command, Result, KbCmdResult, ExitResult
from ..tui import TUIRenderer

class TUIServiceImpl(FrontendService):
    def __init__(self, io_bridge: TerminalPort, files: DiskPort) -> None:
        self.io_bridge = io_bridge
        self.renderer: TUIRenderer = TUIRenderer(io_bridge=self.io_bridge, files=files)
        self._cmd = BootCmd()

    def get_request(self) -> Command:
        if self._cmd: 
            return self._cmd
        ch = self.io_bridge.read_char()
        if ch in IOControl.ABORT_KEYS:
            return UserAborted()
        return KbCmd(char=ch.lower())        

    def post_response(self, result: Result) -> None:
        cmd = None
        match result:
            case StartResult(): 
                cmd = self.renderer.post_question(result, StartCmd, UserDeclinedStart)
            case ClankerizeResult(): 
                cmd = self.renderer.post_question(result, ClankerizeCmd, UserDeclinedClankerize)
            case TerminateResult(): 
                cmd = self.renderer.get_acknowledgement(result, StartupFailed)
            case KbCmdResult(): 
                self.renderer.display_result(result)
            case ExitResult(): 
                self.renderer.display_result(result)
        self._cmd = cmd