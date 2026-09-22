#!/usr/bin/env -S python3 -B
import argparse
import subprocess
import sys
from pathlib import Path


def fail(msg: str) -> None:
    print(f"Save aborted: {msg}", file=sys.stderr)
    sys.exit(1)


def run_cmd(cmd: list[str] | str, shell: bool = False, capture_output: bool = True) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            shell=shell,
        )
    except Exception as e:
        cmd_str = cmd if isinstance(cmd, str) else " ".join(cmd)
        fail(f"failed to execute command '{cmd_str}': {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Safely stage, commit, and push local changes.")
    parser.add_argument("--test_command", type=str, default=None)
    parser.add_argument("--no_test", action="store_true")
    args = parser.parse_args()

    if args.test_command and args.no_test:
        fail("cannot specify both --test_command and --no_test.")

    if not args.test_command and not args.no_test:
        fail("explicit flag required: must provide either --test_command <cmd> or --no_test.")

    repo_root = Path.cwd()
    clanker_path = repo_root / "content" / "clanker.py"
    if not clanker_path.is_file() or not (repo_root / ".git").exists():
        fail(f"must run script from repository root ('{repo_root}').")

    if args.test_command:
        test_res = run_cmd(args.test_command, shell=True, capture_output=False)
        if test_res.returncode != 0:
            fail(f"test command failed with exit code {test_res.returncode}.")

    res = run_cmd(["git", "rev-parse", "--is-inside-work-tree"])
    if res.returncode != 0 or res.stdout.strip() != "true":
        fail(f"not inside a git repository ({repo_root}).")

    if run_cmd(["git", "rev-parse", "--verify", "HEAD"]).returncode != 0:
        fail(f"repository has no commits ({repo_root}).")

    if run_cmd(["git", "config", "user.name"]).returncode != 0:
        fail(f"git user.name not configured ({repo_root}).")

    if run_cmd(["git", "config", "user.email"]).returncode != 0:
        fail(f"git user.email not configured ({repo_root}).")

    if run_cmd(["git", "ls-files", "-u"]).stdout.strip():
        fail("unresolved merge conflicts detected.")

    if run_cmd(["git", "symbolic-ref", "--quiet", "--short", "HEAD"]).returncode != 0:
        fail("detached HEAD.")

    if run_cmd(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"]).returncode != 0:
        fail("no upstream branch configured.")

    git_dir_res = run_cmd(["git", "rev-parse", "--git-dir"])
    git_dir = Path(git_dir_res.stdout.strip())
    for state_file in ["MERGE_HEAD", "REBASE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "BISECT_LOG"]:
        if (git_dir / state_file).exists():
            fail(f"git operation in progress: {state_file}.")

    fetch_res = run_cmd(["git", "fetch"])
    if fetch_res.returncode != 0:
        fail(f"remote fetch failed: {fetch_res.stderr.strip()}")

    res_ahead = run_cmd(["git", "rev-list", "--count", "@{u}..HEAD"])
    ahead_count = int(res_ahead.stdout.strip() or "0")

    res_behind = run_cmd(["git", "rev-list", "--count", "HEAD..@{u}"])
    behind_count = int(res_behind.stdout.strip() or "0")

    if ahead_count > 0 and behind_count > 0:
        ancestor_res = run_cmd(["git", "merge-base", "--is-ancestor", "HEAD", "@{u}"])
        if ancestor_res.returncode != 0:
            fail("local and remote branches have diverged.")

    res_diff_head = run_cmd(["git", "diff", "--quiet", "HEAD"])
    res_untracked = run_cmd(["git", "ls-files", "--others", "--exclude-standard"])
    if res_diff_head.returncode == 0 and not res_untracked.stdout.strip() and behind_count == 0:
        fail("nothing to save (no modified or untracked files found, and not behind remote).")

    add_res = run_cmd(["git", "add", "-A"])
    if add_res.returncode != 0:
        fail(f"failed to stage changes: {add_res.stderr.strip()}")

    if res_diff_head.returncode != 0 or res_untracked.stdout.strip():
        commit_res = run_cmd(["git", "commit", "-m", "save"])
        if commit_res.returncode != 0:
            run_cmd(["git", "reset"])
            fail(f"commit failed: {commit_res.stderr.strip()}")

    if behind_count > 0:
        pull_res = run_cmd(["git", "merge", "--ff-only", "@{u}"])
        if pull_res.returncode != 0:
            fail(f"fast-forward merge failed: {pull_res.stderr.strip()}")

    push_res = run_cmd(["git", "push"])
    if push_res.returncode != 0:
        fail(f"push failed: {push_res.stderr.strip()}")

    print("Save complete.")


if __name__ == "__main__":
    main()