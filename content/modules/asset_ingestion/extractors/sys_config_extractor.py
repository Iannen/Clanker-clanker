from stdlib import dataclass, zip_longest
from core import KBStateResolver, Render, Keyboard, SharedDomButton, PudDomButton, PromptButton
from ...asset_ingestion import ErrorCollector, ValueExtractor, Config


@dataclass
class SysConfigExtractor(ValueExtractor):
    collector: ErrorCollector
    sys_cfg: Config | None
    shared_doms: list[Domain] | None = None
    pud_doms: list[Domain] | None = None

    def get_final_product(self, clank_doms, pud_doms) -> tuple[Render, Keyboard]:
        self.shared_doms = clank_doms
        self.pud_doms = pud_doms
        ui_render = UIRenderParser(self.req_dict(self.sys_cfg.data, ["ui_render"]), self.collector).parse()
        _, kb = self.deliver()
        return ui_render, kb

    def deliver(self) -> tuple[Render | None, Keyboard | None]:
        kb = self._get_btn_map()

        if kb:
            self._inject_shared_doms_to_kb(kb)
            self._inject_pud_doms_to_kb(kb)
        # do I just return them outright?
        if all(x is not None for x in (self.sys_cfg, self.shared_doms, self.pud_doms)):
            return ui_render, kb
        else:
            return None, None


    def _get_btn_map(self) -> Keyboard | None:
        if not self.sys_cfg:
            return None
        return Keyboard(
            shared_dom_btns={},
            pud_dom_btns={},
            prompt_btns={key: PromptButton(key) for key in self.req_str(self.sys_cfg.data, ["button_rows", "prompts_row"])},
        )

    def _inject_shared_doms_to_kb(self, kb: Keyboard) -> None:
        if not self.sys_cfg or self.shared_doms is None:
            return
        shared_dom_keys = self.req_str(self.sys_cfg.data, ["button_rows", "shared_domains_row"])
        pruned_shr_doms = self._handle_domain_overflow(self.shared_doms, shared_dom_keys)
        kb.shared_dom_btns = {key: SharedDomButton(key, dom) for key, dom in zip_longest(shared_dom_keys, pruned_shr_doms, fillvalue=None)}

    def _inject_pud_doms_to_kb(self, kb: Keyboard) -> None:
        if not self.sys_cfg or self.pud_doms is None:
            return
        pud_dom_keys = self.req_str(self.sys_cfg.data, ["button_rows", "pud_domains_row"])
        pruned_pud_doms = self._handle_domain_overflow(self.pud_doms, pud_dom_keys)
        kb.pud_dom_btns = {key: PudDomButton(key, dom) for key, dom in zip_longest(pud_dom_keys, pruned_pud_doms, fillvalue=None)}

    def _handle_domain_overflow(self, domains: list[Domain], row_keys: str) -> list[Domain]:
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
    def parse(self): 
        template = self.req_str(self.data, ["template"])
        return Render(
            template=template,
            resolvers=[],
            inherit_base=False,
            inherit_domain=False,
        )