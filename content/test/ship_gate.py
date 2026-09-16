#!/usr/bin/env -S python3 -B
import os
import sys
import subprocess
import shutil
import json
from pathlib import Path
from abc import ABC, abstractmethod

# =====================================================================
# PATH CONSTANTS
# =====================================================================
CONTENT_ROOT = Path(os.path.realpath(__file__)).parent.parent
REPO_ROOT = CONTENT_ROOT.parent
CLANKER_PATH = CONTENT_ROOT / "clanker.py"
TEST_ROOT = CONTENT_ROOT / "test"
REPORTS_DIR = TEST_ROOT / "reports"
FIXTURES_DIR = TEST_ROOT / "test_repos"


# =====================================================================
# BASE TEST FIXTURE (The Engine)
# =====================================================================
class BaseFixtureTest(ABC):
    def __init__(self, fixture_name: str):
        self.fixture_name = fixture_name
        self.source_fixture = FIXTURES_DIR / fixture_name
        self.sandbox_dir = TEST_ROOT / f"active_sandbox_{fixture_name}"
        
        self.passed = False
        self.error_message = ""

    def setup_sandbox(self) -> bool:
        if not self.source_fixture.exists():
            self.error_message = f"Fixture path not found: {self.source_fixture}"
            return False
            
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        if self.sandbox_dir.exists():
            shutil.rmtree(self.sandbox_dir)
            
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(self.source_fixture, self.sandbox_dir, dirs_exist_ok=True)
        return True

    def run_scenario(self, input_script: list[str], report_filename: str) -> dict:
        """Run clanker in test mode with a specific input sequence and report path."""
        report_path = REPORTS_DIR / report_filename
        result = subprocess.run(
            [sys.executable, "-B", str(CLANKER_PATH), "--test", "--input-script"] + input_script + ["--report-path", str(report_path)],
            cwd=self.sandbox_dir,
            capture_output=True,
            text=True
        )
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "report_path": report_path
        }

    @abstractmethod
    def execute(self) -> bool:
        """Orchestrates test scenarios and assertions."""
        pass


# =====================================================================
# SPECIFIC TEST REPO SPECIFICATIONS
# =====================================================================
class TestRepo1(BaseFixtureTest):
    def __init__(self):
        super().__init__("test_repo_1")

    def execute(self) -> bool:
        if not self.setup_sandbox():
            return False

        try:
            # --- SCENARIO 1: Decline Initialization ---
            res_decline = self.run_scenario(["q"], "test_repo_1_decline.json")
            self.assert_decline_steps(res_decline)

            # Re-setup sandbox for a clean state before the second scenario if needed, 
            # or continue state inspection depending on workflow design.
            self.setup_sandbox()

            # --- SCENARIO 2: Accept Initialization ---
            # Type 'yes' and send Ctrl+D (\x04) to accept
            res_accept = self.run_scenario(["y", "e", "s", "\x04"], "test_repo_1_accept.json")
            self.assert_accept_steps(res_accept)

            self.passed = True
        except AssertionError as e:
            self.passed = False
            self.error_message = str(e)

        return self.passed

    def assert_decline_steps(self, res: dict) -> None:
        if res["exit_code"] != 0:
            raise AssertionError(f"Decline Step Failed: Clanker exited with code {res['exit_code']}. Stderr: {res['stderr'].strip()}")
        
        clanker_meta = self.sandbox_dir / ".clanker"
        if clanker_meta.exists():
            raise AssertionError("Decline Step Failed: Expected .clanker NOT to exist because initialization was declined.")

    def assert_accept_steps(self, res: dict) -> None:
        if res["exit_code"] != 0:
            raise AssertionError(f"Accept Step Failed: Clanker exited with code {res['exit_code']}. Stderr: {res['stderr'].strip()}")
        
        clanker_meta = self.sandbox_dir / ".clanker"
        if not clanker_meta.exists():
            raise AssertionError("Accept Step Failed: Expected .clanker to exist because initialization was accepted.")


# =====================================================================
# STANDALONE INSPECTOR / REPORTER (Phase 2)
# =====================================================================
class GateInspector:
    def __init__(self, fixture_tests: list):
        self.fixture_tests = fixture_tests

    def report(self) -> bool:
        print("\n--------------------------------------------------")
        print("🔍 PHASE 2: INSPECTING RESULTS & REPORTS")
        print("--------------------------------------------------")

        all_passed = True

        for test in self.fixture_tests:
            if test.passed:
                print(f"✅ PASS: Fixture [{test.fixture_name}] — All 3 assertion steps cleared. (Report: {test.report_path})")
            else:
                print(f"❌ FAIL: Fixture [{test.fixture_name}] — {test.error_message}")
                print(f"   💡 Inspectable sandbox left at: {test.sandbox_dir}")
                all_passed = False

        return all_passed


# =====================================================================
# MAIN ORCHESTRATOR
# =====================================================================
def main():
    if not CLANKER_PATH.exists():
        sys.stderr.write(f"❌ Error: Could not find clanker.py at {CLANKER_PATH}\n")
        sys.exit(1)

    print("--------------------------------------------------")
    print("⚙️  PHASE 1: EXECUTING TESTS & GENERATING ARTIFACTS")
    print("--------------------------------------------------")

    # Run fixture test suite
    fixture_tests = [TestRepo1()]
    for test in fixture_tests:
        test.execute()
        print(f"[{'✓' if test.passed else '✗'}] Fixture Test [{test.fixture_name}] executed (Exit Code: {test.exit_code}).")

    # Phase 2: Inspection & Reporting
    inspector = GateInspector(fixture_tests)
    success = inspector.report()

    print("--------------------------------------------------")
    if success:
        print("🎉 ALL QUALITY GATES CLEARED SUCCESSFULLY")
        sys.exit(0)
    else:
        print("💥 QUALITY GATES FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()