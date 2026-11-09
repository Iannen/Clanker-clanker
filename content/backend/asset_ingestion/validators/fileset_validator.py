from backend.core import entities as e
from backend.stdlib import dataclass
from ...asset_ingestion import ErrorCollector, Numap
from backend.core.engine_deps import UnsatisfiedFilesetSubjects

@dataclass
class FilesetValidator2:
    ec: ErrorCollector
    numap: Numap
    clank_doc_assets: e.AssetPack 
    pud_content_assets: e.AssetPack 

    def validate(self):
        items = self.numap.get_entities(e.FilesetItem)
        from_pud = [item for item in items if isinstance(item.ancestor, e.PudFileset)]
        from_clank = [item for item in items if isinstance(item.ancestor, e.SharedFileset)]

        pud_unsatisfied: list[e.FilesetItem] = []
        shared_unsatisfied: list[e.FilesetItem] = []

        if self.pud_content_assets:
            for item in from_pud:
                if not any(p.startswith(item.value) for p in self.pud_content_assets.paths):
                        pud_unsatisfied.append(item)

        if self.clank_doc_assets:
            for item in from_clank:
                if not any(p.startswith(item.value) for p in self.clank_doc_assets.paths):
                        shared_unsatisfied.append(item)

        if pud_unsatisfied:
            self.ec.accept(UnsatisfiedFilesetSubjects(self.pud_content_assets, pud_unsatisfied))
            self.numap.prune(pud_unsatisfied)

        if shared_unsatisfied:
            self.ec.accept(UnsatisfiedFilesetSubjects(self.clank_doc_assets, shared_unsatisfied))
            self.numap.prune(shared_unsatisfied)