#!/usr/bin/env -S python3 -B
import os
import sys
import subprocess
import tempfile
from pathlib import Path

def run_test_1(repo_root: Path) -> bool:
    print("\n--- Test 1: True Repo Inspection ---")
    clanker_dir = repo_root / ".clanker"
    exists = clanker_dir.exists() and clanker_dir.is_dir()
    print(f"📂 Checking true repo: {repo_root}")
    print(f"🔍 .clanker directory present? {'YES' if exists else 'NO'}")
    return True

def run_test_2(content_root: Path, clanker_path: Path) -> bool:
    print("\n--- Test 2: Isolated Sandbox Workspace ---")
    report_path = content_root / "test" / "reports" / "latest_run.json"
    
    # Create a temp directory next to ship_gate.py (inside content/test/)
    test_dir = content_root / "test"
    with tempfile.TemporaryDirectory(dir=test_dir, prefix="sandbox_") as sandbox_dir:
        sandbox_path = Path(sandbox_dir)
        print(f"📦 Created sandbox workspace: {sandbox_path}")
        
        # Execute clanker.py in test mode with sandbox as CWD
        print("🚀 Executing clanker.py in test mode against sandbox...")
        result = subprocess.run(
            [sys.executable, "-B", str(clanker_path), "--test", "--report-path", str(report_path)],
            cwd=sandbox_path,
            capture_output=True,
            text=True
        )
        
        print(f"📊 Clanker Exit Code: {result.returncode}")
        if result.stdout:
            print(f"📝 Clanker Stdout:\n{result.stdout.strip()}")
        if result.stderr:
            print(f"⚠️ Clanker Stderr:\n{result.stderr.strip()}")
            
        if report_path.exists():
            print(f"📄 Report successfully generated at: {report_path}")
        else:
            print("❌ Report file was NOT generated.")
            return False
            
    return result.returncode == 0

def main():
    content_root = Path(os.path.realpath(__file__)).parent.parent
    repo_root = content_root.parent
    clanker_path = content_root / "clanker.py"

    print("--------------------------------------------------")
    print("🧪 SHIP GATE INITIALIZED")
    print(f"📂 Resolved Repo Root    : {repo_root}")
    print(f"📂 Resolved Content Root : {content_root}")
    print(f"🐍 Clanker Script Path   : {clanker_path}")
    print("--------------------------------------------------")

    if not clanker_path.exists():
        sys.stderr.write(f"❌ Error: Could not find clanker.py at {clanker_path}\n")
        sys.exit(1)

    # Run Test 1
    test_1_pass = run_test_1(repo_root)
    
    # Run Test 2
    test_2_pass = run_test_2(content_root, clanker_path)

    print("\n--------------------------------------------------")
    if test_1_pass and test_2_pass:
        print("✅ ALL SHIP GATE TESTS PASSED")
        sys.exit(0)
    else:
        print("❌ SHIP GATE TESTS FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()