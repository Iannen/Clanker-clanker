from dataclasses import dataclass, field
from datetime import datetime
import re
from typing import Optional
from adapters.terminal.scripted_terminal_adapter import ExecutionFrame


class Result:
    def accept(self, visitor):
        snake_name = re.sub(r"(?<!^)(?=[A-Z])", "_", self.__class__.__name__).lower()
        method_name = f"visit_{snake_name}"
        return getattr(visitor, method_name)(self)


@dataclass
class FileReport(Result):
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


@dataclass
class FileAnalysisResults(Result):
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
class ExpectanceResult(Result):
    assertion: str = ""
    passed: bool = False
    details: str = ""


@dataclass
class SandboxOperationsResult(Result):
    operations: list[tuple[str, str, bool]]
    disk_state: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(passed for _, _, passed in self.operations)


@dataclass
class AtomicTestResult(Result):
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


@dataclass
class ContainerResult(Result):
    test_result: AtomicTestResult
    preop_result: Optional[SandboxOperationsResult] = None
    postop_result: Optional[SandboxOperationsResult] = None

    @property
    def passed(self) -> bool:
        pre_ok = self.preop_result.passed if self.preop_result else True
        post_ok = self.postop_result.passed if self.postop_result else True
        return pre_ok and self.test_result.passed and post_ok


@dataclass
class MethodResult(Result):
    method_name: str
    container_results: list[ContainerResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.container_results)

    @property
    def atomic_tests(self) -> list[AtomicTestResult]:
        return [c.test_result for c in self.container_results]


@dataclass
class AssertSuiteResult(Result):
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


@dataclass
class RunResult(Result):
    file_analysis_results: list[FileAnalysisResults]
    assert_suite_results: list[AssertSuiteResult]
    name: str = field(
        default_factory=lambda: datetime.now().strftime("Run<%Y.%m.%d.%H.%M>")
    )
    passed: bool = field(init=False)

    def __post_init__(self) -> None:
        self.passed = (
            all(fa.is_clean for fa in self.file_analysis_results)
            and all(suite.passed for suite in self.assert_suite_results)
        )