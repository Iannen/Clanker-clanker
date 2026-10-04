from stdlib import dataclass, field, Generic, TypeVar, ItemsView
from ...asset_ingestion import ErrorCollector, ValueExtractor, WrongType#, RenderParser, UIRenderParser, DomParser
from core import Config

class BaseConfigExtractor(ValueExtractor):

    def _extract_map[T](
        self, 
        parse_cls: type[T], 
        cfg: Config, 
        parser_args: tuple,
        search_key:str
    ) -> NamedMap[T] | None:
        if not cfg: return None
        target_map = NamedMap(self.ec, parse_cls.entity_cls)

        
        try: raw_entries = self.opt_dict(cfg.data, [search_key], default={})
        except WrongType: self.ec.add_complaint("Wrong type"); raw_entries = {}

        args = parser_args or ()
        for k, v in raw_entries.items():
            target_map.set(k, parse_cls(self.ec).parse(k, v, *args))

        return target_map

    def _extract_single[T](
        self, 
        parse_cls: type[T], 
        cfg: Config, 
        parser_args: tuple,
        search_key:str
    ) -> T | None:
        if not cfg: return None
        
        try: raw_entries = self.opt_dict(cfg.data, [search_key], default={})
        except WrongType: self.ec.add_complaint("Wrong type"); raw_entries = {}

        args = parser_args or ()
        item = parse_cls(self.ec).parse(search_key, raw_entries, *args)

        return item

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

    def __or__(self, other: NamedMap[T]) -> NamedMap[T]:
        if not isinstance(other, NamedMap):
            return NotImplemented
        merged_data = dict(self.data)
        merged_data.update(other.data)
        return NamedMap(self.collector, self.entity_cls, merged_data)

T = TypeVar("T")
@dataclass
class ConfigExtractor(BaseConfigExtractor):
    ec: ErrorCollector
    clank_cfg: Config
    pud_cfg: Config

    def get_maps[T](self, parse_cls: type[T], clank_args: tuple | None = None, pud_args: tuple | None = None) -> tuple[NamedMap[T] | None, NamedMap[T] | None, NamedMap[T] | None]:
        search_key = parse_cls.entity_cls.plural_key
        clank_map = self._extract_map(parse_cls, self.clank_cfg, clank_args, search_key)
        pud_map = self._extract_map(parse_cls, self.pud_cfg, pud_args, search_key)

        return clank_map, pud_map

    def _extract_map[T](
        self, 
        parse_cls: type[T], 
        cfg: Config, 
        parser_args: tuple,
        search_key:str
    ) -> NamedMap[T] | None:
        if not cfg: return None
        target_map = NamedMap(self.ec, parse_cls.entity_cls)

        
        try: raw_entries = self.opt_dict(cfg.data, [search_key], default={})
        except WrongType: self.ec.add_complaint("Wrong type"); raw_entries = {}

        args = parser_args or ()
        for k, v in raw_entries.items():
            target_map.set(k, parse_cls(self.ec).parse(k, v, *args))

        return target_map


T = TypeVar("T")
@dataclass
class SysConfigExtractor(BaseConfigExtractor):
    ec: ErrorCollector
    sys_cfg: Config

    def get_one(self, parse_cls: type, args: tuple | None = None):
        search_key = parse_cls.entity_cls.key_name
        item = self._extract_single(parse_cls, self.sys_cfg, args, search_key)
        return item
