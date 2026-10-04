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
        except WrongType: self.ec.add_complaint("Wrong type"); raw_entries = {} # probably add complaint here
        if not raw_entries: return None

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
    configs: tuple[Config, ...]

    def get_maps[T](
        self, 
        parse_cls: type[T], 
        *args_per_config: tuple | None
    ) -> tuple[NamedMap[T] | None, ...]:
        search_key = parse_cls.entity_cls.plural_key
       
        results: list[NamedMap[T] | None] = []
        for i, cfg in enumerate(self.configs):
            cfg_args = args_per_config[i] if i < len(args_per_config) else None
            extracted_map = self._extract_map(parse_cls, cfg, cfg_args, search_key)
            results.append(extracted_map)

        return tuple(results)

    def _extract_map[T](
        self, 
        parse_cls: type[T], 
        cfg: Config | None, 
        parser_args: tuple | None,
        search_key: str
    ) -> NamedMap[T] | None:
        if not cfg: 
            return None
            
        target_map = NamedMap(self.ec, parse_cls.entity_cls)
        
        try: 
            raw_entries = self.opt_dict(cfg.data, [search_key], default={})
        except WrongType: 
            self.ec.add_complaint("Wrong type")
            raw_entries = {}

        args = parser_args or ()
        for k, v in raw_entries.items():
            target_map.set(k, parse_cls(self.ec).parse(k, v, *args))

        return target_map

    def get_singles[T](
        self, 
        parse_cls: type[T], 
        *args_per_config: tuple | None
    ) -> tuple[T | None, ...]:
        search_key = parse_cls.entity_cls.key_name
        
        results: list[T | None] = []
        for i, cfg in enumerate(self.configs):
            cfg_args = args_per_config[i] if i < len(args_per_config) else None
            extracted_item = self._extract_single(parse_cls, cfg, cfg_args, search_key)
            results.append(extracted_item)

        return tuple(results)


T = TypeVar("T")
@dataclass
class SysConfigExtractor(BaseConfigExtractor):
    ec: ErrorCollector
    sys_cfg: Config
    
    def get_one(self, parse_cls: type, args: tuple | None = None):
        search_key = parse_cls.entity_cls.key_name
        item = self._extract_single(parse_cls, self.sys_cfg, args, search_key)
        return item
