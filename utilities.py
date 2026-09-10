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

    def apply_truncation(self, content: str, spec: TruncationSpec | None) -> str:
        if spec is None:
            return content

        if spec.type == TruncationSpec.TYPE_TAIL:
            if spec.tail_lines is not None:
                lines = content.splitlines()
                if len(lines) > spec.tail_lines:
                    return "**truncated**\n" + "\n".join(lines[-spec.tail_lines:])
            return content

        if spec.type == TruncationSpec.TYPE_REGEX_RANGE:
            lines = content.splitlines()

            if spec.from_line is not None:
                try:
                    pattern = re.compile(spec.from_line)
                except re.error as e:
                    raise ConfigAssemblyFailure(f"Invalid regex for 'from_line': '{spec.from_line}' ({e})")
                
                match_idx = None
                for idx, line in enumerate(lines):
                    if pattern.search(line):
                        match_idx = idx
                        break

                if match_idx is None:
                    raise ConfigAssemblyFailure(
                        f"Truncation pattern 'from_line' ({spec.from_line}) matched no lines in content"
                    )
                lines = lines[match_idx:]

            if spec.up_to is not None:
                try:
                    pattern = re.compile(spec.up_to)
                except re.error as e:
                    raise ConfigAssemblyFailure(f"Invalid regex for 'up_to': '{spec.up_to}' ({e})")

                match_idx = None
                for idx, line in enumerate(lines):
                    if pattern.search(line):
                        match_idx = idx
                        break

                if match_idx is None:
                    raise ConfigAssemblyFailure(
                        f"Truncation pattern 'up_to' ({spec.up_to}) matched no lines in content"
                    )
                lines = lines[:match_idx]

            return "\n".join(lines)

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


class RuntimeConfigBuilder:
    def __init__(
        self,
        pud_cfg: dict,
        sys_cfg: dict,
        shared_cfg: dict,
        collector: ErrorCollector
    ) -> None:
        self.pud_cfg = pud_cfg
        self.sys_cfg = sys_cfg
        self.shared_cfg = shared_cfg
        self.collector = collector
        self.translator = ConfigTranslator(collector)

    def build(self) -> RuntimeConfig:
        self._handle_named_filesets()
        base_resolvers = self.translator.get_resolvers(self.shared_cfg)
        self._handle_domains()
        ui_render, button_map = self._handle_buttons()
        
        #self.collector.raise_if_any()

        return RuntimeConfig(
            keyboard=Keyboard(button_map=button_map, selected_key=None),
            ui_render=ui_render,
            base_resolvers=base_resolvers,
        )

    def _handle_named_filesets(self) -> None:
        shared_map = self.translator.extract_filesets(self.shared_cfg)
        pud_map = self.translator.extract_filesets(self.pud_cfg)
        merged_map = shared_map.merge(pud_map)
        self.translator.set_filesetmap(merged_map)

    def _handle_domains(self) -> None:
        self.shared_domains = self.translator.extract_domains(self.shared_cfg)
        self.pud_domains = self.translator.extract_domains(self.pud_cfg)

    def _handle_buttons(self) -> tuple[Render, dict[str, Button]]:
        ui_render, self.kb_spec = self.translator.process_sys_cfg(self.sys_cfg)
        button_map = self._create_btn_map()
        return ui_render, button_map

    def _create_btn_map(self) -> dict[str, Button]:
        btn_map: dict[str, Button] = {}
        if not self.kb_spec:
            return btn_map

        shr_dom_btns = list(self.kb_spec.shared_domain_keys)
        if len(self.shared_domains) > len(shr_dom_btns):
            self.collector.add_complaint("More shared domains configured than available key slots")
        for key_char, dom in zip(shr_dom_btns, self.shared_domains):
            btn_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=dom)
        for key_char in shr_dom_btns[len(self.shared_domains):]:
            btn_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=None)

        pud_dom_btns = list(self.kb_spec.pud_domain_keys)
        if len(self.pud_domains) > len(pud_dom_btns):
            self.collector.add_complaint("More PUD domains configured than available key slots")
        for key_char, dom in zip(pud_dom_btns, self.pud_domains):
            btn_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=dom)
        for key_char in pud_dom_btns[len(self.pud_domains):]:
            btn_map[key_char] = Button(type=Button.TYPE_DOMAIN, key=key_char, inhabitant=None)

        for key_char in self.kb_spec.prompt_keys:
            btn_map[key_char] = Button(type=Button.TYPE_PROMPT, key=key_char, inhabitant=None)

        return btn_map