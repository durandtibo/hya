#!/usr/bin/env bash
# Test that the format/lint targets skip the files ignored by `.gitignore` (unless USE_GITIGNORE=0), using fake tools that record the files they receive.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

fail() {
	echo "FAIL: $1" >&2
	exit 1
}

# Fake tools: answer --version, and record their arguments (one per line) in $CALLS/<tool>.
mkdir -p "$work/bin" "$work/calls"
for tool in shellcheck shfmt taplo actionlint yamllint checkmake mbake prettier markdownlint; do
	cat >"$work/bin/$tool" <<'SH'
#!/usr/bin/env bash
if [ "${1:-}" = "--version" ]; then echo "${0##*/} 1.0.0"; exit 0; fi
printf '%s\n' "$@" >"$CALLS/${0##*/}"
# Keep a copy of the ignore file (a temporary file removed after the call).
while [ $# -gt 1 ]; do
	[ "$1" = "--ignore-path" ] && cp "$2" "$CALLS/${0##*/}.ignore"
	shift
done
SH
	chmod +x "$work/bin/$tool"
done
export PATH="$work/bin:$PATH"
export CALLS="$work/calls"

# Project: an ignored directory and an ignored file pattern next to regular files, a vendored `.make`, and a tracked file deleted from the work tree.
project="$work/project"
mkdir -p "$project/ignored/.github/workflows" "$project/sub" "$project/.make" "$project/.github/workflows"
cd "$project"
git init -q
git config user.email test@example.com
git config user.name test
printf 'ignored/\n*.gen.sh\nignored.mk\n' >.gitignore
touch ok.sh sub/s.sh x.gen.sh ignored/i.sh .make/v.sh gone.sh
touch ok.toml ignored/i.toml
touch ok.yaml ignored/i.yaml .github/workflows/w.yaml .github/workflows/w.yml ignored/.github/workflows/i.yaml
touch ok.mk ignored.mk
printf 'all:\n\t@true\n' >Makefile
git add gone.sh
git -c commit.gpgsign=false commit -q -m init
rm gone.sh

calls_of() { LC_ALL=C sort "$CALLS/$1" | tr '\n' ' '; }

check() { # check <module> <target> <tool> <expected sorted files, space terminated> [make args...]
	local module="$1" target="$2" tool="$3" expected="$4"
	shift 4
	rm -f "$CALLS/$tool"
	make -f "$repo_root/$module.mk" "$target" "$@" >/dev/null || fail "$module $target $* should succeed"
	[ "$(calls_of "$tool")" = "$expected" ] || fail "$module $target $*: expected [$expected], got [$(calls_of "$tool")]"
}

# 1. Inside a git work tree, ignored files, the vendored .make and deleted tracked files are skipped.
check shell lint-shell shellcheck "ok.sh sub/s.sh "
check shell format-shell shfmt "-l -w ok.sh sub/s.sh "
check toml format-toml taplo "format ok.toml "
check actions lint-actions actionlint "-color .github/workflows/w.yaml .github/workflows/w.yml "
check yaml lint-yaml yamllint "-f .github/workflows/w.yaml .github/workflows/w.yml colored ok.yaml "
check makefile lint-makefile checkmake "Makefile ok.mk "
check makefile format-makefile mbake "--config $repo_root/bake.toml Makefile format ok.mk "

# 2. USE_GITIGNORE=0: the ignored files are processed again (but still not the vendored .make).
check shell lint-shell shellcheck "./ignored/i.sh ./ok.sh ./sub/s.sh ./x.gen.sh " USE_GITIGNORE=0
check toml format-toml taplo "./ignored/i.toml ./ok.toml format " USE_GITIGNORE=0
check makefile lint-makefile checkmake "./Makefile ./ignored.mk ./ok.mk " USE_GITIGNORE=0
check actions lint-actions actionlint "-color ./.github/workflows/w.yaml ./.github/workflows/w.yml ./ignored/.github/workflows/i.yaml " USE_GITIGNORE=0

# 3. Prettier and markdownlint get the ignore files only when USE_GITIGNORE=1.
check yaml format-yaml prettier "**/*.{yml,yaml} --ignore-path --ignore-path --write .gitignore .prettierignore "
check yaml format-yaml prettier "**/*.{yml,yaml} --ignore-path --write .prettierignore " USE_GITIGNORE=0
rm -f "$CALLS/markdownlint"
printf 'ignored/\n' >.markdownlintignore
make -f "$repo_root/markdown.mk" lint-markdown >/dev/null || fail "lint-markdown should succeed"
grep -qx -e '--ignore-path' "$CALLS/markdownlint" || fail "markdownlint should get --ignore-path"
grep -qx 'ignored/' "$CALLS/markdownlint.ignore" || fail "markdownlint ignore file should contain .gitignore or .markdownlintignore patterns"
grep -qx '\*.gen.sh' "$CALLS/markdownlint.ignore" || fail "markdownlint ignore file should contain the .gitignore patterns"
rm -f "$CALLS/markdownlint.ignore"
make -f "$repo_root/markdown.mk" lint-markdown USE_GITIGNORE=0 >/dev/null || fail "lint-markdown USE_GITIGNORE=0 should succeed"
! grep -qx '\*.gen.sh' "$CALLS/markdownlint.ignore" || fail "USE_GITIGNORE=0: .gitignore patterns must not be passed to markdownlint"
grep -qx 'ignored/' "$CALLS/markdownlint.ignore" || fail "USE_GITIGNORE=0: .markdownlintignore must still be used"

# 3b. yamllint walks the path itself when USE_GITIGNORE=0.
check yaml lint-yaml yamllint "-f . colored " USE_GITIGNORE=0

# 3c. Untracked files that are not ignored are processed, as are names with spaces; a nested .gitignore is honoured.
touch "new file.sh" sub/nested.sh sub/skip.sh
printf 'skip.sh\n' >sub/.gitignore
check shell lint-shell shellcheck "new file.sh ok.sh sub/nested.sh sub/s.sh "
rm -f "new file.sh" sub/nested.sh sub/skip.sh sub/.gitignore

# 4. Outside a git repository, find is used, so the files are still found.
nogit="$work/nogit"
mkdir -p "$nogit/sub"
touch "$nogit/a.sh" "$nogit/sub/b.sh"
cd "$nogit"
check shell lint-shell shellcheck "./a.sh ./sub/b.sh "

echo "PASS: test-files-mk"
