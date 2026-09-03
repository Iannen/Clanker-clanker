from __future__ import annotations
from ruamel.yaml import YAML
from clanker import ConfigViolations

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
        for set_name, set_def in cfg_frag.get("sets", {}).items():
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

            for render in domain.get("renders", []):
                if not isinstance(render, dict):
                    continue
                render_name = render.get("name")
                for resolver in render.get("resolvers", []):
                    if not isinstance(resolver, dict):
                        continue
                    if "fileset" in resolver or "varname" in resolver:
                        continue
                    inc = resolver.get("includes", [])
                    exc = resolver.get("excludes", [])
                    if inc or exc:
                        key = _make_key(inc, exc)
                        inline_filesets.append((key, domain_name, render_name))

        for string_key, domain, render in inline_filesets:
            if string_key in named_fileset_map:
                violations.append(
                    f"    domain '{domain}' render '{render}': use named fileset '{named_fileset_map[string_key]}'"
                )

        if violations:
            msg_parts = [filepath] if filepath else []
            msg_parts.extend(violations)
            raise ConfigViolations("\n".join(msg_parts))