ifndef TOOL_INFO_MK_INCLUDED
TOOL_INFO_MK_INCLUDED := 1

# Shared helper used by the install-* targets to report an installed tool.
#
# `$(call show-tool,<tool>)` is a recipe line that prints the tool name, its version (first version
# number printed by `<tool> --version`, `?` if none) and its path, e.g.:
#   actionlint    1.7.12    /opt/homebrew/bin/actionlint
# It warns (without failing) if the tool is not on the `PATH`, e.g. right after a user-level install.

# bake-format off
define show-tool
@tool="$(1)"; \
if path=$$(command -v "$$tool"); then \
version=$$("$$tool" --version </dev/null 2>&1 | grep -o -E '[0-9]+(\.[0-9]+)+' | head -n 1 || true); \
printf '%-13s %-9s %s\n' "$$tool" "$${version:-?}" "$$path"; \
else \
echo "⚠️ $$tool is not on the PATH"; \
fi
endef
# bake-format on

endif
