#!/usr/bin/env bash
# Test that `git-delete-branches` deletes every local branch except the main one.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

fail() {
	echo "FAIL: $1" >&2
	exit 1
}

cd "$work"
git init -q -b main .
git config user.email test@example.com
git config user.name test
git commit -q --allow-empty -m init
git branch feat/a
git branch bugfix/b
git branch maintenance
cat >Makefile <<MK
include $repo_root/git.mk
MK

# Checked out on main: every other branch is deleted, main (and similar names) is kept only if exact.
make git-delete-branches >/dev/null 2>&1 || fail "target should succeed"
[ "$(git branch --format='%(refname:short)')" = "main" ] || fail "only main should remain"

# Custom main branch; the checked-out branch is skipped with a warning.
git branch feat/c
git checkout -q -b dev
out="$(make git-delete-branches GIT_MAIN_BRANCH=main 2>&1)" || fail "should not fail on the current branch"
grep -q "could not delete dev" <<<"$out" || fail "current branch should be reported"
[ "$(git branch --format='%(refname:short)' | sort | tr '\n' ' ')" = "dev main " ] || fail "dev and main should remain"
echo "PASS"
