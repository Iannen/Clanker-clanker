from stdlib import dataclass
from core.engine_deps import (
    KBService,
    FrontendService,
    ExitCommand,
    IngestionService,
    BootCmd,
    ClankerizeCmd,
    StartResult,
    PromptService,
    RenderPromptCmd,
    Command,
    Result,
)

@dataclass(slots=True)
class AppEngine:
    frontend: FrontendService
    kb_service: KBService
    ingestion: IngestionService
    prompt_service: PromptService

    def run(self) -> str:
        item = None
        while True:
            item = self.frontend.get_request() if item is None else item

            match item:
                case BootCmd():
                    res = self.ingestion.get_runtime_config()
                    if isinstance(res, StartResult):
                        self.kb_service.set_runtime(res)
                    item = res
                case ClankerizeCmd():
                    res = self.ingestion.initialize_workspace()
                    if isinstance(res, StartResult):
                        self.kb_service.set_runtime(res)
                    item = res
                case RenderPromptCmd():
                    item = self.prompt_service.render_prompt(item)
                case ExitCommand():
                    break
                case Command():
                    item = self.kb_service.handle_cmd(item)

            if isinstance(item, Result):
                self.frontend.post_response(item)
                item = None

        return item.exit_msg