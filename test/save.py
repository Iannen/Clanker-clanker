#!/usr/bin/env -S python3 -B
""" inline explainer comments forbidden. only user may post inline comments, as means of communication. llm not allowed to make # or multiline comments"""
import re
import subprocess
import sys
from pathlib import Path
from ruamel.yaml import YAML
from typing import NoReturn

MAIN_BRANCH = "main"
DEV_BRANCH = "dev"
TEST_COMMAND_PATH = ("system", "test_command")
APPLY_COMMAND_PATH = ("system", "apply_command")

REPO_ROOT = Path.cwd()
CONFIG_PATH = REPO_ROOT / ".clanker" / "config.yaml"

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

def _test() -> None:
    test_cmd = get_config_value(TEST_COMMAND_PATH)
    test_res = _run_cmd(test_cmd, shell=True, capture_output=False)
    if test_res.returncode != 0:
        _fail(f"test command failed with exit code {test_res.returncode}.")

def ensure_dev_environment() -> None:
    if not (REPO_ROOT / ".git").exists():
        _fail(f"must run script from repository root ('{REPO_ROOT}').")
        
    res = _run_cmd(["git", "rev-parse", "--is-inside-work-tree"])
    if res.returncode != 0 or res.stdout.strip() != "true":
        _fail(f"not inside a git repository ({REPO_ROOT}).")

    if _run_cmd(["git", "rev-parse", "--verify", "HEAD"]).returncode != 0:
        _fail(f"repository has no commits ({REPO_ROOT}).")

    if _run_cmd(["git", "config", "user.name"]).returncode != 0:
        _fail(f"git user.name not configured ({REPO_ROOT}).")

    if _run_cmd(["git", "config", "user.email"]).returncode != 0:
        _fail(f"git user.email not configured ({REPO_ROOT}).")

    if _run_cmd(["git", "ls-files", "-u"]).stdout.strip():
        _fail("unresolved merge conflicts detected.")

    if _run_cmd(["git", "symbolic-ref", "--quiet", "--short", "HEAD"]).returncode != 0:
        _fail("detached HEAD.")

    git_dir_res = _run_cmd(["git", "rev-parse", "--git-dir"])
    git_dir = Path(git_dir_res.stdout.strip())
    for state_file in ["MERGE_HEAD", "REBASE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "BISECT_LOG"]:
        if (git_dir / state_file).exists():
            _fail(f"git operation in progress: {state_file}.")

    res_main = _run_cmd(["git", "rev-parse", "--verify", MAIN_BRANCH])
    if res_main.returncode != 0:
        res_master = _run_cmd(["git", "rev-parse", "--verify", "master"])
        if res_master.returncode == 0:
            _fail(f"found 'master' branch instead of required '{MAIN_BRANCH}' branch. Please rename/reconfigure.")
        else:
            _fail(f"required branch '{MAIN_BRANCH}' not found in repository.")

    res_dev = _run_cmd(["git", "rev-parse", "--verify", DEV_BRANCH])
    if res_dev.returncode != 0:
        print(f"[git] Branch '{DEV_BRANCH}' not found. Creating it from '{MAIN_BRANCH}'...")
        _run_cmd(["git", "checkout", MAIN_BRANCH])
        _run_cmd(["git", "pull", "origin", MAIN_BRANCH])
        res_create = _run_cmd(["git", "checkout", "-b", DEV_BRANCH])
        if res_create.returncode != 0:
            _fail(f"failed to create '{DEV_BRANCH}' branch: {res_create.stderr.strip()}")
        print(f"[git] Successfully created and switched to '{DEV_BRANCH}'.")
    else:
        res = _run_cmd(["git", "symbolic-ref", "--quiet", "--short", "HEAD"])
        if res.returncode != 0:
            _fail("detached HEAD or not on a branch.")
        current_branch = res.stdout.strip()

        if current_branch != DEV_BRANCH:
            print(f"[git] Switching to '{DEV_BRANCH}'...")
            res_co = _run_cmd(["git", "checkout", DEV_BRANCH])
            if res_co.returncode != 0:
                _fail(f"failed to switch to '{DEV_BRANCH}': {res_co.stderr.strip()}")

def get_config_value(keys: tuple[str, ...]) -> str:
    if not CONFIG_PATH.is_file():
        _fail(f"config file not found at '{CONFIG_PATH}'.")
    try:
        yaml = YAML(typ="safe")
        data = yaml.load(CONFIG_PATH)
        if not isinstance(data, dict):
            _fail(f"invalid config format at '{CONFIG_PATH}'.")
        
        current = data
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                _fail(f"missing config path '{'.'.join(keys)}' in config.")
            current = current[key]

        if not isinstance(current, str) or not current:
            _fail(f"mandatory config value at '{'.'.join(keys)}' missing or invalid.")

        return current

    except Exception as e:
        _fail(f"failed to parse config at '{CONFIG_PATH}': {e}")

def process_local_changes() -> str | None:
    res_diff_head = _run_cmd(["git", "diff", "--quiet", "HEAD"])
    res_untracked = _run_cmd(["git", "ls-files", "--others", "--exclude-standard"])
    has_local_changes = res_diff_head.returncode != 0 or bool(res_untracked.stdout.strip())

    if not has_local_changes:
        return None

    add_res = _run_cmd(["git", "add", "-A"])
    if add_res.returncode != 0:
        _fail(f"failed to stage changes: {add_res.stderr.strip()}")

    commit_res = _run_cmd(["git", "commit", "-m", "save"])
    if commit_res.returncode != 0:
        _run_cmd(["git", "reset"])
        _fail(f"commit failed: {commit_res.stderr.strip()}")

    stats_summary = ""
    match = re.search(r"(\d+ files? changed(?:, \d+ insertions?\(\+\))?(?:, \d+ deletions?\(\-\))?)", commit_res.stdout)
    if match:
        stats_summary = f" ({match.group(1)})"

    return stats_summary

def receive() -> None:
    print("Not implemented")

def push() -> None:
    apply_cmd = get_config_value(APPLY_COMMAND_PATH)
    _test()

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

    stats_summary = process_local_changes()
    has_local_changes = stats_summary is not None

    if not has_local_changes and behind_count == 0 and ahead_count == 0:
        _fail("nothing to save (no modified or untracked files found, and fully up to date with remote).")

    if behind_count > 0:
        pull_res = _run_cmd(["git", "merge", "--ff-only", "@{u}"])
        if pull_res.returncode != 0:
            _fail(f"fast-forward merge failed: {pull_res.stderr.strip()}")

    summary_text = stats_summary if stats_summary else ""
    print(f"[git] Pushing to remote{summary_text}")
    push_res = _run_cmd(["git", "push", "-u", "origin", DEV_BRANCH])
    if push_res.returncode != 0:
        _fail(f"push failed: {push_res.stderr.strip()}")

    print("[deploy] Running apply command...")
    apply_res = _run_cmd(apply_cmd, shell=True, capture_output=False)
    if apply_res.returncode != 0:
        _fail(f"apply command failed with exit code {apply_res.returncode}.")
    print("[deploy] Apply successful!")

    print("Save complete.")

def merge() -> None:
    _test()
    process_local_changes()

    print(f"[git] Switching to '{MAIN_BRANCH}'...")
    checkout_res = _run_cmd(["git", "checkout", MAIN_BRANCH])
    if checkout_res.returncode != 0:
        _fail(f"failed to checkout '{MAIN_BRANCH}': {checkout_res.stderr.strip()}")

    pull_res = _run_cmd(["git", "pull", "origin", MAIN_BRANCH])
    if pull_res.returncode != 0:
        _run_cmd(["git", "checkout", DEV_BRANCH])
        _fail(f"failed to pull latest '{MAIN_BRANCH}': {pull_res.stderr.strip()}")

    merge_res = _run_cmd([
        "git", "merge", DEV_BRANCH, "--no-ff",
        "-m", f"Merge branch '{DEV_BRANCH}' into {MAIN_BRANCH}"
    ])
    if merge_res.returncode != 0:
        _run_cmd(["git", "merge", "--abort"])
        _run_cmd(["git", "checkout", DEV_BRANCH])
        _fail(f"failed to merge '{DEV_BRANCH}' into '{MAIN_BRANCH}'.")

    print(f"[git] Pushing '{MAIN_BRANCH}' to remote...")
    push_res = _run_cmd(["git", "push", "origin", MAIN_BRANCH])
    if push_res.returncode != 0:
        _run_cmd(["git", "checkout", DEV_BRANCH])
        _fail(f"push failed: {push_res.stderr.strip()}")

    print(f"[git] Switching back to '{DEV_BRANCH}'...")
    return_res = _run_cmd(["git", "checkout", DEV_BRANCH])
    if return_res.returncode != 0:
        _fail(f"failed to switch back to '{DEV_BRANCH}': {return_res.stderr.strip()}")

    print(f"Sync complete: '{DEV_BRANCH}' merged into '{MAIN_BRANCH}' and pushed.")

def reset() -> None:
    print(f"[git] Fetching latest changes from remote...")
    fetch_res = _run_cmd(["git", "fetch", "origin"])
    if fetch_res.returncode != 0:
        _fail(f"remote fetch failed: {fetch_res.stderr.strip()}")

    print(f"[git] Hard resetting '{DEV_BRANCH}' to 'origin/{MAIN_BRANCH}'...")
    reset_res = _run_cmd(["git", "reset", "--hard", f"origin/{MAIN_BRANCH}"])
    if reset_res.returncode != 0:
        _fail(f"failed to reset branch: {reset_res.stderr.strip()}")

    print(f"[git] Force pushing reset '{DEV_BRANCH}' to remote...")
    push_res = _run_cmd(["git", "push", "origin", DEV_BRANCH, "--force"])
    if push_res.returncode != 0:
        _fail(f"force push failed: {push_res.stderr.strip()}")

    print(f"Reset complete: '{DEV_BRANCH}' has been hard-reset to 'origin/{MAIN_BRANCH}' and force-pushed.")

def print_help() -> None:
    print("Usage: git-ops <command>")
    print("")
    print("Commands:")
    print("  receive   Get new code")
    print("  push      Test, commit local changes, and push")
    print("  merge     Merge current branch into main and push")
    print("  reset     Hard-reset current branch to origin/main")
    sys.exit(0)

def main() -> None:
    if len(sys.argv) < 2:
        print_help()

    cmd = sys.argv[1]
    valid_commands = {"receive", "push", "merge", "reset"}

    if cmd not in valid_commands:
        print_help()

    ensure_dev_environment()

    if cmd == "receive":
        receive()
    elif cmd == "push":
        push()
    elif cmd == "merge":
        merge()
    elif cmd == "reset":
        reset()

if __name__ == "__main__":
    main()