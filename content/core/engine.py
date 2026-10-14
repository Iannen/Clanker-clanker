from stdlib import dataclass
from core import ActionResult
from core.engine_deps import IngestionService, KBService, PromptService, TUIService, StartResult, ClankerizeResult, ExitResult, PromptRenderResult

@dataclass(slots=True)
class AppEngine:
    io: TUIService
    session: IngestionService
    prompt_service: PromptService
    kb_service: KBService

    def run(self) -> str:        
        # should this bootstrap process really be a while loop that either ends with successfull StartResult acquistion, or an ExitResult?
        bootstrap_res = self.session.get_runtime_config()
        tui_res = self.io.run_bootstrap_result(bootstrap_res)

        if isinstance(tui_res, ExitResult):
            return tui_res.exit_msg

        if isinstance(tui_res, ClankerizeResult):
            # the reason I ask is that, if the disk state changes from when user gives clankerize acceptance and this is called, then we may get a covfefe
            start_res = self.session.initialize_workspace()

        if isinstance(tui_res, StartResult):
            start_res = tui_res

        self.kb_service.setup(start_res)
        action_res = ActionResult(ActionResult.BOOTSTRAP_SUCCESS)

        while True:
            ui_data = self.kb_service.get_ui_context()
            self.io.display(ui_data, action_res)
            cmd_result = self.io.get_cmd()
            if cmd_result.type is ExitResult: return cmd_result.exit_msg
            data_res = self.kb_service.handle_cmd(cmd_result)
            if data_res.type is PromptRenderResult:
                action_res = self.prompt_service.render_prompt(data_res.ctx)
            else: action_res = data_res