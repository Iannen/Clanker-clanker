from stdlib import dataclass, field, Generic, TypeVar, ItemsView
from ...asset_ingestion import ErrorCollector, ValueExtractor, WrongType
from core import Config

T = TypeVar("T")

@dataclass
class NamedMap(Generic[T]):
    collector: ErrorCollector
    entity_cls: type[T]
    data: dict[str, T] = field(default_factory=dict)

    def get(self, key: str) -> T | None:
        if key not in self.data:
            self.collector.add_complaint(f"Referenced {self.entity_cls.key_name} '{key}' does not exist")
            return None
        return self.data[key]

    def set(self, key: str, value: T) -> None:
        self.data[key] = value

    def items(self) -> ItemsView[str, T]:
        return self.data.items()

    def values(self):
        return self.data.values()

    def keys(self):
        return self.data.keys()

    def clone(self) -> NamedMap[T]:
        return NamedMap(self.collector, self.entity_cls, dict(self.data))

T = TypeVar("T")
@dataclass
class NamedMapExtractor(ValueExtractor):
    ec: ErrorCollector
    clank_cfg: Config
    pud_cfg: Config

    def get_maps[T](
        self, 
        parse_cls: type[T], 
        clank_args: tuple | None = None, 
        pud_args: tuple | None = None
    ) -> tuple[NamedMap[T] | None, NamedMap[T] | None, NamedMap[T] | None]:
        clank_map = self._extract_map(parse_cls, self.clank_cfg, clank_args)
        pud_map = self._extract_map(parse_cls, self.pud_cfg, pud_args)

        if clank_map is None:
            return None, pud_map, None

        unified_map = clank_map.clone()
        if pud_map:
            for k, v in pud_map.items():
                unified_map.set(k, v)

        return clank_map, pud_map, unified_map

    def _extract_map[T](
        self, 
        parse_cls: type[T], 
        cfg: Config, 
        parser_args: tuple | None = None
    ) -> NamedMap[T] | None:
        if not cfg: return None
        target_map = NamedMap(self.ec, parse_cls.entity_cls)

        try: raw_entries = self.opt_dict(cfg.data, [parse_cls.entity_cls.plural_key], default={})
        except WrongType: self.ec.add_complaint("Wrong type"); raw_entries = {}

        args = parser_args or ()
        for k, v in raw_entries.items():
            target_map.set(k, parse_cls(self.ec).parse(k, v, *args))

        return target_map