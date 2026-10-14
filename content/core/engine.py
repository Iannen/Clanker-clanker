from stdlib import dataclass
from core import ActionResult
from core.engine_deps import IngestionService, KBService, RenderService, TUIService, StartResult, ClankerizeResult, TerminateResult, ExitResult, ClankerizeConfirmed, PromptRenderResult

@dataclass(slots=True)
class AppEngine:
    io: TUIService
    session: IngestionService
    renderer: RenderService
    kb_service: KBService

    def run(self) -> str:        
        bootstrap_res = self.session.get_runtime_config()

        if bootstrap_res.type is StartResult:
            tui_res = self.io.confirm_start(bootstrap_res.report)
        elif bootstrap_res.type is ClankerizeResult:
            tui_res = self.io.confirm_clankerize(bootstrap_res.report)
            if tui_res.type is ClankerizeConfirmed: 
                bootstrap_res = self.session.initialize_workspace()
        elif bootstrap_res.type is TerminateResult:
            tui_res = self.io.inform_termination(bootstrap_res.report)

        if tui_res.type is ExitResult: return tui_res.exit_msg

        self.io.set_ui_render(bootstrap_res.ui_render)
        self.kb_service.setup(bootstrap_res.kb)
        action_res = ActionResult(ActionResult.BOOTSTRAP_SUCCESS)            


        while True:
            ui_render_ctx = self.kb_service.get_ui_context()
            self.io.display(ui_render_ctx, action_res)
            cmd_result = self.io.get_cmd()
            if cmd_result.type is ExitResult: return cmd_result.exit_msg
            data_res = self.kb_service.handle_cmd(cmd_result)
            if data_res.type is PromptRenderResult:
                rendered_text = self.renderer.render_prompt(data_res.ctx)
                action_res = self.io.to_clipboard(rendered_text)
            else: action_res = data_res