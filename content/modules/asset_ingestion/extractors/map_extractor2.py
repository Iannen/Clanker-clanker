from stdlib import dataclass, field, fields, MISSING, get_args, ClassVar, Any
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
        return self.parsers.get(entity_cls)

@dataclass
class NuConfigExtractor(ValueExtractor):
    collector: ErrorCollector
    cfg: Config
    def act_on(self, entity_cls: type, numap: Numap) -> None:
        if not self.cfg: return
        entities_dict = self.opt_dict(self.cfg.data, [entity_cls.plural_key],{})
        parse_cls = numap.get_parser(entity_cls)
        flp = FilelistParser2
        fsp = FilesetParser2
        dp = DomParser2
        for name, entity_data in entities_dict.items():
            entity = parse_cls(self.collector).parse(name, entity_data, numap)
            numap.set_entity(name, entity)       

@dataclass
class BaseParser2(ValueExtractor):
    ec: ErrorCollector
    entity_cls: ClassVar[type[Entity]]

    def preprocess(self, data: dict): return data

    def parse(self, name: str, data: dict, numap: Numap) -> Any:
        data = self.preprocess(data)
        kwargs_out = {}

        for field in fields(self.entity_cls):
            key = field.name
            raw_type = field.type

            has_default = field.default is not MISSING

            type_args = get_args(raw_type)
            is_optional_type = type(None) in type_args
            is_optional = has_default or is_optional_type

            non_none_types = [t for t in type_args if t is not type(None)]
            target_type = non_none_types[0] if non_none_types else raw_type

            if key not in data:
                if not is_optional:
                    self.ec.add_complaint(
                        f"Missing required key '{key}' in {self.entity_cls.__name__}"
                    )
                    continue

                if has_default:
                    kwargs_out[key] = field.default
                else:
                    kwargs_out[key] = None
            else:
                raw_val = data[key]

                if isinstance(target_type, type) and issubclass(target_type, Entity):
                    out = numap.get_entity(target_type, raw_val)
                    if not out:
                        parser_cls = numap.get_parser(target_type)
                        out = parser_cls(self.ec).parse(key, raw_val, numap)
                else:
                    out = data.get(key)
                kwargs_out[key] = out

        return self.entity_cls(**kwargs_out)
"""
@dataclass
class BaseParser2(ValueExtractor):
    ec: ErrorCollector
    entity_cls: ClassVar[type[Entity]]

    def preprocess(self, data: dict): 
        return data

    def parse(self, name: str, data: dict, numap: Numap) -> Any:
        data = self.preprocess(data)
        kwargs_out = {}

        for field in fields(self.entity_cls):
            key = field.name
            raw_type = field.type
            has_default = field.default is not MISSING

            if key not in data:
                if not has_default and type(None) not in get_args(raw_type):
                    self.ec.add_complaint(
                        f"Missing required key '{key}' in {self.entity_cls.__name__}"
                    )
                    continue

                kwargs_out[key] = field.default if has_default else None # probably not ok to give None
            else:
                kwargs_out[key] = self._parse_value(raw_type, data[key], numap, key)

        return self.entity_cls(**kwargs_out)

    def _parse_value(self, target_type: type, value: Any, numap: Numap, key_context: str) -> Any:
        if value is None:
            return None

        args = get_args(target_type)
        if args:
            non_none = [t for t in args if t is not type(None)]
            if len(non_none) == 1:
                target_type = non_none[0]

        origin = getattr(target_type, "__origin__", target_type)

        if isinstance(target_type, type) and issubclass(target_type, Entity):
            if isinstance(value, str):
                entity = numap.get_entity(target_type, value)
                if entity is not None:
                    return entity
            if isinstance(value, dict):
                parser_cls = numap.get_parser(target_type)
                if parser_cls:
                    return parser_cls(self.ec).parse(key_context, value, numap)
            return value

        if origin is list and isinstance(value, list):
            elem_type = get_args(target_type)[0] if get_args(target_type) else Any
            return [self._parse_value(elem_type, item, numap, key_context) for item in value]

        if origin is dict and isinstance(value, dict):
            val_type = get_args(target_type)[1] if len(get_args(target_type)) > 1 else Any
            return {
                k: self._parse_value(val_type, v, numap, k)
                for k, v in value.items()
            }

        return value
"""
@dataclass
class FilesetParser2(BaseParser2): entity_cls: ClassVar[type[Entity]] = Fileset

@dataclass
class DomParser2(ValueExtractor):
    ec: ErrorCollector
    entity_cls = Domain
    def parse(self, name, data, numap:Numap) -> Domain:
        with self.ec.path(name):
            raw_resolvers = self.req_list(data, ["resolvers"])
            raw_prompts = self.req_list(data, ["prompts"])
            resolvers = [ResolverParser2(self.ec).parse("", r, numap)for r in raw_resolvers]
            prompts = self._build_prompts(raw_prompts, numap)
            return Domain(name=name, prompts=prompts, resolvers=resolvers)
            
    def _build_prompts(self, dicts: list[dict], numap) -> list[Prompt]:
        return [PromptParser2(self.ec).parse("", d, numap) for d in dicts]

@dataclass
class PromptParser2(BaseParser2): entity_cls: ClassVar[type[Entity]] = Prompt

@dataclass
class FilelistParser2(ValueExtractor):
    collector: ErrorCollector
    entity_cls = Filelist

    def parse(self, name, data, numap:Numap) -> Filelist:
        files = [self._build_file(f) for f in data]
        return Filelist(files=files)

    def _build_file(self, data: Any) -> File:
        if isinstance(data, dict):
            filename = self.req_str(data, ["file"])
            trunc_spec = self._build_truncation_spec(data)
            return File(name=filename, truncation_spec=trunc_spec)
        return File(name=self.req_str({"file": data}, ["file"]))

    def _build_truncation_spec(self, data: dict[str, Any]) -> TruncationSpec | None:
        tail_lines = self.opt_int(data, ["tail_lines"], [])
        from_line = self.opt_str(data, ["from_line"], [])
        up_to = self.opt_str(data, ["up_to"], [])

        if tail_lines and (from_line or up_to):
            self.collector.add_complaint("TruncationSpec conflict: tail_lines cannot be combined with from_line or up_to")
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
class RenderParser2(ValueExtractor):
    collector: ErrorCollector
    entity_cls: type = Render

    def parse(self, name: str, data: dict, numap: Numap) -> Render:
        template = self.opt_str(data, ["template"], self.entity_cls.template)
        inherit_base = self.opt_bool(data, ["inherit_base"], self.entity_cls.inherit_base)
        inherit_domain = self.opt_bool(data, ["inherit_domain"], self.entity_cls.inherit_domain)
        res_dicts = self.req_list(data, ["resolvers"])
        resolvers = [ResolverParser2(self.collector).parse("", data, numap) for data in res_dicts]
        return Render(
            template=template,
            resolvers=resolvers,
            inherit_base=inherit_base,
            inherit_domain=inherit_domain,
        )
@dataclass
class UIRenderParser2(RenderParser2): 
    collector: ErrorCollector
    entity_cls: type = UIRender
"""
#i need to make it deal with lists, dicts, anything it can encounter
@dataclass
class RenderParser2(BaseParser2): 
    entity_cls: ClassVar[type[Entity]] = Render

    def preprocess(self, data):
        return data

@dataclass
class UIRenderParser2(RenderParser2): entity_cls: ClassVar[type[Entity]] = UIRender
"""
@dataclass
class ResolverParser2(ValueExtractor):
    collector: ErrorCollector
    entity_cls = Resolver

    def parse(self, name, data, numap:Numap) -> Resolver | None:
        res_type = self.req_str(data, ["type"])
        anchor = self.req_str(data, ["anchor"])

        if res_type == "multi-document-retrieval": return MdResParser(self.collector).parse("", data, numap)
        if res_type == "repo_content": return RepoContentResParser(self.collector).parse("", data, numap)
        if res_type == "repo-manifest": return RepoManifestResParser(self.collector).parse("", data, numap)
        if res_type in ("kb_info", "kb_state"): return KBStateResolver(anchor)
        raise ConfigAssembly(f"Unsupported resolver type: '{res_type}'")

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
class RepoManifestResParser(BaseParser2): entity_cls: ClassVar[type[Entity]] = ManifestResolver