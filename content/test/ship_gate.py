#!/usr/bin/env -S python3 -B

import inspect
import re
import shutil
import sys
from pathlib import Path

content_dir = Path(__file__).resolve().parent.parent
if str(content_dir) not in sys.path:
    sys.path.insert(0, str(content_dir))

from base_classes import BaseFixtureTest
from reporter import GateInspector
import assert_classes
from import_checker import ImportVerifier


def main() -> None:
    paths = verify_execution_context()
    reset_working_directories(paths["sandboxes_dir"], paths["reports_dir"])
    test_instances = prepare_and_run_test_suites(
        paths["fixtures_dir"],
        paths["sandboxes_dir"],
        paths["clanker_path"]
    )
    import_checker = run_import_verifier(paths["content_dir"])
    success = evaluate_and_report_results(import_checker, test_instances, paths["reports_dir"])

    status = "✅ SUCCESS" if success else "❌ FAILED"
    print(f"Accumulated test result: {status}")
    sys.exit(0 if success else 1)


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

    content_path = repo_root / "content"
    test_root = content_path / "test"
    return {
        "content_dir": content_path,
        "clanker_path": clanker_path,
        "fixtures_dir": test_root / "test_repos",
        "sandboxes_dir": test_root / "sandboxes",
        "reports_dir": test_root / "reports",
    }


def reset_working_directories(sandboxes_dir: Path, reports_dir: Path) -> None:
    for target_dir in [sandboxes_dir, reports_dir]:
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)


def prepare_and_run_test_suites(fixtures_dir: Path, sandboxes_dir: Path, clanker_path: Path) -> list[BaseFixtureTest]:
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
        sandbox_path = sandboxes_dir / f"active_sandbox_{snake_name}"
        fixture_path = fixtures_dir / cls.TEMPLATE_FIXTURE_NAME

        shutil.copytree(fixture_path, sandbox_path)

        instance = cls(sandbox_path, clanker_path)
        instance.run_tests()
        instances.append(instance)

    return instances


def run_import_verifier(content_dir: Path) -> ImportVerifier:
    return ImportVerifier(content_dir)


def evaluate_and_report_results(import_checker: ImportVerifier, test_instances: list[BaseFixtureTest], reports_dir: Path) -> bool:
    inspector = GateInspector(import_checker, test_instances, reports_dir)
    return inspector.evaluate_and_report()


if __name__ == "__main__":
    main()