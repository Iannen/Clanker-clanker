from stdlib import TypeVar, Generic
from core import FileSet, Filelist
from ...asset_ingestion import ErrorCollector

T = TypeVar("T")


class NamedMap(Generic[T]):
    def __init__(
        self,
        data: dict[str, T],
        collector: ErrorCollector,
        entity_label: str = "item",
    ) -> None:
        self._data = data
        self._collector = collector
        self._entity_label = entity_label

    def get(self, key: str) -> T | None:
        if key not in self._data:
            self._collector.add_complaint(
                f"Referenced {self._entity_label} '{key}' does not exist"
            )
            return None
        return self._data[key]

    def merge(self, other: "NamedMap[T]") -> "NamedMap[T]":
        merged_data = dict(self._data)
        if isinstance(other, NamedMap):
            merged_data.update(other._data)
        return NamedMap(
            data=merged_data,
            collector=self._collector,
            entity_label=self._entity_label,
        )


class FilesetMap(NamedMap[FileSet]):
    def __init__(self, data: dict[str, FileSet], collector: ErrorCollector) -> None:
        super().__init__(data=data, collector=collector, entity_label="fileset")


class FilelistMap(NamedMap[Filelist]):
    def __init__(self, data: dict[str, Filelist], collector: ErrorCollector) -> None:
        super().__init__(data=data, collector=collector, entity_label="filelist")