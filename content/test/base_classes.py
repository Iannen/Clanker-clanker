#!/usr/bin/env -S python3 -B
from results import TestSuiteResult, MethodResult
from pathlib import Path
from typing import Any
from expectance_impls import ActionsFactoryImpl

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
        for method_name, method in assert_methods:
            containers = method(ActionsFactoryImpl())
            if not isinstance(containers, list): containers = [containers]

            container_results = []
            idx = 1
            for container in containers:
                framedump_path = self.sandbox_dir / "framedumps" / f"{method_name}_{idx}.framedump"
                container_results.append(
                    container.run(self.sandbox_dir, self.clanker_path, framedump_path, test_number=idx)
                )
                idx += 1
            method_results.append(MethodResult(method_name, container_results))

        return TestSuiteResult(self.suite_target.__class__.__name__, "", method_results)