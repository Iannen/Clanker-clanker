#!/usr/bin/env -S python3 -B

import sys
from pathlib import Path

content_dir = Path(__file__).resolve().parent.parent
if str(content_dir) not in sys.path:
    sys.path.insert(0, str(content_dir))

from base_classes import TestSuiteRunner
from reporter import GateInspector

def get_verified_clanker_runnable_path(repo_root: Path) -> Path:
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
    return clanker_path

def verify_execution_context() -> dict[str, Path]:
    repo_root = Path.cwd()   
    content_dir = repo_root / "content"
    clanker_path = get_verified_clanker_runnable_path(repo_root)
    test_root = content_dir / "test"
    fixture_dir = test_root / "test_repos"
    sandbox_dir = test_root / "sandboxes"
    reports_dir = test_root / "reports"

    return content_dir, clanker_path, fixture_dir, sandbox_dir, reports_dir

if __name__ == "__main__":
    content_dir, clanker_path, fixture_dir, sandbox_dir, reports_dir = verify_execution_context()

    runner = TestSuiteRunner(
        content_dir = content_dir,
        fixture_dir = fixture_dir,
        sandbox_dir = sandbox_dir,
        clanker_path = clanker_path
    )
    import_reports, test_results = runner.run_tests()

    inspector = GateInspector(
        import_result = import_reports, 
        assert_results = test_results, 
        reports_dir = reports_dir
    )
    success = inspector.evaluate_and_report()
    status = "✅ SUCCESS" if success else "❌ FAILED"
    print(f"Result: {status}")
    sys.exit(0 if success else 1)