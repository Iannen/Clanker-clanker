#!/usr/bin/env -S python3 -B
import argparse
import os
import subprocess
import sys
from pathlib import Path


def fail(msg: str) -> None:
    print(f"❌ SAVE BLOCKED: {msg}", file=sys.stderr)
    print("-" * 50, file=sys.stderr)
    print("CONFIRMED: The script has had NO EFFECT on your repository state.", file=sys.stderr)
    sys.exit(1)


def run_cmd(cmd: list[str] | str, check: bool = False, capture_output: bool = True, shell: bool = False) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            cmd,
            check=check,
            capture_output=capture_output,
            text=True,
            shell=shell,
        )
    except Exception as e:
        cmd_str = cmd if isinstance(cmd, str) else " ".join(cmd)
        fail(f"Failed to execute command '{cmd_str}': {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Safely stage, commit, and push local changes.")
    parser.add_argument(
        "-t",
        "--test_command",
        type=str,
        default=None,
        help="Custom test command to execute before git operations (e.g., 'python3 -B content/test/ship_gate.py').",
    )
    parser.add_argument(
        "--no_test",
        action="store_true",
        help="Explicitly skip running any test command prior to saving.",
    )
    args = parser.parse_args()

    repo_root = Path.cwd()
    clanker_path = repo_root / "content" / "clanker.py"
    if not clanker_path.is_file() or not (repo_root / ".git").exists():
        fail(f"Must run script from repository root ('{repo_root}').")

    if args.test_command and not args.no_test:
        print(f"🛡️  Running test command: '{args.test_command}'...")
        test_res = run_cmd(args.test_command, capture_output=False, shell=True)
        if test_res.returncode != 0:
            fail(f"Test command failed with exit code {test_res.returncode}.")

    res = run_cmd(["git", "rev-parse", "--is-inside-work-tree"])
    if res.returncode != 0 or res.stdout.strip() != "true":
        fail(f"Not inside a git repository ({repo_root}).")

    if run_cmd(["git", "rev-parse", "--verify", "HEAD"]).returncode != 0:
        fail(f"Repository has no commits ({repo_root}).")

    if run_cmd(["git", "config", "user.name"]).returncode != 0:
        fail(f"Git user.name not configured ({repo_root}).")

    if run_cmd(["git", "config", "user.email"]).returncode != 0:
        fail(f"Git user.email not configured ({repo_root}).")

    res_conflicts = run_cmd(["git", "ls-files", "-u"])
    if res_conflicts.stdout.strip():
        fail(f"Unresolved merge conflicts detected ({repo_root}).")

    res_branch = run_cmd(["git", "symbolic-ref", "--quiet", "--short", "HEAD"])
    if res_branch.returncode != 0:
        fail(f"Detached HEAD ({repo_root}).")

    if run_cmd(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"]).returncode != 0:
        fail(f"No upstream branch configured ({repo_root}).")

    git_dir_res = run_cmd(["git", "rev-parse", "--git-dir"])
    git_dir = Path(git_dir_res.stdout.strip())
    for state_file in ["MERGE_HEAD", "REBASE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "BISECT_LOG"]:
        if (git_dir / state_file).exists():
            fail(f"Git operation in progress: {state_file}")

    print("🔄 Fetching latest from remote...")
    fetch_res = run_cmd(["git", "fetch"])
    if fetch_res.returncode != 0:
        fail(f"Remote fetch failed.\nDetails:\n{fetch_res.stderr.strip()}")

    res_behind = run_cmd(["git", "rev-list", "--count", "HEAD..@{u}"])
    behind_count = int(res_behind.stdout.strip() or "0")

    if behind_count > 0:
        ancestor_res = run_cmd(["git", "merge-base", "--is-ancestor", "HEAD", "@{u}"])
        if ancestor_res.returncode == 0:
            print("⏬ Local branch is behind; applying fast-forward pull...")
            pull_res = run_cmd(["git", "merge", "--ff-only", "@{u}"])
            if pull_res.returncode != 0:
                fail(f"Fast-forward merge failed.\nDetails:\n{pull_res.stderr.strip()}")
        else:
            fail("Local and remote branches have diverged. Auto-pull skipped to prevent conflict risks.")

    res_diff_head = run_cmd(["git", "diff", "--quiet", "HEAD"])
    res_untracked = run_cmd(["git", "ls-files", "--others", "--exclude-standard"])
    if res_diff_head.returncode == 0 and not res_untracked.stdout.strip():
        fail("Nothing to save (no modified or untracked files found).")

    print("🚀 Saving changes...")
    add_res = run_cmd(["git", "add", "-A"])
    if add_res.returncode != 0:
        fail(f"Failed to stage changes.\nDetails:\n{add_res.stderr.strip()}")

    commit_res = run_cmd(["git", "commit", "-m", "save"])
    if commit_res.returncode != 0:
        run_cmd(["git", "reset"])
        fail(f"Commit failed.\nDetails:\n{commit_res.stderr.strip()}")

    push_res = run_cmd(["git", "push"])
    if push_res.returncode != 0:
        print("⚠️ Push failed. Rolling back local commit...", file=sys.stderr)
        run_cmd(["git", "reset", "--soft", "HEAD~1"])
        run_cmd(["git", "reset"])
        fail(f"Push failed. Remote rejected the save.\nDetails:\n{push_res.stderr.strip()}")

    print("✅ SAVE COMPLETE")


if __name__ == "__main__":
    main()