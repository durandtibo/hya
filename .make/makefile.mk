ifndef MAKEFILE_MK_INCLUDED
MAKEFILE_MK_INCLUDED := 1

include $(dir $(lastword $(MAKEFILE_LIST)))tool-info.mk
include $(dir $(lastword $(MAKEFILE_LIST)))files.mk

# Targets for formatting and linting Makefiles and *.mk files.
#
# Optional variables (set before including this file):
#   MAKEFILE_PATH         ?= .   # directory searched recursively for Makefile, GNUmakefile and *.mk
#   MAKEFILE_FORMAT_FILES ?=     # if set, shell globs passed to mbake format instead of the search
#   MAKEFILE_LINT_FILES   ?=     # if set, shell globs passed to checkmake instead of the search
#   MBAKE_CONFIG          ?= <this dir>/bake.toml   # config passed to mbake format
#   USE_GITIGNORE ?= 1   # 1: skip the files ignored by .gitignore (see files.mk)

MAKEFILE_PATH ?= .
MAKEFILE_FORMAT_FILES ?=
MAKEFILE_LINT_FILES ?=

# Prints, NUL-separated, the files to process: the given globs ($(1)) if not empty, otherwise
# every Makefile, GNUmakefile and *.mk file below MAKEFILE_PATH (nested directories included).
makefile-files = if [ -n "$(1)" ]; then \
	for pattern in $(1); do \
		for f in $$pattern; do \
			[ -e "$$f" ] && ! $(call is-ignored,$$f) && printf "%s\0" "$$f"; \
		done; \
	done; \
	else \
	{ $(call list-files,$(MAKEFILE_PATH),**/Makefile); \
	$(call list-files,$(MAKEFILE_PATH),**/GNUmakefile); \
	$(call list-files,$(MAKEFILE_PATH),**/*.mk); }; \
	fi

MBAKE_CONFIG ?= $(dir $(lastword $(MAKEFILE_LIST)))bake.toml

CHECKMAKE_VERSION ?= v0.3.2

# mbake has no Homebrew formula, so macOS also goes through pipx/pip.
.PHONY: install-mbake
install-mbake:
	@if ! command -v mbake >/dev/null 2>&1; then \
		echo "📦 mbake not found, installing..."; \
		if command -v pipx >/dev/null 2>&1; then \
			pipx install mbake; \
		elif [ "$$(uname -s)" = "Darwin" ]; then \
			brew install pipx && pipx install mbake; \
		else \
			pip3 install --user --break-system-packages mbake; \
		fi; \
	fi
	$(call show-tool,mbake)

.PHONY: install-checkmake
install-checkmake:
	@if ! command -v checkmake >/dev/null 2>&1; then \
		echo "📦 checkmake not found, installing..."; \
		case "$$(uname -s)" in \
			Darwin) brew install checkmake ;; \
			*) \
			if command -v go >/dev/null 2>&1 && go install github.com/mrtazz/checkmake/cmd/checkmake@latest; then \
				: ; \
			else \
				arch="$$(uname -m)"; \
				case "$$arch" in \
					x86_64) arch=amd64 ;; \
					aarch64|arm64) arch=arm64 ;; \
				esac; \
					curl -fsSL -o /tmp/checkmake "https://github.com/checkmake/checkmake/releases/download/$(CHECKMAKE_VERSION)/checkmake-$(CHECKMAKE_VERSION).linux.$${arch}"; \
					chmod +x /tmp/checkmake; \
					sudo mv /tmp/checkmake /usr/local/bin/checkmake; \
				fi; \
				;; \
		esac; \
	fi
	$(call show-tool,checkmake)

.PHONY: format-makefile
format-makefile: install-mbake ## Format Makefiles and .mk files with mbake
	@echo "✨ Running mbake to format Makefiles..."
	@{ $(call makefile-files,$(MAKEFILE_FORMAT_FILES)); } | xargs -0 -r mbake format --config $(MBAKE_CONFIG)
	@echo "✅ Makefile formatting complete"

.PHONY: lint-makefile
lint-makefile: install-checkmake ## Lint Makefiles and .mk files with checkmake
	@echo "🔍 Running checkmake on Makefiles..."
	@{ $(call makefile-files,$(MAKEFILE_LINT_FILES)); } | xargs -0 -r checkmake
	@echo "✅ Checkmake passed"

endif
