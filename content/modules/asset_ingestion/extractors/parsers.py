from stdlib import dataclass, field, fields, MISSING, get_args, ClassVar, Any, get_args, get_origin, Enum, auto, types, Field
from types import get_original_bases
from typing import get_args, get_origin
from ...asset_ingestion import ValueExtractor, ErrorCollector, Numap
from core import ConfigAssembly, Entity, Filelist, Fileset, Keyboard, Render, UIRender, Resolver, Prompt, File, TruncationSpec, MultiDocResolver, ManifestResolver, RepoContentResolver, KBStateResolver, SharedDomButton, PudDomButton, PromptButton, SharedBaseResolver, PudBaseResolver, SharedDomain, PudDomain

class OuterType(Enum):
    SINGLE = auto()
    LIST = auto()
    DICT = auto()

@dataclass
class NormalField:
    key: str
    value: Any
@dataclass
class EntityField(NormalField):    
    outer_type: OuterType
    inner_type: type
    default_value: Any = MISSING

class BaseParser2[T: Entity](ValueExtractor):
    def __init__(self, ec: ErrorCollector):
        self.ec = ec
        for base in get_original_bases(self.__class__):
            origin = get_origin(base)
            if origin is not None and issubclass(origin, BaseParser2):
                args = get_args(base)
                if args and isinstance(args[0], type):
                    self.entity_cls: type[T] = args[0]
                    break
        else:
            raise AttributeError(f"Could not determine target entity class for {self.__class__.__name__}")

    def preprocess(self, data: dict):
        return data

    def parse(self, name: str | None, data: dict, numap: Numap) -> Any:
        if isinstance(data, str): data = self.preprocess(data)
        elif isinstance(data, dict): data = self.preprocess(data.copy())
        else: raise Exception("data is not dict nor dict")
        if name: data["name"] = name
        
        kwargs_out = {}
        if isinstance(self, UIResParser):
            hook = "hook"
        for raw_field in fields(self.entity_cls):
            field = self._process_raw_field(raw_field, data)           
            out = self._parse_value(field, numap)
            if out is None and field.default_value is MISSING:
                self.ec.add_complaint(f"Missing required key '{field.key}' in {self.entity_cls.__name__}")
            elif out is None:
                out = field.default_value
            kwargs_out[field.key] = out

        return self.entity_cls(**kwargs_out)

    def _process_raw_field(self, raw_field: Field, data) -> EntityField:
        raw_field_name = raw_field.name
        field_value = data.get(raw_field_name)

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

        if type(None) in args: default_value = None
        else: default_value = MISSING if raw_field.default is MISSING else raw_field.default


        return EntityField(
            key=raw_field.name,
            outer_type=outer_type,
            inner_type=inner_type,
            default_value=default_value,
            value=field_value,
        )

    def _parse_value(self,field: EntityField,numap: Numap,) -> Any:
        if not issubclass(field.inner_type, Entity): return field.value
        if field.outer_type == OuterType.LIST:  return [self._get_entity("", d, field, numap) for d in field.value]
        elif field.outer_type == OuterType.DICT:  raise Exception("We found a dict omg!")         
        elif field.outer_type == OuterType.SINGLE: return self._get_entity(field.key, field.value, field, numap)

    def _get_entity(self, name, data, field: EntityField, numap:Numap):
        e = numap.get_entity(field.inner_type, data)
        if not e and not isinstance(data, str):
            parser = numap.get_parser(field.inner_type)
            e = parser.parse(name, data, numap)
        return e

class UIResParser(BaseParser2[KBStateResolver]): pass
class RenderParser2(BaseParser2[Render]): pass
class UIRenderParser2(BaseParser2[UIRender]): pass
class FilesetParser2(BaseParser2[Fileset]): pass
class PromptParser2(BaseParser2[Prompt]): pass
class RepoManifestResParser(BaseParser2[ManifestResolver]): pass
class MdResParser(BaseParser2[MultiDocResolver]): pass
class SharedBaseResParser(BaseParser2[SharedBaseResolver]): pass
class PudBaseResParser(BaseParser2[PudBaseResolver]): pass
class SharedDomParser(BaseParser2[SharedDomain]): pass
class PudDomParser(BaseParser2[PudDomain]): pass
class RepoContentResParser(BaseParser2[RepoContentResolver]):
    def preprocess(self, data: dict) -> dict:
            if "fileset" in data: return data
            return {"fileset": data}

class FilelistParser2(BaseParser2[Filelist]): 
    # the baseparser needs a way to distinguish str which are data and str which are mapkeys
    def parse(self, name, data, numap:Numap) -> Filelist:
        files = [FileParser(self.ec).parse(None, f, numap) for f in data]
        return Filelist(files=files)

class FileParser(BaseParser2[File]):
    def preprocess(self, data):
        if isinstance(data, str): return {"name": data}
        return {"name": data.get("name"),"truncation_spec": data}

class TruncSpecParser(BaseParser2[TruncationSpec]):
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

class KeyboardParser2(BaseParser2[Keyboard]):
    def parse(self, name: str, data: dict, Numap: Numap) -> Keyboard:
        shared_btns = [SharedDomButton(key) for key in self.req_str(data, ["shared_domains_row"])]
        pud_btns = [PudDomButton(key) for key in self.req_str(data, ["pud_domains_row"])]
        prompt_btns = [PromptButton(key) for key in self.req_str(data, ["prompts_row"])]
        return Keyboard({btn.key: btn for btn in shared_btns + pud_btns + prompt_btns})

class ResolverParser2(BaseParser2[Resolver]):
    def parse(self, name, data, numap: Numap) -> Resolver | None:
        return numap.get_parser(self.req_str(data, ["type"])).parse(name, data, numap)