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
    RenderPromptCmd,
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
                    item = self.ingestion.get_runtime_config()
                case ClankerizeCmd():
                    item = self.ingestion.initialize_workspace()
                case RenderPromptCmd():
                    item = self.prompt_service.render_prompt(item)
                case StartCmd():
                    item = self.kb_service.handle_start(item)
                case KbCmd():
                    item = self.kb_service.handle_key(item)
                case ExitCommand():
                    break
            if isinstance(item, Result):
                self.frontend.post_response(item)
                item = None

        return item.exit_msg