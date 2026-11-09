from stdlib import dataclass
from ...asset_ingestion import ErrorCollector, Numap
from core.engine_deps import DomainOverflow
from core import entities as e

@dataclass 
class OverflowHandler2:
    ec: ErrorCollector

    def do_it(self, numap: Numap) -> tuple[e.UIRender | None, e.Keyboard | None]:
        if not numap.get_entity(e.Keyboard, e.Keyboard.key_name): return None, None

        baseres = self._get_proper_baseres(numap)
        clank_doms = numap.get_entities(e.SharedDomain)
        kb = numap.get_entity(e.Keyboard, e.Keyboard.key_name)
        shared_dom_btns = kb.get_btns(e.SharedDomButton)
        pud_dom_btns = kb.get_btns(e.PudDomButton)
        pud_doms = numap.get_entities(e.PudDomain)

        if clank_doms: self._handle_domain_overflow(clank_doms, shared_dom_btns, baseres)
        if pud_doms: self._handle_domain_overflow(pud_doms, pud_dom_btns, baseres)
        ui_render = numap.get_entity(e.UIRender, e.UIRender.key_name)
        return ui_render, kb

    def _get_proper_baseres(self, numap: Numap) -> e.Resolver:
        clank_br = numap.get_entity(e.SharedBaseResolver, e.SharedBaseResolver.key_name)
        pud_br = numap.get_entity(e.PudBaseResolver, e.PudBaseResolver.key_name)
        return pud_br if pud_br else clank_br

    def _handle_domain_overflow(self, domains: list[e.Domain], buttons: list[e.NewBtn], baseres) -> list[e.Domain]:
        row_keys = [btn.key for btn in buttons]
        slot_limit = len(buttons)
        valid_doms = domains[:slot_limit]
        overflow_doms = domains[slot_limit:]

        if overflow_doms: self.ec.accept(DomainOverflow(buttons,overflow_doms))
        for dom, btn in zip(domains, buttons):
            dom.resolvers.append(baseres)
            btn.inhabitant = dom