from stdlib import dataclass, inspect, Any, fields, get_args, get_origin, types, MISSING, Field
from core import Entity
from ...asset_ingestion import ErrorCollector, Config

class Absent: pass
class atomic: pass

class EntityField:
    def __init__(self, raw_field: Field):
        self.raw_field = raw_field
        self.key = raw_field.name
        self.value = Absent
        outer_type_hint = self._extract_nullability(raw_field)
        self._extract_types(outer_type_hint)
        self._resolve_default(raw_field)

    def _extract_nullability(self, raw_field: Field) -> Any:
        raw_type = raw_field.type
        outer_args = get_args(raw_type)
        self.outer_type_nullable = type(None) in outer_args
        outer_type_hint = raw_type
        if get_origin(raw_type) is types.UnionType:
            not_none = [t for t in outer_args if t is not type(None)]
            if len(not_none) == 1:
                outer_type_hint = not_none[0]
            else:
                raise Exception(f"Only 'T' or 'T | None' supported, got: {raw_type}")            
        return outer_type_hint

    def _extract_types(self, outer_type_hint: Any):
        origin = get_origin(outer_type_hint)
        inner_args = get_args(outer_type_hint)         
        self.outer_type = origin if origin else atomic
        self.inner_type = inner_args[0] if origin is list else inner_args[1] if origin is dict else outer_type_hint
        if origin is not None and origin not in (list, dict): raise Exception(f"Unsupported origin type: {origin}")

    def _resolve_default(self, raw_field: Field):
        v = Absent
        if raw_field.default is not MISSING: v = raw_field.default
        elif self.outer_type_nullable: v = None
        self.default_value = v

class ParserCtx:
    def __init__(self, entity_cls: type[Entity]):
        self.entity_cls = entity_cls
        self.fields: list[EntityField] = [EntityField(raw_field) for raw_field in fields(entity_cls)]
        self.unsatisfied_fields: list[Field] = []
        self.instantiated_instances: list[Entity] = []
        self.fetched_instances: list[Entity] = []

    def get_deps(self, all_entity_classes: list[type[Entity]]) -> list[type[Entity]]:
        field_types = [field.inner_type for field in self.fields]
        subs = [sub for sub in all_entity_classes if self.entity_cls in sub.__bases__]

        all_types = set(field_types + subs)
        
        return [
            t for t in all_types 
            if isinstance(t, type) 
            and issubclass(t, Entity) 
            and t is not Entity 
            and t is not self.entity_cls
        ]

def build_parser_map(ec: Any, entity_classes) -> dict[type | str, Any]:
    from ...asset_ingestion import parsers
    parse_base_cls = parsers.BaseParser2

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

def entity_ordering() -> list[type[Entity]]:
    from core import entities
    entity_base_cls = entities.Entity

    entity_cls = [obj for obj in entities.__dict__.values() if inspect.isclass(obj) and issubclass(obj, entity_base_cls) and obj is not entity_base_cls]

    ctx_instances = [ParserCtx(cls) for cls in entity_cls]
    
    satisfied: list[ParserCtx] = []
    unsatisfied: list[ParserCtx] = ctx_instances

    while unsatisfied:
        progress = False
        next_unsatisfied = []
        covered = {ctx.entity_cls for ctx in satisfied}

        for e in unsatisfied:
            if all(dep in covered for dep in e.get_deps(entity_cls)):
                satisfied.append(e)
                progress = True
            else:
                next_unsatisfied.append(e)
        if not progress:
            raise Exception("Circular dependency detected among entity classes!")
        unsatisfied = next_unsatisfied
        
    ordered = [ctx.entity_cls for ctx in satisfied]
    return ordered

class Numap:
    def __init__(self, ec: ErrorCollector, *configs: Config):
        self.ec = ec
        self.configs = configs
        self.entities: dict[tuple[type, str], Entity] = {}
        self.all_entities: list[Entity] = []
        self.ordered_entities = entity_ordering()
        self.parsers = build_parser_map(ec, self.ordered_entities)
        self.cleanup_registry: dict[int, list[Any]] = {}

    def extract_all(self):
        extractors = [NuConfigExtractor(self, self.ec, cfg) for cfg in self.configs]
        for entity in self.ordered_entities:
            for ext in extractors:
                ext.extract_from_map(entity)
                ext.extract_single(entity)

    def register_cleanup(self, entity: Entity, callback: Any) -> None:
        if not isinstance(entity, Entity):
            raise TypeError(f"Expected an instance of Entity, got {type(entity).__name__}")
        self.cleanup_registry.setdefault(id(entity), []).append(callback)

    def prune(self, target: Entity | list[Entity]) -> None:
        if isinstance(target, Entity):
            callbacks = self.cleanup_registry.pop(id(target), [])
            for cb in callbacks:
                cb()
        else:
            for entity in list(target):
                self.prune(entity)

    def register(self, entity: Entity) -> None:
        if not isinstance(entity, Entity):
            raise TypeError(f"Expected an instance of Entity, got {type(entity).__name__}")
        self.all_entities.append(entity)

    def set_entity(self, name: str, entity: Entity, cls: type) -> None:
        if not isinstance(entity, Entity):
            raise TypeError(f"Expected an instance of Entity, got {type(entity).__name__}")
        self.entities[(cls, name)] = entity

    def get_entity(self, entity_cls: type, key: str) -> Entity | None:
        if not isinstance(entity_cls, type) or not issubclass(entity_cls, Entity):
            raise TypeError(f"Expected a subclass of Entity, got {entity_cls}")
        if not isinstance(key, str):
            return None # smell
        return self.entities.get((entity_cls, key))
    
    def get_entities(self, entity_cls: type) -> list[Entity]:
        return [entity for entity in self.all_entities if isinstance(entity, entity_cls)]

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
        if not entities_dict: return 
        parser = self.numap.get_parser(entity_cls)
        for name, entity_data in entities_dict.items():
            entity = parser.parse(name, entity_data, self.numap)
            if entity is not None:
                entity.set_ancestor(self.cfg)
                self.numap.set_entity(name, entity, entity_cls)

    def extract_single(self, entity_cls: type) -> None:
        if not self.cfg: return
        entity_dict = self.cfg.data.get(entity_cls.key_name)
        if not entity_dict: return
        parser = self.numap.get_parser(entity_cls)
        entity = parser.parse(entity_cls.key_name, entity_dict, self.numap)
        if entity is not None:
            entity.set_ancestor(self.cfg)
            self.numap.set_entity(entity_cls.key_name, entity, entity_cls)