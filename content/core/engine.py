from stdlib import dataclass
from core.engine_deps import (
    KBService,
    FrontendService,
    ExitResult,
    IngestionService,
    BootCmd,
    ClankerizeCmd,
    StartResult,
    PromptService,
    PromptRenderPending,
    PromptRenderResult,
)

@dataclass(slots=True)
class AppEngine:
    frontend: FrontendService
    kb_service: KBService
    ingestion: IngestionService
    prompt_service: PromptService

    def run(self) -> str:
        command_result = None
        while not isinstance(command_result, ExitResult):
            command = self.frontend.get_request()

            if isinstance(command, BootCmd):
                res = self.ingestion.get_runtime_config()
                if isinstance(res, StartResult):
                    self.kb_service.cache_goods(res)
                command_result = res
            elif isinstance(command, ClankerizeCmd):
                res = self.ingestion.initialize_workspace()
                if isinstance(res, StartResult):
                    self.kb_service.cache_goods(res)
                command_result = res
            else:
                command_result = self.kb_service.handle_cmd(command)
                if isinstance(command_result, PromptRenderPending):
                    lines, chars = self.prompt_service.render_prompt(command_result.ctx)
                    command_result = PromptRenderResult(
                        kb=command_result.kb,
                        ui_render=command_result.ui_render,
                        btn=command_result.btn,
                        lines=lines,
                        chars=chars,
                        cmd=command_result.cmd,
                    )

            self.frontend.post_response(command_result)
        return command_result.exit_msg