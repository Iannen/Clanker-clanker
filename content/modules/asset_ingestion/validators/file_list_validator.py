from stdlib import dataclass
from core import File
from core.engine_deps import UnsatisfiedFiles
from ...asset_ingestion import ErrorCollector, Numap, AssetPack

@dataclass
class FilelistValidator2:
    ec: ErrorCollector
    clank_doc_assets: AssetPack
    pud_doc_assets: AssetPack
    numap: Numap

    def validate(self):
        if not (self.clank_doc_assets and self.pud_doc_assets): return

        for collision in self.clank_doc_assets.collisions + self.pud_doc_assets.collisions:
            self.ec.accept(collision)

        combined_map = self.pud_doc_assets.resolved_map | self.clank_doc_assets.resolved_map
        files = self.numap.get_entities(File)

        unsatisfied_files: list[File] = []

        for file_item in files:
            target_path = combined_map.get(file_item.name)
            if target_path:
                file_item.path = target_path
            else:
                unsatisfied_files.append(file_item)

        if unsatisfied_files:
            self.ec.accept(UnsatisfiedFiles(unsatisfied_files))
            self.numap.prune(unsatisfied_files)