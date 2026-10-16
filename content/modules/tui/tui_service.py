from stdlib import dataclass
from core import Keyboard, DomButton, PromptButton, CorruptClanker, ClankerAssets
from core.engine_deps import FrontendService, IOControl, TerminalPort, DiskPort, StartResult, ExitCommand, UserDeclinedStart, UserDeclinedClankerize, StartupFailed, UserAborted, KbCmd, NoSuchFile, ClankerizeResult, TerminateResult, KbCmdResult, BootCmd, IngestionResult, StartCmd, ClankerizeCmd, ExitResult, Command
from ..tui import TUIQuestions, TUIContentShaper
@dataclass
class TUIServiceImpl(FrontendService):
    io_bridge: TerminalPort
    files: DiskPort

    def __post_init__(self) -> None:
        self.shaper: TUIContentShaper = TUIContentShaper()
        self._cmd = BootCmd()

    def get_request(self) -> Command:
        cmd = self._cmd if self._cmd else self._get_cmd()
        self._cmd = None
        return cmd

    def _get_cmd(self):
        ch = self.io_bridge.read_char()
        if ch in IOControl.ABORT_KEYS:
            return UserAborted()
        return KbCmd(char=ch.lower())

    def post_response(self, command_result: KbCmdResult) -> None:
        match command_result:
            case ExitResult(): pass
            case IngestionResult(): 
                self._cmd  = self._run_bootstrap_result(command_result)
            case KbCmdResult: self._handle_cmd_result(command_result)

    def _run_bootstrap_result(self, bootstrap_res) -> ExitCommand | ClankerizeResult | StartResult:
        
        if isinstance(bootstrap_res, StartResult):
            if not bootstrap_res.report.get_all_complaints(): return StartCmd(bootstrap_res)
            question = TUIQuestions.start_confirmation(bootstrap_res.report)
            if self.io_bridge.get_acceptance(question):
                return StartCmd(bootstrap_res)
            return UserDeclinedStart()

        if isinstance(bootstrap_res, ClankerizeResult):
            question = TUIQuestions.clankerize_confirmation(bootstrap_res.report)
            if self.io_bridge.get_acceptance(question):
                return ClankerizeCmd()
            return UserDeclinedClankerize()

        if isinstance(bootstrap_res, TerminateResult):
            question = TUIQuestions.termination_acknowledgment(bootstrap_res.report)
            self.io_bridge.get_acceptance(question)
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