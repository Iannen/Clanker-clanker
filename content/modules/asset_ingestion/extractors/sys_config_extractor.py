from stdlib import dataclass, zip_longest
from core import KBStateResolver, Render, Keyboard, SharedDomButton, PudDomButton, PromptButton
from ...asset_ingestion import ErrorCollector, ValueExtractor, Config

@dataclass
class SysConfigExtractor:
    collector: ErrorCollector
    extractor = ValueExtractor()
    def get_ui_render(
        self,
        sys_cfg: Config,
    ) -> tuple[Render]: 
        with self.collector.path("ui_render"):
            ui_render_dict = self.extractor.req_dict(sys_cfg.data, ["ui_render"])

            template = self.extractor.req_str(ui_render_dict, ["template"])
            inherit_base = self.extractor.req_bool(ui_render_dict, ["inherit_base"])
            inherit_domain = self.extractor.req_bool(ui_render_dict, ["inherit_domain"])
            raw_resolvers = self.extractor.req_list(ui_render_dict, ["resolvers"])

            resolvers: list[KBStateResolver] = []
            for r_dict in raw_resolvers:
                res_type = self.extractor.req_str(r_dict, ["type"])
                anchor = self.extractor.req_str(r_dict, ["id"])

                if res_type in ("kb_info", "kb_state"):
                    resolvers.append(KBStateResolver(anchor=anchor))
                else:
                    collector.add_complaint(
                        f"Invalid resolver type '{res_type}' in ui_render; only 'kb_info' or 'kb_state' allowed."
                    )

            if len(resolvers) != 1:
                collector.add_complaint(
                    f"ui_render must carry exactly one KBStateResolver ('kb_info'), found {len(resolvers)}"
                )

            return Render(
                template=template,
                resolvers=resolvers,
                inherit_base=inherit_base,
                inherit_domain=inherit_domain,
            )


    def get_btn_map(self, sys_cfg, shared_doms: list[Domain], pud_doms: list[Domain]) -> Keyboard:
        shared_dom_keys = self.extractor.req_str(sys_cfg.data, ["button_rows", "shared_domains_row"])
        pud_dom_keys = self.extractor.req_str(sys_cfg.data, ["button_rows", "pud_domains_row"])

        pruned_shr_doms = self._handle_domain_overflow(shared_doms, shared_dom_keys)
        pruned_pud_doms = self._handle_domain_overflow(pud_doms, pud_dom_keys)

        return Keyboard(
            shared_dom_btns={key: SharedDomButton(key, dom) for key, dom in zip_longest(shared_dom_keys, pruned_shr_doms, fillvalue=None)},
            pud_dom_btns={key: PudDomButton(key, dom) for key, dom in zip_longest(pud_dom_keys, pruned_pud_doms, fillvalue=None)},
            prompt_btns={key: PromptButton(key) for key in self.extractor.req_str(sys_cfg.data, ["button_rows", "prompts_row"])},
        )
    #need to iterate over all domains, see if they overflow prompt row and complain & discard.

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