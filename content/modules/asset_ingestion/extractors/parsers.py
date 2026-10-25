from stdlib import field, Any
from ...asset_ingestion import ErrorCollector, Numap, ParserCtx, EntityField, Absent, atomic
from core.engine_deps import MissingEntityFields
from core import Entity, Filelist, Keyboard, Resolver, File, RepoContentResolver, SharedDomButton, PudDomButton, PromptButton, FilesetItem

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
            try: data["name"] = name
            except Exception as e:
                pass
        
        ctx = ParserCtx(self.entity_cls)

        for field in ctx.fields:
            self._parse_value(field, data, numap, ctx)
            
            if field.value is Absent:
                ctx.unsatisfied_fields.append(field.raw_field)

        if ctx.unsatisfied_fields:
            # this becomes the rollback. we must destroy fresh entities, but i think this is less of a concern at present.
            self.ec.accept(MissingEntityFields(self.entity_cls, ctx.unsatisfied_fields, data))
            return None

        entity = self.entity_cls(**{f.key: f.value for f in ctx.fields})
        for inst in ctx.instantiated_instances:
            inst.set_ancestor(entity)
        numap.register(entity)

        for field in [f for f in ctx.fields if f.value not in (Absent, None) and issubclass(f.inner_type, Entity)]:
            if field.outer_type == atomic:
                numap.register_cleanup(field.value, lambda e=entity, f=field.key: setattr(e, f, None))
            elif field.outer_type == list:
                for child in field.value:
                    numap.register_cleanup(child, lambda e=entity, f=field.key, c=child: getattr(e, f).remove(c) if c in getattr(e, f) else None)

        return entity

    def _parse_value(self, field: EntityField, data: dict, numap: Numap, ctx: ParserCtx) -> None:

        field_data = data.get(field.key)

        if field_data is None: field.value = field.default_value
        elif not issubclass(field.inner_type, Entity): field.value = field_data
        elif field.outer_type == list: field.value = [e for d in field_data if (e := self._get_entity("", d, field, numap, ctx)) is not None]
        elif field.outer_type == dict: raise Exception("We found a dict omg!")         
        elif field.outer_type == atomic: field.value = self._get_entity(field.key, field_data, field, numap, ctx)

    def _get_entity(self, name, data, field: EntityField, numap: Numap, ctx: ParserCtx):
        e = None
        if isinstance(data, str) and data.startswith("¤"):
            lookup_key = data[1:].lstrip()
            e = numap.get_entity(field.inner_type, lookup_key)
            if e is not None:
                ctx.fetched_instances.append(e)
        else:
            parser = numap.get_parser(field.inner_type)
            e = parser.parse(name, data, numap)
            if e is not None:
                ctx.instantiated_instances.append(e)
        return e

class FilelistParser2(BaseParser2): 
    entity_cls = Filelist
    def preprocess(self, data: dict) -> dict: return {"files": data}

class FileParser(BaseParser2):
    entity_cls = File
    def preprocess(self, data: dict) -> dict:
        if isinstance(data, str): return {"name": data}
        return {"name": data.pop("name"), "truncation_spec": data if data else None}

class RepoContentResParser(BaseParser2):
    entity_cls = RepoContentResolver
    def preprocess(self, data: dict) -> dict:
        if "fileset" in data: return data
        return {
            "anchor": data.pop("anchor", None),
            "type": data.pop("type", None),
            "fileset": data
        }

class FilesetItemparser(BaseParser2):
    entity_cls = FilesetItem
    def preprocess(self, data): return {"value":data}

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