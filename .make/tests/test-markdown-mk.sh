#!/usr/bin/env bash
# Test that Markdown globs (`**/*.md`, `*.md`) reach the tools unexpanded, so the tools resolve them.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# Fake tools: expand the single glob argument themselves (recursive `**`, via python3 since macOS bash 3.2 lacks globstar), record the files found.
mkdir -p "$work/bin"
for tool in markdownlint prettier; do
	cat >"$work/bin/$tool" <<'SH'
#!/usr/bin/env bash
args=("$@")
# Drop the flags added by the module (prettier ignore files, markdownlint ignore file).
while [ "${#args[@]}" -gt 1 ] && [[ "${args[0]}" == --* ]]; do
	case "${args[0]}" in --ignore-path) args=("${args[@]:2}") ;; *) args=("${args[@]:1}") ;; esac
done
[ "${#args[@]}" -eq 1 ] || { echo "expected exactly one glob argument, got: $*" >&2; exit 1; }
python3 -c 'import glob,sys; print("\n".join(sorted(glob.glob(sys.argv[1], recursive=True))))' "${args[0]}" >"$TOOL_FILES"
SH
	chmod +x "$work/bin/$tool"
done
export PATH="$work/bin:$PATH"
export TOOL_FILES="$work/files"

project="$work/project"
mkdir -p "$project/sub/deep"
cd "$project"
touch root.md sub/s.md sub/deep/d.md other.txt

fail() {
	echo "FAIL: $1" >&2
	exit 1
}

check() { # check <target> <var> <glob> <expected files, newline separated>
	rm -f "$TOOL_FILES"
	make -f "$repo_root/markdown.mk" "$1" "$2=$3" >/dev/null || fail "$1 $2='$3' should succeed"
	[ "$(cat "$TOOL_FILES")" = "$4" ] || fail "$1 $2='$3': expected [$4], got [$(cat "$TOOL_FILES")]"
}

all=$'root.md\nsub/deep/d.md\nsub/s.md'
for spec in "lint-markdown MARKDOWN_LINT_GLOB" "format-markdown MARKDOWN_FORMAT_PATH"; do
	# shellcheck disable=SC2086
	set -- $spec
	check "$1" "$2" '**/*.md' "$all"
	check "$1" "$2" '*.md' "root.md"
	check "$1" "$2" 'sub/**/*.md' $'sub/deep/d.md\nsub/s.md'
done

echo "PASS: test-markdown-mk"
