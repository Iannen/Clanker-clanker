from core import Keyboard, DomButton, PromptButton, CorruptClanker, ClankerAssets
from core.engine_deps import FrontendService, IOControl, TerminalPort, DiskPort, StartResult, UserDeclinedStart, UserDeclinedClankerize, StartupFailed, UserAborted, KbCmd, NoSuchFile, ClankerizeResult, TerminateResult, KbCmdResult, BootCmd, IngestionResult, StartCmd, ClankerizeCmd, ExitResult, Command, Result
from ..tui import TUIQuestions, TUIContentShaper

class TUIServiceImpl(FrontendService):
    def __init__(self, io_bridge: TerminalPort, files: DiskPort) -> None:
        self.io_bridge = io_bridge
        self.files = files
        self.shaper: TUIContentShaper = TUIContentShaper()
        self.question_dispatcher: TUIQuestions = TUIQuestions(io_bridge=self.io_bridge)
        self._cmd = BootCmd()

    def get_request(self) -> Command:
        if self._cmd: 
            return self._cmd
        ch = self.io_bridge.read_char()
        if ch in IOControl.ABORT_KEYS:
            return UserAborted()
        return KbCmd(char=ch.lower())       

    def post_response(self, command_result: Result) -> None:
        match command_result:
            case ExitResult(): 
                cmd = None
            case IngestionResult(): 
                cmd = self._run_bootstrap_result(command_result)
            case KbCmdResult(): 
                self._handle_cmd_result(command_result)
                cmd = None
            case _:
                cmd = None
        self._cmd = cmd if cmd else None

    def _run_bootstrap_result(self, bootstrap_res: IngestionResult) -> Command:
        accepted = self.question_dispatcher.dispatch(bootstrap_res)
        match bootstrap_res:
            case StartResult(): 
                return StartCmd(bootstrap_res) if accepted else UserDeclinedStart()
            case ClankerizeResult(): 
                return ClankerizeCmd() if accepted else UserDeclinedClankerize()
            case TerminateResult(): 
                return StartupFailed()

    #belongs in helper class
    def _handle_cmd_result(self, command_result):
        try:
            template = self.files.read_asset(ClankerAssets.layouts.UI)
        except NoSuchFile as ex:
            raise CorruptClanker(f"Error loading template for '{command_result.ui_render.template}': {ex}") from ex
        repl_map = self._res_ui(command_result.kb)
        repl_map["msg"] = self.shaper.shape_command_result(command_result)
        ui_string = self.shaper.hydrate(template, repl_map)
        self.io_bridge.write(f"{ui_string}\n")
        
    #belongs in helper class
    def _res_ui(self, kb: Keyboard) -> dict[str, str]:
        btn_hl = self.files.read_asset(ClankerAssets.layouts.BTN_HL)
        btn_active = self.files.read_asset(ClankerAssets.layouts.BTN_ACTIVE)
        btn_inactive = self.files.read_asset(ClankerAssets.layouts.BTN_INACTIVE)

        repl_map = {}
        for btn in kb.get_btns(DomButton):
            template = btn_inactive
            label = btn.inhabitant.name if btn.inhabitant else ""
            if btn == kb.selected_dom_btn: template = btn_hl
            elif btn.inhabitant: template = btn_active
            repl_map |= self.shaper.shape_button_replacements(btn, label, template)
        for btn in kb.get_btns(PromptButton):
            label = btn.inhabitant.name if btn.inhabitant else ""
            template = btn_active if btn.inhabitant else btn_inactive   
            repl_map |= self.shaper.shape_button_replacements(btn, label, template)
            
        return repl_map