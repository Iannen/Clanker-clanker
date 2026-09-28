#!/usr/bin/env -S python3 -B
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
from import_checker import ImportSuite
from results import ImportSuiteResult, MethodResult, AssertSuiteResult

class TestSuitesRunner:
    def __init__(self, content_dir: Path, fixture_dir: Path, sandbox_dir: Path, clanker_path: Path) -> None:
        self .content_dir = content_dir
        self.fixture_dir = fixture_dir
        self.sandbox_dir = sandbox_dir
        self.clanker_path = clanker_path

    def run_tests(self) -> tuple[ImportSuiteResult, list[AssertSuiteResult]]:
        if self.sandbox_dir.exists(): shutil.rmtree(self.sandbox_dir)
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)

        import_suite_result = ImportSuite(self.content_dir).run_tests()

        assert_suite_results = [
            self._run_assert_class(assert_class) 
            for assert_class in self._get_assert_classes()
        ]

        return import_suite_result, assert_suite_results

    def _run_assert_class(self, assert_class) -> AssertSuiteResult:
            suite_target = assert_class() if isinstance(assert_class, type) else assert_class
            template_fixture_name = getattr(suite_target, "TEMPLATE_FIXTURE_NAME", "")

            snake_name = re.sub(r"(?<!^)(?=[A-Z])", "_", assert_class.__name__).lower()
            sandbox_path = self.sandbox_dir / f"active_sandbox_{snake_name}"
            fixture_path = self.fixture_dir / template_fixture_name

            if fixture_path.exists():
                shutil.copytree(fixture_path, sandbox_path)

            suite_result = self._run_suite_target(suite_target, sandbox_path)
            return suite_result

    def _run_suite_target(self, suite_target: Any, sandbox_dir: Path) -> AssertSuiteResult:
        method_results = []
        assert_methods = [
            (name, getattr(suite_target, name))
            for name, attr in suite_target.__class__.__dict__.items()
            if not name.startswith("_") and callable(getattr(suite_target, name))
        ]

        for method_name, method in assert_methods:
            containers = method(ActionsFactoryImpl())
            if not isinstance(containers, list):
                containers = [containers]

            container_results = []
            idx = 1
            for container in containers:
                framedump_path = sandbox_dir / "framedumps" / f"{method_name}_{idx}.framedump"
                container_results.append(
                    container.run(sandbox_dir, self.clanker_path, framedump_path, test_number=idx)
                )
                idx += 1
            method_results.append(MethodResult(method_name, container_results))

        return AssertSuiteResult(suite_target.__class__.__name__, "", method_results)


    def _get_assert_classes(self):
        assert_classes = [
            cls
            for _, cls in inspect.getmembers(assert_cls_module, inspect.isclass)
            if cls.__module__ == "assert_classes" and issubclass(cls, AssertSuite)
        ]
        if not assert_classes:
            sys.stderr.write("Error: No test classes found in assert_classes.py\n")
            sys.exit(1)
        return assert_classes

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