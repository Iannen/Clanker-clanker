from backend.stdlib import dataclass
from backend.core import entities as e
from backend.core import engine_deps as d

@dataclass(slots=True)
class KBServiceImpl(d.KBService):
    def handle_start(self, cmd: d.StartCmd) -> d.BootstrapSuccess:
        self.kb = cmd.kb
        self.ui_render = cmd.ui_render
        self.last_prompt = None
        return d.BootstrapSuccess(kb=self.kb, ui_render=self.ui_render, cmd=cmd)

    def handle_key(self, cmd: d.KbCmd) -> d.KbServiceEmission:
        btn = self.kb.get(cmd.char)
        if btn is None:
            return d.UnboundKeyResult(kb=self.kb, ui_render=self.ui_render, cmd=cmd)
        match btn:
            case e.DomButton():
                return self._handle_dom_btn(btn, cmd)
            case e.PromptButton():
                return self._handle_prompt_btn(btn, cmd)

    def _handle_dom_btn(self, btn: e.DomButton, cmd: d.KbCmd) -> d.KbServiceEmission:
        self.kb.set_selected_dom_btn(btn)
        self.last_prompt = None
        prompt_btns = self.kb.get_btns(e.PromptButton)
        for p_ptn in prompt_btns:
            p_ptn.inhabitant = None
        if not btn.inhabitant:
            return d.UninhabitedDomainResult(kb=self.kb, ui_render=self.ui_render, btn=btn, cmd=cmd)
        for prompt_btn, prompt in zip(prompt_btns, btn.inhabitant.prompts):
            prompt_btn.inhabitant = prompt
        return d.DomainSelectedResult(kb=self.kb, ui_render=self.ui_render, btn=btn, cmd=cmd)

    def _handle_prompt_btn(self, btn: e.PromptButton, cmd: d.KbCmd) -> d.KbServiceEmission:
        if btn.inhabitant is None:
            return d.UninhabitedPromptResult(kb=self.kb, ui_render=self.ui_render, btn=btn, cmd=cmd)

        dom = self.kb.selected_dom_btn.inhabitant if self.kb.selected_dom_btn else None
        if dom is None:
            return d.UninhabitedPromptResult(kb=self.kb, ui_render=self.ui_render, btn=btn, cmd=cmd)

        if self.last_prompt is not None and btn.inhabitant == self.last_prompt:
            prompt = self.last_prompt
            self.last_prompt = None
            return d.RenderHotPromptCmd(kb=self.kb, ui_render=self.ui_render, cmd=cmd, prompt=prompt, domain=dom)

        self.last_prompt = btn.inhabitant
        return d.RenderNormalPromptCmd(kb=self.kb, ui_render=self.ui_render, cmd=cmd, prompt=btn.inhabitant, domain=dom)