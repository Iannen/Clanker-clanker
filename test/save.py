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

def ensure_dev_environment() -> Path:
    repo_root = Path.cwd()
    if not (repo_root / ".git").exists():
        _fail(f"must run script from repository root ('{repo_root}').")
        
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

    return repo_root

def load_configured_commands(repo_root: Path) -> tuple[str, str]:
    """ 
    perhaps we can declare the path to the two commands we extract as constants (up with the branch constants)
    then this can be general method which is used to grab a command at a path
    """
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


def receive(repo_root: Path) -> None:
    print("Not implemented")

def push(repo_root: Path) -> None:
    test_cmd, apply_cmd = load_configured_commands(repo_root)

    test_res = _run_cmd(test_cmd, shell=True, capture_output=False)
    if test_res.returncode != 0:
        _fail(f"test command failed with exit code {test_res.returncode}.")

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

    stats_summary, has_local_changes = process_local_changes()

    if not has_local_changes and behind_count == 0 and ahead_count == 0:
        _fail("nothing to save (no modified or untracked files found, and fully up to date with remote).")

    if behind_count > 0:
        pull_res = _run_cmd(["git", "merge", "--ff-only", "@{u}"])
        if pull_res.returncode != 0:
            _fail(f"fast-forward merge failed: {pull_res.stderr.strip()}")

    print(f"[git] Pushing to remote{stats_summary}")
    push_res = _run_cmd(["git", "push", "-u", "origin", DEV_BRANCH])
    if push_res.returncode != 0:
        _fail(f"push failed: {push_res.stderr.strip()}")

    print("[deploy] Running apply command...")
    apply_res = _run_cmd(apply_cmd, shell=True, capture_output=False)
    if apply_res.returncode != 0:
        _fail(f"apply command failed with exit code {apply_res.returncode}.")
    print("[deploy] Apply successful!")

    print("Save complete.")

def merge(repo_root: Path) -> None:
    test_cmd, _ = load_configured_commands(repo_root)

    test_res = _run_cmd(test_cmd, shell=True, capture_output=False)
    if test_res.returncode != 0:
        _fail(f"test command failed with exit code {test_res.returncode}.")

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

def reset(repo_root: Path) -> None:
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

    repo_root = ensure_dev_environment()

    if cmd == "receive":
        receive(repo_root)
    elif cmd == "push":
        push(repo_root)
    elif cmd == "merge":
        merge(repo_root)
    elif cmd == "reset":
        reset(repo_root)

if __name__ == "__main__":
    main()