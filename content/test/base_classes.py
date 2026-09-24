#!/usr/bin/env -S python3 -B
import json
import sys
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from expectance_impls import Result, AtomicTest
from adapters.terminal.scripted_terminal_adapter import ExecutionFrame


@dataclass
class TestSuiteResult:
    suite_name: str
    results: list[Result] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)


class BaseFixtureTest:
    TEMPLATE_FIXTURE_NAME: str = ""

    def __init__(self, sandbox_dir: Path, clanker_path: Path) -> None:
        self.sandbox_dir = sandbox_dir
        self.clanker_path = clanker_path
        self._replay_seq: list[str] = []

    def run_tests(self) -> TestSuiteResult:
        tests = self._get_tests()
        suite_result = TestSuiteResult(suite_name=self.__class__.__name__)
        for test in tests:
            suite_result.results.extend(self._run_test(test))
        return suite_result

    def _run_test(self, test: AtomicTest) -> list[Result]:
        self._replay_seq.extend(test.sequence)
        framedump_path = self.sandbox_dir / "framedumps" / test.frames_filename
        frames = self._run_put(framedump_path)

        results = test.evaluate(frames)
        
        if test.reset_sequence:
            self._replay_seq = []
        return results

    def _run_put(self, framedump_path: Path) -> list[ExecutionFrame]:
        cmd = [
            sys.executable,
            "-B",
            str(self.clanker_path),
            "--test",
            "--input-script",
            *self._replay_seq,
            "--framedump-path",
            str(framedump_path),
        ]

        try:
            subprocess.run(
                cmd,
                cwd=self.sandbox_dir,
                capture_output=True,
                text=True,
                timeout=10.0,
            )
        except Exception as ex:
            print(ex)

        with open(framedump_path, "r", encoding="utf-8") as f:
            report_data = json.load(f)
            return [ExecutionFrame(**r) for r in report_data["records"]]

    def _get_tests(self) -> list[AtomicTest]:
        assert_methods = [
            attr_name
            for attr_name in self.__class__.__dict__.keys()
            if not attr_name.startswith("_") and callable(getattr(self, attr_name))
        ]

        atomic_tests: list[AtomicTest] = []

        for method_name in assert_methods:
            method = getattr(self, method_name)
            tests = method()

            if isinstance(tests, list):
                for index, test in enumerate(tests, start=1):
                    test.name = f"{method_name} #{index}"
                    test.frames_filename = f"{method_name}_{index}.framedump"
                    atomic_tests.append(test)
            elif tests is not None:
                test = tests
                test.name = method_name
                test.frames_filename = f"{method_name}.framedump"
                atomic_tests.append(tests)

        return atomic_tests