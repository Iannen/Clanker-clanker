from stdlib import dataclass
from core import (
    ActionResult,
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
    Command,
    CommandResult,
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

    def setup(self, start_res) -> CommandResult:
        self.kb: Keyboard = start_res.kb
        self.ui_render: Render = start_res.ui_render
        self.last_prompt: Prompt | None = None
        msg = ActionResult(ActionResult.BOOTSTRAP_SUCCESS)
        return BootstrapSuccess(ctx=self.get_ui_context(), msg=msg, cmd=getattr(start_res, "cmd", None))

    def get_ui_context(self) -> UIRenderContext:
        return UIRenderContext(
            kb=self.kb,
            ui_render=self.ui_render
        )

    def handle_cmd(self, cmd: Command) -> CommandResult:
        btn = self.kb.get(cmd.char)
        if btn is None:
            msg = ActionResult(ActionResult.UNBOUND_KEY.format(key=cmd.char))
            return UnboundKeyResult(ctx=self.get_ui_context(), msg=msg, cmd=cmd)
        match(btn):
            case(DomButton()): return self._handle_dom_btn(btn, cmd)
            case(PromptButton()): return self._handle_prompt_btn(btn, cmd)

    def _handle_dom_btn(self, btn: DomButton, cmd: Command) -> CommandResult:
        self.kb.set_selected_dom_btn(btn)
        self.last_prompt = None    
        prompt_btns = self.kb.get_btns(PromptButton)
        for p_ptn in prompt_btns: p_ptn.inhabitant = None
        if not btn.inhabitant:
            msg = ActionResult(ActionResult.KEY_EMPTY)
            return UninhabitedDomainResult(ctx=self.get_ui_context(), msg=msg, btn=btn, cmd=cmd)
        for prompt_btn, prompt in zip(prompt_btns, btn.inhabitant.prompts):
            prompt_btn.inhabitant = prompt
        msg = ActionResult(ActionResult.DOMAIN_SELECTED.format(domain=btn.inhabitant.name, key=btn.key))
        return DomainSelectedResult(ctx=self.get_ui_context(), msg=msg, btn=btn, cmd=cmd)

    def _handle_prompt_btn(self, btn: PromptButton, cmd: Command) -> CommandResult:
        if self.last_prompt is not None and btn.inhabitant == self.last_prompt:
            ctx = HotRenderContext(kb=self.kb, prompt=self.last_prompt)
            self.last_prompt = None
            lines, chars = self.prompt_service.render_prompt(ctx)
            msg = ActionResult(ActionResult.COPIED_TO_CLIPBOARD.format(lines=lines, chars=chars))
            return PromptRenderResult(ctx=self.get_ui_context(), msg=msg, btn=btn, lines=lines, chars=chars, cmd=cmd)
            
        self.last_prompt = btn.inhabitant
        if btn.inhabitant is None:
            msg = ActionResult(ActionResult.UNBOUND_KEY.format(key=btn.key))
            return UninhabitedPromptResult(ctx=self.get_ui_context(), msg=msg, btn=btn, cmd=cmd)
            
        ctx = StandardRenderContext(kb=self.kb, prompt=btn.inhabitant)
        lines, chars = self.prompt_service.render_prompt(ctx)
        msg = ActionResult(ActionResult.COPIED_TO_CLIPBOARD.format(lines=lines, chars=chars))
        return PromptRenderResult(ctx=self.get_ui_context(), msg=msg, btn=btn, lines=lines, chars=chars, cmd=cmd)