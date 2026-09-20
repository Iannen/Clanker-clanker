#!/usr/bin/env -S python3 -B
import json
import subprocess
from pathlib import Path
from abc import ABC, abstractmethod

class Expectance(ABC):
    @abstractmethod
    def to_result(self, run_state: dict, sandbox_dir: Path) -> Result:
        pass

class ExitMsg(Expectance):
    def __init__(self, expected_msg: str) -> None:
        self.expected_msg = expected_msg

    def to_result(self, run_state: dict, sandbox_dir: Path) -> Result:
        actual = run_state.get("exit_msg")
        passed = actual == self.expected_msg
        details = "" if passed else f"Expected exit_msg '{self.expected_msg}', got '{actual}'"
        return Result(
            assertion="ExitMsg",
            passed=passed,
            details=details,
        )


class DiskState(Expectance):
    def __init__(self, expected_paths: list[str] | set[str]) -> None:
        self.expected_paths = list(expected_paths)


class UIRender(Expectance):
    def __init__(self, expected_lines: str | list[str]) -> None:
        if isinstance(expected_lines, str):
            self.expected_lines = [expected_lines]
        else:
            self.expected_lines = list(expected_lines)


class PromptRender(Expectance):
    def __init__(self, expected_prompt: str) -> None:
        self.expected_prompt = expected_prompt

class AtomicTest:
    name: str
    sequence: list[str]
    expects: list[Expectance]

class Result:pass

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
            match expectance:
                case ExitMsg():
                    self.results.append(Result())
                case DiskState():
                    self.results.append(Result())
                case UIRender():
                    self.results.append(Result())
                case PromptRender():
                    self.results.append(Result())

    def _run_put(self) -> dict:
        cmd = [
            sys.executable,
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

        return {
            "exit_code": exit_code,
            "exit_msg": exit_msg,
            "ui_frames": ui_frames,
            "rendered_prompts": rendered_prompts,
            "inputs_consumed": inputs_consumed,
            "stderr": stderr,
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

class GateInspector:
    def __init__(self, test_instances: list[BaseFixtureTest], reports_dir: Path) -> None:
        self.test_instances = test_instances
        self.reports_dir = reports_dir

    def evaluate_and_report(self) -> bool:
        """Serializes in-memory test results to JSON report files and prints console summary."""
        all_passed = True
        total_assertions = 0
        failed_assertions = 0

        print("\n" + "=" * 60)
        print(" SHIP GATE EVALUATION REPORT")
        print("=" * 60)

        for instance in self.test_instances:
            cls_name = instance.__class__.__name__
            report_file = self.reports_dir / f"{cls_name.lower()}.json"

            # Serialize in-memory test results to the reports directory
            payload = {
                "test_class": cls_name,
                "fixture_used": instance.TEMPLATE_FIXTURE_NAME,
                "sandbox_dir": str(instance.sandbox_dir),
                "results": instance.results,
            }

            report_file.write_text(json.dumps(payload, indent=2))

            # Evaluate execution outcomes
            instance_passed = True
            print(f"\n[SUITE] {cls_name}")

            for res in instance.results:
                total_assertions += 1
                status = "PASS" if res["passed"] else "FAIL"

                if not res["passed"]:
                    instance_passed = False
                    all_passed = False
                    failed_assertions += 1

                print(f"  - [{status}] {res['assertion']}")
                if not res["passed"] and res.get("details"):
                    print(f"      Details: {res['details']}")

            suite_status = "PASSED" if instance_passed else "FAILED"
            print(f"  Summary: {suite_status}")

        print("\n" + "-" * 60)
        print(
            f"TOTAL: {total_assertions} assertions | "
            f"PASSED: {total_assertions - failed_assertions} | "
            f"FAILED: {failed_assertions}"
        )
        print("=" * 60 + "\n")

        return all_passed