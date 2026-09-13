# From this file we extract the workers, one at a time, in detached fashion, without altering or deleting anything from here
# Then, when they are all ready, we 'flip the switch' upstream ,and the below becomes dead code, slated for deletion
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from app.deps.ingestion import Report
from asset_ingestion.commons.kb_spec import KbSpec
from asset_ingestion.commons.fileset_map import FilesetMap
from asset_ingestion.commons.value_extractor import ValueExtractor
from app.models import (
    Domain,
    Prompt,
    Render,
    File,
    Filelist,
    FileSet,
    Resolver,
    MultiDocResolver,
    RepoContentResolver,
    ManifestResolver,
    KBStateResolver,
    TruncationSpec,
    ConfigAssembly,
)
class ConfigTranslator:
    def __init__(self, collector: ErrorCollector) -> None:
        self.extractor = ValueExtractor()
        self.collector = collector
        self._filesetmap: FilesetMap | None = None

    def set_collector(self, collector: ErrorCollector) -> None:
        self.collector = collector

    def get_collector(self) -> ErrorCollector:
        return self.collector

    def set_filesetmap(self, filesetmap: FilesetMap) -> None:
        self._filesetmap = filesetmap

    def extract_filesets(
        self, doms_cfg_dict: dict[str, Any]
    ) -> FilesetMap:
        raw_filesets = self.extractor.req_dict(doms_cfg_dict, ["filesets"], default={})
        result = {}
        for k, v in raw_filesets.items():
            result[k] = self._build_fileset(v)
        return FilesetMap(data=result, collector=self.collector)

    def extract_domains(
        self,
        doms_cfg_dict: dict[str, Any],
    ) -> list[Domain]:
        raw_domains = self.extractor.req_list(doms_cfg_dict, ["domains"])
        domains = []
        for d in raw_domains:
            name = self.extractor.req_str(d, ["name"])
            raw_resolvers = self.extractor.req_list(d, ["resolvers"])
            raw_prompts = self.extractor.req_list(d, ["prompts"])

            resolvers = [self._build_resolver(r, self.collector) for r in raw_resolvers]
            prompts = self._build_prompts(raw_prompts, self.collector)
            domains.append(Domain(name=name, prompts=prompts, resolvers=resolvers))
        return domains

    def process_sys_cfg(
        self, sys_cfg: dict[str, Any]
    ) -> tuple[Render, KbSpec]:
        kb_spec = KbSpec(
            shared_domain_keys=self.extractor.req_str(sys_cfg, ["button_rows", "shared_domains_row"]),
            pud_domain_keys=self.extractor.req_str(sys_cfg, ["button_rows", "pud_domains_row"]),
            prompt_keys=self.extractor.req_str(sys_cfg, ["button_rows", "prompts_row"]),
        )
        ui_render_data = self.extractor.req_dict(sys_cfg, ["ui_render"])
        ui_render = self._build_render(ui_render_data, self.collector)
        return ui_render, kb_spec

    def get_resolvers(
        self,
        shared_domains_data: dict[str, Any],
    ) -> list[Resolver]:
        raw_resolvers = self.extractor.req_list(shared_domains_data, ["base_resolvers"], default=[])
        return [self._build_resolver(r, self.collector) for r in raw_resolvers]

    def _build_prompts(
        self,
        dicts: list[dict[str, Any]],
        collector: ErrorCollector,
    ) -> list[Prompt]:
        prompts = []
        for d in dicts:
            name = self.extractor.req_str(d, ["name"])
            render_dict = self.extractor.req_dict(d, ["render"], default={})
            render = self._build_render(render_dict, collector)
            prompts.append(Prompt(name=name, render=render))
        return prompts

    def _build_render(
        self,
        render_dict: dict[str, Any],
        collector: ErrorCollector,
    ) -> Render:
        template = self.extractor.req_str(render_dict, ["template"], Render.template)
        inherit_base = self.extractor.req_bool(render_dict, ["inherit_base"], Render.inherit_base)
        inherit_domain = self.extractor.req_bool(render_dict, ["inherit_domain"], Render.inherit_domain)
        raw_resolvers = self.extractor.req_list(render_dict, ["resolvers"])
        resolvers = [self._build_resolver(r, collector) for r in raw_resolvers]
        return Render(
            template=template,
            resolvers=resolvers,
            inherit_base=inherit_base,
            inherit_domain=inherit_domain,
        )

    def _build_fileset(self, raw_data: Any) -> FileSet:
        includes = self.extractor.req_list(raw_data, ["includes"])
        excludes = self.extractor.req_list(raw_data, ["excludes"], default=[])
        return FileSet(includes=includes, excludes=excludes)

    def _build_truncation_spec(self, data: dict[str, Any]) -> TruncationSpec | None:
        has_tail = "tail_lines" in data
        has_from = "from_line" in data
        has_upto = "up_to" in data

        if has_tail and (has_from or has_upto):
            self.collector.add_complaint(
                "TruncationSpec conflict: tail_lines cannot be combined with from_line or up_to"
            )
            return None

        if has_tail:
            tail_lines = self.extractor.req_int(data, ["tail_lines"], default=None)
            if tail_lines is None:
                self.collector.add_complaint("TruncationSpec error: tail_lines must be an integer")
                return None
            return TruncationSpec(type=TruncationSpec.TYPE_TAIL, tail_lines=tail_lines)

        if has_from or has_upto:
            from_line = self.extractor.req_str(data, ["from_line"], default=None) if has_from else None
            up_to = self.extractor.req_str(data, ["up_to"], default=None) if has_upto else None
            return TruncationSpec(
                type=TruncationSpec.TYPE_REGEX_RANGE,
                from_line=from_line,
                up_to=up_to,
            )

        trunc_keys = {"tail_lines", "from_line", "up_to"}
        if any(k in data for k in trunc_keys):
            self.collector.add_complaint("TruncationSpec error: invalid truncation specification")
            return None

        return None

    def _build_file(self, data: Any) -> File:
        if isinstance(data, dict):
            filename = self.extractor.req_str(data, ["file"])
            trunc_spec = self._build_truncation_spec(data)
            return File(name=filename, truncation_spec=trunc_spec)
        return File(name=self.extractor.req_str({"file": data}, ["file"]))

    def _build_resolver(
        self,
        data: dict[str, Any],
        collector: ErrorCollector,
    ) -> Resolver:
        res_type = self.extractor.req_str(data, ["type"])
        anchor = self.extractor.req_str(data, ["id"])

        if res_type == "multi-document-retrieval":
            raw_files = self.extractor.req_list(data, ["files"], default=[])
            file_objs = [self._build_file(f) for f in raw_files]
            return MultiDocResolver(anchor=anchor, files=Filelist(files=file_objs))

        if res_type == "repo_content":
            if "fileset" in data:
                fileset_val = self.extractor.req_str_or_dict(data, ["fileset"])
            else:
                fileset_val = {
                    "includes": self.extractor.req_list(data, ["includes"]),
                    "excludes": self.extractor.req_list(data, ["excludes"], default=[]),
                }

            if isinstance(fileset_val, str):
                fileset_obj = self._filesetmap.get(fileset_val) if self._filesetmap else None
            else:
                fileset_obj = self._build_fileset(fileset_val)
            return RepoContentResolver(anchor=anchor, fileset=fileset_obj or FileSet(includes=[], excludes=[]))

        if res_type == "repo-manifest":
            if "pud_fileset" not in data and "shared_fileset" not in data:
                raise ConfigAssembly(
                    f"Manifest resolver '{anchor}' must specify at least 'pud_fileset' or 'shared_fileset'"
                )

            pud_val = self.extractor.req_str_or_dict(data, ["pud_fileset"], default={})
            shared_val = self.extractor.req_str_or_dict(data, ["shared_fileset"], default={})

            if isinstance(pud_val, str):
                pud_fileset_obj = self._filesetmap.get(pud_val) if self._filesetmap else None
            else:
                pud_fileset_obj = self._build_fileset(pud_val) if pud_val else None

            if isinstance(shared_val, str):
                shared_fileset_obj = self._filesetmap.get(shared_val) if self._filesetmap else None
            elif isinstance(shared_val, dict) and shared_val:
                shared_fileset_obj = self._build_fileset(shared_val)
            else:
                shared_fileset_obj = None

            return ManifestResolver(
                anchor=anchor,
                pud_fileset=pud_fileset_obj or FileSet(includes=[], excludes=[]),
                shared_fileset=shared_fileset_obj,
            )

        if res_type in ("kb_info", "kb_state"):
            return KBStateResolver(anchor=anchor)

        raise ConfigAssembly(f"Unsupported resolver type: '{res_type}'")


from dataclasses import dataclass
from asset_ingestion.commons.error_collector import ErrorCollector
from asset_ingestion.translation_system.config_dtos import ConfigTranslator
from app.models import Button, RuntimeConfig, Keyboard

@dataclass
class DomainOverflow:
    sys_cfg_name: str
    row_keys: str
    domain_names: list[str]
    cfg_filename: str
    overflow_count: int

    def get_msg(self) -> str:
        overflowing = ", ".join(self.domain_names[-self.overflow_count:])
        return (
            f"Domain overflow in '{self.cfg_filename}' ({self.sys_cfg_name}): "
            f"{self.overflow_count} domain(s) overflowed key slots '{self.row_keys}'. "
            f"Excess domains: [{overflowing}]"
        )

class RuntimeConfigAssembler:
    def assemble(self, sys_cfg: dict, pud_cfg: dict, shared_cfg: dict) -> tuple[Report, RuntimeConfig]:
        collector = ErrorCollector()
        ctx = Ctx(sys_cfg, pud_cfg, shared_cfg, collector, ConfigTranslator(collector))

        self._handle_named_filesets(ctx)
        base_resolvers = ctx.translator.get_resolvers(ctx.shared_cfg)
        self._handle_domains(ctx)
        ui_render, button_map = self._handle_buttons(ctx)

        return ctx.collector, RuntimeConfig(
            keyboard=Keyboard(button_map=button_map, selected_key=None),
            ui_render=ui_render,
            base_resolvers=base_resolvers,
        )

    def _handle_named_filesets(self, ctx: Ctx) -> None:
        shared_map = ctx.translator.extract_filesets(ctx.shared_cfg)
        pud_map = ctx.translator.extract_filesets(ctx.pud_cfg)
        merged_map = shared_map.merge(pud_map)
        ctx.translator.set_filesetmap(merged_map)

    def _handle_domains(self, ctx: Ctx) -> None:
        ctx.shared_doms = ctx.translator.extract_domains(ctx.shared_cfg)
        ctx.pud_doms = ctx.translator.extract_domains(ctx.pud_cfg)

    def _handle_buttons(self, ctx: Ctx) -> tuple[Render, dict[str, Button]]:
        ui_render, ctx.kb_spec = ctx.translator.process_sys_cfg(ctx.sys_cfg)
        button_map = self._create_btn_map(ctx)
        return ui_render, button_map

    def _create_btn_map(self, ctx: Ctx) -> dict[str, Button]:
        btn_map: dict[str, Button] = {}
        if not ctx.kb_spec:
            return btn_map

        shr_dom_btns = list(ctx.kb_spec.shared_domain_keys)
        shared_doms = ctx.shared_doms or []
        if len(shared_doms) > len(shr_dom_btns):
            overflow_cnt = len(shared_doms) - len(shr_dom_btns)
            dof = DomainOverflow(
                sys_cfg_name="shared_domains_row",
                row_keys=ctx.kb_spec.shared_domain_keys,
                domain_names=[d.name for d in shared_doms],
                cfg_filename=CfgFragments.SHARED_CFG,
                overflow_count=overflow_cnt,
            )
            ctx.collector.record_domain_overflow(dof)

        for key_char, dom in zip(shr_dom_btns, shared_doms):
            btn_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=dom)
        for key_char in shr_dom_btns[len(shared_doms):]:
            btn_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=None)

        pud_dom_btns = list(ctx.kb_spec.pud_domain_keys)
        pud_doms = ctx.pud_doms or []
        if len(pud_doms) > len(pud_dom_btns):
            overflow_cnt = len(pud_doms) - len(pud_dom_btns)
            dof = DomainOverflow(
                sys_cfg_name="pud_domains_row",
                row_keys=ctx.kb_spec.pud_domain_keys,
                domain_names=[d.name for d in pud_doms],
                cfg_filename=CfgFragments.PUD_CFG,
                overflow_count=overflow_cnt,
            )
            ctx.collector.record_domain_overflow(dof)

        for key_char, dom in zip(pud_dom_btns, pud_doms):
            btn_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=dom)
        for key_char in pud_dom_btns[len(pud_doms):]:
            btn_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=None)

        for key_char in ctx.kb_spec.prompt_keys:
            btn_map[key_char] = Button(type=Button.TYPE_PROMPT, key=key_char, inhabitant=None)

        return btn_map

@dataclass
class Ctx:
    sys_cfg: dict
    pud_cfg: dict
    shared_cfg: dict
    collector: ErrorCollector
    translator: ConfigTranslator
    shared_doms: list[Domain] | None = None
    pud_doms: list[Domain] | None = None
    kb_spec: KbSpec | None = None