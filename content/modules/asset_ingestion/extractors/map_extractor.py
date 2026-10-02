from stdlib import Generic, TypeVar, dataclass, field
from ...asset_ingestion import Config, ErrorCollector, ValueExtractor, WrongType

@dataclass
class NamedMap[T]:
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

    def clone(self) -> NamedMap[T]:
        return NamedMap(self.collector, self.entity_cls, dict(self.data))


@dataclass
class NamedMapExtractor[T](ValueExtractor):
    ec: ErrorCollector
    clank_cfg: Config
    pud_cfg: Config

    def get_maps(self, parse_cls: type) -> tuple[NamedMap[T] | None, NamedMap[T] | None]:
        clank_map = self._extract_map(parse_cls, self.clank_cfg)
        pud_map = self._extract_map(parse_cls, self.pud_cfg, clank_map)
        return clank_map, pud_map

    def _extract_map(self, parse_cls: type, cfg: Config, old_map: NamedMap[T] | None = None) -> NamedMap[T] | None:
        if not cfg: return None
        res_map = old_map.clone() if old_map else NamedMap(self.ec, parse_cls.entity_cls)

        try: raw_entries = self.opt_dict(cfg.data, [parse_cls.entity_cls.plural_key], default={})
        except WrongType: self.ec.add_complaint("Wrong type"); raw_entries = {}

        for k, v in raw_entries.items():
            res_map.set(k, parse_cls(v, self.ec).parse())

        return res_map