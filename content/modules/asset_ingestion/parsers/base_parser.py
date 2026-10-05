from stdlib import dataclass, ClassVar, Any, fields, MISSING, get_args
from core import Entity, Fileset
from ...asset_ingestion import ErrorCollector, ValueExtractor

@dataclass
class BaseParser(ValueExtractor):
    ec: ErrorCollector
    entity_cls: ClassVar[type[Entity]]

    def parse(self, name: str, data: dict, *args, **kwargs) -> Any:
        if not isinstance(data, dict):
            self.ec.add_complaint(f"Expected dict for {self.entity_cls.__name__}, got {type(data).__name__}")
            return None

        kwargs_out = {}
        for f in fields(self.entity_cls):
            key = f.name
            
            has_default = f.default is not MISSING or f.default_factory is not MISSING
            type_args = get_args(f.type)
            is_optional = has_default or (type(None) in type_args)

            if key not in data:
                if not is_optional:
                    self.ec.add_complaint(f"Missing required key '{key}' in {self.entity_cls.__name__}")
                    continue
                kwargs_out[key] = f.default if f.default is not MISSING else None
            else:
                kwargs_out[key] = data[key]

        return self.entity_cls(**kwargs_out)

@dataclass
class FilesetParser(BaseParser): entity_cls = Fileset


"""
from stdlib import dataclass, field
from core import Domain, Filelist, Keyboard, Render, Resolver
from ...asset_ingestion import DomParser, FilelistParser, KeyboardParser, RenderParser, ResolverParser

@dataclass
class Numap:
    entities: dict[tuple[type, str], Entity] = field(default_factory=dict)
    parsers: dict[type, type] = field(
        default_factory=lambda: {
            Domain: DomParser,
            Filelist: FilelistParser,
            Keyboard: KeyboardParser,
            Render: RenderParser,
            Resolver: ResolverParser,
        }
    )

    def set(self, entity: Entity, name: str) -> None:
        if not isinstance(entity, Entity):
            raise TypeError(f"Expected an instance of Entity, got {type(entity).__name__}")
        self.entities[(type(entity), name)] = entity

    def get(self, entity_cls: type, key: str) -> Entity | type | None:
        if not isinstance(entity_cls, type) or not issubclass(entity_cls, Entity):
            raise TypeError(f"Expected a subclass of Entity, got {entity_cls}")
            
        res = self.entities.get((entity_cls, key))
        if res is None:
            res = self.parsers.get(entity_cls)
        return res

@dataclass
class NuConfigExtractor:
    collector: ErrorCollector
    cfg: Config
    def act_on(self, entity_cls: type, map: Numap) -> Numap:
        return map
"""