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
    def __init__(self, translator: ConfigTranslator | None = None) -> None:
        self.translator = translator or ConfigTranslator()

    def assemble(self, config_data: dict, kb_def_data: dict, shared_domains_data: dict) -> RuntimeConfig:
        fileset_map = self._get_filesetmap(shared_domains_data, config_data)
        shared_domains = self.translator.extract_domains(shared_domains_data, fileset_map)
        pud_domains = self.translator.extract_domains(config_data, fileset_map)
        ui_render, kb_spec = self.translator.process_sys_cfg(kb_def_data)

        button_map = self._create_btn_map(kb_spec, shared_domains, pud_domains)

        base_resolvers = [
            self.translator._build_resolver_from_dto(self.translator.dto_fact.resolver_cfg(r), fileset_map)
            for r in shared_domains_data.get("base_resolvers", [])
        ]

        keyboard = Keyboard(button_map=button_map, selected_key=None)

        return RuntimeConfig(
            keyboard=keyboard,
            ui_render=ui_render,
            base_resolvers=base_resolvers,
        )

    def _get_filesetmap(self, sharedcfg: dict, pudcfg: dict) -> dict[str, FileSet]:
        shared_sets = self.translator.extract_filesets(sharedcfg)
        pud_sets = self.translator.extract_filesets(pudcfg)
        merged = dict(shared_sets)
        merged.update(pud_sets)
        return merged

    def _create_btn_map(self, kb_spec: KbSpec, shared_domains: list[Domain], pud_domains: list[Domain]) -> dict[str, Button]:
        btn_map: dict[str, Button] = {}

        shr_dom_btns = list(kb_spec.shared_domain_keys)
        if len(shared_domains) > len(shr_dom_btns):
            raise ConfigAssemblyFailure("More shared domains configured than available key slots")
        for key_char, dom in zip(shr_dom_btns, shared_domains):
            btn_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=dom)
        for key_char in shr_dom_btns[len(shared_domains):]:
            btn_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=None)

        pud_dom_btns = list(kb_spec.pud_domain_keys)
        if len(pud_domains) > len(pud_dom_btns):
            raise ConfigAssemblyFailure("More PUD domains configured than available key slots")
        for key_char, dom in zip(pud_dom_btns, pud_domains):
            btn_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=dom)
        for key_char in pud_dom_btns[len(pud_domains):]:
            btn_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=None)

        for key_char in kb_spec.prompt_keys:
            btn_map[key_char] = Button(type=Button.TYPE_PROMPT, key=key_char, inhabitant=None)

        return btn_map