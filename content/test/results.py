from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
import re
from typing import Optional
from adapters.terminal.scripted_terminal_adapter import ExecutionFrame

class Outcome(IntEnum):
    INIT = 0
    PASS = 1
    FAIL = 2
    UNDEFINED = 3

@dataclass
class Result:
    outcome: Outcome = field(default=Outcome.INIT, kw_only=True)

    def accept(self, visitor):
        snake_name = re.sub(r"(?<!^)(?=[A-Z])", "_", self.__class__.__name__).lower()
        method_name = f"visit_{snake_name}"
        return getattr(visitor, method_name)(self)

    def __post_init__(self) -> None:
        if self.outcome != Outcome.INIT : return
        child_outcomes: list[Outcome] = []
        for val in self.__dict__.values():
            if isinstance(val, Result):
                child_outcomes.append(val.outcome)
            elif isinstance(val, (list, tuple, set)):
                for item in val:
                    if isinstance(item, Result):
                        child_outcomes.append(item.outcome)
        self.outcome = max(child_outcomes) if child_outcomes else Outcome.UNDEFINED

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

    def __post_init__(self) -> None:
        self.outcome = Outcome.PASS if self.is_clean else Outcome.FAIL

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

    def __post_init__(self) -> None:
        for r in self.reports:
            if r.outcome == Outcome.INIT:
                r.__post_init__()

        if not self.reports or self.is_clean:
            self.outcome = Outcome.PASS
        else:
            self.outcome = Outcome.FAIL

@dataclass
class ExpectanceResult(Result):
    assertion: str = ""
    details: str = ""

@dataclass
class SandboxOperationsResult(Result):
    operations: list[tuple[str, str, Outcome]]
    disk_state: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
            if self.outcome != Outcome.INIT:
                return
            op_outcomes = [outcome for _, _, outcome in self.operations]
            # Max outcome ensures FAIL (2) overrides PASS (1), or PASS if all pass
            self.outcome = max(op_outcomes) if op_outcomes else Outcome.PASS

@dataclass
class AtomicTestResult(Result):
    test_number: int
    name: str
    expectance_results: list[ExpectanceResult] = field(default_factory=list)
    frames: list[ExecutionFrame] = field(default_factory=list)

    @property
    def total_expectances(self) -> int:
        return len(self.expectance_results)

    @property
    def passed_expectances(self) -> int:
        return sum(1 for r in self.expectance_results if r.outcome == Outcome.PASS)

@dataclass
class ContainerResult(Result):
    test_result: AtomicTestResult
    preop_result: Optional[SandboxOperationsResult] = None
    postop_result: Optional[SandboxOperationsResult] = None

@dataclass
class MethodResult(Result):
    method_name: str
    container_results: list[ContainerResult] = field(default_factory=list)

    @property
    def atomic_tests(self) -> list[AtomicTestResult]:
        return [c.test_result for c in self.container_results]

@dataclass
class AssertSuiteResult(Result):
    suite_name: str
    report_filename: str
    method_results: list[MethodResult]

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
        return sum(1 for t in self.all_atomic_tests if t.outcome == Outcome.PASS)

    @property
    def failed_tests(self) -> int:
        return sum(1 for t in self.all_atomic_tests if t.outcome == Outcome.FAIL)

@dataclass
class RunResult(Result):
    file_analysis_results: list[FileAnalysisResults]
    assert_suite_results: list[AssertSuiteResult]
    name: str = field(
        default_factory=lambda: datetime.now().strftime("Run<%Y.%m.%d.%H.%M>")
    )