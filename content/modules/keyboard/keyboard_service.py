from core import (
    ActionResult,
    Filelist,
    HotPromptRequested,
    MultiDocResolver,
    Prompt,
    Render,
    Resolver,
    Keyboard,
    DomButton,
    PudDomButton,
    SharedDomButton,
    PromptButton,
)
from core.engine_deps import KBService, RenderContext, UIRenderContext

class KBServiceImpl(KBService):
    def setup(self,kb: Keyboard) -> None:
        self.kb: Keyboard = kb
        self.last_prompt: Prompt | None = None

    def get_ui_context(self) -> UIRenderContext:
        return UIRenderContext(
            kb=self.kb
        )
    def get_hot_prompt_context(self) -> RenderContext:
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
            files=Filelist(files=instruction_files)
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

    def handle_key(self, key: str) -> tuple[ActionResult | None, RenderContext | None]:
        btn = self.kb.get(key)
        if btn is None: res = ActionResult(ActionResult.UNBOUND_KEY.format(key=key)) # here we should say 'not a key in system'
        match(btn):
            case(DomButton()): res, ctx = self._handle_dom_btn(btn)
            case(PromptButton()): res, ctx = self._handle_prompt_btn(btn)
        return res, ctx

    def _handle_dom_btn(self, btn): # dont deal with uninhabitated domprompts, tests let slip
        self.kb.set_selected_dom_btn(btn)
        self.last_prompt = None   
        prompt_btns = self.kb.get_btns(PromptButton)
        for p_ptn in prompt_btns: p_ptn.inhabitant = None
        for prompt_btn, prompt in zip(prompt_btns, btn.inhabitant.prompts):
            prompt_btn.inhabitant = prompt
        res = ActionResult(ActionResult.DOMAIN_SELECTED.format(domain=btn.inhabitant.name, key=btn.key))
        return res, None

    def _handle_prompt_btn(self, btn):
        if self.last_prompt is not None and btn.inhabitant == self.last_prompt: raise HotPromptRequested
        self.last_prompt = btn.inhabitant
        res, ctx = None, None
        if btn.inhabitant is None: res = ActionResult(ActionResult.UNBOUND_KEY.format(key=btn.key))
        else:ctx = RenderContext(self.kb,btn.inhabitant.render,)
        return res, ctx