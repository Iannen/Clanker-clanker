from backend.stdlib import re
from backend.core import entities as e


class PromptContentShaper:

    def process(self, content: str, file: e.File | None) -> str:
        if file is not None and file.name and file.name.endswith(".output-template"):
            content = self._substitute_placeholders(content)
        truncation_spec = file.truncation_spec if file is not None else None
        return self.apply_truncation(content, truncation_spec)

    def _substitute_placeholders(self, content: str) -> str:
        for pair in e.Delims.__dict__.values():
            if isinstance(pair, tuple) and len(pair) == 2:
                content = content.replace(pair[0], pair[1])
        return content

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