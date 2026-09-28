from dataclasses import dataclass, field

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

    def to_dict(self) -> dict:
        return {
            "rel_path": self.rel_path,
            "forbidden_import_statements": self.forbidden_import_statements,
            "dangling_imports": self.dangling_imports,
            "undeclared_imports": self.undeclared_imports,
        }

    def to_console(self) -> list[str]:
        lines = [f"    ❌ {self.rel_path}"]
        for err in (
            self.forbidden_import_statements
            + self.dangling_imports
            + self.undeclared_imports
        ):
            lines.append(f"        * {err}")
        return lines


@dataclass(slots=True)
class ImportSuiteResult:
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

    def to_dict(self) -> list[dict]:
        return [r.to_dict() for r in self.reports]

    def to_console(self) -> str:
        if self.is_clean:
            lines = [
                f"✅ Import Checker - {self.total_files_checked} files clean",
                "    Report: import_checker.json",
            ]
        else:
            lines = ["❌ Import Checker"]
            for r in self.reports:
                if not r.is_clean:
                    lines.extend(r.to_console())
            lines.append("    Report: import_checker.json")
        return "\n".join(lines)


@dataclass(slots=True)
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


@dataclass(slots=True)
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

    def to_console(self) -> str:
        if self.crashed:
            return f"        💀 Test #{self.test_number} - Application terminated unexpectedly"
        test_icon = "✅" if self.passed else "❌"
        return (
            f"        {test_icon} Test #{self.test_number} - "
            f"{self.passed_expectances}/{self.total_expectances} expectances"
        )


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

    def to_dict(self) -> dict:
        return {
            "test_result": self.test_result.to_dict(),
            "preop_result": self.preop_result.to_dict() if self.preop_result else None,
            "postop_result": self.postop_result.to_dict() if self.postop_result else None,
            "passed": self.passed,
        }


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

    def to_dict(self) -> dict:
        return {
            "method_name": self.method_name,
            "passed": self.passed,
            "container_results": [c.to_dict() for c in self.container_results],
        }

    def to_console(self) -> str:
        method_icon = "✅" if self.passed else "❌"
        lines = [f"    {method_icon} {self.method_name}"]
        for test in self.atomic_tests:
            lines.append(test.to_console())
        return "\n".join(lines)


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

    def to_dict(self) -> dict:
        return {
            "suite_name": self.suite_name,
            "report_filename": self.report_filename,
            "passed": self.passed,
            "methods": [m.to_dict() for m in self.method_results],
        }

    def to_console(self) -> str:
        class_icon = "✅" if self.passed else "❌"
        lines = [f"\n{class_icon} {self.suite_name}"]
        for m in self.method_results:
            lines.append(m.to_console())
        lines.append(f"    Report: {self.report_filename}")
        return "\n".join(lines)