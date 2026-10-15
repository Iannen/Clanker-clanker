from stdlib import dataclass
from core import Render, Keyboard, DomButton, PromptButton, CorruptClanker, ClankerAssets
from core.engine_deps import FrontendService, IOControl, TerminalPort, DiskPort, StartResult, ExitCommand, UserDeclinedStart, UserDeclinedClankerize, StartupFailed, UserAborted, Command, NoSuchFile, ClankerizeResult, TerminateResult, CommandResult
from ..tui import TUIQuestions, TUIContentShaper
@dataclass
class TUIServiceImpl(FrontendService):
    io_bridge: TerminalPort
    files: DiskPort

    def __post_init__(self) -> None:
        self.shaper: TUIContentShaper = TUIContentShaper()

    def set_ui_render(self, ui_render: Render) -> None:
        pass

    def exchange(self, command_result: CommandResult) -> Command | ExitCommand:
        template = self._get_template(command_result.ctx.ui_render)
        repl_map = self._res_ui(command_result.ctx.kb)
        repl_map["msg"] = self.shaper.shape_command_result(command_result)
        ui_string = self.shaper.hydrate(template, repl_map)
        self.io_bridge.write(f"{ui_string}\n")

        ch = self.io_bridge.read_char()
        if ch in IOControl.ABORT_KEYS:
            return UserAborted()
        return Command(char=ch.lower())

    def _get_template(self, render: Render) -> str:
        try:
            return self.files.read_asset(ClankerAssets.layouts.UI)
        except NoSuchFile as ex:
            raise CorruptClanker(f"Error loading template for '{render.template}': {ex}") from ex

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

    def run_bootstrap_result(self, bootstrap_res) -> ExitCommand | ClankerizeResult | StartResult:
        
        if isinstance(bootstrap_res, StartResult):
            if not bootstrap_res.report.get_all_complaints(): return bootstrap_res
            question = TUIQuestions.start_confirmation(bootstrap_res.report)
            if self.io_bridge.get_acceptance(question):
                return bootstrap_res
            return UserDeclinedStart()

        if isinstance(bootstrap_res, ClankerizeResult):
            question = TUIQuestions.clankerize_confirmation(bootstrap_res.report)
            if self.io_bridge.get_acceptance(question):
                return bootstrap_res
            return UserDeclinedClankerize()

        if isinstance(bootstrap_res, TerminateResult):
            question = TUIQuestions.termination_acknowledgment(bootstrap_res.report)
            self.io_bridge.get_acceptance(question)
            return StartupFailed()

    def get_cmd(self) -> Command | ExitCommand:
        ch = self.io_bridge.read_char()
        if ch in IOControl.ABORT_KEYS:
            return UserAborted()
        return Command(char=ch.lower())