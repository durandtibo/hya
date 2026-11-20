ifndef MARKDOWN_MK_INCLUDED
MARKDOWN_MK_INCLUDED := 1

include $(dir $(lastword $(MAKEFILE_LIST)))tool-info.mk
include $(dir $(lastword $(MAKEFILE_LIST)))files.mk

# Targets for formatting and linting Markdown files.
#
# Optional variables (set before including this file):
#   MARKDOWN_FORMAT_PATH ?= **/*.md      # path or glob passed to prettier
#   MARKDOWN_LINT_GLOB   ?= **/*.md      # glob passed to markdownlint
#   USE_GITIGNORE ?= 1   # 1: skip the files ignored by .gitignore (see files.mk)

MARKDOWN_FORMAT_PATH ?= **/*.md
MARKDOWN_LINT_GLOB ?= **/*.md

include $(dir $(lastword $(MAKEFILE_LIST)))prettier.mk

.PHONY: format-markdown
format-markdown: install-prettier ## Format Markdown files with prettier
	@echo "✨ Running prettier to format Markdown files..."
	@output=$$(prettier $(PRETTIER_IGNORE_ARGS) --write '$(MARKDOWN_FORMAT_PATH)' 2>&1); status=$$?; \
	echo "$$output"; \
	if [ $$status -ne 0 ] && ! echo "$$output" | grep -q "No files matching the pattern"; then \
		exit $$status; \
	fi
	@echo "✅ Prettier formatting complete"

.PHONY: install-markdownlint
install-markdownlint:
	@if ! command -v markdownlint >/dev/null 2>&1; then \
		echo "📦 markdownlint not found, installing..."; \
		npm install -g markdownlint-cli; \
	fi
	$(call show-tool,markdownlint)

.PHONY: lint-markdown
lint-markdown: install-markdownlint ## Lint Markdown files with markdownlint
	@echo "🔍 Running markdownlint on Markdown files..."
	@ignore="$$(mktemp)"; trap 'rm -f "$$ignore"' EXIT; \
	if [ "$(USE_GITIGNORE)" = 1 ]; then cat .gitignore >>"$$ignore" 2>/dev/null || true; fi; \
		cat .markdownlintignore >>"$$ignore" 2>/dev/null || true; \
		markdownlint --ignore-path "$$ignore" '$(MARKDOWN_LINT_GLOB)'
	@echo "✅ Markdownlint passed"

endif
