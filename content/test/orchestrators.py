import json
from pathlib import Path
from typing import Optional
import re
import shutil
from dataclasses import dataclass, field
from adapters.terminal.scripted_terminal_adapter import ExecutionFrame
from abc import ABC
import inspect
from pathlib import Path
import re
import shutil
import sys
from typing import Any

import assert_classes as assert_cls_module
from base_classes import AssertSuite
from expectance_impls import ActionsFactoryImpl
from import_checker import FileAnalysisSuite
from results import FileAnalysisResults, MethodResult, AssertSuiteResult

class TestSuitesRunner:
    def __init__(self, content_dir: Path, fixture_dir: Path, sandbox_dir: Path, clanker_path: Path) -> None:
        self .content_dir = content_dir
        self.fixture_dir = fixture_dir
        self.sandbox_dir = sandbox_dir
        self.clanker_path = clanker_path

    def run_tests(self) -> tuple[list[FileAnalysisResults], list[AssertSuiteResult]]:
        if self.sandbox_dir.exists(): shutil.rmtree(self.sandbox_dir)
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)

        file_suite_results = self._run_file_analysis_suites()
        assert_suite_results = self._run_assert_suites()

        return file_suite_results, assert_suite_results

    def _run_file_analysis_suites(self):
        return [FileAnalysisSuite(self.content_dir).analyse_files()]

    def _run_assert_suites(self) -> List[AssertSuiteResult]:
        assert_classes = [
            cls
            for _, cls in inspect.getmembers(assert_cls_module, inspect.isclass)
            if cls.__module__ == "assert_classes" and issubclass(cls, AssertSuite)
        ]
        return [
            assert_class(
                sandbox_dir=self.sandbox_dir,
                fixture_dir=self.fixture_dir,
                clanker_path=self.clanker_path,
                factory=ActionsFactoryImpl(),
            ).run()
            for assert_class in assert_classes
        ]

@dataclass(slots=True)
class GateInspector:
    import_results: [FileAnalysisResults]
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
            json.dump(
                [result.to_dict() for result in self.import_results], 
                f, 
                indent=2
            )

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

        import_pass = all(res.is_clean for res in self.import_results)
        for res in self.import_results:
            print(res.to_console())

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