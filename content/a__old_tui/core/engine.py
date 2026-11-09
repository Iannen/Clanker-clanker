from stdlib import dataclass
from core.engine_deps import (
    KBService,
    FrontendService,
    IngestionService,
    BootCmd,
    ClankerizeCmd,
    StartCmd,
    KbCmd,
    ExitCommand,
    PromptService,
    RenderNormalPromptCmd,
    RenderHotPromptCmd,
    Request,
    Result,
)

@dataclass(slots=True)
class AppEngine:
    frontend: FrontendService
    kb_service: KBService
    ingestion: IngestionService
    prompt_service: PromptService

    def run(self) -> str:
        req: Request = self.frontend.get_request()
        while True:
            match req.item:
                case BootCmd():
                    req.item = self.ingestion.get_runtime_config()
                case ClankerizeCmd():
                    req.item = self.ingestion.initialize_workspace()
                case RenderNormalPromptCmd() | RenderHotPromptCmd():
                    req.item = self.prompt_service.render_prompt(req.item)
                case StartCmd():
                    req.item = self.kb_service.handle_start(req.item)
                case KbCmd():
                    req.item = self.kb_service.handle_key(req.item)
                case ExitCommand():
                    break
            if isinstance(req.item, Result):
                self.frontend.post_response(req)
                req = self.frontend.get_request()

        return req.item.exit_msg