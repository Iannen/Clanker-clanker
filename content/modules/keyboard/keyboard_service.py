from stdlib import dataclass
from core import (
    DomButton,
    PromptButton,
)
from core.engine_deps import (
    KBService,
    PromptService,
    KbCmd,
    KbCmdResult,
    DomainSelectedResult,
    UnboundKeyResult,
    PromptRenderResult,
    UninhabitedPromptResult,
    UninhabitedDomainResult,
    BootstrapSuccess,
    StandardRenderContext,
    HotRenderContext,
    IngestionService,
    ExitCommand,
    ExitResult,
    BootCmd,
    StartCmd,
    ClankerizeCmd,
    Command,
    Result,
    StartResult
)

@dataclass(slots=True)
class KBServiceImpl(KBService):
    prompt_service: PromptService
    ingestion: IngestionService

    def handle_cmd(self, cmd: Command) -> Result:
        match cmd:
            case BootCmd(): 
                res = self.ingestion.get_runtime_config()
                if isinstance(res, StartResult):
                    self._cache_goods(res)
                return res
            case ClankerizeCmd(): 
                res = self.ingestion.initialize_workspace()
                if isinstance(res, StartResult):
                    self._cache_goods(res)
                return res
            case ExitCommand(): 
                return ExitResult(cmd)
            case StartCmd(): 
                self.last_prompt = None
                return BootstrapSuccess(kb=self.kb, ui_render=self.ui_render, cmd=None)            
            case KbCmd(): 
                btn = self.kb.get(cmd.char)
                if btn is None:
                    return UnboundKeyResult(kb=self.kb, ui_render=self.ui_render, cmd=cmd)
                match(btn):
                    case(DomButton()): return self._handle_dom_btn(btn, cmd)
                    case(PromptButton()): return self._handle_prompt_btn(btn, cmd)

    def _cache_goods(self, res: StartResult) -> None:
        self.kb = res.kb
        self.ui_render = res.ui_render
        self.last_prompt = None

    def _handle_dom_btn(self, btn: DomButton, cmd: KbCmd) -> KbCmdResult:
        self.kb.set_selected_dom_btn(btn)
        self.last_prompt = None    
        prompt_btns = self.kb.get_btns(PromptButton)
        for p_ptn in prompt_btns: p_ptn.inhabitant = None
        if not btn.inhabitant:
            return UninhabitedDomainResult(kb=self.kb, ui_render=self.ui_render, btn=btn, cmd=cmd)
        for prompt_btn, prompt in zip(prompt_btns, btn.inhabitant.prompts):
            prompt_btn.inhabitant = prompt
        return DomainSelectedResult(kb=self.kb, ui_render=self.ui_render, btn=btn, cmd=cmd)

    def _handle_prompt_btn(self, btn: PromptButton, cmd: KbCmd) -> KbCmdResult:
        if self.last_prompt is not None and btn.inhabitant == self.last_prompt:
            ctx = HotRenderContext(kb=self.kb, prompt=self.last_prompt)
            self.last_prompt = None
            lines, chars = self.prompt_service.render_prompt(ctx)
            return PromptRenderResult(kb=self.kb, ui_render=self.ui_render, btn=btn, lines=lines, chars=chars, cmd=cmd)
            
        self.last_prompt = btn.inhabitant
        if btn.inhabitant is None:
            return UninhabitedPromptResult(kb=self.kb, ui_render=self.ui_render, btn=btn, cmd=cmd)
            
        ctx = StandardRenderContext(kb=self.kb, prompt=btn.inhabitant)
        lines, chars = self.prompt_service.render_prompt(ctx)
        return PromptRenderResult(kb=self.kb, ui_render=self.ui_render, btn=btn, lines=lines, chars=chars, cmd=cmd)