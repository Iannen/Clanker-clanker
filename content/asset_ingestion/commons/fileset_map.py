class FilesetMap:
    def __init__(self, data: dict[str, FileSet], collector: ErrorCollector) -> None:
        self._data = data
        self._collector = collector

    def get(self, key: str) -> FileSet | None:
        if key not in self._data:
            self._collector.add_complaint(f"Referenced fileset '{key}' does not exist")
            return None
        return self._data[key]

    def merge(self, other: FilesetMapABC) -> FilesetMapABC:
        merged_data = dict(self._data)
        if isinstance(other, FilesetMap):
            merged_data.update(other._data)
        return FilesetMap(data=merged_data, collector=self._collector)