#!/usr/bin/env -S python3 -B

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

""" git helpers """
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

def _checkout(branch: str) -> None:
    res = _run_cmd(["git", "symbolic-ref", "--quiet", "--short", "HEAD"])
    if res.returncode == 0 and res.stdout.strip() == branch:
        return

    verify_res = _run_cmd(["git", "rev-parse", "--verify", branch])
    if verify_res.returncode == 0:
        print(f"[git] Switching to '{branch}'...")
        cmd = ["git", "checkout", branch]
    else:
        print(f"[git] Creating and switching to '{branch}'...")
        cmd = ["git", "checkout", "-b", branch]

    co_res = _run_cmd(cmd)
    if co_res.returncode != 0:
        _fail(f"failed to switch to/create '{branch}': {co_res.stderr.strip()}")

def _push(branch: str, remote: str = "origin", force: bool = False) -> None:
    cmd = ["git", "push"]
    if branch == DEV_BRANCH:
        cmd.extend(["-u", remote, branch])
    elif force:
        cmd.extend([remote, branch, "--force"])
    else:
        cmd.extend([remote, branch])

    push_res = _run_cmd(cmd)
    if push_res.returncode != 0:
        if branch == MAIN_BRANCH:
            _checkout(DEV_BRANCH)
        _fail(f"push failed: {push_res.stderr.strip()}")

def _fetch() -> None:
    fetch_res = _run_cmd(["git", "fetch"])
    if fetch_res.returncode != 0:
        _fail(f"remote fetch failed: {fetch_res.stderr.strip()}")

""" other helpers """
def _test() -> None:
    test_cmd = _get_config_value(TEST_COMMAND_PATH)
    test_res = _run_cmd(test_cmd, shell=True, capture_output=False)
    if test_res.returncode != 0:
        _fail(f"test command failed with exit code {test_res.returncode}.")

def _get_config_value(keys: tuple[str, ...]) -> str:
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

def ensure_dev_environment() -> None:
    res = _run_cmd(["git", "rev-parse", "--show-prefix"])
    if res.returncode != 0 or res.stdout.strip() != "":
        _fail(f"must run script from repository root ('{REPO_ROOT}').")

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
        _checkout(MAIN_BRANCH)
        _run_cmd(["git", "pull", "origin", MAIN_BRANCH])
        _checkout(DEV_BRANCH)
        print(f"[git] Successfully created and switched to '{DEV_BRANCH}'.")
    else:
        res = _run_cmd(["git", "symbolic-ref", "--quiet", "--short", "HEAD"])
        if res.returncode != 0:
            _fail("detached HEAD or not on a branch.")
        
        _checkout(DEV_BRANCH)

def receive() -> None:
    print("Not implemented")

def push() -> None:
    _test()
    _fetch()

    res_ahead = _run_cmd(["git", "rev-list", "--count", "@{u}..HEAD"])
    ahead_count = int(res_ahead.stdout.strip() or "0")

    res_behind = _run_cmd(["git", "rev-list", "--count", "HEAD..@{u}"])
    behind_count = int(res_behind.stdout.strip() or "0")

    if ahead_count > 0 and behind_count > 0:
        ancestor_res = _run_cmd(["git", "merge-base", "--is-ancestor", "HEAD", "@{u}"])
        if ancestor_res.returncode != 0:
            _fail("local and remote branches have diverged.")

    stats_summary = process_local_changes()
    has_local_changes = stats_summary is not None

    if not has_local_changes and behind_count == 0 and ahead_count == 0:
        _fail("nothing to save (no modified or untracked files found, and fully up to date with remote).")

    if behind_count > 0:
        pull_res = _run_cmd(["git", "merge", "--ff-only", "@{u}"])
        if pull_res.returncode != 0:
            _fail(f"fast-forward merge failed: {pull_res.stderr.strip()}")

    _push(DEV_BRANCH)

    apply_cmd = _get_config_value(APPLY_COMMAND_PATH)
    apply_res = _run_cmd(apply_cmd, shell=True, capture_output=False)
    if apply_res.returncode != 0:
        _fail(f"apply command failed with exit code {apply_res.returncode}.")

    summary_text = stats_summary if stats_summary else ""
    print(f"Save complete{summary_text}.")

def merge() -> None:
    _test()
    process_local_changes()

    _checkout(MAIN_BRANCH)
    pull_res = _run_cmd(["git", "pull", "origin", MAIN_BRANCH])
    if pull_res.returncode != 0:
        _checkout(DEV_BRANCH)
        _fail(f"failed to pull latest '{MAIN_BRANCH}': {pull_res.stderr.strip()}")

    merge_res = _run_cmd([
        "git", "merge", DEV_BRANCH, "--no-ff",
        "-m", f"Merge branch '{DEV_BRANCH}' into {MAIN_BRANCH}"
    ])
    if merge_res.returncode != 0:
        _run_cmd(["git", "merge", "--abort"])
        _checkout(DEV_BRANCH)
        _fail(f"failed to merge '{DEV_BRANCH}' into '{MAIN_BRANCH}'.")

    _push(MAIN_BRANCH)
    _checkout(DEV_BRANCH)

    print(f"Merge complete: '{DEV_BRANCH}' merged into '{MAIN_BRANCH}' and pushed.")

def reset() -> None:
    _fetch()
    reset_res = _run_cmd(["git", "reset", "--hard", f"origin/{MAIN_BRANCH}"])
    if reset_res.returncode != 0:
        _fail(f"failed to reset branch: {reset_res.stderr.strip()}")
    _push(DEV_BRANCH, force=True)
    print(f"Reset complete: '{DEV_BRANCH}' has been reset to 'origin/{MAIN_BRANCH}'.")

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