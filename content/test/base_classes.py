#!/usr/bin/env -S python3 -B
from reporter import TestSuiteResult, MethodResult, AtomicTestResult
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from adapters.terminal.scripted_terminal_adapter import ExecutionFrame, ScriptedTerminalAdapter


class BaseFixtureTest:
    def __init__(self, suite_target: Any, sandbox_dir: Path, clanker_path: Path) -> None:
        self.suite_target = suite_target() if isinstance(suite_target, type) else suite_target
        self.sandbox_dir = sandbox_dir
        self.clanker_path = clanker_path
        self.TEMPLATE_FIXTURE_NAME: str = getattr(self.suite_target, "TEMPLATE_FIXTURE_NAME", "")

    def run_tests(self) -> TestSuiteResult:
        from expectance_impls import ActionsFactoryImpl, ExecutionImpl, SandboxImpl

        suite_result = TestSuiteResult(suite_name=self.suite_target.__class__.__name__)
        assert_methods = [
            attr_name
            for attr_name in self.suite_target.__class__.__dict__.keys()
            if not attr_name.startswith("_") and callable(getattr(self.suite_target, attr_name))
        ]

        for method_name in assert_methods:
            method = getattr(self.suite_target, method_name)
            actions = ActionsFactoryImpl()
            items = method(actions)

            if not isinstance(items, list):
                items = [items] if items is not None else []

            method_result = MethodResult(method_name=method_name)
            atomic_idx = 1

            for item in items:
                if isinstance(item, SandboxImpl):
                    sb_results = item.execute(self.sandbox_dir)
                    method_result.action_results.extend(sb_results)
                elif isinstance(item, ExecutionImpl):
                    item.name = f"{method_name} #{atomic_idx}"
                    item.frames_filename = f"{method_name}_{atomic_idx}.framedump"
                    atomic_result = self._run_test(item, atomic_idx)
                    method_result.action_results.append(atomic_result)
                    atomic_idx += 1

            suite_result.method_results.append(method_result)

        return suite_result

    def _run_test(self, test: "ExecutionImpl", test_num: int) -> AtomicTestResult:
        framedump_path = self.sandbox_dir / "framedumps" / test.frames_filename
        frames = self._run_put(test.sequence, framedump_path)
        return test.to_result(frames, test_number=test_num)

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