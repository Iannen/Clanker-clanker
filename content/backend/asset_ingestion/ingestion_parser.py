
import re
from dataclasses import dataclass, field

from backend.core import entities as e


@dataclass
class IngestionParseResult:
    creates: list[tuple[str, str]]
    updates: list[tuple[str, str]]
    deletes: list[str]
    errors: list[str]
    expanded: list[str] = field(default_factory=list)


class IngestionParser:
    _show_re = re.compile(
        r'^<show\s+path="(?P<path>[^"]+)"\s*/>\s*$'
    )

    _open_re = re.compile(
        r"^(?:"
        + r"(?P<create_open>" + re.escape(e.Delims.CREATE_FILESET_UL[1]) + r")(?P<create_path>.+?)" + re.escape(e.Delims.FILESET_OPEN_END_TAG[1])
        + r"|"
        + r"(?P<update_open>" + re.escape(e.Delims.UPDATE_FILESET_UL[1]) + r")(?P<update_path>.+?)" + re.escape(e.Delims.FILESET_OPEN_END_TAG[1])
        + r"|"
        + r"(?P<delete_open>" + re.escape(e.Delims.DELETE_FILESET_UL[1]) + r")(?P<delete_path>.+?)" + re.escape(e.Delims.FILESET_CLOSED_END_TAG[1])
        + r")$"
    )

    _close_re = re.compile(
        r"^(?:"
        + r"(?P<create_close>" + re.escape(e.Delims.CREATE_FILESET_BL[1]) + r")(?P<create_path>.+?)" + re.escape(e.Delims.FILESET_OPEN_END_TAG[1])
        + r"|"
        + r"(?P<update_close>" + re.escape(e.Delims.UPDATE_FILESET_BL[1]) + r")(?P<update_path>.+?)" + re.escape(e.Delims.FILESET_OPEN_END_TAG[1])
        + r")$"
    )

    def parse(self, raw_text: str) -> IngestionParseResult:
        lines = raw_text.splitlines()
        creates: list[tuple[str, str]] = []
        updates: list[tuple[str, str]] = []
        deletes: list[str] = []
        expanded: list[str] = []
        errors: list[str] = []

        i = 0
        n = len(lines)

        while i < n:
            line = lines[i].strip()

            show_match = self._show_re.match(line)
            if show_match:
                expanded.append(show_match.group("path").strip())
                i += 1
                continue

            m = self._open_re.match(line)

            if m is None:
                i += 1
                continue

            if m.group("delete_open") is not None:
                deletes.append(m.group("delete_path").strip())
                i += 1
                continue

            if m.group("create_open") is not None:
                action = "create"
                path = m.group("create_path").strip()
                close_group = "create_close"
                close_path_group = "create_path"
            else:
                action = "update"
                path = m.group("update_path").strip()
                close_group = "update_close"
                close_path_group = "update_path"

            # Scan forward for the matching closing bookend.
            j = i + 1
            content_lines: list[str] = []
            found = False

            while j < n:
                cm = self._close_re.match(lines[j].strip())
                if (
                    cm
                    and cm.group(close_group) is not None
                    and cm.group(close_path_group).strip() == path
                ):
                    found = True
                    break
                content_lines.append(lines[j])
                j += 1

            if not found:
                errors.append(f"Unclosed bookend for {action} '{path}'")
                i += 1
                continue

            content = self._strip_triple_backticks("\n".join(content_lines))

            if action == "create":
                creates.append((path, content))
            else:
                updates.append((path, content))

            i = j + 1

        return IngestionParseResult(
            creates=creates,
            updates=updates,
            deletes=deletes,
            errors=errors,
            expanded=expanded,
        )

    @staticmethod
    def _strip_triple_backticks(content: str) -> str:
        lines = content.splitlines()

        start = 0
        for idx, line in enumerate(lines):
            if line.strip().startswith("```"):
                start = idx + 1
                break

        end = len(lines)
        for idx in range(len(lines) - 1, -1, -1):
            if lines[idx].strip().startswith("```"):
                end = idx
                break

        if start < end:
            lines = lines[start:end]

        return "\n".join(lines)
