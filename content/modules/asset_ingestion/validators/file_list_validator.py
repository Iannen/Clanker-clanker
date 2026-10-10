from stdlib import dataclass
from core import File, MultiDocResolver
from core.engine_deps.ingestion import UnsatisfiedFiles
from ...asset_ingestion import ErrorCollector, Numap, AssetPack

@dataclass
class FilelistValidator2:
    ec: ErrorCollector
    clank_doc_assets: AssetPack
    pud_doc_assets: AssetPack
    numap: Numap

    def validate(self):
        if not (self.clank_doc_assets and self.pud_doc_assets): return

        for collision in self.clank_doc_assets.collisions + self.pud_doc_assets.collisions: self.ec.accept(collision)

        combined_map = self.pud_doc_assets.resolved_map | self.clank_doc_assets.resolved_map
        md_resolvers = self.numap.get_entities(MultiDocResolver)

        unsatisfied_files: list[File] = []

        for mdr in md_resolvers:
            remaining_files = []
            for file_item in mdr.files.files:
                target_path = combined_map.get(file_item.name)
                if target_path:
                    file_item.path = target_path
                    remaining_files.append(file_item)
                else:
                    unsatisfied_files.append(file_item)
            mdr.files.files = remaining_files

        if unsatisfied_files:
            self.ec.accept(UnsatisfiedFiles(unsatisfied_files))