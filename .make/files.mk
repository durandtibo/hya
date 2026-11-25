ifndef FILES_MK_INCLUDED
FILES_MK_INCLUDED := 1

# Shared helpers that make the format/lint targets skip the files ignored by git.
#
# Optional variables (set before including this file, or on the command line):
#   USE_GITIGNORE ?= 1   # 1: skip the files ignored by `.gitignore`; any other value: do not
#
# Helpers (used inside recipes):
#   `$(call list-files,<dir>,<glob>)` prints, NUL-separated, the files below `<dir>` that match
#   `<glob>` (a `**/`-prefixed glob such as `**/*.sh`). Inside a git work tree with
#   `USE_GITIGNORE=1`, it lists the tracked and untracked files that are not ignored; otherwise it
#   falls back to `find`. Vendored `.make` directories are always skipped. Pipe it to
#   `xargs -0 -r <tool>`.
#   `$(call is-ignored,<file>)` is a shell condition that succeeds if `<file>` is ignored by git
#   and `USE_GITIGNORE=1`.
#   `$(use-gitignore)` is a shell condition that succeeds inside a git work tree with
#   `USE_GITIGNORE=1`.

USE_GITIGNORE ?= 1

use-gitignore = [ "$(USE_GITIGNORE)" = 1 ] && git rev-parse --is-inside-work-tree >/dev/null 2>&1

is-ignored = ( $(use-gitignore) && git check-ignore -q -- "$(1)" )

# The `xargs` filter drops files that are tracked but deleted from the work tree.
list-files = if $(use-gitignore); then \
	git ls-files -z --cached --others --exclude-standard -- ':(glob)$(1)/$(2)' ':(exclude,glob)**/.make/**' \
	| xargs -0 sh -c 'for f; do [ -e "$$f" ] && printf "%s\0" "$$f"; done' _; \
	else \
	find $(1) -type d -name '.make' -prune -o -type f -path '*/$(patsubst **/%,%,$(2))' -print0; \
	fi

endif
