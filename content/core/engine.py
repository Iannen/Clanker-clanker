from stdlib import dataclass
from core.engine_deps import KBService, FrontendService, ExitResult

@dataclass(slots=True)
class AppEngine:
    frontend: FrontendService
    kb_service: KBService

    def run(self) -> str:        
        command_result = None
        while not isinstance(command_result, ExitResult):
            command = self.frontend.get_request()
            command_result = self.kb_service.handle_cmd(command)
            self.frontend.post_response(command_result)
        return command_result.exit_msg