from stdlib import Any
from app import FileSet
from asset_ingestion import ErrorCollector, FilesetMap, ValueExtractor


class FilesetParser:
    def __init__(
        self,
        fileset_cfg: Any,
        collector: ErrorCollector,
        fileset_map: FilesetMap | None = None,
    ) -> None:
        self.fileset_cfg = fileset_cfg
        self.collector = collector
        self.fileset_map = fileset_map
        self.extractor = ValueExtractor()

    def parse(self) -> FileSet:
        if isinstance(self.fileset_cfg, str):
            if self.fileset_map is not None:
                fileset_obj = self.fileset_map.get(self.fileset_cfg)
                if fileset_obj is not None:
                    return fileset_obj
            return FileSet(includes=[], excludes=[])

        if isinstance(self.fileset_cfg, dict):
            includes = self.extractor.req_list(self.fileset_cfg, ["includes"])
            excludes = self.extractor.req_list(self.fileset_cfg, ["excludes"], default=[])
            return FileSet(includes=includes, excludes=excludes)

        return FileSet(includes=[], excludes=[])