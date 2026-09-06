from __future__ import annotations
import copy
import re
from typing import Any
from ruamel.yaml import YAML
from models import *
from config_dtos import *

class DefaultContentShaper:
    def normalize_file_spec(self, item: str | dict) -> tuple[str, int | None]:
        if isinstance(item, dict):
            return item.get("file", ""), item.get("tail_lines")
        return item, None

    def trim_to_tail(self, content: str, tail_lines: int | None) -> str:
        if tail_lines is not None:
            lines = content.splitlines()
            if len(lines) > tail_lines:
                return "**truncated**\n" + "\n".join(lines[-tail_lines:])
        return content

    def hydrate(self, delim: str, template: str, replacements: dict[str, str]) -> str:
        pattern = re.compile(rf"{delim}([^{delim}]+){delim}")
        return pattern.sub(
            lambda m: replacements.get(m.group(1).strip(), m.group(0)),
            template
        )

class ConfigValidator:
    def __init__(self) -> None:
        self.yaml = YAML()

    def assert_no_quotes(self, raw_text: str, filepath: str = "") -> None:
        violations = []
        for idx, line in enumerate(raw_text.splitlines(), start=1):
            if "'" in line:
                parts = line.split("'")
                if len(parts) == 3:
                    content = parts[1]
                    is_digits = content.isdigit()
                    has_double_quote = '"' in content
                    if not (is_digits or has_double_quote):
                        violations.append(f"    line {idx} has quotes: {line}")
                else:
                    violations.append(f"    line {idx} has quotes: {line}")
            elif '"' in line:
                violations.append(f"    line {idx} has quotes: {line}")
                
        if violations:
            msg_parts = [filepath] if filepath else []
            msg_parts.extend(violations)
            raise ConfigViolations("\n".join(msg_parts))

    def get_as_dict(self, raw_text: str) -> dict:
        return self.yaml.load(raw_text) or {}

    def assert_filesets_not_neglected(self, cfg_frag: dict, filepath: str = "") -> None:
        violations = []

        def _make_key(includes: list, excludes: list) -> str:
            inc_str = ",".join(sorted(str(x) for x in includes))
            exc_str = ",".join(sorted(str(x) for x in excludes))
            return f"inc:[{inc_str}]|exc:[{exc_str}]"

        named_fileset_map: dict[str, str] = {}
        for set_name, set_def in cfg_frag.get("filesets", {}).items():
            if isinstance(set_def, dict):
                inc = set_def.get("includes", [])
                exc = set_def.get("excludes", [])
                key = _make_key(inc, exc)
                named_fileset_map[key] = set_name

        inline_filesets: list[tuple[str, str | None, str | None]] = []
        for domain in cfg_frag.get("domains", []):
            if not isinstance(domain, dict):
                continue
            domain_name = domain.get("name")
            for resolver in domain.get("resolvers", []):
                if not isinstance(resolver, dict):
                    continue
                if "fileset" in resolver or "varname" in resolver:
                    continue
                inc = resolver.get("includes", [])
                exc = resolver.get("excludes", [])
                if inc or exc:
                    key = _make_key(inc, exc)
                    inline_filesets.append((key, domain_name, None))

            for prompt in domain.get("prompts", []):
                if not isinstance(prompt, dict):
                    continue
                prompt_name = prompt.get("name")
                render = prompt.get("render")
                if not isinstance(render, dict):
                    continue
                for resolver in render.get("resolvers", []):
                    if not isinstance(resolver, dict):
                        continue
                    if "fileset" in resolver or "varname" in resolver:
                        continue
                    inc = resolver.get("includes", [])
                    exc = resolver.get("excludes", [])
                    if inc or exc:
                        key = _make_key(inc, exc)
                        inline_filesets.append((key, domain_name, prompt_name))

        for string_key, domain, render in inline_filesets:
            if string_key in named_fileset_map:
                violations.append(
                    f"    domain '{domain}' render '{render}': use named fileset '{named_fileset_map[string_key]}'"
                )

        if violations:
            msg_parts = [filepath] if filepath else []
            msg_parts.extend(violations)
            raise ConfigViolations("\n".join(msg_parts))

class RuntimeConfigAssembler:
    def __init__(self) -> None:
        self.dto_fact = DTOFactory()

    def assemble(self, config_data: dict, kb_def_data: dict, shared_domains_data: dict) -> RuntimeConfig:
        sys_dto = self.dto_fact.sys_cfg(kb_def_data)

        button_map = self._build_button_map(sys_dto)

        named_filesets = self._build_named_filesets(
            shared_domains_data.get("filesets", {}),
            config_data.get("filesets", {})
        )

        shared_domains = self._build_domains(shared_domains_data.get("domains", []), named_filesets)
        self._populate_domain_buttons(button_map, sys_dto.shared_domain_keys, shared_domains)

        pud_domains = self._build_domains(config_data.get("domains", []), named_filesets)
        self._populate_domain_buttons(button_map, sys_dto.pud_domain_keys, pud_domains)

        base_render = self._build_render(sys_dto.ui_render_data, named_filesets)

        base_resolvers = self._build_resolvers(
            shared_domains_data.get("base_resolvers", []), 
            named_filesets
        )

        keyboard = Keyboard(
            button_map=button_map,
            selected_key=None
        )

        return RuntimeConfig(
            keyboard=keyboard,
            ui_render=base_render,
            base_resolvers=base_resolvers
        )

    def _build_named_filesets(
        self, shared_sets: dict[str, Any], pud_sets: dict[str, Any]
    ) -> dict[str, FileSet]:
        result = {}
        for k, v in shared_sets.items():
            result[k] = self._build_fileset(v)
        for k, v in pud_sets.items():
            result[k] = self._build_fileset(v)
        return result

    def _build_resolvers(self, res_dicts: list[dict], named_filesets: dict[str, FileSet]) -> list[Resolver]:
        resolvers = []
        for res_dict in res_dicts:
            dto = self.dto_fact.resolver_cfg(res_dict)
            resolvers.append(self._build_resolver_from_dto(dto, named_filesets))
        return resolvers

    def _populate_domain_buttons(
        self, button_map: dict[str, Button], keys: str, domains: list[Domain]
    ) -> None:
        for prim_char, domain in zip(keys, domains):
            button_map[prim_char].inhabitant = domain

    def _build_fileset(self, data: dict[str, Any] | None) -> FileSet:
        return FileSet(
            includes=data.get("includes", []),
            excludes=data.get("excludes", []),
        )

    def _build_file(self, raw_item: str | dict, is_full_path: bool = False) -> File:
        if isinstance(raw_item, dict):
            name = raw_item.get("file", raw_item.get("name", ""))
            tail_lines = raw_item.get("tail_lines")
            full_path = raw_item.get("full_path_from_pud", is_full_path)
            trunc_spec = TruncationSpec(tail_lines=tail_lines) if tail_lines is not None else None
            return File(name=name, full_path_from_pud=full_path, truncation_spec=trunc_spec)
        return File(name=str(raw_item), full_path_from_pud=is_full_path)

    def _build_resolver_from_dto(self, dto: ResolverDTO, named_filesets: dict[str, FileSet]) -> Resolver:
        if dto.type in ("multi-document-retrieval", "full-path-file-retrieval"):
            is_full_path = dto.type == "full-path-file-retrieval"
            raw_files = dto.files or []
            file_objs = [self._build_file(f, is_full_path=is_full_path) for f in raw_files]
            return MultiDocResolver(
                anchor=dto.anchor,
                files=Filelist(files=file_objs)
            )

        if dto.type == "repo_content":
            if isinstance(dto.fileset, str):
                fileset_obj = named_filesets.get(dto.fileset)
            else:
                fileset_obj = self._build_fileset(dto.fileset)
            return RepoContentResolver(
                anchor=dto.anchor,
                fileset=fileset_obj
            )

        if dto.type == "repo-manifest":
            if isinstance(dto.pud_fileset, str):
                pud_fileset_obj = named_filesets.get(dto.pud_fileset)
            else:
                pud_fileset_obj = self._build_fileset(dto.pud_fileset)

            if isinstance(dto.shared_fileset, str):
                shared_fileset_obj = named_filesets.get(dto.shared_fileset)
            elif isinstance(dto.shared_fileset, dict):
                shared_fileset_obj = self._build_fileset(dto.shared_fileset)
            else:
                shared_fileset_obj = None

            return ManifestResolver(
                anchor=dto.anchor,
                pud_fileset=pud_fileset_obj,
                shared_fileset=shared_fileset_obj
            )

        if dto.type in ("kb_info", "kb_state"):
            return KBStateResolver(anchor=dto.anchor)

        raise ValueError(f"Unsupported resolver type: {dto.type}")

    def _build_render(self, data: dict[str, Any], named_filesets: dict[str, FileSet]) -> Render:
        dto = self.dto_fact.render_cfg(data)
        resolvers = self._build_resolvers(dto.resolver_dicts, named_filesets)
        return Render(
            template=dto.template,
            resolvers=resolvers,
            inherit_base=dto.inherit_base,
            inherit_domain=dto.inherit_domain,
        )

    def _build_prompts(self, dicts: list[dict[str, Any]], named_filesets: dict[str, FileSet]) -> list[Prompt]:
        prompts = []
        for d in dicts:
            prdto = self.dto_fact.prompt_cfg(d)
            render = self._build_render(prdto.render, named_filesets)
            prompts.append(Prompt(name=prdto.name, render=render))
        return prompts

    def _build_domains(self, dicts: list[dict[str, Any]], named_filesets: dict[str, FileSet]) -> list[Domain]:
        domains = []
        for d in dicts:
            dto = self.dto_fact.domain_cfg(d)
            resolvers = self._build_resolvers(dto.resolvers, named_filesets)
            prompts = self._build_prompts(dto.prompts, named_filesets)
            domains.append(
                Domain(
                    name=dto.name,
                    prompts=prompts,
                    resolvers=resolvers
                )
            )
        return domains

    def _build_button_map(self, sys_dto: SystemConfigDataDTO) -> dict[str, Button]:
        button_map = {}

        for key_char in sys_dto.shared_domain_keys:
            button_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=None)

        for key_char in sys_dto.pud_domain_keys:
            button_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=None)

        for key_char in sys_dto.prompt_keys:
            button_map[key_char] = Button(type=Button.TYPE_PROMPT, key=key_char, inhabitant=None)

        return button_map