import re
from dataclasses import dataclass

from backend.core import entities as e


@dataclass
class IngestionParseResult:
    creates: list[tuple[str, str]]
    updates: list[tuple[str, str]]
    deletes: list[str]
    errors: list[str]


class IngestionParser:
    _bookend_re = re.compile(
        r"^" + e.Delims.FILESET_START_OPEN[1]
        + r"\s*(create|update|delete)\s*:\s*(.+?)\s*"
        + e.Delims.FILESET_START_CLOSE[1]
        + r"$"
    )

    _close_bookend_re = re.compile(
        r"^" + e.Delims.FILESET_END_OPEN[1]
        + r"\s*(create|update|delete)\s*:\s*(.+?)\s*"
        + e.Delims.FILESET_END_CLOSE[1]
        + r"$"
    )

    def parse(self, raw_text: str) -> IngestionParseResult:
        lines = raw_text.splitlines()
        creates: list[tuple[str, str]] = []
        updates: list[tuple[str, str]] = []
        deletes: list[str] = []
        errors: list[str] = []

        i = 0
        n = len(lines)

        while i < n:
            m = self._bookend_re.match(lines[i].strip())

            if m is None:
                i += 1
                continue

            action = m.group(1)
            path = m.group(2).strip()

            if action == "delete":
                deletes.append(path)
                i += 1
                continue

            # create or update: scan forward for the matching closing bookend
            j = i + 1
            content_lines: list[str] = []
            found = False

            while j < n:
                cm = self._close_bookend_re.match(lines[j].strip())
                if cm and cm.group(1) == action and cm.group(2).strip() == path:
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