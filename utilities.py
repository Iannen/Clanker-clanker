from __future__ import annotations
import copy
import re
from typing import Any
from ruamel.yaml import YAML
from clanker import ConfigViolations
from models import (
    Button,
    Config,
    Domain,
    Keyboard,
    Prompt,
    Render,
    Resolver,
    RuntimeConfig,
)

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
                if len(parts) == 3:  # exactly one pair (start, content, end)
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
    def assemble(self, config_data: dict, kb_def_data: dict, shared_domains_data: dict) -> RuntimeConfig:
        sets_map = {**shared_domains_data.get("filesets", {}), **config_data.get("filesets", {})}

        shared_domains = shared_domains_data.get("domains", [])
        user_domains = config_data.get("domains", [])
        combined_domains = shared_domains + user_domains

        domains = [self._build_domain(d, sets_map) for d in combined_domains]

        kb_def = kb_def_data.get("kb_def", {})
        button_map = self._build_button_map(kb_def.get("rows", {}))

        domain_keys = kb_def.get("rows", {}).get("domain_row", [])
        for prim_char, domain_obj in zip(domain_keys, domains):
            button_map[prim_char].inhabitant = domain_obj

        base_render = self._build_render(kb_def.get("render", {}), sets_map)
        base_resolvers = [self._build_resolver(r, sets_map) for r in shared_domains_data.get("base_resolvers", [])]

        keyboard = Keyboard(
            button_map=button_map,
            selected_key=None
        )

        return RuntimeConfig(
            keyboard=keyboard,
            ui_render=base_render,
            base_resolvers=base_resolvers
        )

    def _build_resolver(self, data: dict, sets_map: dict[str, Any]) -> Resolver:
        res_copy = copy.deepcopy(data)
        res_id = res_copy.pop("id")
        res_type = Resolver.Type(res_copy.pop("type"))

        pointer_key = res_copy.pop("fileset", None)
        if pointer_key and pointer_key in sets_map:
            set_val = sets_map[pointer_key]
            if isinstance(set_val, dict):
                res_copy.update(copy.deepcopy(set_val))

        for fs_key in ("pud_fileset", "shared_fileset"):
            if fs_key in res_copy and isinstance(res_copy[fs_key], str):
                target_alias = res_copy[fs_key]
                if target_alias in sets_map:
                    res_copy[fs_key] = copy.deepcopy(sets_map[target_alias])

        return Resolver(id=res_id, type=res_type, payload=res_copy)

    def _build_render(self, data: dict, sets_map: dict[str, Any]) -> Render:
        resolvers = [self._build_resolver(r, sets_map) for r in data.get("resolvers", [])]
        return Render(
            template=data.get("template", "prompt_template"),
            resolvers=resolvers,
            inherit_base=data.get("inherit_base", True),
            inherit_domain=data.get("inherit_domain", True)
        )

    def _build_prompt(self, data: dict, sets_map: dict[str, Any]) -> Prompt:
        return Prompt(
            name=data["name"],
            render=self._build_render(data.get("render", {}), sets_map)
        )

    def _build_domain(self, data: dict, sets_map: dict[str, Any]) -> Domain:
        prompts = [self._build_prompt(p, sets_map) for p in data.get("prompts", [])]
        resolvers = [self._build_resolver(r, sets_map) for r in data.get("resolvers", [])]
        return Domain(
            name=data["name"],
            prompts=prompts,
            resolvers=resolvers
        )

    def _build_button_map(self, rows_data: dict) -> dict[str, Button]:
        button_map = {}
        for row_key, row_keys in rows_data.items():
            for key_char in row_keys:
                btn = Button(
                    type=row_key,
                    key=key_char,
                    inhabitant=None
                )
                button_map[key_char] = btn
        return button_map