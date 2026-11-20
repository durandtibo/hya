#!/usr/bin/env bash
# Test that `check-tools` and `check-tool-releases` report found and missing tools, lists all of them, and exits with 127 when one is missing.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

fail() {
	echo "FAIL: $1" >&2
	exit 1
}

# Fake tools on a PATH that also keeps the system commands needed by make.
mkdir -p "$work/bin"
for t in fake-a fake-b; do
	printf '#!/bin/sh\n' >"$work/bin/$t"
	if [ "$t" = fake-a ]; then printf 'echo "fake-a 1.2.3"\n' >>"$work/bin/$t"; fi
	chmod +x "$work/bin/$t"
done

cat >"$work/Makefile" <<MK
include $repo_root/tools.mk
MK
cd "$work"

# All tools available: success.
out="$(PATH="$work/bin:$PATH" make check-tools TOOLS="fake-a fake-b" 2>&1)" || fail "should succeed when all tools are available"
grep -Eq "✅ fake-a +1\.2\.3 +$work/bin/fake-a" <<<"$out" || fail "fake-a should be reported with its version and path"
grep -Eq "✅ fake-b +\? +$work/bin/fake-b" <<<"$out" || fail "a tool without version output should be reported with ?"
grep -q "All the 2 tools are available" <<<"$out" || fail "missing success summary"

# One tool missing: all tools are still listed and make fails with 127.
rc=0
out="$(PATH="$work/bin:$PATH" make check-tools TOOLS="fake-a missing-tool fake-b" 2>&1)" || rc=$?
[ "$rc" -ne 0 ] || fail "should fail when a tool is missing"
grep -q "Error 127" <<<"$out" || fail "should exit with code 127"
grep -Eq "❌ missing-tool +not found" <<<"$out" || fail "missing tool should be reported"
grep -q "✅ fake-b" <<<"$out" || fail "tools after a missing one should still be listed"
grep -q "Missing: missing-tool" <<<"$out" || fail "missing summary should name the tool"

# check-tool-releases: a fake curl stands in for the network, so the test stays offline.
cat >"$work/bin/curl" <<'SH'
#!/bin/sh
case "$*" in
*releases/tags/v1.2.3*) echo '{"published_at": "2026-02-03T04:05:06Z"}' ;;
*) exit 22 ;;
esac
SH
chmod +x "$work/bin/curl"
out="$(PATH="$work/bin:$PATH" make check-tool-releases TOOLS="fake-a fake-b" TOOL_SOURCES="fake-a=github:o/r fake-b=github:o/r" 2>&1)" || fail "check-tool-releases should succeed when all tools are available"
grep -Eq "✅ fake-a +1\.2\.3 +2026-02-03 +$work/bin/fake-a" <<<"$out" || fail "fake-a should be reported with its release date"
grep -Eq "✅ fake-b +\? +\? +$work/bin/fake-b" <<<"$out" || fail "a tool without version should have no date"
out="$(PATH="$work/bin:$PATH" make check-tool-releases TOOLS="fake-a" TOOL_SOURCES="" 2>&1)" || fail "a tool without source should not fail"
grep -Eq "✅ fake-a +1\.2\.3 +\? " <<<"$out" || fail "a tool without source should show ? as date"
rc=0
out="$(PATH="$work/bin:$PATH" make check-tool-releases TOOLS="fake-a missing-tool" 2>&1)" || rc=$?
[ "$rc" -ne 0 ] || fail "check-tool-releases should fail when a tool is missing"
grep -q "Error 127" <<<"$out" || fail "check-tool-releases should exit with 127 when a tool is missing"

# update-tools: fake package managers record their calls; only installed tools are upgraded.
mkdir -p "$work/pm"
# `brew list` knows fake-a only; `npm ls -g` knows fake-b only; the update commands succeed.
cat >"$work/pm/brew" <<'SH'
#!/bin/sh
echo "brew $*" >>"$UPDATE_LOG"
if [ "$1" = outdated ]; then echo "$3 1.0 < 2.0"; fi
if [ "$1" = list ]; then [ "$3" = fake-a ]; fi
SH
cat >"$work/pm/npm" <<'SH'
#!/bin/sh
echo "npm $*" >>"$UPDATE_LOG"
if [ "$1" = ls ]; then [ "$4" = fake-b ]; fi
SH
printf '#!/bin/sh\n' >"$work/bin/fake-c"
chmod +x "$work/bin/fake-c" "$work/pm/brew" "$work/pm/npm"
export UPDATE_LOG="$work/update.log"
: >"$UPDATE_LOG"
out="$(PATH="$work/pm:$work/bin:$PATH" make update-tools TOOLS="fake-a fake-b missing-tool fake-c" 2>&1)" || fail "update-tools should succeed"
grep -q "brew upgrade fake-a" "$UPDATE_LOG" || fail "fake-a should be upgraded with brew"
grep -q "npm install -g fake-b@latest" "$UPDATE_LOG" || fail "fake-b should be upgraded with npm"
grep -q "missing-tool is not installed, skipped" <<<"$out" || fail "a missing tool should be skipped"
if grep -q "missing-tool" "$UPDATE_LOG"; then fail "a missing tool must not be touched"; fi
grep -q "fake-c was not installed by a supported package manager" <<<"$out" || fail "an unmanaged tool should be left alone"
if grep -Eq "upgrade fake-c|fake-c@latest" "$UPDATE_LOG"; then fail "an unmanaged tool must not be upgraded"; fi

# A tool that is already up to date is not upgraded and gives no warning.
cat >"$work/pm/brew" <<'SH'
#!/bin/sh
echo "brew $*" >>"$UPDATE_LOG"
if [ "$1" = list ]; then exit 0; fi
SH
: >"$UPDATE_LOG"
out="$(PATH="$work/pm:$work/bin:$PATH" make update-tools TOOLS="fake-a" 2>&1)" || fail "an up-to-date tool should not fail"
grep -q "fake-a is already up to date" <<<"$out" || fail "an up-to-date tool should be reported as such"
if grep -q "brew upgrade" "$UPDATE_LOG"; then fail "an up-to-date tool must not be upgraded"; fi
if grep -qi "warning" <<<"$out"; then fail "an up-to-date tool must not give a warning"; fi

# A failing upgrade is reported, the other tools are still updated, and make fails.
cat >"$work/pm/brew" <<'SH'
#!/bin/sh
echo "brew $*" >>"$UPDATE_LOG"
if [ "$1" = list ]; then exit 0; fi
if [ "$1" = outdated ]; then echo "$3 1.0 < 2.0"; exit 0; fi
exit 1
SH
: >"$UPDATE_LOG"
rc=0
out="$(PATH="$work/pm:$work/bin:$PATH" make update-tools TOOLS="fake-a fake-b" 2>&1)" || rc=$?
[ "$rc" -ne 0 ] || fail "update-tools should fail when an upgrade fails"
grep -q "Failed: fake-a" <<<"$out" || fail "the failed tool should be named"

# The default TOOLS covers the tools used by the repo.
out="$(make -n check-tools)"
for t in actionlint bats checkmake gh markdownlint mbake prettier shellcheck shfmt taplo yamllint zizmor; do
	grep -qw "$t" <<<"$out" || fail "default TOOLS should include $t"
done
echo "PASS"
