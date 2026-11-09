from stdlib import Queue
from core.engine_deps import (
    FrontendService, DiskPort, TerminalPort, StartResult,
    UserDeclinedStart, UserDeclinedClankerize, StartupFailed,
    ClankerizeResult, TerminateResult, BootCmd,
    Request, KbServiceEmission,
    PromptRenderResult,
)
from ..tui import TUIRenderer

class FrontendServiceImpl(FrontendService):
    def __init__(self, io_bridge: TerminalPort, files: DiskPort) -> None:
        self._queue: Queue[Request] = Queue()
        self.renderer: TUIRenderer = TUIRenderer(io_bridge=io_bridge, files=files, queue=self._queue)
        self._queue.put(Request(id=self.renderer._next_id(), item=BootCmd()))

    def get_request(self) -> Request:
        return self.renderer.read_request()

    def post_response(self, req: Request) -> None:
        match req.item:
            case StartResult():
                self.renderer.post_question(req.item, UserDeclinedStart)
            case ClankerizeResult():
                self.renderer.post_question(req.item, UserDeclinedClankerize)
            case TerminateResult():
                self.renderer.get_acknowledgement(req.item, StartupFailed)
            case KbServiceEmission():
                if isinstance(req.item, PromptRenderResult):
                    self.renderer.io_bridge.to_clipboard(req.item.text)
                self.renderer.display_result(req.item)