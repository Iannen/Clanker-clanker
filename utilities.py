from __future__ import annotations
from ruamel.yaml import YAML
from clanker import ConfigViolations

class ConfigValidator:
    def __init__(self) -> None:
        self.yaml = YAML()

    def _assert_no_quotes(self, raw_text: str, filepath: str) -> None:
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

    def validate_cfg_frag(self, raw_text: str, filepath: str = "") -> dict:
        self._assert_no_quotes(raw_text, filepath)
        return self.yaml.load(raw_text)
