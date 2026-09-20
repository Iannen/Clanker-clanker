#!/usr/bin/env -S python3 -B
import json
import sys
import subprocess
from pathlib import Path
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import re

class Expectance(ABC):
    @abstractmethod
    def to_result(self, run_state: dict, sandbox_dir: Path) -> Result:
        pass

class ExitMsg(Expectance):
    def __init__(self, expected_msg: str) -> None:
        self.expected_msg = expected_msg

    def to_result(self, run_state: dict, sandbox_dir: Path) -> Result:
        actual = run_state.get("exit_msg")
        passed = self.expected_msg in actual

        assertion = f"ExitMsg contains '{self.expected_msg}'"
        
        details = "" if passed else f"Expected exit_msg '{self.expected_msg}', got '{actual}'"
        return Result(
            assertion=assertion,
            passed=passed,
            details=details,
        )

class StderrContains(Expectance):
    def __init__(self, expected_text: str) -> None:
        self.expected_text = expected_text

    def to_result(self, run_state: dict, sandbox_dir: Path) -> Result:
        actual = run_state.get("stderr", "")
        passed = self.expected_text in actual
        details = "" if passed else f"Expected stderr to contain '{self.expected_text}', got '{actual}'"
        return Result(assertion=f"Stderr contains '{self.expected_text}'", passed=passed, details=details)

class DiskState(Expectance):
    def __init__(self, expected_paths: list[str] | set[str]) -> None:
        self.expected_paths = list(expected_paths)

    def to_result(self, run_state: dict, sandbox_dir: Path) -> Result:
        actual_paths = set(run_state.get("disk_paths", []))
        
        missing = []
        for expected in self.expected_paths:
            rel_path = expected
            if rel_path.startswith("<PUD>"):
                rel_path = rel_path[len("<PUD>"):].lstrip("/")
            if rel_path not in actual_paths and not (sandbox_dir / rel_path).exists():
                missing.append(expected)

        passed = len(missing) == 0
        assertion = "Disk state matches expected repository contract paths"
        details = "" if passed else f"Missing expected paths on disk: {missing}"
        return Result(assertion=assertion, passed=passed, details=details)


@dataclass
class Regex:
    pattern: str
    validator: Optional[Callable[[re.Match], bool]] = None

class UIRender(Expectance):
    def __init__(self, expected: str | Regex) -> None:
        self.expected = expected

    def to_result(self, run_state: dict, sandbox_dir: Path) -> Result:
        ui_frames = run_state.get("ui_frames", [])
        latest_frame = ui_frames[-1] if ui_frames else "(No UI frames captured)"
        
        if isinstance(self.expected, Regex):
            match = re.search(self.expected.pattern, latest_frame)
            if match and self.expected.validator:
                passed = self.expected.validator(match)
            else:
                passed = bool(match)
            
            assertion = f"Latest UI render matches regex pattern with validation: '{self.expected.pattern}'"
            target_desc = self.expected.pattern
        else:
            passed = self.expected in latest_frame
            assertion = f"Latest UI render contains text: '{self.expected}'"
            target_desc = self.expected

        if passed:
            details = ""
        else:
            details = f"Expected UI pattern/validation not met: '{target_desc}'\n\n--- Latest UI Render ---\n{latest_frame}"

        return Result(
            assertion=assertion,
            passed=passed,
            details=details,
        )

class PromptRender(Expectance):
    def __init__(self, expected_prompt: str) -> None:
        self.expected_prompt = expected_prompt

@dataclass
class AtomicTest:
    sequence: list[str]
    expects: list[Expectance] | Expectance
    name: str = ""
    reset_sequence: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.expects, list):
            self.expects = [self.expects]

@dataclass
class Result:
    assertion: str = ""
    passed: bool = False
    details: str = ""

    def to_dict(self) -> dict:
        res = {
            "assertion": self.assertion,
            "passed": self.passed,
        }
        if self.details:
            res["details"] = self.details
        return res

class BaseFixtureTest:
    TEMPLATE_FIXTURE_NAME: str = ""

    def __init__(self, sandbox_dir: Path, clanker_path: Path) -> None:
        self.sandbox_dir = sandbox_dir
        self.clanker_path = clanker_path
        self.report_path = self.sandbox_dir / "latest_run.json"
        self.results: list[Result] = []
        self._replay_seq: list[str] = []

    def run_tests(self) -> None:
        tests = self._get_tests()
        for test in tests:
            self._run_test(test)
        pass

    def _run_test(self, test: AtomicTest): 
        self._replay_seq = self._replay_seq + test.sequence
        run_state = self._run_put()
        for expectance in test.expects:
            self.results.append(expectance.to_result(run_state, self.sandbox_dir))
        if test.reset_sequence:
            self._replay_seq = []

    def _run_put(self) -> dict:
        cmd = [
            sys.executable,
            "-B",
            str(self.clanker_path),
            "--test",
            "--input-script",
            *self._replay_seq,
            "--report-path",
            str(self.report_path),
        ]

        try:
            completed = subprocess.run(
                cmd,
                cwd=self.sandbox_dir,
                capture_output=True,
                text=True,
                timeout=10.0,
            )
            exit_code = completed.returncode
            exit_msg = completed.stdout.strip()
            stderr = completed.stderr
        except subprocess.TimeoutExpired as ex:
            exit_code = -1
            exit_msg = ex.stdout.decode("utf-8").strip() if ex.stdout else ""
            stderr = "Execution timed out"

        ui_frames = []
        rendered_prompts = []
        inputs_consumed = 0

        if self.report_path.is_file():
            try:
                with open(self.report_path, "r", encoding="utf-8") as f:
                    report_data = json.load(f)
                    ui_frames = report_data.get("frames", [])
                    rendered_prompts = report_data.get("clipboards", [])
                    inputs_consumed = report_data.get("inputs_consumed", 0)
            except Exception:
                pass

        disk_paths = []
        if self.sandbox_dir.is_dir():
            for path in self.sandbox_dir.rglob("*"):
                disk_paths.append(str(path.relative_to(self.sandbox_dir)))

        return {
            "exit_code": exit_code,
            "exit_msg": exit_msg,
            "ui_frames": ui_frames,
            "rendered_prompts": rendered_prompts,
            "inputs_consumed": inputs_consumed,
            "stderr": stderr,
            "disk_paths": disk_paths,
        }

    def _get_tests(self) -> list[AtomicTest]:
        assert_methods = [
            attr_name
            for attr_name in self.__class__.__dict__.keys()
            if not attr_name.startswith("_") and callable(getattr(self, attr_name))
        ]

        atomic_tests: list[AtomicTest] = []

        for method_name in assert_methods:
            method = getattr(self, method_name)
            result = method()

            if isinstance(result, list):
                for index, test in enumerate(result, start=1):
                    test.name = f"{method_name} #{index}"
                    atomic_tests.append(test)
            elif result is not None:
                result.name = method_name
                atomic_tests.append(result)

        return atomic_tests