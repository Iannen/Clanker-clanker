from stdlib import dataclass, zip_longest, Any
from core import Render, Keyboard, SharedDomButton, PudDomButton, PromptButton, Domain
from ...asset_ingestion import ErrorCollector, ValueExtractor, Config

@dataclass
class SysConfigExtractor(ValueExtractor):
    collector: ErrorCollector
    sys_cfg: Config | None
    clank_doms: list[Domain] | None = None
    pud_doms: list[Domain] | None = None

    def get_final_product(self, clank_doms: list[Domain], pud_doms: list[Domain]) -> tuple[Render, Keyboard | None]:
        self.clank_doms = clank_doms
        self.pud_doms = pud_doms
        ui_render = UIRenderParser(self.req_dict(self.sys_cfg.data, ["ui_render"]), self.collector).parse()

        kb = self._get_btn_map()
        return ui_render, kb

    def _get_btn_map(self) -> Keyboard | None:
        if not self.sys_cfg:
            return None

        return Keyboard(
            shared_dom_btns=self._get_shared_dom_btns(),
            pud_dom_btns=self._get_pud_dom_btns(),
            prompt_btns={key: PromptButton(key) for key in self.req_str(self.sys_cfg.data, ["button_rows", "prompts_row"])},
        )

    def _get_shared_dom_btns(self) -> dict[str, SharedDomButton]:
        if not self.sys_cfg or self.clank_doms is None:
            return {}

        shared_dom_keys = self.req_str(self.sys_cfg.data, ["button_rows", "shared_domains_row"])
        pruned_shr_doms = self._handle_domain_overflow(self.clank_doms, shared_dom_keys)
        return {key: SharedDomButton(key, dom) for key, dom in zip_longest(shared_dom_keys, pruned_shr_doms, fillvalue=None)}

    def _get_pud_dom_btns(self) -> dict[str, PudDomButton]:
        if not self.sys_cfg or self.pud_doms is None:
            return {}

        pud_dom_keys = self.req_str(self.sys_cfg.data, ["button_rows", "pud_domains_row"])
        pruned_pud_doms = self._handle_domain_overflow(self.pud_doms, pud_dom_keys)
        return {key: PudDomButton(key, dom) for key, dom in zip_longest(pud_dom_keys, pruned_pud_doms, fillvalue=None)}

    def _handle_domain_overflow(self, domains: list[Domain], row_keys: str) -> list[Domain]:
        domains = list(domains.values())
        slot_limit = len(row_keys)
        valid_doms = domains[:slot_limit]
        overflow_doms = domains[slot_limit:]

        if overflow_doms:
            complaint = f"Domain overflow in row '{row_keys}': received {len(domains)} domains, but only {slot_limit} slots are available."
            for dom in overflow_doms:
                complaint += f"\n\tDomain '{dom.name}' was discarded."

            self.collector.add_complaint(complaint)

        return valid_doms

@dataclass
class UIRenderParser(ValueExtractor):
    data: dict[str, Any]
    collector: ErrorCollector

    def parse(self) -> Render:
        template = self.req_str(self.data, ["template"])
        return Render(
            template=template,
            resolvers=[],
            inherit_base=False,
            inherit_domain=False,
        )