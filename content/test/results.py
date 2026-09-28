from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from adapters.terminal.scripted_terminal_adapter import ExecutionFrame


@dataclass(slots=True)
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

    def accept(self, visitor):
        return visitor.visit_file_report(self)


@dataclass(slots=True)
class FileAnalysisResults:
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

    def accept(self, visitor):
        return visitor.visit_file_analysis_results(self)


@dataclass(slots=True)
class ExpectanceResult:
    assertion: str = ""
    passed: bool = False
    details: str = ""

    def accept(self, visitor):
        return visitor.visit_expectance_result(self)


@dataclass(slots=True)
class SandboxOperationsResult:
    operations: list[tuple[str, str, bool]]
    disk_state: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(passed for _, _, passed in self.operations)

    def accept(self, visitor):
        return visitor.visit_sandbox_operations_result(self)


@dataclass(slots=True)
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

    def accept(self, visitor):
        return visitor.visit_atomic_test_result(self)


@dataclass(slots=True)
class ContainerResult:
    test_result: AtomicTestResult
    preop_result: Optional[SandboxOperationsResult] = None
    postop_result: Optional[SandboxOperationsResult] = None

    @property
    def passed(self) -> bool:
        pre_ok = self.preop_result.passed if self.preop_result else True
        post_ok = self.postop_result.passed if self.postop_result else True
        return pre_ok and self.test_result.passed and post_ok

    def accept(self, visitor):
        return visitor.visit_container_result(self)


@dataclass(slots=True)
class MethodResult:
    method_name: str
    container_results: list[ContainerResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.container_results)

    @property
    def atomic_tests(self) -> list[AtomicTestResult]:
        return [c.test_result for c in self.container_results]

    def accept(self, visitor):
        return visitor.visit_method_result(self)


@dataclass(slots=True)
class AssertSuiteResult:
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

    def accept(self, visitor):
        return visitor.visit_assert_suite_result(self)


class RunResult:
    __slots__ = (
        "file_analysis_results",
        "assert_suite_results",
        "name",
        "passed",
    )

    def __init__(
        self,
        file_analysis_results: list[FileAnalysisResults],
        assert_suite_results: list[AssertSuiteResult],
    ) -> None:
        self.file_analysis_results = file_analysis_results
        self.assert_suite_results = assert_suite_results
        self.name = datetime.now().strftime("Run<%Y.%m.%d.%H.%M>")
        self.passed = (
            all(fa.is_clean for fa in self.file_analysis_results)
            and all(suite.passed for suite in self.assert_suite_results)
        )

    def accept(self, visitor):
        return visitor.visit_run_result(self)