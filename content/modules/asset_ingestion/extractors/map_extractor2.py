from stdlib import dataclass, inspect, Any, fields, get_args, get_origin, types, MISSING, Field
from core import entities as e
from core.engine_deps import MissingEntityFields

from ...asset_ingestion import ErrorCollector, Config

class Absent: pass
class atomic: pass

@dataclass
class EntityField:
    raw_field: Field
    key: str
    outer_type: type
    inner_type: type
    raw_data: Any
    value: Any

    @classmethod
    def from_field(cls, raw_field: Field, field_data: Any) -> "EntityField":
        raw_type = raw_field.type
        outer_args = get_args(raw_type)
        is_nullable = type(None) in outer_args
       
        outer_type_hint = raw_type
        if get_origin(raw_type) is types.UnionType:
            not_none = [t for t in outer_args if t is not type(None)]
            if len(not_none) == 1: outer_type_hint = not_none[0]
            else: raise Exception(f"Only 'T' or 'T | None' supported, got: {raw_type}")
        origin = get_origin(outer_type_hint)
        inner_args = get_args(outer_type_hint)
        outer_type = origin if origin else atomic
        
        if origin is not None and origin not in (list, dict): raise Exception(f"Unsupported origin type: {origin}")
            
        inner_type = inner_args[0] if origin is list else inner_args[1] if origin is dict else outer_type_hint

        if raw_field.default is not MISSING: default_value = raw_field.default
        elif is_nullable: default_value = None
        else: default_value = Absent

        value = Absent
        if field_data is None: value = default_value
        elif field_data is not Absent and not issubclass(inner_type, e.Entity): value = field_data

        return cls(
            raw_field=raw_field,
            key=raw_field.name,
            outer_type=outer_type,
            inner_type=inner_type,
            raw_data=field_data,
            value=value
        )

class ParserCtx:
    def __init__(self, entity_cls: type[e.Entity], data: dict = {}):
        self.entity_cls = entity_cls
        self.data = data
        self.fields: list[EntityField] = [ EntityField.from_field(raw_field, data.get(raw_field.name)) for raw_field in fields(entity_cls)]
        self.unsatisfied_fields: list[Field] = []
        self.instantiated_instances: list[e.Entity] = []

    def get_deps(self, all_entity_classes: list[e.type[e.Entity]]) -> list[type[e.Entity]]:
        field_types = [field.inner_type for field in self.fields]
        subs = [sub for sub in all_entity_classes if self.entity_cls in sub.__bases__]

        all_types = set(field_types + subs)
        
        return [
            t for t in all_types 
            if isinstance(t, type) 
            and issubclass(t, e.Entity) 
            and t is not e.Entity 
            and t is not self.entity_cls
        ]

def build_ordered_parsers(ec: Any) -> dict[type | str, Any]:
    entity_base_cls = e.Entity
    entity_classes = [ obj for obj in e.__dict__.values() if inspect.isclass(obj) and issubclass(obj, entity_base_cls) and obj is not entity_base_cls]

    ctx_instances = {cls: ParserCtx(cls) for cls in entity_classes}
    satisfied: list[type[e.Entity]] = []
    unsatisfied = list(ctx_instances.values())

    while unsatisfied:
        progress = False
        next_unsatisfied = []
        covered = set(satisfied)

        for ctx in unsatisfied:
            if all(dep in covered for dep in ctx.get_deps(entity_classes)):
                satisfied.append(ctx.entity_cls)
                progress = True
            else: next_unsatisfied.append(ctx)
        if not progress: raise Exception("Circular dependency detected among entity classes!")
        unsatisfied = next_unsatisfied

    parse_base_cls = BaseParser2
    parse_classes = {obj.entity_cls: obj(ec) for obj in globals().values()if inspect.isclass(obj) and issubclass(obj, BaseParser2) and obj is not BaseParser2 and getattr(obj, "entity_cls", None)}
    
    parser_map: dict[type | str, Any] = {}

    for cls in satisfied:
        parser_inst = parse_classes.get(cls) or BaseParser2(ec)
        parser_inst.entity_cls = cls
        
        parser_map[cls] = parser_inst
        if hasattr(cls, "type") and isinstance(cls.type, str): parser_map[cls.type] = parser_inst

    return parser_map

class Numap:
    def __init__(self, ec: ErrorCollector, *configs: Config):
        self.ec = ec
        self.configs = configs
        self.entities: dict[tuple[type, str], e.Entity] = {}
        self.all_entities: list[e.Entity] = []
        self.ordered_parsers = build_ordered_parsers(ec)
        self.cleanup_registry: dict[int, list[Any]] = {}

    def extract_all(self):
        for parser in dict.fromkeys(self.ordered_parsers.values()):
            for cfg in self.configs: 
                if cfg: self._extract(cfg, parser.entity_cls, parser)

    def _extract(self, cfg: Config, entity_cls: type, parser: Any) -> None:
        items = []

        if entities_dict := cfg.data.get(entity_cls.plural_key): items.extend(entities_dict.items())

        if entity_dict := cfg.data.get(entity_cls.key_name): items.append((entity_cls.key_name, entity_dict))

        for name, entity_data in items:
            if entity := parser.parse(name, entity_data, self):
                entity.set_ancestor(cfg)
                self.set_entity(name, entity, entity_cls)

    def register_cleanup(self, entity: e.Entity, callback: Any) -> None:
        if not isinstance(entity, e.Entity): raise TypeError(f"Expected an instance of Entity, got {type(entity).__name__}")
        self.cleanup_registry.setdefault(id(entity), []).append(callback)

    def prune(self, target: e.Entity | list[e.Entity]) -> None:
        if isinstance(target, e.Entity):
            callbacks = self.cleanup_registry.pop(id(target), [])
            for cb in callbacks: cb()
        else:
            for entity in list(target):
                self.prune(entity)

    def register(self, entity: e.Entity) -> None:
        if not isinstance(entity, e.Entity):
            raise TypeError(f"Expected an instance of Entity, got {type(entity).__name__}")
        self.all_entities.append(entity)

    def set_entity(self, name: str, entity: e.Entity, cls: type) -> None:
        if not isinstance(entity, e.Entity):
            raise TypeError(f"Expected an instance of Entity, got {type(entity).__name__}")
        self.entities[(cls, name)] = entity

    def get_entity(self, entity_cls: type, key: str) -> e.Entity | None:
        if not isinstance(entity_cls, type) or not issubclass(entity_cls, e.Entity):
            raise TypeError(f"Expected a subclass of Entity, got {entity_cls}")
        if not isinstance(key, str):
            return None
        return self.entities.get((entity_cls, key))
    
    def get_entities(self, entity_cls: type) -> list[e.Entity]:
        return [entity for entity in self.all_entities if isinstance(entity, entity_cls)]

    def get_parser(self, entity_cls: type | str) -> type:
        parser = self.ordered_parsers.get(entity_cls)
        if not parser:
            raise Exception(f"No parse class registered for {entity_cls.__name__}")
        return parser

class BaseParser2:
    def __init__(self, ec: ErrorCollector):
        self.ec = ec

    def preprocess(self, data: dict):
        return data

    def parse(self, name: str | None, data: dict, numap: Numap) -> Any:
        data = self.preprocess(data.copy()) if isinstance(data, (dict, list)) else self.preprocess(data)

        if name: data["name"] = name
        ctx = ParserCtx(self.entity_cls, data)

        for field in ctx.fields:
            if field.value is Absent: self._parse_value(field, numap, ctx)
            
            if field.value is Absent: ctx.unsatisfied_fields.append(field.raw_field)

        if ctx.unsatisfied_fields:
            self.ec.accept(MissingEntityFields(self.entity_cls, ctx.unsatisfied_fields, data))
            return None

        entity = self.entity_cls(**{f.key: f.value for f in ctx.fields})
        for inst in ctx.instantiated_instances:
            inst.set_ancestor(entity)
        numap.register(entity)

        for field in [f for f in ctx.fields if f.value not in (Absent, None) and issubclass(f.inner_type, e.Entity)]:
            if field.outer_type == atomic:
                numap.register_cleanup(field.value, lambda inst=entity, f=field.key: setattr(inst, f, None))
            elif field.outer_type == list:
                for child in field.value:
                    numap.register_cleanup(child, lambda inst=entity, f=field.key, c=child: getattr(inst, f).remove(c) if c in getattr(inst, f) else None)

        return entity

    def _parse_value(self, field: EntityField, numap: Numap, ctx: ParserCtx) -> None:
        if field.outer_type == list:
            field.value = [inst for d in field.raw_data if (inst := self._get_entity("", d, field, numap, ctx)) is not None]
        elif field.outer_type == dict:
            raise Exception("We found a dict omg!")         
        elif field.outer_type == atomic:
            field.value = self._get_entity(field.key, field.raw_data, field, numap, ctx)

    def _get_entity(self, name, data, field: EntityField, numap: Numap, ctx: ParserCtx):
        e = None
        if isinstance(data, str) and data.startswith("¤"):
            lookup_key = data[1:].lstrip()
            e = numap.get_entity(field.inner_type, lookup_key)
        else:
            parser = numap.get_parser(field.inner_type)
            e = parser.parse(name, data, numap)
            if e is not None:
                ctx.instantiated_instances.append(e)
        return e

class FilelistParser2(BaseParser2): 
    entity_cls = e.Filelist
    def preprocess(self, data: dict) -> dict: return {"files": data}

class FileParser(BaseParser2):
    entity_cls = e.File
    def preprocess(self, data: dict) -> dict:
        if isinstance(data, str): return {"name": data}
        return {"name": data.pop("name"), "truncation_spec": data if data else None}

class RepoContentResParser(BaseParser2):
    entity_cls = e.RepoContentResolver
    def preprocess(self, data: dict) -> dict:
        if "fileset" in data: return data
        return {
            "anchor": data.pop("anchor", None),
            "type": data.pop("type", None),
            "fileset": data
        }

class FilesetItemparser(BaseParser2):
    entity_cls = e.FilesetItem
    def preprocess(self, data): return {"value":data}

class ResolverParser2(BaseParser2):
    entity_cls = e.Resolver
    def parse(self, name, data, numap: Numap) -> e.Resolver | None:
        return numap.get_parser(data.get("type")).parse(name, data, numap)

class KeyboardParser2(BaseParser2):
    entity_cls = e.Keyboard
    def parse(self, name: str, data: dict, numap: Numap) -> e.Keyboard:        
        shared_btns = [e.SharedDomButton(key, None) for key in data.get("shared_domains_row", [])]
        pud_btns = [e.PudDomButton(key, None) for key in data.get("pud_domains_row", [])]
        prompt_btns = [e.PromptButton(key, None) for key in data.get("prompts_row", [])]

        keyboard = e.Keyboard({btn.key: btn for btn in shared_btns + pud_btns + prompt_btns}, None)
        for item in shared_btns + pud_btns + prompt_btns + [keyboard]: numap.register(item)
        return keyboard