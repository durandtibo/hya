#!/usr/bin/env bash
# Test that `gh-rerun-failed` re-runs only failed/cancelled runs and honours the limit and branch, using a fake `gh`.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# Fake gh: `run list` records its args and prints the ids of the canned runs matching the conclusions the real --jq filter selects; `run rerun` records its args.
mkdir -p "$work/bin"
cat >"$work/bin/gh" <<'SH'
#!/usr/bin/env bash
if [ "$1 $2" = "run list" ]; then
	echo "$*" >>"$GH_LOG"
	# Canned runs (id:conclusion): failure, success, cancelled, in progress, timed_out
	for run in 1:failure 2:success 3:cancelled 4: 5:timed_out; do
		case "${run#*:}" in failure | cancelled | timed_out) echo "${run%%:*}" ;; esac
	done
elif [ "$1 $2" = "run rerun" ]; then
	echo "$3 $4" >>"$GH_RERUN"
	# Simulate a run that cannot be retried
	if [ "$3" = "${GH_UNRERUNNABLE:-}" ]; then
		echo "run $3 cannot be rerun; This workflow run cannot be retried" >&2
		exit 1
	fi
else
	exit 1
fi
SH
chmod +x "$work/bin/gh"
export PATH="$work/bin:$PATH"
export GH_LOG="$work/log" GH_RERUN="$work/rerun"

fail() {
	echo "FAIL: $1" >&2
	exit 1
}

: >"$GH_LOG"
: >"$GH_RERUN"
make -f "$repo_root/github.mk" gh-rerun-failed >/dev/null || fail "gh-rerun-failed should succeed"
grep -q -- "--limit 5" "$GH_LOG" || fail "default limit should be 5: $(cat "$GH_LOG")"
if grep -q -- "--branch" "$GH_LOG"; then fail "no --branch expected by default"; fi
[ "$(cat "$GH_RERUN")" = $'1 --failed\n3 --failed\n5 --failed' ] || fail "unexpected reruns: $(cat "$GH_RERUN")"

: >"$GH_LOG"
make -f "$repo_root/github.mk" gh-rerun-failed GITHUB_RERUN_LIMIT=10 GITHUB_RERUN_BRANCH=my/branch >/dev/null || fail "with variables should succeed"
grep -q -- "--limit 10" "$GH_LOG" || fail "limit override ignored: $(cat "$GH_LOG")"
grep -q -- "--branch my/branch" "$GH_LOG" || fail "branch override ignored: $(cat "$GH_LOG")"

: >"$GH_RERUN"
out="$(GH_UNRERUNNABLE=3 make -f "$repo_root/github.mk" gh-rerun-failed 2>&1)" || fail "a run that cannot be re-run must not fail the target"
echo "$out" | grep -q "Warning: run 3 could not be re-run" || fail "missing warning: $out"
echo "$out" | grep -q "Re-triggered 2 run(s), 1 skipped" || fail "unexpected summary: $out"
[ "$(cat "$GH_RERUN")" = $'1 --failed\n3 --failed\n5 --failed' ] || fail "remaining runs should still be re-run: $(cat "$GH_RERUN")"

echo "OK"
