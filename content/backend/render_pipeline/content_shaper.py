from backend.stdlib import re
from backend.core import entities as e


class PromptContentShaper:

    _TOKEN_RE = re.compile(r'§([a-z_]+),\s*([a-z_]+)(?:,\s*([^§]+?))?(?:,\s*([^§]+?))?§')

    def process(self, content: str, file: e.File | None) -> str:
        if file is not None and file.name and file.name.endswith(".output-template"):
            content = self._substitute_placeholders(content)
        truncation_spec = file.truncation_spec if file is not None else None
        return self.apply_truncation(content, truncation_spec)

    def _substitute_placeholders(self, content: str) -> str:
        def _repl(m: re.Match) -> str:
            verb = m.group(1)
            op = m.group(2)
            arg1 = m.group(3).strip() if m.group(3) else None
            arg2 = m.group(4).strip() if m.group(4) else None

            if op == "open":
                if arg1 is None:
                    return m.group(0)
                return e.Delims.open(verb, arg1)
            elif op == "close":
                return e.Delims.close(verb)
            elif op == "selfclose":
                if arg1 is None:
                    return m.group(0)
                loc = int(arg2) if arg2 is not None else None
                return e.Delims.self_close(verb, arg1, loc=loc)
            return m.group(0)

        return self._TOKEN_RE.sub(_repl, content)

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