from stdlib import dataclass, field, inspect
from core import Entity, Config
from ...asset_ingestion import ValueExtractor, ErrorCollector

def _load_parsers() -> dict[type, type]:
    import modules.asset_ingestion.extractors.parsers as parsers_module
    base_cls = parsers_module.BaseParser2
    return {
        cls.entity_cls: cls
        for cls in parsers_module.__dict__.values()
        if inspect.isclass(cls)
        and issubclass(cls, base_cls)
        and cls is not base_cls
        and hasattr(cls, "entity_cls")
    }

@dataclass
class Numap:
    entities: dict[tuple[type, str], Entity] = field(default_factory=dict)
    parsers: dict[type, type] = field(default_factory=_load_parsers)

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

    def get_parser(self, entity_cls: type) -> type:
        if not isinstance(entity_cls, type) or not issubclass(entity_cls, Entity):
            raise TypeError(f"Expected a subclass of Entity, got {entity_cls}")
        parse_cls = self.parsers.get(entity_cls)
        if not parse_cls: raise Exception(f"No parse class registered for {entity_cls.__name__}")
        return parse_cls

@dataclass
class NuConfigExtractor(ValueExtractor):
    numap: Numap
    collector: ErrorCollector
    cfg: Config
    def extract_from_map(self, entity_cls: type) -> None:
        if not self.cfg: return
        entities_dict = self.opt_dict(self.cfg.data, [entity_cls.plural_key],{})
        parse_cls = self.numap.get_parser(entity_cls)
        for name, entity_data in entities_dict.items():
            entity = parse_cls(self.collector).parse(name, entity_data, self.numap)
            self.numap.set_entity(name, entity, entity_cls)       
    def extract_single(self, entity_cls: type) -> None:
        if not self.cfg: return
        entity_dict = self.opt_dict(self.cfg.data, [entity_cls.key_name],{})
        if not entity_dict: entity = None
        else:
            parse_cls = self.numap.get_parser(entity_cls)
            entity = parse_cls(self.collector).parse(entity_cls.key_name, entity_dict, self.numap)
        self.numap.set_entity(entity_cls.key_name, entity, entity_cls)