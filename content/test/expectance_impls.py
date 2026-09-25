from pathlib import Path
import re
import shutil
from typing import Callable, Optional

from adapters.terminal.scripted_terminal_adapter import ExecutionFrame
from core import PathTokens
from reporter import ExpectanceResult, SandboxOperationsResult, AtomicTestResult

def shadow_of(impl_class):
    def decorator(cls):
        real_methods = {
            m for m in dir(impl_class)
            if not m.startswith("_") and m != "to_result"
        }
        shadow_methods = {m for m in dir(cls) if not m.startswith("_")}
        missing = real_methods - shadow_methods
        if missing:
            raise TypeError(f"{cls.__name__} out of sync. Missing: {missing}")

        orig_init = getattr(cls, "__init__", None)

        def new_init(self, *args, **kwargs):
            self._impl = impl_class(*args, **kwargs)
            if orig_init and orig_init is not object.__init__:
                orig_init(self, *args, **kwargs)

        cls.__init__ = new_init

        for method_name in real_methods:
            def make_forwarder(name):
                def forwarder(self, *args, **kwargs):
                    res = getattr(self._impl, name)(*args, **kwargs)
                    if res is self._impl:
                        return self
                    return res
                return forwarder

            setattr(cls, method_name, make_forwarder(method_name))

        return cls
    return decorator


class ExpectanceCheck:
    def evaluate(self, frames: list[ExecutionFrame]) -> ExpectanceResult:
        raise NotImplementedError


class ExitMsgCheck(ExpectanceCheck):
    def __init__(self, expected_msg: str) -> None:
        self.expected_msg = expected_msg

    def evaluate(self, frames: list[ExecutionFrame]) -> ExpectanceResult:
        frame = frames[-1]
        actual = frame.exit_msg or ""
        passed = self.expected_msg in actual
        assertion = f"ExitMsg contains '{self.expected_msg}'"
        details = "" if passed else f"Expected exit_msg '{self.expected_msg}', got '{actual}'"
        return ExpectanceResult(assertion=assertion, passed=passed, details=details)


class DiskStateCheck(ExpectanceCheck):
    def __init__(self, expected_paths: list[str] | set[str]) -> None:
        sanitized = []
        for path in expected_paths:
            p = str(path)
            if p.startswith(PathTokens.PUD):
                p = p[len(PathTokens.PUD):].lstrip("/\\")
            sanitized.append(p)
        self.expected_paths = sanitized

    def evaluate(self, frames: list[ExecutionFrame]) -> ExpectanceResult:
        frame = frames[-2]
        actual_paths = set(frame.disk_paths)
        missing = []
        for expected in self.expected_paths:
            rel_path = expected
            if rel_path.startswith("<PUD>"):
                rel_path = rel_path[len("<PUD>"):].lstrip("/")
            if rel_path not in actual_paths:
                missing.append(expected)

        passed = len(missing) == 0
        assertion = "Disk state matches expected repository contract paths"

        if passed:
            details = ""
        else:
            expected_formatted = ",\n".join(f"'{p}'" for p in self.expected_paths)
            actual_formatted = "\n".join(f"'{p}'" for p in frame.disk_paths) if frame.disk_paths else "(empty)"
            details = (
                f"Missing expected paths on disk:\n"
                f"expected:\n{expected_formatted}\n"
                f"actual:\n{actual_formatted}"
            )

        return ExpectanceResult(assertion=assertion, passed=passed, details=details)


class UIRenderCheck(ExpectanceCheck):
    def __init__(self, template: str) -> None:
        self.template = template
        self.validators: dict[str, Callable[[str], bool]] = {}

    def where(self, field: str, predicate: Callable[[str], bool]) -> "UIRenderCheck":
        self.validators[field] = predicate
        return self

    def evaluate(self, frames: list[ExecutionFrame]) -> ExpectanceResult:
        frame = frames[-2]
        latest_frame = frame.latest_write or "(No UI render captured)"

        parts = []
        last_idx = 0
        for match in re.finditer(r"\{(\w+)\}", self.template):
            parts.append(re.escape(self.template[last_idx:match.start()]))
            field_name = match.group(1)
            parts.append(f"(?P<{field_name}>.+?)")
            last_idx = match.end()
        parts.append(re.escape(self.template[last_idx:]))
        built_regex = "".join(parts)

        match = re.search(built_regex, latest_frame)
        passed = bool(match)
        details = ""

        if passed and match:
            for field_name, predicate in self.validators.items():
                val = match.group(field_name)
                if not predicate(val):
                    passed = False
                    details = f"Validation failed for field '{field_name}' with value '{val}'"
                    break
        elif not passed:
            details = f"Expected UI pattern not found: '{self.template}'\n\n--- Latest UI Render ---\n{latest_frame}"

        assertion = f"Latest UI render matches template: '{self.template}'"
        return ExpectanceResult(assertion=assertion, passed=passed, details=details)


class PromptRenderCheck(ExpectanceCheck):
    def __init__(self) -> None:
        self.expected_prompt = ""
        self.minimum_lines: Optional[int] = None

    def contains(self, expected_prompt: str) -> "PromptRenderCheck":
        self.expected_prompt = expected_prompt
        return self

    def min_lines(self, count: int) -> "PromptRenderCheck":
        self.minimum_lines = count
        return self

    def evaluate(self, frames: list[ExecutionFrame]) -> ExpectanceResult:
        frame = frames[-2]
        latest_prompt = frame.latest_clipboard or ""
        passed = True
        failures = []

        if self.expected_prompt and self.expected_prompt not in latest_prompt:
            passed = False
            failures.append(f"Expected prompt text '{self.expected_prompt}' not found.")

        if self.minimum_lines is not None:
            line_count = len(latest_prompt.splitlines()) if latest_prompt else 0
            if line_count < self.minimum_lines:
                passed = False
                failures.append(f"Expected at least {self.minimum_lines} lines, got {line_count}.")

        assertion_parts = []
        if self.expected_prompt:
            assertion_parts.append(f"contains '{self.expected_prompt}'")
        if self.minimum_lines is not None:
            assertion_parts.append(f"min_lines >= {self.minimum_lines}")

        assertion = f"Prompt render check ({', '.join(assertion_parts)})"
        details = "\n".join(failures) if not passed else ""
        return ExpectanceResult(assertion=assertion, passed=passed, details=details)


class SandboxOperations:
    def __init__(self) -> None:
        self._actions: list[tuple[str, str, Callable[[Path], None]]] = []

    def _sanitize_path(self, raw_path: str) -> str:
        p = str(raw_path)
        if p.startswith(PathTokens.PUD):
            p = p[len(PathTokens.PUD):].lstrip("/\\")
        elif p.startswith("<PUD>"):
            p = p[len("<PUD>"):].lstrip("/\\")
        return p

    def create_dirs(self, *paths: str) -> "SandboxOperations":
        sanitized = [self._sanitize_path(p) for p in paths]
        def action(sandbox_dir: Path) -> None:
            for p in sanitized:
                (sandbox_dir / p).mkdir(parents=True, exist_ok=True)
        self._actions.append(("create_dirs", f"create_dirs: {', '.join(sanitized)}", action))
        return self

    def create_file(self, path: str, content: str = "") -> "SandboxOperations":
        sanitized = self._sanitize_path(path)
        def action(sandbox_dir: Path) -> None:
            target = sandbox_dir / sanitized
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        self._actions.append(("create_file", f"create_file: {sanitized}", action))
        return self

    def edit_file(self, path: str, old: str, new: str) -> "SandboxOperations":
        sanitized = self._sanitize_path(path)
        def action(sandbox_dir: Path) -> None:
            target = sandbox_dir / sanitized
            text = target.read_text(encoding="utf-8")
            updated = text.replace(old, new)
            target.write_text(updated, encoding="utf-8")
        self._actions.append(("edit_file", f"edit_file: {sanitized}", action))
        return self

    def rm(self, *paths: str) -> "SandboxOperations":
        sanitized = [self._sanitize_path(p) for p in paths]
        def action(sandbox_dir: Path) -> None:
            for p in sanitized:
                target = sandbox_dir / p
                if target.is_dir() and not target.is_symlink():
                    shutil.rmtree(target, ignore_errors=True)
                else:
                    target.unlink(missing_ok=True)
        self._actions.append(("rm", f"rm: {', '.join(sanitized)}", action))
        return self

    def execute(self, sandbox_dir: Path) -> list[SandboxOperationsResult]:
        results = []
        for op_type, desc, action in self._actions:
            action(sandbox_dir)
            results.append(SandboxOperationsResult(operation_type=op_type, description=desc, passed=True))
        return results


class AtomicTestImpl:
    def __init__(self, sequence: list[str]) -> None:
        self.sequence = sequence
        self.name: str = ""
        self.frames_filename: str = ""
        self._checks: list[ExpectanceCheck] = []

    def expect_exit_msg(self, expected_msg: str) -> "AtomicTestImpl":
        self._checks.append(ExitMsgCheck(expected_msg))
        return self

    def expect_disk_has(self, expected_paths: list[str] | set[str]) -> "AtomicTestImpl":
        self._checks.append(DiskStateCheck(expected_paths))
        return self

    def expect_ui_contains(self, template: str) -> "AtomicTestImpl":
        check = UIRenderCheck(template)
        self._checks.append(check)
        return self

    def where(self, field: str, predicate: Callable[[str], bool]) -> "AtomicTestImpl":
        if self._checks and isinstance(self._checks[-1], UIRenderCheck):
            self._checks[-1].where(field, predicate)
        return self

    def expect_prompt_contains(self, expected_prompt: str) -> "AtomicTestImpl":
        if self._checks and isinstance(self._checks[-1], PromptRenderCheck):
            check = self._checks[-1]
        else:
            check = PromptRenderCheck()
            self._checks.append(check)
        check.contains(expected_prompt)
        return self

    def expect_prompt_min_lines(self, count: int) -> "AtomicTestImpl":
        if self._checks and isinstance(self._checks[-1], PromptRenderCheck):
            check = self._checks[-1]
        else:
            check = PromptRenderCheck()
            self._checks.append(check)
        check.min_lines(count)
        return self

    def to_result(self, frames: list[ExecutionFrame], test_number: int) -> AtomicTestResult:
        if frames and frames[-1].exit_code == 1:
            crash_msg = f"Unexpected crash (exit code 1):\n{frames[-1].stderr or ''}"
            return AtomicTestResult(
                test_number=test_number,
                name=self.name,
                expectance_results=[],
                frames=frames,
                crashed=True,
                crash_message=crash_msg,
            )

        expectance_results = [
            check.evaluate(frames) for check in self._checks
        ]
        return AtomicTestResult(
            test_number=test_number,
            name=self.name,
            expectance_results=expectance_results,
            frames=frames,
            crashed=False,
            crash_message=None,
        )


AtomicTest = AtomicTestImpl