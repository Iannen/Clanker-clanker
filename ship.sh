#!/usr/bin/env bash
set -uo pipefail

fail() {
    echo "❌ SHIP BLOCKED: $1"
    echo "--------------------------------------------------"
    echo "CONFIRMED: The script has had NO EFFECT on your repository state."
    exit 1
}

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || fail "Not inside a git repository ($PWD)."
git rev-parse --verify HEAD >/dev/null 2>&1          || fail "Repository has no commits ($PWD)."
git config user.name >/dev/null 2>&1                 || fail "Git user.name not configured ($PWD)."
git config user.email >/dev/null 2>&1                || fail "Git user.email not configured ($PWD)."

git ls-files -u | grep -q .                          && fail "Unresolved merge conflicts detected ($PWD)."

branch=$(git symbolic-ref --quiet --short HEAD)      || fail "Detached HEAD ($PWD)."
git rev-parse --abbrev-ref --symbolic-full-name "@{u}" >/dev/null 2>&1 || fail "No upstream branch configured ($PWD)."

for state in MERGE_HEAD REBASE_HEAD CHERRY_PICK_HEAD REVERT_HEAD BISECT_LOG; do
    [ -e "$(git rev-parse --git-dir)/$state" ]        && fail "Git operation in progress: $state"
done

echo "🔄 Fetching latest from remote..."
FETCH_ERR=$(git fetch 2>&1) || fail "Remote fetch failed.\nDetails:\n$FETCH_ERR"

behind=$(git rev-list --count HEAD.."@{u}")
[ "$behind" -eq 0 ] || fail "Local branch is behind upstream. Please pull first."

if git diff --quiet HEAD -- && [ -z "$(git ls-files --others --exclude-standard)" ]; then
    fail "Nothing to ship (no modified or untracked files found)."
fi

echo "🚀 Shipping changes..."

git add .

if ! COMMIT_ERR=$(git commit -m "ship" 2>&1); then
    git reset >/dev/null 2>&1
    fail "Commit failed.\nDetails:\n$COMMIT_ERR"
fi

if ! PUSH_ERR=$(git push 2>&1); then
    echo "⚠️ Push failed. Rolling back local commit..."
    git reset --soft HEAD~1 >/dev/null 2>&1
    git reset >/dev/null 2>&1 
    fail "Push failed. Remote rejected the ship.\nDetails:\n$PUSH_ERR"
fi

echo "✅ SHIP COMPLETE"
