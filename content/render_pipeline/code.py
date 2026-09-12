from __future__ import annotations
import re
from contracts.render_system_contract import ContentShaper
from models import ConfigAssemblyFailure, TruncationSpec

class DefaultContentShaper(ContentShaper):
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