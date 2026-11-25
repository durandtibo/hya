#!/usr/bin/env bash
# Test that `format-makefile` and `lint-makefile` find Makefiles in nested directories (skipping ignored files and `.make`), honour MAKEFILE_PATH, USE_GITIGNORE=0 and explicit globs, and skip unmatched globs.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# Fake checkmake: answers --version (called by install-checkmake) without recording it, records its arguments and fails if any is not an existing file.
mkdir -p "$work/bin"
cat >"$work/bin/checkmake" <<'SH'
#!/usr/bin/env bash
if [ "${1:-}" = "--version" ]; then echo "checkmake 1.0.0"; exit 0; fi
echo "$*" >"$CHECKMAKE_ARGS_FILE"
for f in "$@"; do
	[ -f "$f" ] || { echo "Error opening '$f'" >&2; exit 1; }
done
SH
chmod +x "$work/bin/checkmake"
# Fake mbake: answers --version, records its arguments.
cat >"$work/bin/mbake" <<'SH'
#!/usr/bin/env bash
if [ "${1:-}" = "--version" ]; then echo "mbake 1.0.0"; exit 0; fi
echo "$*" >"$MBAKE_ARGS_FILE"
SH
chmod +x "$work/bin/mbake"
export MBAKE_ARGS_FILE="$work/mbake-args"
export PATH="$work/bin:$PATH"
export CHECKMAKE_ARGS_FILE="$work/args"

project="$work/project"
mkdir -p "$project"
cd "$project"
printf '.PHONY: all\nall:\n\t@true\n' >Makefile

fail() {
	echo "FAIL: $1" >&2
	exit 1
}

# 0. Nested files are found by default; a vendored .make and ignored files are skipped.
mkdir -p a/b .make ign
touch a/b/n.mk a/Makefile .make/v.mk ign/i.mk
printf 'ign/\n' >.gitignore
git init -q .
make -f "$repo_root/makefile.mk" lint-makefile >/dev/null || fail "nested search should pass"
[ "$(tr ' ' '\n' <"$CHECKMAKE_ARGS_FILE" | LC_ALL=C sort | tr '\n' ' ')" = "Makefile a/Makefile a/b/n.mk " ] || fail "nested: got: $(cat "$CHECKMAKE_ARGS_FILE")"
sorted_args() { tr ' ' '\n' <"$1" | grep -v '^$' | LC_ALL=C sort | tr '\n' ' '; }
# format-makefile gets the same nested files (after `format --config <file>`).
make -f "$repo_root/makefile.mk" format-makefile >/dev/null || fail "nested format should pass"
[ "$(sed 's|^format --config [^ ]* ||' "$MBAKE_ARGS_FILE" | tr ' ' '\n' | LC_ALL=C sort | tr '\n' ' ')" = "Makefile a/Makefile a/b/n.mk " ] || fail "nested format: got: $(cat "$MBAKE_ARGS_FILE")"
# GNUmakefile and MAKEFILE_PATH: only the files below the given directory.
touch a/GNUmakefile
make -f "$repo_root/makefile.mk" lint-makefile MAKEFILE_PATH=a >/dev/null || fail "MAKEFILE_PATH should pass"
[ "$(sorted_args "$CHECKMAKE_ARGS_FILE")" = "a/GNUmakefile a/Makefile a/b/n.mk " ] || fail "MAKEFILE_PATH: got: $(cat "$CHECKMAKE_ARGS_FILE")"
# USE_GITIGNORE=0 includes the ignored file but still skips .make.
make -f "$repo_root/makefile.mk" lint-makefile USE_GITIGNORE=0 >/dev/null || fail "USE_GITIGNORE=0 should pass"
[ "$(sorted_args "$CHECKMAKE_ARGS_FILE")" = "./Makefile ./a/GNUmakefile ./a/Makefile ./a/b/n.mk ./ign/i.mk " ] || fail "USE_GITIGNORE=0: got: $(cat "$CHECKMAKE_ARGS_FILE")"
# Explicit globs replace the search (nested files are not added).
make -f "$repo_root/makefile.mk" lint-makefile MAKEFILE_LINT_FILES="a/*.mk a/Makefile" >/dev/null || fail "explicit globs should pass"
[ "$(sorted_args "$CHECKMAKE_ARGS_FILE")" = "a/Makefile " ] || fail "explicit globs: got: $(cat "$CHECKMAKE_ARGS_FILE")"
rm -rf a .make ign .gitignore .git

# 1. Explicit globs with no *.mk file: only Makefile is linted.
rm -f "$CHECKMAKE_ARGS_FILE"
make -f "$repo_root/makefile.mk" lint-makefile MAKEFILE_LINT_FILES="Makefile *.mk" >/dev/null || fail "default patterns without *.mk should pass"
[ "$(cat "$CHECKMAKE_ARGS_FILE")" = "Makefile" ] || fail "expected only Makefile, got: $(cat "$CHECKMAKE_ARGS_FILE")"

# 2. Default search with a *.mk file: both files are linted.
touch extra.mk
make -f "$repo_root/makefile.mk" lint-makefile >/dev/null || fail "default patterns with *.mk should pass"
[ "$(cat "$CHECKMAKE_ARGS_FILE")" = "./Makefile ./extra.mk" ] || fail "expected Makefile and extra.mk, got: $(cat "$CHECKMAKE_ARGS_FILE")"

# 3. Nothing matches: checkmake is not run and the target succeeds.
rm -f "$CHECKMAKE_ARGS_FILE"
make -f "$repo_root/makefile.mk" lint-makefile MAKEFILE_LINT_FILES="no-such-dir/*.mk" >/dev/null || fail "no matching files should not fail"
[ ! -e "$CHECKMAKE_ARGS_FILE" ] || fail "checkmake should not run when nothing matches"

# 4. format-makefile: nothing matches, mbake is not run and the target succeeds.
rm -f "$MBAKE_ARGS_FILE"
make -f "$repo_root/makefile.mk" format-makefile MAKEFILE_FORMAT_FILES="no-such-dir/*.mk" >/dev/null || fail "no matching files should not fail"
[ ! -e "$MBAKE_ARGS_FILE" ] || fail "mbake should not run when nothing matches"

echo "PASS: test-makefile-mk"
