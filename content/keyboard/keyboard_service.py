from app.deps.keyboard import KBService, RenderContext, UIRenderContext
from app.entities import Button, Resolver, Prompt
from app.presentation import ActionResult

class KBServiceImpl(KBService):
    def setup(self, btn_map: dict[str, Button], base_resolvers: list[Resolver]) -> None:
        self.button_map = btn_map
        self.selected_key: str | None = None
        self.base_resolvers = base_resolvers
        self._wire_num_row()
        self._set_selected_num_btn(None)

    def get_ui_context(self) -> UIRenderContext:
        return UIRenderContext(
            btn_map=self.button_map,
            selected_key=self.selected_key
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
        return RenderContext(
            btn_map=self.button_map,
            selected_key=self.selected_key,
            render=btn.inhabitant.render,
            base_resolvers=self.base_resolvers
        )