from stdlib import Queue
from core.engine_deps import (
    FrontendService, DiskPort, TerminalPort, StartResult,
    UserDeclinedStart, UserDeclinedClankerize, StartupFailed,
    ClankerizeResult, TerminateResult, BootCmd,
    Command, Result, KbServiceEmission,
    PromptRenderResult,
)
from ..tui import TUIRenderer

class FrontendServiceImpl(FrontendService):
    def __init__(self, io_bridge: TerminalPort, files: DiskPort) -> None:
        self._queue: Queue[Command] = Queue()
        self._queue.put(BootCmd())
        self.renderer: TUIRenderer = TUIRenderer(io_bridge=io_bridge, files=files, queue=self._queue)

    def get_request(self) -> Command:
        return self.renderer.read_request()

    def post_response(self, result: Result) -> None:
        match result:
            case StartResult():
                self.renderer.post_question(result, UserDeclinedStart)
            case ClankerizeResult():
                self.renderer.post_question(result, UserDeclinedClankerize)
            case TerminateResult():
                self.renderer.get_acknowledgement(result, StartupFailed)
            case KbServiceEmission():
                if isinstance(result, PromptRenderResult):
                    self.renderer.io_bridge.to_clipboard(result.text)
                self.renderer.display_result(result)