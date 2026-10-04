from stdlib import dataclass
from core import Fileset
from ...asset_ingestion import ErrorCollector, ValueExtractor

@dataclass
class FilesetParser(ValueExtractor):
    collector: ErrorCollector
    entity_cls = Fileset

    def parse(self, name, data) -> Fileset:
        includes = self.req_list(data, ["includes"])
        excludes = self.opt_list(data, ["excludes"], default=[])
        return Fileset(includes=includes, excludes=excludes)