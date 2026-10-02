from stdlib import Any, dataclass
from core import FileSet
from ...asset_ingestion import ErrorCollector, ValueExtractor

@dataclass
class FilesetParser(ValueExtractor):
    data: dict
    collector: ErrorCollector
    entity_cls = FileSet

    def parse(self) -> FileSet:
        includes = self.req_list(self.data, ["includes"])
        excludes = self.opt_list(self.data, ["excludes"], default=[])
        return FileSet(includes=includes, excludes=excludes)