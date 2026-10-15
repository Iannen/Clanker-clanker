from stdlib import dataclass
from core import (
    ActionResult,
    Filelist,
    MultiDocResolver,
    Prompt,
    Render,
    Keyboard,
    DomButton,
    PromptButton,
)
from core.engine_deps import KBService, PromptService, RenderContext, UIRenderContext, Command, CommandResult, DomainSelectedResult, UnboundKeyResult, PromptRenderResult, UninhabitedPromptResult, UninhabitedDomainResult

@dataclass(slots=True)
class KBServiceImpl(KBService):
    prompt_service: PromptService

    def setup(self, start_res) -> None:
        self.kb: Keyboard = start_res.kb
        self.ui_render: Render = start_res.ui_render
        self.last_prompt: Prompt | None = None

    def get_ui_context(self) -> UIRenderContext:
        return UIRenderContext(
            kb=self.kb,
            ui_render=self.ui_render
        )

    def _get_hot_prompt_context(self) -> RenderContext:
        template = self.last_prompt.render.template
        domain_resolvers = self.kb.selected_dom_btn.inhabitant.resolvers
        prompt_resolvers = self.last_prompt.render.resolvers

        md_resolvers = [
            r for r in (domain_resolvers + prompt_resolvers)
            if isinstance(r, MultiDocResolver)
        ]

        instruction_files = [
            f for r in md_resolvers
            for f in r.files.files
            if f.name.endswith(".mode_instruction") or f.name.endswith(".output_instruction") or f.name.endswith(".history")
        ]

        lone_resolver = MultiDocResolver(
            anchor="prompt_fragments",
            files=Filelist(None, files=instruction_files)
        )

        ephemeral_render = Render(
            template=template,
            resolvers=[lone_resolver],
            inherit_base=False,
            inherit_domain=False
        )
        self.active_prompt_key = self.last_prompt = None
        return RenderContext(
            kb=self.kb,
            render=ephemeral_render,
        )

    def handle_cmd(self, cmd: Command) -> CommandResult:
        btn = self.kb.get(cmd.char)
        if btn is None:
            msg = ActionResult(ActionResult.UNBOUND_KEY.format(key=cmd.char))
            return UnboundKeyResult(ctx=self.get_ui_context(), msg=msg, btn=None)
        match(btn):
            case(DomButton()): return self._handle_dom_btn(btn)
            case(PromptButton()): return self._handle_prompt_btn(btn)

    def _handle_dom_btn(self, btn: DomButton) -> CommandResult:
        self.kb.set_selected_dom_btn(btn)
        self.last_prompt = None    
        prompt_btns = self.kb.get_btns(PromptButton)
        for p_ptn in prompt_btns: p_ptn.inhabitant = None
        if not btn.inhabitant:
            msg = ActionResult(ActionResult.KEY_EMPTY)
            return UninhabitedDomainResult(ctx=self.get_ui_context(), msg=msg, btn=btn)
        for prompt_btn, prompt in zip(prompt_btns, btn.inhabitant.prompts):
            prompt_btn.inhabitant = prompt
        msg = ActionResult(ActionResult.DOMAIN_SELECTED.format(domain=btn.inhabitant.name, key=btn.key))
        return DomainSelectedResult(ctx=self.get_ui_context(), msg=msg, btn=btn)

    def _handle_prompt_btn(self, btn: PromptButton) -> CommandResult:
        if self.last_prompt is not None and btn.inhabitant == self.last_prompt:
            ctx = self._get_hot_prompt_context()
            msg = self.prompt_service.render_prompt(ctx)
            return PromptRenderResult(ctx=self.get_ui_context(), msg=msg, btn=btn)
        self.last_prompt = btn.inhabitant
        if btn.inhabitant is None:
            msg = ActionResult(ActionResult.UNBOUND_KEY.format(key=btn.key))
            return UninhabitedPromptResult(ctx=self.get_ui_context(), msg=msg, btn=btn)
        ctx = RenderContext(self.kb, btn.inhabitant.render)
        msg = self.prompt_service.render_prompt(ctx)
        return PromptRenderResult(ctx=self.get_ui_context(), msg=msg, btn=btn)