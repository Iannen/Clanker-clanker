from stdlib import dataclass
from core import Keyboard, SharedDomButton, PudDomButton, PromptButton
from ...asset_ingestion import ValueExtractor, ErrorCollector
@dataclass
class KeyboardParser(ValueExtractor):
    collector: ErrorCollector
    entity_cls: type = Keyboard

    def parse(self, name: str, data: dict) -> Keyboard:

        shared_keys = self.req_str(data, ["shared_domains_row"])
        pud_keys = self.req_str(data, ["pud_domains_row"])
        prompt_keys = self.req_str(data, ["prompts_row"])

        return Keyboard(
            shared_dom_btns={key: SharedDomButton(key) for key in shared_keys},
            pud_dom_btns={key: PudDomButton(key) for key in pud_keys},
            prompt_btns={key: PromptButton(key) for key in prompt_keys},
        )