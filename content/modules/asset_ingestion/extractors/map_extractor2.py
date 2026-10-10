from stdlib import dataclass, inspect, Any
from core import Entity
from ...asset_ingestion import ErrorCollector, Config

def build_parser_map(ec: Any) -> dict[type | str, Any]:
    from core import entities
    from ...asset_ingestion import parsers

    entity_base_cls = entities.Entity
    parse_base_cls = parsers.BaseParser2

    entity_classes = [
        obj for obj in entities.__dict__.values()
        if inspect.isclass(obj) and issubclass(obj, entity_base_cls) and obj is not entity_base_cls
    ]
    parse_classes = [
        obj for obj in parsers.__dict__.values()
        if inspect.isclass(obj) and issubclass(obj, parse_base_cls) and obj is not parse_base_cls
    ]
    parsers: dict[type | str, Any] = {}

    def _register(entity_cls: type, parser_inst: Any) -> None:
        parsers[entity_cls] = parser_inst
        if hasattr(entity_cls, "type") and isinstance(entity_cls.type, str):
            parsers[entity_cls.type] = parser_inst

    for cls in parse_classes:
        parser_inst = cls(ec)
        if parser_inst.entity_cls:
            _register(parser_inst.entity_cls, parser_inst)

    for cls in entity_classes:
        if cls not in parsers:
            parser_inst = parse_base_cls(ec)
            parser_inst.entity_cls = cls
            _register(cls, parser_inst)

    return parsers

class Numap:
    def __init__(self, ec: Any):
        self.entities: dict[tuple[type, str], Entity] = {}
        self.parsers = build_parser_map(ec)

    def set_entity(self, name: str, entity: Entity, cls: type) -> None:
        if not isinstance(entity, (Entity, type(None))):
            raise TypeError(f"Expected an instance of Entity, got {type(entity).__name__}")
        self.entities[(cls, name)] = entity

    def get_entity(self, entity_cls: type, key: str) -> Entity | None:
        if not isinstance(entity_cls, type) or not issubclass(entity_cls, Entity):
            raise TypeError(f"Expected a subclass of Entity, got {entity_cls}")
        if not isinstance(key, str):
            return None
        return self.entities.get((entity_cls, key))

    def get_entities(self, entity_cls: type) -> list[Entity]:
        return [
            entity
            for entity in self.entities.values()
            if isinstance(entity, entity_cls)
        ]

    def get_parser(self, entity_cls: type | str) -> type:
        parser = self.parsers.get(entity_cls)
        if not parser: raise Exception(f"No parse class registered for {entity_cls.__name__}")
        return parser

@dataclass
class NuConfigExtractor:
    numap: Numap
    collector: ErrorCollector
    cfg: Config
    def extract_from_map(self, entity_cls: type) -> None:
        if not self.cfg: return
        entities_dict = self.cfg.data.get(entity_cls.plural_key)
        if not entities_dict: return # complain?
        parser = self.numap.get_parser(entity_cls)
        for name, entity_data in entities_dict.items():
            entity = parser.parse(name, entity_data, self.numap)
            self.numap.set_entity(name, entity, entity_cls)       
    def extract_single(self, entity_cls: type) -> None:
        if not self.cfg: return
        #entity_dict = self.opt_dict(self.cfg.data, [entity_cls.key_name],{})
        entity_dict = self.cfg.data.get(entity_cls.key_name)
        if not entity_dict: return
        parser = self.numap.get_parser(entity_cls)
        entity = parser.parse(entity_cls.key_name, entity_dict, self.numap)
        self.numap.set_entity(entity_cls.key_name, entity, entity_cls)