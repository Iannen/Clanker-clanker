from stdlib import dataclass, field, fields, MISSING, get_args, ClassVar, Any, get_args, get_origin, Enum, auto, types, Field
from core import Config, Entity, Domain, Filelist, Fileset, Keyboard, Render, UIRender, Resolver, Prompt, File, TruncationSpec, MultiDocResolver, ManifestResolver, RepoContentResolver, KBStateResolver, SharedDomButton, PudDomButton, PromptButton
from core import ConfigAssembly
from ...asset_ingestion import ValueExtractor, ErrorCollector


@dataclass
class Numap:
    entities: dict[tuple[type, str], Entity] = field(default_factory=dict)
    parsers: dict[type, type] = field(
        default_factory=lambda: {
            Domain: DomParser2,
            Filelist: FilelistParser2,
            Fileset: FilesetParser2,
            Keyboard: KeyboardParser2,
            Render: RenderParser2,
            UIRender: UIRenderParser2,
            Resolver: ResolverParser2,
            Prompt: PromptParser2
        }
    )

    def set_entity(self, name: str, entity: Entity) -> None:
        if not isinstance(entity, Entity):
            raise TypeError(f"Expected an instance of Entity, got {type(entity).__name__}")
        self.entities[(type(entity), name)] = entity

    def get_entity(self, entity_cls: type, key: str) -> Entity | None:
        if not isinstance(entity_cls, type) or not issubclass(entity_cls, Entity):
            raise TypeError(f"Expected a subclass of Entity, got {entity_cls}")
        if not isinstance(key, str):
            return None
        return self.entities.get((entity_cls, key))

    def get_parser(self, entity_cls: type) -> type:
        if not isinstance(entity_cls, type) or not issubclass(entity_cls, Entity):
            raise TypeError(f"Expected a subclass of Entity, got {entity_cls}")
        parse_cls = self.parsers.get(entity_cls)
        if not parse_cls: raise Exception(f"No parse class registered for {entity_cls.__name__}")
        return parse_cls

@dataclass
class NuConfigExtractor(ValueExtractor):
    collector: ErrorCollector
    cfg: Config
    def act_on(self, entity_cls: type, numap: Numap) -> None:
        if not self.cfg: return
        entities_dict = self.opt_dict(self.cfg.data, [entity_cls.plural_key],{})
        parse_cls = numap.get_parser(entity_cls)
        for name, entity_data in entities_dict.items():
            entity = parse_cls(self.collector).parse(name, entity_data, numap)
            numap.set_entity(name, entity)       

class OuterType(Enum):
    SINGLE = auto()
    LIST = auto()
    DICT = auto()


@dataclass
class EntityField:
    name: str
    data: Any
    outer_type: OuterType
    inner_type: type
    default_value: Any = MISSING


@dataclass
class BaseParser2(ValueExtractor):
    ec: ErrorCollector
    entity_cls: ClassVar[type[Entity]]

    def preprocess(self, data: dict):
        return data

    def parse(self, name: str | None, data: dict, numap: Numap) -> Any:
        if name: data["name"] = name
        data = self.preprocess(data)
        if not isinstance(data, dict):
            raise Exception("data is not dict")
        
        kwargs_out = {}

        for raw_field in fields(self.entity_cls):
            field = self._process_raw_field(raw_field, data)           
            out = self._parse_value(field, numap)
            if out is None and field.default_value is MISSING:
                self.ec.add_complaint(f"Missing required key '{field.name}' in {self.entity_cls.__name__}")
            elif out is None:
                out = field.default_value
            kwargs_out[field.name] = out

        return self.entity_cls(**kwargs_out)

    def _process_raw_field(self, raw_field: Field, data) -> EntityField:
        raw_field_name = raw_field.name
        field_data = data.get(raw_field_name)


        raw_type = raw_field.type
        
        args = get_args(raw_type)
        if get_origin(raw_type) is types.UnionType:
            not_none = [t for t in args if t is not type(None)]
            if len(not_none) == 1:
                outer_type_hint = not_none[0]
            else:
                raise Exception(f"Only 'T' or 'T | None' supported, got: {raw_type}")
        else:
            outer_type_hint = raw_type

        origin = get_origin(outer_type_hint)

        if origin is None:
            outer_type = OuterType.SINGLE
            inner_type = outer_type_hint
        elif origin is list:
            elem_args = get_args(outer_type_hint)
            outer_type = OuterType.LIST
            inner_type = elem_args[0] if elem_args else Any
        elif origin is dict:
            dict_args = get_args(outer_type_hint)
            outer_type = OuterType.DICT
            inner_type = dict_args[1] if len(dict_args) > 1 else Any
        else:
            raise Exception(f"Unsupported origin type: {origin}")

        if raw_field.default is not MISSING:
            default_value = raw_field.default
        elif raw_field.default_factory is not MISSING:
            default_value = raw_field.default_factory()
        elif type(None) in args:
            default_value = None
        else:
            default_value = MISSING

        return EntityField(
            name=raw_field.name,
            outer_type=outer_type,
            inner_type=inner_type,
            default_value=default_value,
            data=field_data,
        )

    def _parse_value(self,field: EntityField,numap: Numap,) -> Any:
        if not issubclass(field.inner_type, Entity): return field.data
        if field.outer_type == OuterType.LIST:  return [self._get_entity("", d, field, numap) for d in field.data]
        elif field.outer_type == OuterType.DICT:  raise Exception("We found a dict omg!")         
        elif field.outer_type == OuterType.SINGLE: return self._get_entity(field.name, field.data, field, numap)

    def _get_entity(self, name, data, field: EntityField, numap:Numap):
        e = numap.get_entity(field.inner_type, data)
        if not e:
            pc = numap.get_parser(field.inner_type)
            e = pc(self.ec).parse(name, data, numap)
        return e

@dataclass
class RenderParser2(BaseParser2): entity_cls: ClassVar[type[Entity]] = Render
@dataclass
class UIRenderParser2(RenderParser2): entity_cls: ClassVar[type[Entity]] = UIRender
@dataclass
class FilesetParser2(BaseParser2): entity_cls: ClassVar[type[Entity]] = Fileset
@dataclass
class DomParser2(BaseParser2): entity_cls: ClassVar[type[Entity]] = Domain
@dataclass
class PromptParser2(BaseParser2): entity_cls: ClassVar[type[Entity]] = Prompt
@dataclass
class RepoManifestResParser(BaseParser2): entity_cls: ClassVar[type[Entity]] = ManifestResolver
@dataclass 
class MdResParser(BaseParser2): entity_cls: ClassVar[type[Entity]] = MultiDocResolver
@dataclass
class RepoContentResParser(BaseParser2):
    entity_cls: ClassVar[type[Entity]] = RepoContentResolver
    def preprocess(self, data: dict) -> dict:
            if "fileset" in data: return data
            new_data = data.copy()
            fileset = {}
            if "includes" in new_data: fileset["includes"] = new_data.pop("includes")
            if "excludes" in new_data: fileset["excludes"] = new_data.pop("excludes")
            new_data["fileset"] = fileset
            return new_data

@dataclass
class FilelistParser2(BaseParser2): 
    entity_cls: ClassVar[type[Entity]] = Filelist

    def parse(self, name, data, numap:Numap) -> Filelist:
        files = [FileParser(self.ec).parse(None, f, numap) for f in data]
        return Filelist(files=files)


@dataclass 
class FileParser(BaseParser2):
    entity_cls: ClassVar[type[Entity]] = File
    
    def preprocess(self, data):
        i = 2
        # 'plan-mode.mode_instruction'
        # {'file': 'project-history.history', 'tail_lines': 16}
        if isinstance(data, str): return {"name": data}
        return data

    """
    def parse(self, name, data, numap:Numap) -> Filelist: 
        if isinstance(data, dict):
            filename = self.req_str(data, ["file"])
            trunc_spec = TruncSpecParser(self.ec).parse(None, data, numap)
            return File(name=filename, truncation_spec=trunc_spec)
        return File(name=self.req_str({"file": data}, ["file"]))
    """
@dataclass
class TruncSpecParser(BaseParser2):
    entity_cls: ClassVar[type[Entity]] = RepoContentResolver
    def preprocess(self, data: dict):
        return data
    def parse(self, name, data, numap:Numap) -> TruncationSpec:
        tail_lines = self.opt_int(data, ["tail_lines"], [])
        from_line = self.opt_str(data, ["from_line"], [])
        up_to = self.opt_str(data, ["up_to"], [])

        if tail_lines and (from_line or up_to):
            self.ec.add_complaint("TruncationSpec conflict: tail_lines cannot be combined with from_line or up_to")
            return None

        if tail_lines: return TruncationSpec(TruncationSpec.TYPE_TAIL, tail_lines)
            

        if from_line or up_to:
            return TruncationSpec(
                type=TruncationSpec.TYPE_REGEX_RANGE,
                from_line=from_line,
                up_to=up_to,
            )

@dataclass
class KeyboardParser2(ValueExtractor):
    collector: ErrorCollector
    entity_cls: type = Keyboard

    def parse(self, name: str, data: dict) -> Keyboard:
        shared_keys = self.req_str(data, ["shared_domains_row"])
        pud_keys = self.req_str(data, ["pud_domains_row"])
        prompt_keys = self.req_str(data, ["prompts_row"])

        return Keyboard(
            shared_dom_btns={key: SharedDomButton(key) for key in shared_keys},
            pud_dom_btns={key: PudDomButton(key) for key in pud_keys},
            prompt_btns={key: PromptButton(key) for key in prompt_keys},
        )

@dataclass
class ResolverParser2(ValueExtractor):
    collector: ErrorCollector
    entity_cls = Resolver

    def parse(self, name, data, numap:Numap) -> Resolver | None:
        res_type = self.req_str(data, ["type"])
        anchor = self.req_str(data, ["anchor"])

        if res_type == "multi-document-retrieval": return MdResParser(self.collector).parse(None, data, numap)
        if res_type == "repo_content": return RepoContentResParser(self.collector).parse(None, data, numap)
        if res_type == "repo-manifest": return RepoManifestResParser(self.collector).parse(None, data, numap)
        if res_type in ("kb_info", "kb_state"): return KBStateResolver(anchor)
        raise ConfigAssembly(f"Unsupported resolver type: '{res_type}'")

