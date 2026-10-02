from stdlib import TypeVar, Generic, dataclass, field
from core import FileSet, Filelist
from ...asset_ingestion import ErrorCollector

T = TypeVar("T")

@dataclass
class NamedMap(Generic[T]):
    collector: ErrorCollector
    entity_cls: type[T]
    data: dict[str, T] = field(default_factory=dict)

    def get(self, key: str) -> T | None:
        if key not in self.data:
            label = self.entity_cls.__name__.lower()
            self.collector.add_complaint(
                f"Referenced {label} '{key}' does not exist"
            )
            return None
        return self.data[key]

    def set(self, key: str, value: T) -> None:
        self.data[key] = value