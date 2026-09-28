#!/usr/bin/env -S python3 -B
from abc import ABC
import inspect
from pathlib import Path
import re
import shutil
import sys
from typing import Any

import assert_classes as assert_cls_module
from expectance_impls import ActionsFactoryImpl
from import_checker import ImportSuite
from results import ImportSuiteResult, MethodResult, AssertSuiteResult

class myclass:
    def method(self):
        print("hlleo")

class TestSuitesRunner:
    def __init__(self, content_dir: Path, fixture_dir: Path, sandbox_dir: Path, clanker_path: Path) -> None:
        self .content_dir = content_dir
        self.fixture_dir = fixture_dir
        self.sandbox_dir = sandbox_dir
        self.clanker_path = clanker_path

    def run_tests(self) -> tuple[ImportSuiteResult, list[AssertSuiteResult]]:
        if self.sandbox_dir.exists(): shutil.rmtree(self.sandbox_dir)
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)

        import_suite_result = ImportSuite(self.content_dir).run_tests()

        assert_suite_results = [
            self._run_assert_class(assert_class) 
            for assert_class in self._get_assert_classes()
        ]

        return import_suite_result, assert_suite_results

    def _run_assert_class(self, assert_class) -> AssertSuiteResult:
            suite_target = assert_class() if isinstance(assert_class, type) else assert_class
            template_fixture_name = getattr(suite_target, "TEMPLATE_FIXTURE_NAME", "")

            snake_name = re.sub(r"(?<!^)(?=[A-Z])", "_", assert_class.__name__).lower()
            sandbox_path = self.sandbox_dir / f"active_sandbox_{snake_name}"
            fixture_path = self.fixture_dir / template_fixture_name

            if fixture_path.exists():
                shutil.copytree(fixture_path, sandbox_path)

            suite_result = self._run_suite_target(suite_target, sandbox_path)
            return suite_result

    def _run_suite_target(self, suite_target: Any, sandbox_dir: Path) -> AssertSuiteResult:
        method_results = []
        assert_methods = [
            (name, getattr(suite_target, name))
            for name, attr in suite_target.__class__.__dict__.items()
            if not name.startswith("_") and callable(getattr(suite_target, name))
        ]

        for method_name, method in assert_methods:
            containers = method(ActionsFactoryImpl())
            if not isinstance(containers, list):
                containers = [containers]

            container_results = []
            idx = 1
            for container in containers:
                framedump_path = sandbox_dir / "framedumps" / f"{method_name}_{idx}.framedump"
                container_results.append(
                    container.run(sandbox_dir, self.clanker_path, framedump_path, test_number=idx)
                )
                idx += 1
            method_results.append(MethodResult(method_name, container_results))

        return AssertSuiteResult(suite_target.__class__.__name__, "", method_results)


    def _get_assert_classes(self):
        assert_classes = [
            cls
            for _, cls in inspect.getmembers(assert_cls_module, inspect.isclass)
            if cls.__module__ == "assert_classes" and not issubclass(cls, ABC)
        ]
        if not assert_classes:
            sys.stderr.write("Error: No test classes found in assert_classes.py\n")
            sys.exit(1)
        return assert_classes