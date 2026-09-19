#!/usr/bin/env -S python3 -B

import inspect
import json
import os
import shutil
import subprocess
import sys
from abc import ABC
from pathlib import Path

SCRIPT_PATH = Path(os.path.abspath(__file__))
if SCRIPT_PATH.is_symlink():
    SCRIPT_PATH = SCRIPT_PATH.readlink()

TEST_ROOT = SCRIPT_PATH.parent.resolve()
CONTENT_ROOT = TEST_ROOT.parent
CLANKER_PATH = CONTENT_ROOT / "clanker.py"

if str(TEST_ROOT) not in sys.path:
    sys.path.insert(0, str(TEST_ROOT))

if str(CONTENT_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTENT_ROOT))


def main() -> None:
    if not CLANKER_PATH.exists():
        sys.stderr.write(f"Error: Could not find clanker.py at {CLANKER_PATH}\n")
        sys.exit(1)

    for target_dir in [BaseFixtureTest.SANDBOXES_DIR, BaseFixtureTest.REPORTS_DIR]:
        if target_dir.exists():
            shutil.rmtree(target_dir)

    import assert_classes

    test_classes = [
        cls for name, cls in inspect.getmembers(assert_classes, inspect.isclass)
        if cls.__module__ == "assert_classes"
    ]

    if not test_classes:
        sys.stderr.write("Error: No test classes found in assert_classes.py\n")
        sys.exit(1)

    for cls in test_classes:
        instance = cls()
        instance.run_tests()

    interpreter = GateInspector(test_classes)
    success = interpreter.evaluate_and_report()

    if success:
        sys.exit(0)
    else:
        sys.exit(1)


class COMMAND:
    START_APP = "START_APP"
    TERMINATE_APP = "TERMINATE_APP"


class INFOSOURCE:
    TERMINAL_WRITE = "TERMINAL_WRITE"
    PROGRAM_EXIT_MSG = "PROGRAM_EXIT_MSG"
    TO_CLIPBOARD_CONTENT = "TO_CLIPBOARD_CONTENT"
    DISK = "DISK"


class BaseFixtureTest(ABC):
    FIXTURES_DIR = TEST_ROOT / "test_repos"
    SANDBOXES_DIR = TEST_ROOT / "sandboxes"
    REPORTS_DIR = TEST_ROOT / "reports"

    TEMPLATE_FIXTURE_NAME: str = ""
    SANDBOX_DEST_NAME: str = ""
    REPORT_FILENAME: str = ""

    def __init__(self):
        import re
        if not self.TEMPLATE_FIXTURE_NAME:
            raise ValueError(f"{self.__class__.__name__} must define TEMPLATE_FIXTURE_NAME")

        class_name = self.__class__.__name__
        snake_name = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower()

        sandbox_name = self.SANDBOX_DEST_NAME or f"active_sandbox_{snake_name}"
        report_name = self.REPORT_FILENAME or f"{snake_name}.json"

        self.source_fixture = self.FIXTURES_DIR / self.TEMPLATE_FIXTURE_NAME
        self.sandbox_dir = self.SANDBOXES_DIR / sandbox_name
        self.report_file = self.REPORTS_DIR / report_name
        self.records: list[dict] = []

    def _setup(self) -> None:
        self.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        self.SANDBOXES_DIR.mkdir(parents=True, exist_ok=True)

        if self.sandbox_dir.exists():
            shutil.rmtree(self.sandbox_dir)

        shutil.copytree(self.source_fixture, self.sandbox_dir)

    def _execute_cli(self, input_script: list[str]) -> tuple[int, str, dict]:
        temp_scenario_report = self.REPORTS_DIR / f"_temp_{self.report_file.name}"

        result = subprocess.run(
            [sys.executable, "-B", str(CLANKER_PATH), "--test", "--input-script"] + input_script + ["--report-path", str(temp_scenario_report)],
            cwd=self.sandbox_dir,
            capture_output=True,
            text=True
        )

        adapter_data = {}
        if temp_scenario_report.exists():
            with open(temp_scenario_report, "r", encoding="utf-8") as f:
                adapter_data = json.load(f)
            temp_scenario_report.unlink()

        return result.returncode, result.stdout, adapter_data

    def run_tests(self) -> None:
        self._setup()

        spec_methods = [
            getattr(self, m) for m in self.__class__.__dict__
            if not m.startswith("_") and callable(getattr(self, m))
        ]

        active_sequence: list[str] = []

        for method in spec_methods:
            specs = method()
            if isinstance(specs, dict):
                specs = [specs]

            for idx, spec in enumerate(specs):
                if spec.get("before") == COMMAND.START_APP:
                    active_sequence = []

                active_sequence.extend(spec.get("sequence", []))

                expected = spec.get("expected", {})
                source = expected.get("source")

                exit_code, stdout_msg, adapter_data = self._execute_cli(active_sequence)

                frames = adapter_data.get("frames", [])
                clipboards = adapter_data.get("clipboards", [])

                actual_val = None
                if source == INFOSOURCE.PROGRAM_EXIT_MSG:
                    actual_val = stdout_msg.strip()
                elif source == INFOSOURCE.TERMINAL_WRITE:
                    actual_val = frames[-1] if frames else ""
                elif source == INFOSOURCE.TO_CLIPBOARD_CONTENT:
                    actual_val = clipboards[-1] if clipboards else ""
                elif source == INFOSOURCE.DISK:
                    expected_paths = expected.get("value", [])
                    actual_val = [
                        p for p in expected_paths
                        if (self.sandbox_dir / p).exists()
                    ]

                actual = {
                    "exit_code": exit_code,
                    "value": actual_val,
                    "clipboards": clipboards,
                    "frames_count": len(frames)
                }

                method_display = method.__name__ if len(specs) == 1 else f"{method.__name__}[{idx}]"

                record = {
                    "assert_method": method_display,
                    "input_sequence": active_sequence.copy(),
                    "actual": actual,
                    "expected": expected
                }
                if "before" in spec:
                    record["before"] = spec["before"]
                if "after" in spec:
                    record["after"] = spec["after"]

                self.records.append(record)

                if spec.get("after") == COMMAND.TERMINATE_APP:
                    active_sequence = []

        self._flush_report()

    def _flush_report(self) -> None:
        report_payload = {
            "test_class": self.__class__.__name__,
            "sandbox_dir": str(self.sandbox_dir),
            "records": self.records
        }
        with open(self.report_file, "w", encoding="utf-8") as f:
            json.dump(report_payload, f, indent=2)


class GateInspector:
    def __init__(self, test_classes: list[type[BaseFixtureTest]]):
        self.test_classes = test_classes

    def evaluate_and_report(self) -> bool:
        overall_success = True

        import re
        for cls in self.test_classes:
            report_filename = cls.REPORT_FILENAME or f"{re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()}.json"
            report_file = BaseFixtureTest.REPORTS_DIR / report_filename
            print(f"\n{cls.__name__}")

            if not report_file.exists():
                print(f"  ❌ missing report file: {report_file}")
                overall_success = False
                continue

            with open(report_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            for record in data.get("records", []):
                method_display_name = record["assert_method"].replace("_", " ")
                actual = record["actual"]
                expected = record["expected"]

                passed = True

                if "value" in expected:
                    exp_val = expected["value"]
                    act_val = actual.get("value")
                    if isinstance(exp_val, str) and "<..>" in exp_val:
                        import re
                        pattern = "^" + re.escape(exp_val).replace(r"\<\.\.\>", ".*") + "$"
                        if not act_val or not re.match(pattern, act_val):
                            passed = False
                    elif isinstance(exp_val, list):
                        if sorted(act_val or []) != sorted(exp_val):
                            passed = False
                    elif act_val != exp_val:
                        passed = False

                status = "pass" if passed else "fail"
                if not passed:
                    overall_success = False

                print(f"  {method_display_name}: {status}")

        return overall_success


if __name__ == "__main__":
    main()