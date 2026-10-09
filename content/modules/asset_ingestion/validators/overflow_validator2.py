from stdlib import dataclass
from ...asset_ingestion import ErrorCollector, Numap, DomainOverflow
from core import Keyboard, Resolver, SharedDomButton, PudDomButton, Domain, NewBtn, SharedBaseResolver, PudBaseResolver, SharedDomain, PudDomain, UIRender
@dataclass 
class OverflowHandler2:
    ec: ErrorCollector

    # check correct br, crit if no clank br
    # discard overflowing domains
    # discard overflowing prompts
    # return finished kb
    def do_it(self, numap: Numap) -> tuple[UIRender | None, Keyboard | None]:
        if not numap.get_entity(Keyboard, Keyboard.key_name): return None, None # we can still check prompts overflow if not kb

        baseres = self._get_proper_baseres(numap)
        clank_doms = numap.get_entities(SharedDomain)
        kb = numap.get_entity(Keyboard, Keyboard.key_name)
        shared_dom_btns = kb.get_btns(SharedDomButton)
        pud_dom_btns = kb.get_btns(PudDomButton)
        pud_doms = numap.get_entities(PudDomain)

        if clank_doms: self._handle_domain_overflow(clank_doms, shared_dom_btns, baseres)
        if pud_doms: self._handle_domain_overflow(pud_doms, pud_dom_btns, baseres)

        ui_render = numap.get_entity(UIRender, UIRender.key_name)
        return ui_render, kb

    def _get_proper_baseres(self, numap: Numap) -> Resolver:
        #if no clank br complain
        # if no br at all complain critically
        clank_br = numap.get_entity(SharedBaseResolver, SharedBaseResolver.key_name)
        pud_br = numap.get_entity(PudBaseResolver, PudBaseResolver.key_name)
        return pud_br if pud_br else clank_br

    def _handle_domain_overflow(self, domains: list[Domain], buttons: list[NewBtn], baseres) -> list[Domain]:
        row_keys = [btn.key for btn in buttons]
        slot_limit = len(buttons)
        valid_doms = domains[:slot_limit]
        overflow_doms = domains[slot_limit:]

        if overflow_doms: self.ec.accept(DomainOverflow(buttons,overflow_doms))
        for dom, btn in zip(domains, buttons):
            dom.resolvers.append(baseres)
            btn.inhabitant = dom