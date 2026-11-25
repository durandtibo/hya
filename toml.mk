ifndef TOML_MK_INCLUDED
TOML_MK_INCLUDED := 1

include $(dir $(lastword $(MAKEFILE_LIST)))tool-info.mk
include $(dir $(lastword $(MAKEFILE_LIST)))files.mk

# Targets for formatting TOML files.
#
# Optional variables (set before including this file):
#   TOML_FORMAT_PATH ?= .   # path searched for *.toml files passed to taplo
#   USE_GITIGNORE ?= 1   # 1: skip the files ignored by .gitignore (see files.mk)

TOML_FORMAT_PATH ?= .

.PHONY: install-taplo
install-taplo:
	@if ! command -v taplo >/dev/null 2>&1; then \
		echo "📦 taplo not found, installing..."; \
		case "$$(uname -s)" in \
			Darwin) brew install taplo ;; \
			*) npm install -g @taplo/cli ;; \
		esac; \
	fi
	$(call show-tool,taplo)

.PHONY: format-toml
format-toml: install-taplo ## Format TOML files with taplo
	@echo "✨ Running taplo to format TOML files..."
	@$(call list-files,$(TOML_FORMAT_PATH),**/*.toml) | xargs -0 -r taplo format
	@echo "✅ Taplo formatting complete"

endif
