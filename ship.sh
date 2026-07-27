#!/usr/bin/env bash
# set -e is removed intentionally so we can handle rollbacks manually on failure
set -uo pipefail

fail() {
    echo "❌ SHIP BLOCKED: $1"
    echo "--------------------------------------------------"
    echo "CONFIRMED: The script has had NO EFFECT on your repository state."
    exit 1
}

# ============================================================
# PHASE 1: PRE-ACTION VALIDATION (Idempotent Safety Checks)
# ============================================================

# Basic environment checks
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || fail "Not inside a git repository."
git rev-parse --verify HEAD >/dev/null 2>&1          || fail "Repository has no commits."
git config user.name >/dev/null 2>&1                 || fail "Git user.name not configured."
git config user.email >/dev/null 2>&1                || fail "Git user.email not configured."

# Git state checks
git diff --check >/dev/null 2>&1                     || fail "Whitespace or patch errors detected."


git ls-files -u | grep -q .                          && fail "Unresolved merge conflicts detected."

branch=$(git symbolic-ref --quiet --short HEAD)      || fail "Detached HEAD."
git rev-parse --abbrev-ref --symbolic-full-name "@{u}" >/dev/null 2>&1 || fail "No upstream branch configured."

for state in MERGE_HEAD REBASE_HEAD CHERRY_PICK_HEAD REVERT_HEAD BISECT_LOG; do
    [ -e "$(git rev-parse --git-dir)/$state" ]        && fail "Git operation in progress: $state"
done

# Network / Remote sync checks (capturing error messages)
echo "🔄 Fetching latest from remote..."
FETCH_ERR=$(git fetch 2>&1) || fail "Remote fetch failed.\nDetails:\n$FETCH_ERR"

behind=$(git rev-list --count HEAD.."@{u}")
[ "$behind" -eq 0 ] || fail "Local branch is behind upstream. Please pull first."

# Better "Nothing to ship" check (Looks at tracked AND untracked files)
if git diff --quiet HEAD -- && [ -z "$(git ls-files --others --exclude-standard)" ]; then
    fail "Nothing to ship (no modified or untracked files found)."
fi

# ============================================================
# PHASE 2: SAFE ACTION (With Automatic Rollback)
# ============================================================
echo "🚀 Shipping changes..."

# 1. Stage everything
git add .

# 2. Commit (Capture errors if any)
if ! COMMIT_ERR=$(git commit -m "ship" 2>&1); then
    # If commit fails, undo the staging
    git reset >/dev/null 2>&1
    fail "Commit failed.\nDetails:\n$COMMIT_ERR"
fi

# 3. Push (Capture errors if any)
if ! PUSH_ERR=$(git push 2>&1); then
    # CRITICAL ROLLBACK: Push failed, so undo the local commit but keep the file changes
    echo "⚠️ Push failed. Rolling back local commit..."
    git reset --soft HEAD~1 >/dev/null 2>&1
    git reset >/dev/null 2>&1 # Unstage files to return to exact starting state
    fail "Push failed. Remote rejected the ship.\nDetails:\n$PUSH_ERR"
fi

# ============================================================
# PHASE 3: SUCCESS
# ============================================================
echo "✅ SHIP COMPLETE"
