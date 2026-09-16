from app.deps.keyboard import KBService, RenderContext, UIRenderContext
from app.entities import Keyboard, Resolver, Button, Prompt
from app.presentation import ActionResult

class KBServiceImpl(KBService):
    def setup(self, keyboard: Keyboard, base_resolvers: list[Resolver]) -> None:
        self.keyboard = keyboard
        self.base_resolvers = base_resolvers
        self._wire_num_row()
        self._set_selected_num_btn(None)

    def get_ui_context(self) -> UIRenderContext:
        return UIRenderContext(keyboard=self.keyboard)

    def handle_key(self, key: str) -> tuple[ActionResult | None, RenderContext | None]:
        btn = self.keyboard.button_map.get(key)
        if btn is None:
            return None, None
        if callable(btn.action):
            res = btn.action(key)
            if isinstance(res, RenderContext):
                return None, res
            if isinstance(res, ActionResult):
                return res, None
        return ActionResult(f"No action bound to key '{key}'"), None

    def _wire_num_row(self) -> None:
        for btn in self.keyboard.get_unique_buttons(Button.TYPE_DOMAIN):
            btn.action = self._set_selected_num_btn

    def _set_selected_num_btn(self, key: str | None) -> ActionResult:
        if key is None:
            case = "none"
        else:
            ref_btn = self.keyboard.button_map[key]
            if ref_btn.type != Button.TYPE_DOMAIN:
                raise ValueError("Selected button is not a number button")
            case = "empty" if ref_btn.inhabitant is None else "inhabited"

        self.keyboard.selected_key = key
        prompt_btns = self.keyboard.get_unique_buttons(Button.TYPE_PROMPT)

        for b in prompt_btns:
            b.inhabitant = b.action = None

        if case == "inhabited":
            for p_btn, prompt in zip(prompt_btns, ref_btn.inhabitant.prompts):
                p_btn.inhabitant = prompt
                p_btn.action = self._create_render_context

            return ActionResult(f"Domain '{ref_btn.inhabitant.name}' on key '{key}' selected")

        msg = "Selection cleared" if case == "none" else f"Domain 'None' on key '{key}' selected"
        return ActionResult(msg)

    def _create_render_context(self, key: str) -> RenderContext | ActionResult:
        btn = self.keyboard.button_map.get(key)
        if btn is None or btn.inhabitant is None or not isinstance(btn.inhabitant, Prompt):
            return ActionResult(f"No prompt assigned to key '{key}'")
        return RenderContext(
            render=btn.inhabitant.render,
            keyboard=self.keyboard,
            base_resolvers=self.base_resolvers
        )