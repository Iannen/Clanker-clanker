from backend.stdlib import dataclass
from ...asset_ingestion import ErrorCollector, Numap
from backend.core import entities as e

@dataclass 
class OverflowHandler2:
    ec: ErrorCollector

    def do_it(self, numap: Numap) -> None:
        baseres = self._get_proper_baseres(numap)
        clank_doms = numap.get_entities(e.SharedDomain)
        pud_doms = numap.get_entities(e.PudDomain)

        if clank_doms: self._append_baseres(clank_doms, baseres)
        if pud_doms: self._append_baseres(pud_doms, baseres)

    def _get_proper_baseres(self, numap: Numap) -> e.Resolver:
        clank_br = numap.get_entity(e.SharedBaseResolver, e.SharedBaseResolver.key_name)
        pud_br = numap.get_entity(e.PudBaseResolver, e.PudBaseResolver.key_name)
        return pud_br if pud_br else clank_br

    def _append_baseres(self, domains: list[e.Domain], baseres: e.Resolver) -> None:
        for dom in domains:
            dom.resolvers.append(baseres)