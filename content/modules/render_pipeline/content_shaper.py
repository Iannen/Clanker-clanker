from stdlib import re
from core import TruncationSpec, NewBtn
class SystemKeys:
    DELIM = "§"

class ContentShaper:
    
    def apply_truncation(self, content: str, spec: TruncationSpec | None) -> str:
        if spec is None:
            return content

        lines = content.splitlines()

        # Step 1: Cut everything above 'from_line'
        if spec.from_line:
            lines = self._cut_before_regex(lines, spec.from_line)

        # Step 2: Cut everything from 'up_to' onwards
        if spec.up_to:
            lines = self._cut_from_regex(lines, spec.up_to)

        # Step 3: Take last N lines
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


    def _cut_before_regex(self, lines: list[str], pattern_str: str) -> list[str]:
        idx = self._find_match_idx(lines, pattern_str)
        return lines if idx is None else lines[idx:]


    def _cut_from_regex(self, lines: list[str], pattern_str: str) -> list[str]:
        idx = self._find_match_idx(lines, pattern_str)
        return lines if idx is None else lines[:idx]

    def shape_button_replacements(self, btn: NewBtn, label: str, template: str) -> dict[str, str]:
        lines = template.strip("\n").splitlines()
        norm_label = label[:6].ljust(6)
        mapped_lines = [
            lines[0],
            lines[1],
            lines[2].replace(SystemKeys.DELIM, btn.key, 1),
            lines[3],
            lines[4].replace(SystemKeys.DELIM * 6, norm_label, 1),
        ]
        return {f"{btn.key}{idx}": line for idx, line in enumerate(mapped_lines)}

    def shape_action_result(self, msg: str, width: int = 117) -> str:
        return f"{msg:<{width}}"[:width]

    def hydrate(self, template: str, replacements: dict[str, str]) -> str:
        pattern = re.compile(rf"{SystemKeys.DELIM}([^{SystemKeys.DELIM}]+){SystemKeys.DELIM}")
        return pattern.sub(
            lambda m: replacements.get(m.group(1).strip(), m.group(0)),
            template
        )