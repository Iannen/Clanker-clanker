from stdlib import dataclass
from core import ActionResult
from core.engine_deps import IngestionService, KBService, FrontendService, StartResult, ClankerizeResult, ExitCommand, CommandResult

@dataclass(slots=True)
class AppEngine:
    frontend: FrontendService
    session: IngestionService
    kb_service: KBService

    def run(self) -> str:        
        bootstrap_res = self.session.get_runtime_config()

        while True:
            tui_res = self.frontend.run_bootstrap_result(bootstrap_res)

            if isinstance(tui_res, ExitCommand): return tui_res.exit_msg
            elif isinstance(tui_res, ClankerizeResult): bootstrap_res = self.session.initialize_workspace()
            elif isinstance(tui_res, StartResult): break
            else: raise Exception(f"Unexpected bootstrap result type: {type(tui_res)}")

        self.kb_service.setup(tui_res)
        action_res = ActionResult(ActionResult.BOOTSTRAP_SUCCESS)
        command_result = CommandResult(
            ctx=self.kb_service.get_ui_context(),
            msg=action_res
        )

        while True:
            command = self.frontend.exchange(command_result)
            if isinstance(command, ExitCommand): return command.exit_msg
            command_result = self.kb_service.handle_cmd(command)