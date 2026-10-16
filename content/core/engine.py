from stdlib import dataclass
from core.engine_deps import IngestionService, KBService, FrontendService, StartResult, ClankerizeResult, ExitCommand

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

        command_result = self.kb_service.setup(tui_res)
        self.frontend.post_response(command_result)

        while True:
            command = self.frontend.get_request()
            if isinstance(command, ExitCommand): return command.exit_msg
            command_result = self.kb_service.handle_cmd(command)
            self.frontend.post_response(command_result)