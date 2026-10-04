from stdlib import dataclass
from ...asset_ingestion import NamedMap, ErrorCollector
from core import Keyboard, Resolver, SharedDomButton, PudDomButton, Domain, NewBtn
@dataclass 
class OverflowHandler:
    ec: ErrorCollector

    # check correct br, crit if no clank br
    # discard overflowing domains
    # discard overflowing prompts
    # return finished kb
    def do_it(self, br_cl: Resolver, br_pud: Resolver, clank_doms: NamedMap, pud_doms: NamedMap, kb: Keyboard) -> Keyboard | None:
        if not kb: return None # we can still check prompts overflow if not kb

        baseres = self._get_proper_baseres(br_cl, br_pud)
        if clank_doms: self._handle_domain_overflow(clank_doms, kb.get_btns(SharedDomButton), baseres)
        if pud_doms: self._handle_domain_overflow(pud_doms, kb.get_btns(PudDomButton), baseres)

        return kb

    def _get_proper_baseres(self, br_cl: Resolver, br_pud: Resolver) -> Resolver:
        return br_pud if br_pud else br_cl

    def _handle_domain_overflow(self, domains: list[Domain], buttons: list[NewBtn], baseres) -> list[Domain]:
        row_keys = [btn.key for btn in buttons]
        dom_list = list(domains.values())
        slot_limit = len(buttons)
        valid_doms = dom_list[:slot_limit]
        overflow_doms = dom_list[slot_limit:]

        if overflow_doms:
            complaint = f"Domain overflow in row '{row_keys}': received {len(dom_list)} domains, but only {slot_limit} slots are available."
            for dom in overflow_doms:
                complaint += f"\n\tDomain '{dom.name}' was discarded."

            self.collector.add_complaint(complaint)
        for dom, btn in zip(dom_list, buttons):
            # put baseres in dom here
            dom.resolvers.append(baseres)
            btn.inhabitant = dom