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
from results import FileAnalysisResults, MethodResult, AssertSuiteResult, RunResult
from visitors.dict_visitor import JsonSerializerVisitor
from visitors.console_visitor import ConsoleReportVisitor
from visitors.html_visitor import HtmlReportVisitor
class TestSuitesRunner:
    def __init__(
        self,
        content_dir: Path,
        fixture_dir: Path,
        sandbox_dir: Path,
        clanker_path: Path,
    ) -> None:
        self.content_dir = content_dir
        self.fixture_dir = fixture_dir
        self.sandbox_dir = sandbox_dir
        self.clanker_path = clanker_path

    def run_tests(self) -> RunResult:
        if self.sandbox_dir.exists():
            shutil.rmtree(self.sandbox_dir)
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)

        file_suite_results = self._run_file_analysis_suites()
        assert_suite_results = self._run_assert_suites()

        return RunResult(
            file_analysis_results=file_suite_results,
            assert_suite_results=assert_suite_results,
        )

    def _run_file_analysis_suites(self) -> list[FileAnalysisResults]:
        return [FileAnalysisSuite(self.content_dir).analyse_files()]

    def _run_assert_suites(self) -> list[AssertSuiteResult]:
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
    run_result: RunResult
    reports_dir: Path

    def evaluate_and_report(self) -> bool:
        if self.reports_dir.exists():
            shutil.rmtree(self.reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        self._write_report_file()
        self.write_console_report()

        return self.run_result.passed

    def _write_report_file(self) -> None:
        report_file = self.reports_dir / f"{self.run_result.name}.json"
        serialized_data = self.run_result.accept(JsonSerializerVisitor())
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(serialized_data, f, indent=2)

        html_report_file = self.reports_dir / f"{self.run_result.name}.html"
        html_content = self.run_result.accept(HtmlReportVisitor())
        with open(html_report_file, "w", encoding="utf-8") as f:
            f.write(html_content)

    def write_console_report(self) -> None:
        print(self.run_result.accept(ConsoleReportVisitor()))