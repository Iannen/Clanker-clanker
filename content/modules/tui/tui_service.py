from stdlib import dataclass
from core import ActionResult, Render, Keyboard, DomButton, PromptButton, CorruptClanker, ClankerAssets
from core.engine_deps import TUIService, IOControl, TerminalPort, DiskPort, ExitResult, StartConfirmed, ClankerizeConfirmed, Command, Report, UIRenderContext, NoSuchFile
from ..tui import TUIQuestions, ContentShaper
@dataclass
class TUIServiceImpl(TUIService):
    io_bridge: TerminalPort
    files: DiskPort

    def __post_init__(self) -> None:
        self.shaper: ContentShaper = ContentShaper()
        self._ui_render: Render | None = None

    def set_ui_render(self, ui_render: Render) -> None:
        self._ui_render = ui_render

    def display(self, ctx: UIRenderContext, msg: ActionResult) -> None:
        if self._ui_render is None:
            raise CorruptClanker("UI render spec has not been configured.")
        template = self._get_template(self._ui_render)
        repl_map = self._res_ui(ctx.kb)
        repl_map["msg"] = self.shaper.shape_action_result(msg.message)
        ui_string = self._hydrate(template, repl_map)
        self.io_bridge.write(f"{ui_string}\n")

    def _hydrate(self, template: str, replacements: dict[str, str]) -> str:
        return self.shaper.hydrate(template, replacements)

    def _get_template(self, render: Render) -> str:
        try:
            match render.template:
                case "ui_template":
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

    def confirm_start(self, report: Report) -> StartConfirmed | ExitResult:
        if not report.get_all_complaints(): return StartConfirmed()
        question = TUIQuestions.start_confirmation(report)
        if self.io_bridge.get_acceptance(question):
            return StartConfirmed()
        return ExitResult("User declined program start")

    def confirm_clankerize(self, report: Report) -> ClankerizeConfirmed | ExitResult:
        question = TUIQuestions.clankerize_confirmation(report)
        if self.io_bridge.get_acceptance(question):
            return ClankerizeConfirmed()
        return ExitResult("User declined to clankerize project")

    def inform_termination(self, report: Report) -> ExitResult:
        question = TUIQuestions.termination_acknowledgment(report)
        self.io_bridge.get_acceptance(question)
        return ExitResult("Program could not start")

    def to_clipboard(self, text_content: str) -> ActionResult: # this goes to Renderservice, which becomes promptservice
        lines_count = self.io_bridge.to_clipboard(text_content)
        char_count = len(text_content)
        return ActionResult(ActionResult.COPIED_TO_CLIPBOARD.format(lines=lines_count, chars=char_count))

    def get_cmd(self) -> Command | ExitResult:
        ch = self.io_bridge.read_char()
        if ch in IOControl.ABORT_KEYS:
            return ExitResult(ActionResult.MSG_DEFAULT)
        return Command(char=ch.lower())