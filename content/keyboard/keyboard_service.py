from app import (
    ActionResult,
    Button,
    Filelist,
    HotPromptRequested,
    MultiDocResolver,
    Prompt,
    Render,
    Resolver,
)
from app.deps import KBService, RenderContext, UIRenderContext

class KBServiceImpl(KBService):
    def setup(self, btn_map: dict[str, Button], base_resolvers: list[Resolver]) -> None:
        self.button_map = btn_map
        self.selected_key: str | None = None
        self.base_resolvers = base_resolvers
        self.active_prompt_key: str | None = None
        self.active_prompt: Prompt | None = None
        self._wire_num_row()
        self._set_selected_num_btn(None)

    def get_ui_context(self) -> UIRenderContext:
        return UIRenderContext(
            btn_map=self.button_map,
            selected_key=self.selected_key
        )
    def get_hot_prompt_context(self) -> RenderContext:
        template = self.active_prompt.render.template

        domain_resolvers = self.button_map[self.selected_key].inhabitant.resolvers
        prompt_resolvers = self.active_prompt.render.resolvers

        md_resolvers = [
            r for r in (domain_resolvers + prompt_resolvers + self.base_resolvers)
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
        self.active_prompt_key = self.active_prompt = None
        return RenderContext(
            btn_map=self.button_map,
            selected_key=self.selected_key,
            render=ephemeral_render,
            base_resolvers=[]
        )

    def handle_key(self, key: str) -> tuple[ActionResult | None, RenderContext | None]:
        btn = self.button_map.get(key)
        if btn is None:
            return None, None
        if callable(btn.action):
            res = btn.action(key)
            if isinstance(res, RenderContext):
                return None, res
            if isinstance(res, ActionResult):
                return res, None
        return ActionResult(ActionResult.UNBOUND_KEY.format(key=key)), None

    def _get_unique_buttons(self, btn_type: str | None = None) -> list[Button]:
        unique = {btn.key: btn for btn in self.button_map.values()}.values()
        if btn_type is None:
            return list(unique)
        return [btn for btn in unique if btn.type == btn_type]

    def _wire_num_row(self) -> None:
        for btn in self._get_unique_buttons(Button.TYPE_DOMAIN):
            btn.action = self._set_selected_num_btn

    def _set_selected_num_btn(self, key: str | None) -> ActionResult:
        self.active_prompt_key = None
        self.active_prompt = None

        if key is None:
            return ActionResult(ActionResult.BOOTSTRAP_SUCCESS)

        ref_btn = self.button_map[key]
        if ref_btn.type != Button.TYPE_DOMAIN:
            raise ValueError("Selected button is not a number button")

        self.selected_key = key
        prompt_btns = self._get_unique_buttons(Button.TYPE_PROMPT)

        for b in prompt_btns:
            b.inhabitant = b.action = None

        if ref_btn.inhabitant is not None:
            for p_btn, prompt in zip(prompt_btns, ref_btn.inhabitant.prompts):
                p_btn.inhabitant = prompt
                p_btn.action = self._create_render_context

            return ActionResult(ActionResult.DOMAIN_SELECTED.format(domain=ref_btn.inhabitant.name, key=key))

        return ActionResult(ActionResult.KEY_EMPTY.format(key=key))

    def _create_render_context(self, key: str) -> RenderContext | ActionResult:
        btn = self.button_map.get(key)
        if btn is None or btn.inhabitant is None or not isinstance(btn.inhabitant, Prompt):
            return ActionResult(ActionResult.NO_PROMPT_BOUND.format(key=key))

        if key == self.active_prompt_key:
            raise HotPromptRequested()

        self.active_prompt_key = key
        self.active_prompt = btn.inhabitant

        return RenderContext(
            btn_map=self.button_map,
            selected_key=self.selected_key,
            render=btn.inhabitant.render,
            base_resolvers=self.base_resolvers
        )