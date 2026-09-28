#!/usr/bin/env -S python3 -B
from reporter import TestSuiteResult, MethodResult, AtomicTestResult, ContainerResult
import json
from pathlib import Path
import subprocess
import sys
from typing import Any
from expectance_impls import ActionsFactoryImpl
from adapters.terminal.scripted_terminal_adapter import ExecutionFrame, ScriptedTerminalAdapter


class BaseFixtureTest:
    def __init__(self, suite_target: Any, sandbox_dir: Path, clanker_path: Path) -> None:
        self.suite_target = suite_target() if isinstance(suite_target, type) else suite_target
        self.sandbox_dir = sandbox_dir
        self.clanker_path = clanker_path
        self.TEMPLATE_FIXTURE_NAME: str = getattr(self.suite_target, "TEMPLATE_FIXTURE_NAME", "")

    def run_tests(self) -> TestSuiteResult:
        method_results = []        
        assert_methods = [
            (name, getattr(self.suite_target, name))
            for name, attr in self.suite_target.__class__.__dict__.items()
            if not name.startswith("_") and callable(getattr(self.suite_target, name))
        ]
        for method_name, method in assert_methods: #TODO: clean
            containers = method(ActionsFactoryImpl())
            if not isinstance(containers, list): containers = [containers]

            container_results = []
            idx = 1
            for container in containers:
                framedump_path = self.sandbox_dir / "framedumps" / f"{method_name}_{idx}.framedump"
                
                preop_out = container.preop.execute(self.sandbox_dir)
                frames = self._run_put(container.sequence, framedump_path)
                test_res = container.expect.evaluate(frames, name=container.name, test_number=idx)

                postop_out = container.postop.execute(self.sandbox_dir)

                container_results.append(
                    ContainerResult(
                        test_result=test_res,
                        preop_result=preop_out,
                        postop_result=postop_out,
                    )
                )
                idx += 1
            method_results.append(MethodResult(method_name, container_results))

        return TestSuiteResult(self.suite_target.__class__.__name__, "", method_results)

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
            latest_input=ScriptedTerminalAdapter.CRASH_EVENT,
            exit_code=1,
            stderr=stderr_output,
        )
        existing_frames.append(crash_frame)
        return existing_frames