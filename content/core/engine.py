from stdlib import dataclass
from core import ActionResult
from core.engine_deps import IngestionService, KBService, RenderService, TUIService, StartResult, ClankerizeResult, ExitResult, PromptRenderResult

@dataclass(slots=True)
class AppEngine:
    io: TUIService
    session: IngestionService
    renderer: RenderService
    kb_service: KBService

    def run(self) -> str:        
        bootstrap_res = self.session.get_runtime_config()
        tui_res = self.io.run_bootstrap_result(bootstrap_res)

        if isinstance(tui_res, ExitResult):
            return tui_res.exit_msg

        if isinstance(tui_res, ClankerizeResult):
            start_res = self.session.initialize_workspace()

        if isinstance(tui_res, StartResult):
            start_res = tui_res

        self.io.set_ui_render(start_res.ui_render)
        self.kb_service.setup(start_res.kb)
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