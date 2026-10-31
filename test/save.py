#!/usr/bin/env -S python3 -B
import re
import subprocess
import sys
from pathlib import Path
from ruamel.yaml import YAML
from typing import NoReturn

def _fail(msg: str) -> NoReturn:
    print(f"Save aborted: {msg}", file=sys.stderr)
    sys.exit(1)

def _run_cmd(cmd: list[str] | str, shell: bool = False, capture_output: bool = True) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            shell=shell,
        )
    except Exception as e:
        cmd_str = cmd if isinstance(cmd, str) else " ".join(cmd)
        _fail(f"failed to execute command '{cmd_str}': {e}")

def validate_repo_root() -> Path:
    repo_root = Path.cwd()
    if not (repo_root / ".git").exists():
        _fail(f"must run script from repository root ('{repo_root}').")
    return repo_root

def load_configured_commands(repo_root: Path) -> tuple[str, str]:
    cfg_file = repo_root / ".clanker" / "config.yaml"
    if not cfg_file.is_file():
        _fail(f"config file not found at '{cfg_file}'.")
    try:
        yaml = YAML(typ="safe")
        data = yaml.load(cfg_file)
        if not isinstance(data, dict):
            _fail(f"invalid config format at '{cfg_file}'.")
        
        system_cfg = data.get("system")
        if not isinstance(system_cfg, dict):
            _fail("missing 'system' section in config.")

        test_cmd = system_cfg.get("test_command")
        if not test_cmd or not isinstance(test_cmd, str):
            _fail("mandatory 'test_command' missing or invalid in config.")

        apply_cmd = system_cfg.get("apply_command")
        if not apply_cmd or not isinstance(apply_cmd, str):
            _fail("mandatory 'apply_command' missing or invalid in config.")

        return test_cmd, apply_cmd

    except Exception as e:
        _fail(f"failed to parse config at '{cfg_file}': {e}")

def get_current_branch() -> str:
    res = _run_cmd(["git", "symbolic-ref", "--quiet", "--short", "HEAD"])
    if res.returncode != 0:
        _fail("detached HEAD or not on a branch.")
    return res.stdout.strip()

def verify_git_environment(repo_root: Path) -> None:
    res = _run_cmd(["git", "rev-parse", "--is-inside-work-tree"])
    if res.returncode != 0 or res.stdout.strip() != "true":
        _fail(f"not inside a git repository ({repo_root}).")

    if _run_cmd(["git", "rev-parse", "--verify", "HEAD"]).returncode != 0:
        _fail(f"repository has no commits ({repo_root}).")

    if _run_cmd(["git", "config", "user.name"]).returncode != 0:
        _fail(f"git user.name not configured ({repo_root}).")

    if _run_cmd(["git", "config", "user.email"]).returncode != 0:
        _fail(f"git user.email not configured ({repo_root}).")

    if _run_cmd(["git", "ls-files", "-u"]).stdout.strip():
        _fail("unresolved merge conflicts detected.")

    if _run_cmd(["git", "symbolic-ref", "--quiet", "--short", "HEAD"]).returncode != 0:
        _fail("detached HEAD.")

    git_dir_res = _run_cmd(["git", "rev-parse", "--git-dir"])
    git_dir = Path(git_dir_res.stdout.strip())
    for state_file in ["MERGE_HEAD", "REBASE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "BISECT_LOG"]:
        if (git_dir / state_file).exists():
            _fail(f"git operation in progress: {state_file}.")

def check_remote_sync() -> tuple[int, int]:
    print("[git] Checking remote...")
    fetch_res = _run_cmd(["git", "fetch"])
    if fetch_res.returncode != 0:
        _fail(f"remote fetch failed: {fetch_res.stderr.strip()}")

    res_ahead = _run_cmd(["git", "rev-list", "--count", "@{u}..HEAD"])
    ahead_count = int(res_ahead.stdout.strip() or "0")

    res_behind = _run_cmd(["git", "rev-list", "--count", "HEAD..@{u}"])
    behind_count = int(res_behind.stdout.strip() or "0")

    if ahead_count > 0 and behind_count > 0:
        ancestor_res = _run_cmd(["git", "merge-base", "--is-ancestor", "HEAD", "@{u}"])
        if ancestor_res.returncode != 0:
            _fail("local and remote branches have diverged.")

    print("[git] Synced with remote.")
    return ahead_count, behind_count

def process_local_changes() -> tuple[str, bool]:
    res_diff_head = _run_cmd(["git", "diff", "--quiet", "HEAD"])
    res_untracked = _run_cmd(["git", "ls-files", "--others", "--exclude-standard"])
    has_local_changes = res_diff_head.returncode != 0 or bool(res_untracked.stdout.strip())

    stats_summary = ""
    if has_local_changes:
        add_res = _run_cmd(["git", "add", "-A"])
        if add_res.returncode != 0:
            _fail(f"failed to stage changes: {add_res.stderr.strip()}")

        commit_res = _run_cmd(["git", "commit", "-m", "save"])
        if commit_res.returncode != 0:
            _run_cmd(["git", "reset"])
            _fail(f"commit failed: {commit_res.stderr.strip()}")

        match = re.search(r"(\d+ files? changed(?:, \d+ insertions?\(\+\))?(?:, \d+ deletions?\(\-\))?)", commit_res.stdout)
        if match:
            stats_summary = f" ({match.group(1)})"

    return stats_summary, has_local_changes

def sync_branch(target_branch: str) -> None:
    repo_root = validate_repo_root()
    test_cmd, _ = load_configured_commands(repo_root)

    test_res = _run_cmd(test_cmd, shell=True, capture_output=False)
    if test_res.returncode != 0:
        _fail(f"test command failed with exit code {test_res.returncode}.")

    verify_git_environment(repo_root)
    current_branch = get_current_branch()

    if current_branch == target_branch:
        _fail(f"cannot sync '{target_branch}' into itself. You are already checked out on '{target_branch}'. Run without arguments to save.")

    process_local_changes()

    print(f"[git] Switching to '{target_branch}'...")
    checkout_res = _run_cmd(["git", "checkout", target_branch])
    if checkout_res.returncode != 0:
        _fail(f"failed to checkout '{target_branch}': {checkout_res.stderr.strip()}")

    pull_res = _run_cmd(["git", "pull", "origin", target_branch])
    if pull_res.returncode != 0:
        _run_cmd(["git", "checkout", current_branch])
        _fail(f"failed to pull latest '{target_branch}': {pull_res.stderr.strip()}")

    merge_res = _run_cmd(["git", "merge", current_branch, "--no-ff", "-m", f"Merge branch '{current_branch}' into {target_branch}"])
    if merge_res.returncode != 0:
        _run_cmd(["git", "merge", "--abort"])
        _run_cmd(["git", "checkout", current_branch])
        _fail(f"failed to merge '{current_branch}' into '{target_branch}'.")

    print(f"[git] Pushing '{target_branch}' to remote...")
    push_res = _run_cmd(["git", "push", "origin", target_branch])
    if push_res.returncode != 0:
        _run_cmd(["git", "checkout", current_branch])
        _fail(f"push failed: {push_res.stderr.strip()}")

    print(f"[git] Switching back to '{current_branch}'...")
    return_res = _run_cmd(["git", "checkout", current_branch])
    if return_res.returncode != 0:
        _fail(f"failed to switch back to '{current_branch}': {return_res.stderr.strip()}")

    print(f"Sync complete: '{current_branch}' merged into '{target_branch}' and pushed.")

def reset_branch(target_branch: str = "main") -> None:
    repo_root = validate_repo_root()
    verify_git_environment(repo_root)
    current_branch = get_current_branch()

    if current_branch == target_branch:
        _fail(f"safety block: cannot reset '{target_branch}' onto itself! Switch to a feature branch (like 'dev') first.")

    print(f"[git] Fetching latest changes from remote...")
    fetch_res = _run_cmd(["git", "fetch", "origin"])
    if fetch_res.returncode != 0:
        _fail(f"remote fetch failed: {fetch_res.stderr.strip()}")

    print(f"[git] Hard resetting '{current_branch}' to 'origin/{target_branch}'...")
    reset_res = _run_cmd(["git", "reset", "--hard", f"origin/{target_branch}"])
    if reset_res.returncode != 0:
        _fail(f"failed to reset branch: {reset_res.stderr.strip()}")

    print(f"[git] Force pushing reset '{current_branch}' to remote...")
    push_res = _run_cmd(["git", "push", "origin", current_branch, "--force"])
    if push_res.returncode != 0:
        _fail(f"force push failed: {push_res.stderr.strip()}")

    print(f"Reset complete: '{current_branch}' has been hard-reset to 'origin/{target_branch}' and force-pushed.")

def run_normal_workflow() -> None:
    repo_root = validate_repo_root()
    test_cmd, apply_cmd = load_configured_commands(repo_root)

    test_res = _run_cmd(test_cmd, shell=True, capture_output=False)
    if test_res.returncode != 0:
        _fail(f"test command failed with exit code {test_res.returncode}.")

    verify_git_environment(repo_root)
    ahead_count, behind_count = check_remote_sync()
    stats_summary, has_local_changes = process_local_changes()

    if not has_local_changes and behind_count == 0 and ahead_count == 0:
        _fail("nothing to save (no modified or untracked files found, and fully up to date with remote).")

    if behind_count > 0:
        pull_res = _run_cmd(["git", "merge", "--ff-only", "@{u}"])
        if pull_res.returncode != 0:
            _fail(f"fast-forward merge failed: {pull_res.stderr.strip()}")

    print(f"[git] Pushing to remote{stats_summary}")
    push_res = _run_cmd(["git", "push"])
    if push_res.returncode != 0:
        _fail(f"push failed: {push_res.stderr.strip()}")

    print("[deploy] Running apply command...")
    apply_res = _run_cmd(apply_cmd, shell=True, capture_output=False)
    if apply_res.returncode != 0:
        _fail(f"apply command failed with exit code {apply_res.returncode}.")
    print("[deploy] Apply successful!")

    print("Save complete.")

def main() -> None:
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "reset":
            target = sys.argv[2] if len(sys.argv) > 2 else "main"
            reset_branch(target)
        else:
            target_branch = cmd
            sync_branch(target_branch)
    else:
        run_normal_workflow()

if __name__ == "__main__":
    main()