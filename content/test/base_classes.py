#!/usr/bin/env -S python3 -B
import json
import sys
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from expectance_impls import Result, AtomicTest
from adapters.terminal.scripted_terminal_adapter import ExecutionFrame, ScriptedTerminalAdapter


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
        self.report_path = self.sandbox_dir / "latest_run.json"
        self._replay_seq: list[str] = []

    def run_tests(self) -> TestSuiteResult:
        tests = self._get_tests()
        suite_result = TestSuiteResult(suite_name=self.__class__.__name__)
        for test in tests:
            suite_result.results.extend(self._run_test(test))
        return suite_result

    def _run_test(self, test: AtomicTest) -> list[Result]:
        self._replay_seq.extend(test.sequence)
        frames = self._run_put()

        target_frame = frames[-1]
        results = test.evaluate(target_frame)
        
        if test.reset_sequence:
            self._replay_seq = []
        return results

    def _run_put(self) -> list[ExecutionFrame]:
        clean_replay_seq = [s for s in self._replay_seq if s != "__END_APP__"]

        cmd = [
            sys.executable,
            "-B",
            str(self.clanker_path),
            "--test",
            "--input-script",
            *clean_replay_seq,
            "--report-path",
            str(self.report_path),
        ]

        try:
            completed = subprocess.run(
                cmd,
                cwd=self.sandbox_dir,
                capture_output=True,
                text=True,
                timeout=10.0,
            )
            exit_code = completed.returncode
            stdout = completed.stdout.strip()
            stderr = completed.stderr
        except subprocess.TimeoutExpired as ex:
            exit_code = -1
            stdout = ex.stdout.decode("utf-8").strip() if ex.stdout else ""
            stderr = "Execution timed out"

        frames: list[ExecutionFrame] = []

        if self.report_path.is_file():
            try:
                with open(self.report_path, "r", encoding="utf-8") as f:
                    report_data = json.load(f)
                    raw_records = report_data.get("records", [])
                    for record in raw_records:
                        frames.append(
                            ExecutionFrame(
                                latest_input=record.get("latest_input"),
                                latest_write=record.get("latest_write"),
                                latest_clipboard=record.get("latest_clipboard"),
                                disk_paths=record.get("disk_paths", []),
                            )
                        )
            except Exception:
                pass

        final_disk_paths = []
        if self.sandbox_dir.is_dir():
            for path in sorted(self.sandbox_dir.rglob("*")):
                final_disk_paths.append(str(path.relative_to(self.sandbox_dir)))

        if self._replay_seq and self._replay_seq[-1] == ScriptedTerminalAdapter.END_APP_EVENT:
            frames.append(
                ExecutionFrame(
                    latest_input=ScriptedTerminalAdapter.END_APP_EVENT,
                    exit_code=exit_code,
                    stdout=stdout,
                    stderr=stderr,
                    disk_paths=final_disk_paths,
                )
            )
        return frames

    def _get_tests(self) -> list[AtomicTest]:
        assert_methods = [
            attr_name
            for attr_name in self.__class__.__dict__.keys()
            if not attr_name.startswith("_") and callable(getattr(self, attr_name))
        ]

        atomic_tests: list[AtomicTest] = []

        for method_name in assert_methods:
            method = getattr(self, method_name)
            result = method()

            if isinstance(result, list):
                for index, test in enumerate(result, start=1):
                    test.name = f"{method_name} #{index}"
                    atomic_tests.append(test)
            elif result is not None:
                result.name = method_name
                atomic_tests.append(result)

        return atomic_tests