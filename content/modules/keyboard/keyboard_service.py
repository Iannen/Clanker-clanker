from stdlib import dataclass
from core import (
    Keyboard,
    DomButton,
    PromptButton,
    Prompt,
    Render
)
from core.engine_deps import (
    KBService,
    PromptService,
    UIRenderContext,
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
)

@dataclass(slots=True)
class KBServiceImpl(KBService):
    prompt_service: PromptService

    def setup(self, start_res) -> KbCmdResult:
        self.kb: Keyboard = start_res.kb
        self.ui_render: Render = start_res.ui_render
        self.last_prompt: Prompt | None = None
        return BootstrapSuccess(ctx=self.get_ui_context(), cmd=getattr(start_res, "cmd", None))

    def get_ui_context(self) -> UIRenderContext:
        return UIRenderContext(
            kb=self.kb,
            ui_render=self.ui_render
        )

    def handle_cmd(self, cmd: KbCmd) -> KbCmdResult:
        btn = self.kb.get(cmd.char)
        if btn is None:
            return UnboundKeyResult(ctx=self.get_ui_context(), cmd=cmd)
        match(btn):
            case(DomButton()): return self._handle_dom_btn(btn, cmd)
            case(PromptButton()): return self._handle_prompt_btn(btn, cmd)

    def _handle_dom_btn(self, btn: DomButton, cmd: KbCmd) -> KbCmdResult:
        self.kb.set_selected_dom_btn(btn)
        self.last_prompt = None    
        prompt_btns = self.kb.get_btns(PromptButton)
        for p_ptn in prompt_btns: p_ptn.inhabitant = None
        if not btn.inhabitant:
            return UninhabitedDomainResult(ctx=self.get_ui_context(), btn=btn, cmd=cmd)
        for prompt_btn, prompt in zip(prompt_btns, btn.inhabitant.prompts):
            prompt_btn.inhabitant = prompt
        return DomainSelectedResult(ctx=self.get_ui_context(), btn=btn, cmd=cmd)

    def _handle_prompt_btn(self, btn: PromptButton, cmd: KbCmd) -> KbCmdResult:
        if self.last_prompt is not None and btn.inhabitant == self.last_prompt:
            ctx = HotRenderContext(kb=self.kb, prompt=self.last_prompt)
            self.last_prompt = None
            lines, chars = self.prompt_service.render_prompt(ctx)
            return PromptRenderResult(ctx=self.get_ui_context(), btn=btn, lines=lines, chars=chars, cmd=cmd)
            
        self.last_prompt = btn.inhabitant
        if btn.inhabitant is None:
            return UninhabitedPromptResult(ctx=self.get_ui_context(), btn=btn, cmd=cmd)
            
        ctx = StandardRenderContext(kb=self.kb, prompt=btn.inhabitant)
        lines, chars = self.prompt_service.render_prompt(ctx)
        return PromptRenderResult(ctx=self.get_ui_context(), btn=btn, lines=lines, chars=chars, cmd=cmd)