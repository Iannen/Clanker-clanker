from stdlib import dataclass
from core import (
    DomButton,
    PromptButton,
)
from core.engine_deps import (
    KBService,
    KbCmd,
    KbCmdResult,
    DomainSelectedResult,
    UnboundKeyResult,
    UninhabitedPromptResult,
    UninhabitedDomainResult,
    BootstrapSuccess,
    StandardRenderContext,
    HotRenderContext,
    RenderPromptCmd,
    StartCmd,
    StartResult,
)

@dataclass(slots=True)
class KBServiceImpl(KBService):
    def handle_start(self, cmd: StartCmd) -> BootstrapSuccess:
        self.last_prompt = None
        return BootstrapSuccess(kb=self.kb, ui_render=self.ui_render, cmd=None)

    def handle_key(self, cmd: KbCmd) -> KbCmdResult | RenderPromptCmd:
        btn = self.kb.get(cmd.char)
        if btn is None:
            return UnboundKeyResult(kb=self.kb, ui_render=self.ui_render, cmd=cmd)
        match btn:
            case DomButton():
                return self._handle_dom_btn(btn, cmd)
            case PromptButton():
                return self._handle_prompt_btn(btn, cmd)

    def set_runtime(self, res: StartResult | StartCmd) -> None:
        self.kb = res.kb
        self.ui_render = res.ui_render
        self.last_prompt = None

    def _handle_dom_btn(self, btn: DomButton, cmd: KbCmd) -> KbCmdResult:
        self.kb.set_selected_dom_btn(btn)
        self.last_prompt = None
        prompt_btns = self.kb.get_btns(PromptButton)
        for p_ptn in prompt_btns:
            p_ptn.inhabitant = None
        if not btn.inhabitant:
            return UninhabitedDomainResult(kb=self.kb, ui_render=self.ui_render, btn=btn, cmd=cmd)
        for prompt_btn, prompt in zip(prompt_btns, btn.inhabitant.prompts):
            prompt_btn.inhabitant = prompt
        return DomainSelectedResult(kb=self.kb, ui_render=self.ui_render, btn=btn, cmd=cmd)

    def _handle_prompt_btn(self, btn: PromptButton, cmd: KbCmd) -> RenderPromptCmd:
        if self.last_prompt is not None and btn.inhabitant == self.last_prompt:
            ctx = HotRenderContext(kb=self.kb, prompt=self.last_prompt)
            self.last_prompt = None
            return RenderPromptCmd(ctx=ctx, btn=btn, kb=self.kb, ui_render=self.ui_render, cmd=cmd)

        self.last_prompt = btn.inhabitant
        if btn.inhabitant is None:
            return UninhabitedPromptResult(kb=self.kb, ui_render=self.ui_render, btn=btn, cmd=cmd)

        ctx = StandardRenderContext(kb=self.kb, prompt=btn.inhabitant)
        return RenderPromptCmd(ctx=ctx, btn=btn, kb=self.kb, ui_render=self.ui_render, cmd=cmd)