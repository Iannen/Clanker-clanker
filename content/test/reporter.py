import json
from pathlib import Path
from typing import Optional
import re
from dataclasses import dataclass, field
from adapters.terminal.scripted_terminal_adapter import ExecutionFrame


@dataclass
class GateInspector:
    import_reports: ImportReports
    test_results: list[TestSuiteResult]
    reports_dir: Path

    def evaluate_and_report(self) -> bool:
        self._write_file_reports()
        return self.write_console_report()

    def _write_file_reports(self) -> None:
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        import_data = [
            {
                "rel_path": r.rel_path,
                "forbidden_import_statements": r.forbidden_import_statements,
                "dangling_imports": r.dangling_imports,
                "undeclared_imports": r.undeclared_imports,
            }
            for r in self.import_reports.reports
        ]
        with open(
            self.reports_dir / "import_checker.json",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(import_data, f, indent=2)

        for suite in self.test_results:
            snake_name = re.sub(r"(?<!^)(?=[A-Z])", "_", suite.suite_name).lower()
            report_file = f"{snake_name}.json"
            suite.report_filename = report_file

            with open(self.reports_dir / report_file, "w", encoding="utf-8") as f:
                json.dump(suite.to_dict(), f, indent=2)

    def write_console_report(self) -> bool:
        print("============================================================")
        print("Test results")
        print("============================================================")

        import_pass = self._report_import_verification()
        tests_pass = True

        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        crashed_tests = 0

        for suite in self.test_results:
            if not suite.passed:
                tests_pass = False

            total_tests += suite.total_tests
            passed_tests += suite.passed_tests
            failed_tests += suite.failed_tests
            crashed_tests += suite.crashed_tests

            class_icon = "✅" if suite.passed else "❌"
            print(f"\n{class_icon} {suite.suite_name}")

            for m in suite.method_results:
                method_icon = "✅" if m.passed else "❌"
                print(f"    {method_icon} {m.method_name}")

                for test in m.atomic_tests:
                    if test.crashed:
                        print(f"        💀 Test #{test.test_number} - Application terminated unexpectedly")
                    else:
                        test_icon = "✅" if test.passed else "❌"
                        print(
                            f"        {test_icon} Test #{test.test_number} - "
                            f"{test.passed_expectances}/{test.total_expectances} expectances"
                        )

            print(f"    Report: {suite.report_filename}")

        print("\n------------------------------------------------------------")
        print(
            f"TOTAL: {total_tests} tests | PASSED: {passed_tests} | "
            f"FAILED: {failed_tests} | CRASHED: {crashed_tests}"
        )
        print("============================================================")

        return import_pass and tests_pass

    def _report_import_verification(self) -> bool:
        if self.import_reports.is_clean:
            print(f"✅ Import Checker - {self.import_reports.total_files_checked} files clean")
            print("    Report: import_checker.json")
            return True

        print("❌ Import Checker")
        for report in self.import_reports.reports:
            if not report.is_clean:
                print(f"    ❌ {report.rel_path}")
                for err in (
                    report.forbidden_import_statements
                    + report.dangling_imports
                    + report.undeclared_imports
                ):
                    print(f"        * {err}")
        print("    Report: import_checker.json")
        return False

@dataclass
class AtomicTestResult:
    test_number: int
    name: str
    expectance_results: list[ExpectanceResult] = field(default_factory=list)
    frames: list[ExecutionFrame] = field(default_factory=list)
    crashed: bool = False
    crash_message: Optional[str] = None

    @property
    def passed(self) -> bool:
        if self.crashed:
            return False
        return all(r.passed for r in self.expectance_results)

    @property
    def total_expectances(self) -> int:
        return len(self.expectance_results)

    @property
    def passed_expectances(self) -> int:
        return sum(1 for r in self.expectance_results if r.passed)

    def to_dict(self) -> dict:
        return {
            "test_number": self.test_number,
            "name": self.name,
            "passed": self.passed,
            "crashed": self.crashed,
            "crash_message": self.crash_message,
            "expectances": [r.to_dict() for r in self.expectance_results],
            "frames": [frame.__dict__ for frame in self.frames],
        }

@dataclass
class ContainerResult:
    test_result: AtomicTestResult
    preop_result: Optional[SandboxOperationsResult] = None
    postop_result: Optional[SandboxOperationsResult] = None

    @property
    def passed(self) -> bool:
        pre_ok = self.preop_result.passed if self.preop_result else True
        post_ok = self.postop_result.passed if self.postop_result else True
        return pre_ok and self.test_result.passed and post_ok

    def to_dict(self) -> dict:
        return {
            "test_result": self.test_result.to_dict(),
            "preop_result": self.preop_result.to_dict() if self.preop_result else None,
            "postop_result": self.postop_result.to_dict() if self.postop_result else None,
            "passed": self.passed,
        }


@dataclass
class MethodResult:
    method_name: str
    container_results: list[ContainerResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.container_results)

    @property
    def atomic_tests(self) -> list[AtomicTestResult]:
        return [c.test_result for c in self.container_results]

    def to_dict(self) -> dict:
        return {
            "method_name": self.method_name,
            "passed": self.passed,
            "container_results": [c.to_dict() for c in self.container_results],
        }


@dataclass
class TestSuiteResult:
    suite_name: str
    report_filename: str
    method_results: list[MethodResult]

    @property
    def passed(self) -> bool:
        return all(m.passed for m in self.method_results)

    @property
    def all_atomic_tests(self) -> list[AtomicTestResult]:
        return [
            t
            for m in self.method_results
            for t in m.atomic_tests
        ]

    @property
    def total_tests(self) -> int:
        return len(self.all_atomic_tests)

    @property
    def passed_tests(self) -> int:
        return sum(1 for t in self.all_atomic_tests if t.passed)

    @property
    def failed_tests(self) -> int:
        return sum(1 for t in self.all_atomic_tests if not t.passed and not t.crashed)

    @property
    def crashed_tests(self) -> int:
        return sum(1 for t in self.all_atomic_tests if t.crashed)

    def to_dict(self) -> dict:
        return {
            "suite_name": self.suite_name,
            "report_filename": self.report_filename,
            "passed": self.passed,
            "methods": [m.to_dict() for m in self.method_results],
        }

@dataclass
class ExpectanceResult:
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

@dataclass
class SandboxOperationsResult:
    operations: list[tuple[str, str, bool]]
    disk_state: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(passed for _, _, passed in self.operations)

    def to_dict(self) -> dict:
        return {
            "type": "sandbox_operations",
            "passed": self.passed,
            "operations": [
                {
                    "operation": op_type,
                    "description": desc,
                    "passed": passed,
                }
                for op_type, desc, passed in self.operations
            ],
            "disk_state": self.disk_state,
        }

@dataclass
class ImportReports:
    reports: list[FileReport] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return all(r.is_clean for r in self.reports)

    @property
    def total_files_checked(self) -> int:
        return len(self.reports)

    @property
    def total_violations(self) -> int:
        return sum(
            len(r.forbidden_import_statements)
            + len(r.dangling_imports)
            + len(r.undeclared_imports)
            for r in self.reports
        )

@dataclass
class FileReport:
    rel_path: str
    forbidden_import_statements: list[str] = field(default_factory=list)
    dangling_imports: list[str] = field(default_factory=list)
    undeclared_imports: list[str] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return not (
            self.forbidden_import_statements
            or self.dangling_imports
            or self.undeclared_imports
        )