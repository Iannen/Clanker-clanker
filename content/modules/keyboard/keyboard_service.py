from stdlib import dataclass
from core import entities as e
from core.engine_deps import (
    KBService,
    KbCmd,
    KbServiceEmission,
    DomainSelectedResult,
    UnboundKeyResult,
    UninhabitedPromptResult,
    UninhabitedDomainResult,
    BootstrapSuccess,
    RenderNormalPromptCmd,
    RenderHotPromptCmd,
    StartCmd,
)

@dataclass(slots=True)
class KBServiceImpl(KBService):
    def handle_start(self, cmd: StartCmd) -> BootstrapSuccess:
        self.kb = cmd.kb
        self.ui_render = cmd.ui_render
        self.last_prompt = None
        return BootstrapSuccess(kb=self.kb, ui_render=self.ui_render, cmd=cmd)

    def handle_key(self, cmd: KbCmd) -> KbServiceEmission:
        btn = self.kb.get(cmd.char)
        if btn is None:
            return UnboundKeyResult(kb=self.kb, ui_render=self.ui_render, cmd=cmd)
        match btn:
            case e.DomButton():
                return self._handle_dom_btn(btn, cmd)
            case e.PromptButton():
                return self._handle_prompt_btn(btn, cmd)

    def _handle_dom_btn(self, btn: e.DomButton, cmd: KbCmd) -> KbServiceEmission:
        self.kb.set_selected_dom_btn(btn)
        self.last_prompt = None
        prompt_btns = self.kb.get_btns(e.PromptButton)
        for p_ptn in prompt_btns:
            p_ptn.inhabitant = None
        if not btn.inhabitant:
            return UninhabitedDomainResult(kb=self.kb, ui_render=self.ui_render, btn=btn, cmd=cmd)
        for prompt_btn, prompt in zip(prompt_btns, btn.inhabitant.prompts):
            prompt_btn.inhabitant = prompt
        return DomainSelectedResult(kb=self.kb, ui_render=self.ui_render, btn=btn, cmd=cmd)

    def _handle_prompt_btn(self, btn: e.PromptButton, cmd: KbCmd) -> KbServiceEmission:
        if btn.inhabitant is None:
            return UninhabitedPromptResult(kb=self.kb, ui_render=self.ui_render, btn=btn, cmd=cmd)

        dom = self.kb.selected_dom_btn.inhabitant if self.kb.selected_dom_btn else None
        if dom is None:
            return UninhabitedPromptResult(kb=self.kb, ui_render=self.ui_render, btn=btn, cmd=cmd)

        if self.last_prompt is not None and btn.inhabitant == self.last_prompt:
            prompt = self.last_prompt
            self.last_prompt = None
            return RenderHotPromptCmd(kb=self.kb, ui_render=self.ui_render, cmd=cmd, prompt=prompt, domain=dom)

        self.last_prompt = btn.inhabitant
        return RenderNormalPromptCmd(kb=self.kb, ui_render=self.ui_render, cmd=cmd, prompt=btn.inhabitant, domain=dom)