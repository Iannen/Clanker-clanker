import json
from pathlib import Path
from typing import Optional
import re
import shutil
from dataclasses import dataclass, field
from adapters.terminal.scripted_terminal_adapter import ExecutionFrame


@dataclass(slots=True)
class GateInspector:
    import_result: ImportSuiteResult
    assert_results: list[AssertSuiteResult]
    reports_dir: Path

    def evaluate_and_report(self) -> bool:
        if self.reports_dir.exists(): shutil.rmtree(self.reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        self._write_file_reports()
        return self.write_console_report()

    def _write_file_reports(self) -> None:
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        with open(
            self.reports_dir / "import_checker.json",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(self.import_result.to_dict(), f, indent=2)

        for suite in self.assert_results:
            snake_name = re.sub(r"(?<!^)(?=[A-Z])", "_", suite.suite_name).lower()
            report_file = f"{snake_name}.json"
            suite.report_filename = report_file

            with open(self.reports_dir / report_file, "w", encoding="utf-8") as f:
                json.dump(suite.to_dict(), f, indent=2)

    def write_console_report(self) -> bool:
        print("============================================================")
        print("Test results")
        print("============================================================")

        import_pass = self.import_result.is_clean
        print(self.import_result.to_console())

        tests_pass = True
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        crashed_tests = 0

        for suite in self.assert_results:
            if not suite.passed:
                tests_pass = False

            total_tests += suite.total_tests
            passed_tests += suite.passed_tests
            failed_tests += suite.failed_tests
            crashed_tests += suite.crashed_tests

            print(suite.to_console())

        print("\n------------------------------------------------------------")
        print(
            f"TOTAL: {total_tests} tests | PASSED: {passed_tests} | "
            f"FAILED: {failed_tests} | CRASHED: {crashed_tests}"
        )
        print("============================================================")

        return import_pass and tests_pass