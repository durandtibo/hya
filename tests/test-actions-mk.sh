#!/usr/bin/env bash
# Test `install-zizmor` (installs zizmor only when missing) and `lint-actions-security` (which files zizmor receives and how
# failures propagate), with fake tools and no network.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

fail() {
	echo "FAIL: $1" >&2
	exit 1
}

# Minimal PATH: only make, uname, chmod, grep and head are real, so a zizmor/brew/uv installed on the machine is hidden.
mkdir -p "$work/base" "$work/fake"
for cmd in make uname chmod grep head; do
	ln -s "$(command -v "$cmd")" "$work/base/$cmd"
done
run_make() {
	PATH="$work/fake:$work/base" make -f "$repo_root/actions.mk" install-zizmor 2>&1
}

# Fake installer that records its call and puts a fake zizmor on the PATH.
installer="uv"
[ "$(uname -s)" = "Darwin" ] && installer="brew"
cat >"$work/fake/$installer" <<SH
#!/bin/sh
echo "\$*" >>"$work/calls"
printf '#!/bin/sh\n' >"$work/fake/zizmor"
chmod +x "$work/fake/zizmor"
SH
chmod +x "$work/fake/$installer"

# 1. zizmor missing: it is installed with the platform installer.
out="$(run_make)" || fail "install should succeed when zizmor is missing"
grep -q "zizmor not found" <<<"$out" || fail "should report that zizmor is missing"
grep -q "zizmor" "$work/calls" || fail "$installer should be called with zizmor"
[ -x "$work/fake/zizmor" ] || fail "zizmor should be installed"

# 2. zizmor present: nothing is installed.
rm -f "$work/calls"
out="$(run_make)" || fail "install should succeed when zizmor is present"
[ ! -e "$work/calls" ] || fail "installer must not be called when zizmor is present"
! grep -q "not found" <<<"$out" || fail "should be silent when zizmor is present"

# 3. Linux without any installer: fails with a hint.
if [ "$(uname -s)" != "Darwin" ]; then
	rm -f "$work/fake/zizmor" "$work/fake/uv"
	rc=0
	out="$(run_make)" || rc=$?
	[ "$rc" -ne 0 ] || fail "should fail without any installer"
	grep -q "Please install zizmor" <<<"$out" || fail "should explain how to install zizmor"
fi

# 4. lint-actions-security passes the workflow and action files to zizmor, and only those.
proj="$work/proj"
mkdir -p "$proj/.github/workflows" "$proj/.github/actions/one" "$proj/.github/actions/two" "$proj/.make/.github/workflows"
for f in .github/workflows/a.yaml .github/workflows/b.yml .github/actions/one/action.yml \
	.github/actions/two/action.yaml .github/workflows/notes.txt .github/actions/one/README.md \
	.make/.github/workflows/vendored.yaml; do
	: >"$proj/$f"
done
mkdir -p "$work/zfake"
cat >"$work/zfake/zizmor" <<SH
#!/bin/sh
[ "\$1" = "--version" ] && { echo "zizmor 0.0.0"; exit 0; }
printf '%s\n' "\$@" >"$work/zizmor-args"
exit \${FAKE_ZIZMOR_RC:-0}
SH
chmod +x "$work/zfake/zizmor"
run_lint() {
	(cd "$proj" && PATH="$work/zfake:$PATH" make -f "$repo_root/actions.mk" lint-actions-security \
		ACTIONS_LINT_PATH=. USE_GITIGNORE=0 2>&1)
}
out="$(run_lint)" || fail "lint-actions-security should succeed when zizmor succeeds"
grep -q "Zizmor passed" <<<"$out" || fail "should report success"
for f in workflows/a.yaml workflows/b.yml actions/one/action.yml actions/two/action.yaml; do
	grep -q "\.github/$f\$" "$work/zizmor-args" || fail "zizmor should receive $f"
done
! grep -q -e "notes.txt" -e "README.md" -e "vendored" "$work/zizmor-args" || fail "zizmor must only receive workflow and action files"

# 5. A zizmor failure fails the target.
rc=0
FAKE_ZIZMOR_RC=1 run_lint >/dev/null || rc=$?
[ "$rc" -ne 0 ] || fail "lint-actions-security should fail when zizmor fails"

# 6. No workflow or action file: zizmor is not called and the target succeeds.
rm -f "$work/zizmor-args"
empty="$work/empty"
mkdir -p "$empty"
(cd "$empty" && PATH="$work/zfake:$PATH" make -f "$repo_root/actions.mk" lint-actions-security \
	ACTIONS_LINT_PATH=. USE_GITIGNORE=0 >/dev/null 2>&1) || fail "should succeed without files"
[ ! -e "$work/zizmor-args" ] || fail "zizmor must not be called without files"
echo "PASS"
