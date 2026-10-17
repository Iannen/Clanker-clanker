from core.engine_deps import FrontendService, IOControl, TerminalPort, DiskPort, StartResult, UserDeclinedStart, UserDeclinedClankerize, StartupFailed, UserAborted, KbCmd, ClankerizeResult, TerminateResult, BootCmd, StartCmd, ClankerizeCmd, Command, Result
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
        """I feel this method has lost track of the results. it should account for all results that may appear.
         it should also map each possible result to a command or to None.
         perhaps the helper can have contract like
           - method that accepts a result, and two  possible cmd 
                 it runs the result by the user, and returns bool
           - a method that accepts a result and one optional cmd defaulting to None
                - displays the result, and then returns the command
        so then our switch here becomes just a big router table, kinda
        """

        self._cmd = None
        accepted = self.renderer.display(result)
        match result:
            case StartResult(): 
                self._cmd = StartCmd() if accepted else UserDeclinedStart()
            case ClankerizeResult(): 
                self._cmd = ClankerizeCmd() if accepted else UserDeclinedClankerize()
            case TerminateResult(): 
                self._cmd = StartupFailed()