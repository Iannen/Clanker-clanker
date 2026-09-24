#!/usr/bin/env -S python3 -B
import json
import sys
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from expectance_impls import Result, AtomicTest, SandboxOperations
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

    def run_tests(self) -> TestSuiteResult:
        actions = self._get_actions()
        suite_result = TestSuiteResult(suite_name=self.__class__.__name__)
        for action in actions:
            if isinstance(action, SandboxOperations):
                action.execute(self.sandbox_dir)
            elif isinstance(action, AtomicTest):
                suite_result.results.extend(self._run_test(action))
        return suite_result

    def _run_test(self, test: AtomicTest) -> list[Result]:
        framedump_path = self.sandbox_dir / "framedumps" / test.frames_filename
        frames = self._run_put(test.sequence, framedump_path)
        
        if frames and frames[-1].exit_code == 1:
            return [
                Result(
                    assertion=f"The subprocess crashed",
                    passed=False,
                    details=f"Unexpected crash (exit code 1):\n{frames[-1].stderr or ''}"
                )
            ]

        return test.evaluate(frames)

    def _run_put(self, sequence: list[str], framedump_path: Path) -> list[ExecutionFrame]:
        cmd = [
            sys.executable,
            "-B",
            str(self.clanker_path),
            "--test",
            "--input-script",
            *sequence,
            "--framedump-path",
            str(framedump_path),
        ]

        exit_code = 0
        stderr_output = ""

        try:
            proc = subprocess.run(
                cmd,
                cwd=self.sandbox_dir,
                capture_output=True,
                text=True,
                timeout=10.0,
            )
            exit_code = proc.returncode
            stderr_output = proc.stderr
        except Exception as ex:
            exit_code = 1
            stderr_output = str(ex)

        existing_frames = []
        if framedump_path.exists():
            try:
                with open(framedump_path, "r", encoding="utf-8") as f:
                    report_data = json.load(f)
                    existing_frames = [ExecutionFrame(**r) for r in report_data["records"]]
            except Exception:
                pass

        if exit_code == 0:
            return existing_frames

        crash_frame = ExecutionFrame(
            latest_input=ScriptedTerminalAdapter.END_APP_EVENT,
            exit_code=1,
            stderr=stderr_output,
        )
        existing_frames.append(crash_frame)
        return existing_frames

    def _get_actions(self) -> list[AtomicTest | SandboxOperations]:
        assert_methods = [
            attr_name
            for attr_name in self.__class__.__dict__.keys()
            if not attr_name.startswith("_") and callable(getattr(self, attr_name))
        ]

        actions: list[AtomicTest | SandboxOperations] = []

        for method_name in assert_methods:
            method = getattr(self, method_name)
            items = method()

            if not isinstance(items, list):
                items = [items] if items is not None else []

            atomic_idx = 1
            for item in items:
                if isinstance(item, AtomicTest):
                    item.name = f"{method_name} #{atomic_idx}"
                    item.frames_filename = f"{method_name}_{atomic_idx}.framedump"
                    atomic_idx += 1
                    actions.append(item)
                elif isinstance(item, SandboxOperations):
                    actions.append(item)

        return actions