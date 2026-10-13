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
from core.engine_deps import KBService, RenderContext, UIRenderContext, Command, Result, ActionFeedbackResult, PromptRenderResult, NullCommandResult, DomainSelectedResult, UninhabitatedDomainResult, UninhabitatedPromptResult

class KBServiceImpl(KBService):
    def setup(self,kb: Keyboard) -> None:
        self.kb: Keyboard = kb
        self.last_prompt: Prompt | None = None

    def get_ui_context(self) -> UIRenderContext:
        return UIRenderContext(
            kb=self.kb
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

    def handle_cmd(self, cmd: Command) -> Result:
        btn = self.kb.get(cmd.char)
        if btn is None:
            return NullCommandResult(ActionResult(ActionResult.UNBOUND_KEY.format(key=cmd.char)))
        match(btn):
            case(DomButton()): return self._handle_dom_btn(btn)
            case(PromptButton()): return self._handle_prompt_btn(btn)

    def _handle_dom_btn(self, btn) -> ActionFeedbackResult:
        self.kb.set_selected_dom_btn(btn)
        self.last_prompt = None    
        prompt_btns = self.kb.get_btns(PromptButton)
        for p_ptn in prompt_btns: p_ptn.inhabitant = None
        if not btn.inhabitant:
            return UninhabitatedDomainResult(ActionResult.KEY_EMPTY)
        for prompt_btn, prompt in zip(prompt_btns, btn.inhabitant.prompts):
            prompt_btn.inhabitant = prompt
        return DomainSelectedResult(ActionResult.DOMAIN_SELECTED.format(domain=btn.inhabitant.name, key=btn.key))

    def _handle_prompt_btn(self, btn) -> PromptRenderResult | ActionFeedbackResult:
        if self.last_prompt is not None and btn.inhabitant == self.last_prompt:
            return PromptRenderResult(self._get_hot_prompt_context())
        self.last_prompt = btn.inhabitant
        if btn.inhabitant is None:
            return UninhabitatedPromptResult(ActionResult.UNBOUND_KEY.format(key=btn.key))
        ctx = RenderContext(self.kb, btn.inhabitant.render)
        return PromptRenderResult(ctx)