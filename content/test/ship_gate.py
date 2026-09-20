#!/usr/bin/env -S python3 -B

import inspect
import re
import shutil
import sys
from pathlib import Path

from base_classes import BaseFixtureTest, GateInspector
import assert_classes


def main() -> None:
    context = verify_execution_context()
    test_instances = instantiate_test_classes(context)
    setup_sandboxes_and_reports(context, test_instances)
    run_tests(test_instances)
    evaluate_tests(test_instances)


def verify_execution_context() -> dict[str, Path]:
    repo_root = Path.cwd()
    clanker_path = repo_root / "content" / "clanker.py"
    gate_script_path = repo_root / "content" / "test" / "ship_gate.py"

    if not clanker_path.is_file():
        sys.stderr.write(
            f"[CRITICAL FAILURE] Must run from repository root.\n"
            f"Missing target binary at: {clanker_path}\n"
        )
        sys.exit(1)

    if Path(__file__).resolve() != gate_script_path.resolve():
        sys.stderr.write(
            f"[CRITICAL FAILURE] Invalid execution context.\n"
            f"Expected script location: {gate_script_path}\n"
            f"Actual resolved script:  {Path(__file__).resolve()}\n"
        )
        sys.exit(1)

    test_root = repo_root / "content" / "test"
    return {
        "repo_root": repo_root,
        "test_root": test_root,
        "fixtures_dir": test_root / "test_repos",
        "sandboxes_dir": test_root / "sandboxes",
        "reports_dir": test_root / "reports",
    }


def instantiate_test_classes(context: dict[str, Path]):
    from base_classes import BaseFixtureTest
    import assert_classes

    discovered_classes = [
        cls
        for name, cls in inspect.getmembers(assert_classes, inspect.isclass)
        if cls.__module__ == "assert_classes" and issubclass(cls, BaseFixtureTest)
    ]

    if not discovered_classes:
        sys.stderr.write("Error: No test classes found in assert_classes.py\n")
        sys.exit(1)

    instances = []
    for cls in discovered_classes:
        snake_name = re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()
        fixture_path = context["fixtures_dir"] / cls.TEMPLATE_FIXTURE_NAME
        sandbox_path = context["sandboxes_dir"] / f"active_sandbox_{snake_name}"
        report_path = context["reports_dir"] / f"{snake_name}.json"

        instance = cls(sandbox_path, context["clanker_path"])
        instances.append(instance)

    return instances


def setup_sandboxes_and_reports(context: dict[str, Path], test_instances) -> None:
    for target_dir in [context["sandboxes_dir"], context["reports_dir"]]:
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

    for instance in test_instances:
        snake_name = re.sub(r"(?<!^)(?=[A-Z])", "_", instance.__class__.__name__).lower()
        instance.sandbox_dir = context["sandboxes_dir"] / f"active_sandbox_{snake_name}"
        
        fixture_path = context["fixtures_dir"] / instance.TEMPLATE_FIXTURE_NAME
        shutil.copytree(fixture_path, instance.sandbox_dir)


def run_tests(test_instances) -> None:
    for instance in test_instances:
        instance.run_tests()


def evaluate_tests(test_instances) -> None:
    from base_classes import GateInspector

    interpreter = GateInspector(test_instances)
    success = interpreter.evaluate_and_report()

    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()