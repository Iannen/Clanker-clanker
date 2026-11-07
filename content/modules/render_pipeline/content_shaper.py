from stdlib import re
from core import entities as e

class SystemKeys:
    DELIM = "§"

class PromptContentShaper:

    def apply_truncation(self, content: str, spec: e.TruncationSpec | None) -> str:
        if spec is None:
            return content

        lines = content.splitlines()

        if spec.from_line:
            idx = self._find_match_idx(lines, spec.from_line)
            if idx is not None:
                lines = lines[idx:]

        if spec.up_to:
            idx = self._find_match_idx(lines, spec.up_to)
            if idx is not None:
                lines = lines[:idx]

        if spec.tail_lines is not None and len(lines) > spec.tail_lines:
            return "**truncated**\n" + "\n".join(lines[-spec.tail_lines:])

        return "\n".join(lines)

    def _find_match_idx(self, lines: list[str], pattern_str: str) -> int | None:
        try:
            pattern = re.compile(pattern_str)
        except re.error:
            return None

        for idx, line in enumerate(lines):
            if pattern.search(line):
                return idx
        return None

    def hydrate(self, template: str, replacements: dict[str, str]) -> str:
        pattern = re.compile(rf"{SystemKeys.DELIM}([^{SystemKeys.DELIM}]+){SystemKeys.DELIM}")
        return pattern.sub(
            lambda m: replacements.get(m.group(1).strip(), m.group(0)),
            template
        )