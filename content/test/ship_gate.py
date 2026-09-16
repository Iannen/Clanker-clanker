#!/usr/bin/env -S python3 -B
import os
import sys
import subprocess
import shutil
import json
from pathlib import Path

# =====================================================================
# PATH CONSTANTS
# =====================================================================
CONTENT_ROOT = Path(os.path.realpath(__file__)).parent.parent
REPO_ROOT = CONTENT_ROOT.parent
CLANKER_PATH = CONTENT_ROOT / "clanker.py"
TEST_ROOT = CONTENT_ROOT / "test"
REPORTS_DIR = TEST_ROOT / "reports"
REPORT_PATH = REPORTS_DIR / "latest_run.json"
FIXTURES_DIR = TEST_ROOT / "test_repos"
SANDBOX_DIR = TEST_ROOT / "active_sandbox"


# =====================================================================
# PHASE 1: EXECUTION & GENERATION
# =====================================================================
def phase_1_execute() -> dict:
    print("--------------------------------------------------")
    print("⚙️  PHASE 1: EXECUTING TESTS & GENERATING ARTIFACTS")
    print("--------------------------------------------------")
    
    results = {}

    # --- Test 1 Execution ---
    clanker_dir = REPO_ROOT / ".clanker"
    results["test_1"] = {
        "name": "True Repo Inspection",
        "passed": clanker_dir.exists() and clanker_dir.is_dir(),
        "detail": f"Checked root {REPO_ROOT}"
    }
    print(f"[{'✓' if results['test_1']['passed'] else '✗'}] Test 1 executed.")

    # --- Test 2 Execution ---
    source_fixture = FIXTURES_DIR / "test_repo_1"
    if not source_fixture.exists():
        results["test_2"] = {
            "name": "Fixture Workspace (test_repo_1)",
            "passed": False,
            "detail": f"Fixture not found at {source_fixture}"
        }
    else:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        if SANDBOX_DIR.exists():
            shutil.rmtree(SANDBOX_DIR)
        SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source_fixture, SANDBOX_DIR, dirs_exist_ok=True)

        # Run clanker in test mode (capturing stdout/stderr quietly for Phase 1)
        proc_result = subprocess.run(
            [sys.executable, "-B", str(CLANKER_PATH), "--test", "--report-path", str(REPORT_PATH)],
            cwd=SANDBOX_DIR,
            capture_output=True,
            text=True
        )

        results["test_2"] = {
            "name": "Fixture Workspace (test_repo_1)",
            "passed": proc_result.returncode == 0,
            "exit_code": proc_result.returncode,
            "report_path": REPORT_PATH,
            "detail": "Sandbox execution completed"
        }
        print(f"[{'✓' if results['test_2']['passed'] else '✗'}] Test 2 executed (Exit Code: {proc_result.returncode}).")

    return results


# =====================================================================
# PHASE 2: RUMMAGING & REPORTING
# =====================================================================
def phase_2_inspect(results: dict) -> bool:
    print("\n--------------------------------------------------")
    print("🔍 PHASE 2: INSPECTING RESULTS & REPORTS")
    print("--------------------------------------------------")

    all_passed = True

    # Inspect Test 1
    t1 = results.get("test_1", {})
    if t1.get("passed"):
        print(f"✅ PASS: {t1['name']} — .clanker directory verified in project root.")
    else:
        print(f"❌ FAIL: {t1['name']} — .clanker directory missing. (Details: {t1.get('detail')})")
        all_passed = False

    # Inspect Test 2 (and rummage through the JSON report)
    t2 = results.get("test_2", {})
    report_file = t2.get("report_path")
    
    if t2.get("passed"):
        # Rummage through JSON report for extra sanity metrics if it exists
        frame_count = 0
        if report_file and report_file.exists():
            try:
                with open(report_file, "r") as f:
                    report_data = json.load(f)
                    # Assuming your ScriptedIOBridge stores frames or history in a list/dict
                    frame_count = len(report_data.get("frames", report_data.get("history", [])))
            except Exception:
                pass
        
        print(f"✅ PASS: {t2['name']} — Sandbox run successful. (Report: {report_file})")
    else:
        print(f"❌ FAIL: {t2['name']} — Execution failed. Review report at: {report_file}")
        all_passed = False

    return all_passed


def main():
    if not CLANKER_PATH.exists():
        sys.stderr.write(f"❌ Error: Could not find clanker.py at {CLANKER_PATH}\n")
        sys.exit(1)

    # Execute Phase 1
    execution_results = phase_1_execute()

    # Execute Phase 2
    success = phase_2_inspect(execution_results)

    print("--------------------------------------------------")
    if success:
        print("🎉 ALL QUALITY GATES CLEARED SUCCESSFULLY")
        print(f"💡 Inspectable sandbox left at: {SANDBOX_DIR}")
        sys.exit(0)
    else:
        print("💥 QUALITY GATES FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()