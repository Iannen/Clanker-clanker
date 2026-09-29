from __future__ import annotations

import dataclasses
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any, Callable, Optional, Self

from adapters.terminal.scripted_terminal_adapter import ExecutionFrame
from assert_classes import ActionsFactory, Asserts, Sandbox, TestContainer
from core import PathTokens
from results import AtomicTestResult, ContainerResult, ExpectanceResult, SandboxOperationsResult, Outcome

class Assert:
    frame_pos: int = -2
    def __init__(self, expected: Any = None) -> None:
        self.expected = expected
        self.validators: dict[str, Callable[[str], bool]] = {}

    def where(self, field: str, predicate: Callable[[str], bool]) -> Self:
        self.validators[field] = predicate
        return self

    def _parse_class_name(self) -> tuple[str, str]:
        words = [
            w.lower()
            for w in re.findall(r"[A-Z][a-z0-9]*", self.__class__.__name__)
        ]
        frame_fields = {f.name for f in dataclasses.fields(ExecutionFrame)}
        for i in range(1, len(words)):
            attr_candidate = "_".join(words[:i])
            if attr_candidate in frame_fields:
                op_candidate = "_".join(words[i:])
                return attr_candidate, op_candidate
        raise ValueError(f"No valid ExecutionFrame attribute prefix found in {self.__class__.__name__}")

    def _execute_phase_one(self, actual: Any, op_name: str) -> tuple[Outcome, dict[str, str], str]:
        outcome = Outcome.FAIL
        matches: dict[str, str] = {}
        details = ""

        if actual is None:
            details = f"Target frame attribute is None (expected '{self.expected}')"
        elif isinstance(self.expected, str) and "{" in self.expected and "}" in self.expected:
            parts = []
            last_idx = 0
            for match in re.finditer(r"\{(\w+)\}", self.expected):
                parts.append(re.escape(self.expected[last_idx:match.start()]))
                field_name = match.group(1)
                parts.append(f"(?P<{field_name}>.+?)")
                last_idx = match.end()
            parts.append(re.escape(self.expected[last_idx:]))
            built_regex = "".join(parts)

            regex_match = re.search(built_regex, str(actual))
            if regex_match:
                outcome = Outcome.PASS
                matches = regex_match.groupdict()
                matches.setdefault("lines", str(actual))
                matches.setdefault("chars", str(actual))
                matches.setdefault("text", str(actual))
            else:
                details = f"Expected template pattern not found: '{self.expected}'\n\n--- Actual ---\n{actual}"
        elif op_name == "contains":
            if str(self.expected) in str(actual): outcome = Outcome.PASS
            details = "" if outcome == Outcome.PASS else f"Expected '{self.expected}' to be contained in '{actual}'"
            matches = {
                "lines": str(actual),
                "chars": str(actual),
                "text": str(actual),
            }
        elif op_name == "has":
            actual_set = set(actual) if isinstance(actual, (list, set, tuple)) else set()
            expected_list = remove_token(self.expected) if isinstance(self.expected, (list, set, tuple)) else [remove_token(self.expected)]
            missing = [p for p in expected_list if p not in actual_set]
            outcome = Outcome.PASS if len(missing) == 0 else Outcome.FAIL
            details = "" if outcome else f"Missing expected items: {missing}"
        elif op_name == "min_lines":
            line_count = len(str(actual).splitlines()) if actual is not None else 0
            outcome = Outcome.PASS if line_count >= int(self.expected) else Outcome.FAIL
            details = "" if outcome else f"Expected minimum {self.expected} lines, got {line_count}"
            matches = {
                "lines": str(actual),
                "chars": str(actual),
                "text": str(actual),
            }
        else:
            raise NotImplementedError(f"Unsupported primary operation: '{op_name}'")
        return outcome, matches, details

    def evaluate(self, frames: list[ExecutionFrame]) -> ExpectanceResult:
        attr_name, op_name = self._parse_class_name()
        actual = getattr(frames[self.frame_pos], attr_name, None)

        outcome, captured_matches, details = self._execute_phase_one(actual, op_name)

        if outcome == Outcome.PASS:
            for field_name, predicate in self.validators.items():
                if field_name not in captured_matches:
                    outcome = Outcome.FAIL
                    details = f"Predicate field '{field_name}' not found in template matches."
                    break

                val = captured_matches[field_name]
                if not predicate(val):
                    outcome = Outcome.FAIL
                    details = f"Validation failed for field '{field_name}' with value '{val}'"
                    break

        formatted_attr = attr_name.replace("_", " ").title()
        assertion_str = f"{formatted_attr} {op_name}: '{self.expected}'"
        return ExpectanceResult(assertion=assertion_str, outcome=outcome, details=details if not outcome else "")

class ExitMsgContains(Assert): frame_pos = -1
class DiskManifestHas(Assert): pass
class UiRenderContains(Assert): pass
class PromptRenderContains(Assert): pass
class PromptRenderMinLines(Assert): pass

class AssertsImpl(Asserts):
    def __init__(self, parent: TestContainer) -> None:
        self._parent = parent
        self._asserts: list[Assert] = []

    def exit_msg_contains(self, expected_msg: str) -> TestContainer:
        self._asserts.append(ExitMsgContains(expected_msg))
        return self._parent

    def disk_manifest_has(self, expected_paths: list[str] | set[str]) -> TestContainer:
        self._asserts.append(DiskManifestHas(list(expected_paths)))
        return self._parent

    def ui_render_contains(self, template: str) -> TestContainer:
        self._asserts.append(UiRenderContains(template))
        return self._parent

    def prompt_render_contains(self, expected_prompt: str) -> TestContainer:
        self._asserts.append(PromptRenderContains(expected_prompt))
        return self._parent

    def prompt_render_min_lines(self, count: int) -> TestContainer:
        self._asserts.append(PromptRenderMinLines(count))
        return self._parent

    def where(self, field: str, predicate: Callable[[str], bool]) -> TestContainer:
        if self._asserts:
            self._asserts[-1].where(field, predicate)
        return self._parent

    def evaluate(self, frames: list[ExecutionFrame], name: str, test_number: int) -> AtomicTestResult:
        expectance_results = [
            check.evaluate(frames) for check in self._asserts
        ]
        return AtomicTestResult(
            test_number=test_number,
            name=name,
            expectance_results=expectance_results,
            frames=frames,
        )

class TestContainerImpl(TestContainer):
    def __init__(self, sequence: list[str], name: str = "") -> None:
        self.sequence = sequence
        self.name = name
        self._preop = SandboxImpl(parent=self)
        self._expect = AssertsImpl(self)
        self._postop = SandboxImpl(parent=self)

    @property
    def preop(self) -> SandboxImpl:
        return self._preop

    @property
    def expect(self) -> AssertsImpl:
        return self._expect

    @property
    def postop(self) -> SandboxImpl:
        return self._postop

    def run(self, sandbox_dir: Path, clanker_path: Path, framedump_path: Path, test_number: int = 1) -> ContainerResult: # CR carries crash msg
        preop_out = self._preop.execute(sandbox_dir)
        frames = self._run_put(sandbox_dir, clanker_path, framedump_path)

        if len(frames) >= 2 and frames[-1].exit_code == 0:
            test_res = self._expect.evaluate(frames, name=self.name, test_number=test_number)
        else:
            stderr_msg = frames[-1].stderr if frames and frames[-1].stderr else ""
            crash_msg = f"Unexpected crash (exit code 1):\n{stderr_msg}"
            test_res = AtomicTestResult(
                test_number=test_number,
                name=self.name,
                expectance_results=[],
                frames=frames,
            )

        postop_out = self._postop.execute(sandbox_dir)

        return ContainerResult(
            test_result=test_res,
            preop_result=preop_out,
            postop_result=postop_out,
        )

    def _run_put(self, sandbox_dir: Path, clanker_path: Path, framedump_path: Path) -> list[ExecutionFrame]:
        cmd = [
            sys.executable,
            "-B",
            str(clanker_path),
            "--test",
            "--input-script",
            *self.sequence,
            "--framedump-path",
            str(framedump_path),
        ]

        exit_code = 0
        stderr_output = ""

        try:
            proc = subprocess.run(
                cmd,
                cwd=sandbox_dir,
                capture_output=True,
                text=True,
                timeout=10.0,
            )
            exit_code = proc.returncode
            stderr_output = proc.stderr
        except Exception as ex:
            exit_code = 1
            stderr_output = str(ex)

        existing_frames = []
        if framedump_path.exists():
            try:
                with open(framedump_path, "r", encoding="utf-8") as f:
                    report_data = json.load(f)
                    existing_frames = [ExecutionFrame(**r) for r in report_data["records"]]
            except Exception:
                pass

        if exit_code == 0:
            return existing_frames

        crash_frame = ExecutionFrame(
            latest_input=ScriptedTerminalAdapter.CRASH_EVENT,
            exit_code=1,
            stderr=stderr_output,
        )
        existing_frames.append(crash_frame)
        return existing_frames

class SandboxImpl(Sandbox):
    def __init__(self, parent: TestContainer | None = None) -> None:
        self._parent = parent
        self._actions: list[tuple[str, str, Callable[[Path], None]]] = []

    def create_dirs(self, *paths: str) -> TestContainer | Self:
        sanitized = remove_token(paths)
        def action(sandbox_dir: Path) -> None:
            for p in sanitized:
                (sandbox_dir / p).mkdir(parents=True, exist_ok=True)
        self._actions.append(("create_dirs", f"create_dirs: {', '.join(sanitized)}", action))
        return self._parent if self._parent is not None else self

    def create_file(self, path: str, content: str = "") -> TestContainer | Self:
        sanitized = remove_token(path)
        def action(sandbox_dir: Path) -> None:
            target = sandbox_dir / sanitized
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        self._actions.append(("create_file", f"create_file: {sanitized}", action))
        return self._parent if self._parent is not None else self

    def edit_file(self, path: str, old: str, new: str) -> TestContainer | Self:
        sanitized = remove_token(path)
        def action(sandbox_dir: Path) -> None:
            target = sandbox_dir / sanitized
            text = target.read_text(encoding="utf-8")
            updated = text.replace(old, new)
            target.write_text(updated, encoding="utf-8")
        self._actions.append(("edit_file", f"edit_file: {sanitized}", action))
        return self._parent if self._parent is not None else self

    def rm(self, *paths: str) -> TestContainer | Self:
        sanitized = remove_token(paths)
        def action(sandbox_dir: Path) -> None:
            for p in sanitized:
                target = sandbox_dir / p
                if target.is_dir() and not target.is_symlink():
                    shutil.rmtree(target, ignore_errors=True)
                else:
                    target.unlink(missing_ok=True)
        self._actions.append(("rm", f"rm: {', '.join(sanitized)}", action))
        return self._parent if self._parent is not None else self

    def execute(self, sandbox_dir: Path) -> SandboxOperationsResult | None:
        if not self._actions: return None
        ops = []
        for op_type, desc, action in self._actions:
            try:
                action(sandbox_dir)
                outcome = Outcome.PASS
            except Exception:
                outcome = Outcome.FAIL
            ops.append((op_type, desc, outcome))
        return SandboxOperationsResult(ops, get_disk_state(sandbox_dir))

class ActionsFactoryImpl(ActionsFactory):
    def create_test(self, sequence: list[str], name: str = "") -> TestContainer:
        return TestContainerImpl(sequence, name)

def remove_token(raw_path: str | list[str]) -> str | list[str]:
    if isinstance(raw_path, str):
        return raw_path.removeprefix(PathTokens.PUD).lstrip("/\\")
    return [p.removeprefix(PathTokens.PUD).lstrip("/\\") for p in raw_path]

def get_disk_state(sandbox_dir: Path) -> list[str]:
    paths = []
    for p in sandbox_dir.rglob("*"):
        rel = p.relative_to(sandbox_dir)
        if rel.parts and rel.parts[0] == "framedumps":
            continue
        paths.append(str(rel))
    return sorted(paths)

class myclass:
    def method(self):
        print("hlleo")