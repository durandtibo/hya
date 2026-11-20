ifndef YAML_MK_INCLUDED
YAML_MK_INCLUDED := 1

include $(dir $(lastword $(MAKEFILE_LIST)))tool-info.mk
include $(dir $(lastword $(MAKEFILE_LIST)))files.mk

# Targets for formatting and linting YAML files.
#
# Optional variables (set before including this file):
#   YAML_FORMAT_PATH ?= **/*.{yml,yaml}   # path or glob passed to prettier
#   YAML_LINT_PATH   ?= .                 # path passed to yamllint
#   USE_GITIGNORE ?= 1   # 1: skip the files ignored by .gitignore (see files.mk)

YAML_FORMAT_PATH ?= **/*.{yml,yaml}
YAML_LINT_PATH ?= .

include $(dir $(lastword $(MAKEFILE_LIST)))prettier.mk

.PHONY: format-yaml
format-yaml: install-prettier ## Format YAML files with prettier
	@echo "✨ Running prettier to format YAML files..."
	@output=$$(prettier $(PRETTIER_IGNORE_ARGS) --write '$(YAML_FORMAT_PATH)' 2>&1); status=$$?; \
	echo "$$output"; \
	if [ $$status -ne 0 ] && ! echo "$$output" | grep -q "No files matching the pattern"; then \
		exit $$status; \
	fi
	@echo "✅ Prettier formatting complete"

.PHONY: install-yamllint
install-yamllint:
	@if ! command -v yamllint >/dev/null 2>&1; then \
		echo "📦 yamllint not found, installing..."; \
		case "$$(uname -s)" in \
			Darwin) brew install yamllint ;; \
			*) pip3 install --user yamllint ;; \
		esac; \
	fi
	$(call show-tool,yamllint)

.PHONY: lint-yaml
lint-yaml: install-yamllint ## Lint YAML files with yamllint
	@echo "🔍 Running yamllint on YAML files..."
	@if $(use-gitignore); then \
		{ $(call list-files,$(YAML_LINT_PATH),**/*.yml); $(call list-files,$(YAML_LINT_PATH),**/*.yaml); } \
			| xargs -0 -r yamllint -f colored; \
	else \
		yamllint -f colored $(YAML_LINT_PATH); \
	fi
	@echo "✅ Yamllint passed"

endif
