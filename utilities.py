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

class FilesetMapProtocol(Protocol):
    def get(self, key: str) -> FileSet | None: ...
    def merge(self, other: FilesetMapProtocol) -> FilesetMapProtocol: ...

class ConfigTranslatorProtocol(Protocol):
    def set_collector(self, collector: ErrorCollector) -> None: ...
    def get_collector(self) -> ErrorCollector: ...
    def extract_filesets(
        self, doms_cfg_dict: dict[str, Any]
    ) -> FilesetMapProtocol: ...
    def set_filesetmap(self, filesetmap: FilesetMapProtocol) -> None: ...
    def extract_domains(
        self,
        doms_cfg_dict: dict[str, Any],
    ) -> list[Domain]: ...
    def process_sys_cfg(
        self, sys_cfg: dict[str, Any]
    ) -> tuple[Render, KbSpec]: ...
    def get_resolvers(
        self,
        shared_domains_data: dict[str, Any],
    ) -> list[Resolver]: ...


class RuntimeConfigAssembler:
    def __init__(
        self,
        translator: ConfigTranslatorProtocol | None = None,
        collector: ErrorCollector | None = None,
    ) -> None:
        self.collector = collector or ErrorCollector()
        self.translator = translator or ConfigTranslator()
        self.translator.set_collector(self.collector)

    def assemble(self, pud_cfg: dict, sys_cfg: dict, shared_cfg: dict) -> RuntimeConfig:
        shared_map = self.translator.extract_filesets(shared_cfg)
        pud_map = self.translator.extract_filesets(pud_cfg)
        merged_map = shared_map.merge(pud_map)
        self.translator.set_filesetmap(merged_map)

        base_resolvers = self.translator.get_resolvers(shared_cfg)
        shared_domains = self.translator.extract_domains(shared_cfg)
        pud_domains = self.translator.extract_domains(pud_cfg)
        ui_render, kb_spec = self.translator.process_sys_cfg(sys_cfg)

        button_map = self._create_btn_map(kb_spec, shared_domains, pud_domains)

        self.collector.raise_if_any()

        keyboard = Keyboard(button_map=button_map, selected_key=None)

        return RuntimeConfig(
            keyboard=keyboard,
            ui_render=ui_render,
            base_resolvers=base_resolvers,
        )

    def _create_btn_map(
        self,
        kb_spec: KbSpec,
        shared_domains: list[Domain],
        pud_domains: list[Domain],
    ) -> dict[str, Button]:
        btn_map: dict[str, Button] = {}

        shr_dom_btns = list(kb_spec.shared_domain_keys)
        if len(shared_domains) > len(shr_dom_btns):
            self.collector.add_complaint("More shared domains configured than available key slots")
        for key_char, dom in zip(shr_dom_btns, shared_domains):
            btn_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=dom)
        for key_char in shr_dom_btns[len(shared_domains):]:
            btn_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=None)

        pud_dom_btns = list(kb_spec.pud_domain_keys)
        if len(pud_domains) > len(pud_dom_btns):
            self.collector.add_complaint("More PUD domains configured than available key slots")
        for key_char, dom in zip(pud_dom_btns, pud_domains):
            btn_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=dom)
        for key_char in pud_dom_btns[len(pud_domains):]:
            btn_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=None)

        for key_char in kb_spec.prompt_keys:
            btn_map[key_char] = Button(type=Button.TYPE_PROMPT, key=key_char, inhabitant=None)

        return btn_map