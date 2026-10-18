from stdlib import Queue
from core.engine_deps import (
    FrontendService, DiskPort, TerminalPort, StartResult, 
    UserDeclinedStart, UserDeclinedClankerize, StartupFailed, 
    ClankerizeResult, TerminateResult, BootCmd, 
    StartCmd, ClankerizeCmd, Command, Result, KbCmdResult, ExitResult
)
from ..tui import TUIRenderer

class FrontendServiceImpl(FrontendService):
    def __init__(self, io_bridge: TerminalPort, files: DiskPort) -> None:
        self.renderer: TUIRenderer = TUIRenderer(io_bridge=io_bridge, files=files)
        self._queue: Queue[Command] = Queue()
        self._queue.put(BootCmd())

    def get_request(self) -> Command:
        if not self._queue.empty():
            return self._queue.get()
        return self.renderer.read_request()

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
        if cmd is not None:
            self._queue.put(cmd)