from stdlib import field, fields, MISSING, get_args, Any, get_args, get_origin, types, Field, get_args, get_origin
from ...asset_ingestion import ErrorCollector, Numap
from core.engine_deps.ingestion import MissingEntityFields
from core import Entity, Filelist, Keyboard, Resolver, File, RepoContentResolver, SharedDomButton, PudDomButton, PromptButton

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

class BaseParser2:
    def __init__(self, ec: ErrorCollector):
        self.ec = ec

    def preprocess(self, data: dict):
        return data

    def parse(self, name: str | None, data: dict, numap: Numap) -> Any:
        if isinstance(data, (str, type(None), list)):
            data = self.preprocess(data)
        elif isinstance(data, dict):
            data = self.preprocess(data.copy())
        else: 
            raise Exception("data is not dict, string nor list")
        if name:
            data["name"] = name
        
        fields_list: list[EntityField] = []
        unsatisfied_fields = []

        for raw_field in fields(self.entity_cls):
            field = EntityField(raw_field)
            self._parse_value(field, data, numap)
            
            if field.value is Absent:
                unsatisfied_fields.append(field.raw_field)

            fields_list.append(field)

        if unsatisfied_fields:
            self.ec.accept(MissingEntityFields(self.entity_cls, unsatisfied_fields, data))
            return None

        entity = self.entity_cls(**{f.key: f.value for f in fields_list})
        numap.register(entity)
        return entity

    def _parse_value(self, field: EntityField, data: dict, numap: Numap) -> None:
        field_data = data.get(field.key)

        if field_data is None: field.value = field.default_value
        elif not issubclass(field.inner_type, Entity): field.value = field_data
        elif field.outer_type == list: field.value = [e for d in field_data if (e := self._get_entity("", d, field, numap)) is not None]
        elif field.outer_type == dict: raise Exception("We found a dict omg!")         
        elif field.outer_type == atomic: field.value = self._get_entity(field.key, field_data, field, numap)

    def _get_entity(self, name, data, field: EntityField, numap: Numap):
        e = numap.get_entity(field.inner_type, data)
        if not e and not isinstance(data, str):
            parser = numap.get_parser(field.inner_type)
            e = parser.parse(name, data, numap)
        return e

class FilelistParser2(BaseParser2): 
    entity_cls = Filelist
    def preprocess(self, data: dict) -> dict:
        return {"files": [{"name": file} if isinstance(file, str) else file for file in data]}

class FileParser(BaseParser2):
    entity_cls = File
    def preprocess(self, data: dict) -> dict:
        return {
            "name": data.pop("name"),
            "truncation_spec": data if data else None
        }

class RepoContentResParser(BaseParser2):
    entity_cls = RepoContentResolver
    def preprocess(self, data: dict) -> dict:
        if "fileset" in data: return data
        return {
            "anchor": data.pop("anchor", None),
            "type": data.pop("type", None),
            "fileset": data
        }

class ResolverParser2(BaseParser2):
    entity_cls = Resolver
    def parse(self, name, data, numap: Numap) -> Resolver | None:
        return numap.get_parser(data.get("type")).parse(name, data, numap)

class KeyboardParser2(BaseParser2):
    entity_cls = Keyboard
    def parse(self, name: str, data: dict, numap: Numap) -> Keyboard:       
        shared_btns = [SharedDomButton(key, None) for key in data.get("shared_domains_row", [])]
        pud_btns = [PudDomButton(key, None) for key in data.get("pud_domains_row", [])]
        prompt_btns = [PromptButton(key, None) for key in data.get("prompts_row", [])]
                    
        keyboard = Keyboard({btn.key: btn for btn in shared_btns + pud_btns + prompt_btns}, None)
        for item in shared_btns + pud_btns + prompt_btns + [keyboard]: numap.register(item)
        return keyboard