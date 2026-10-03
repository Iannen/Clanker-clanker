from stdlib import dataclass
from core import FileSet
from ...asset_ingestion import ErrorCollector, ValueExtractor

@dataclass
class FilesetParser(ValueExtractor):
    collector: ErrorCollector
    entity_cls = FileSet

    def parse(self, name, data) -> FileSet:
        includes = self.req_list(data, ["includes"])
        excludes = self.opt_list(data, ["excludes"], default=[])
        return FileSet(includes=includes, excludes=excludes)