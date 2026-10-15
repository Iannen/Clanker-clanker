from stdlib import dataclass
from core import ActionResult
from core.engine_deps import IngestionService, KBService, PromptService, FrontendService, StartResult, ClankerizeResult, ExitResult, PromptRenderResult

@dataclass(slots=True)
class AppEngine:
    frontend: FrontendService
    session: IngestionService
    prompt_service: PromptService
    kb_service: KBService

    def run(self) -> str:        
        bootstrap_res = self.session.get_runtime_config()

        while True:
            tui_res = self.frontend.run_bootstrap_result(bootstrap_res)

            if isinstance(tui_res, ExitResult): return tui_res.exit_msg
            elif isinstance(tui_res, ClankerizeResult): bootstrap_res = self.session.initialize_workspace()
            elif isinstance(tui_res, StartResult): break
            else: raise Exception(f"Unexpected bootstrap result type: {type(tui_res)}")

        self.kb_service.setup(tui_res)
        action_res = ActionResult(ActionResult.BOOTSTRAP_SUCCESS)

        while True:
            ui_data = self.kb_service.get_ui_context()
            command = self.frontend.exchange(ui_data, action_res)
            if isinstance(command, ExitResult): return command.exit_msg
            data_res = self.kb_service.handle_cmd(command)
            if isinstance(data_res, PromptRenderResult): action_res = self.prompt_service.render_prompt(data_res.ctx)
            else: action_res = data_res