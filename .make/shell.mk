ifndef SHELL_MK_INCLUDED
SHELL_MK_INCLUDED := 1

include $(dir $(lastword $(MAKEFILE_LIST)))tool-info.mk
include $(dir $(lastword $(MAKEFILE_LIST)))files.mk

# Targets for formatting and linting shell scripts.
#
# Optional variables (set before including this file):
#   SHELL_FORMAT_PATH ?= .   # path passed to shfmt (walked recursively)
#   SHELL_LINT_PATH   ?= .   # path searched for *.sh files passed to shellcheck
#   USE_GITIGNORE ?= 1   # 1: skip the files ignored by .gitignore (see files.mk)

SHELL_FORMAT_PATH ?= .
SHELL_LINT_PATH ?= .
SHFMT_VERSION ?= v3.10.0

.PHONY: install-shellcheck
install-shellcheck:
	@if ! command -v shellcheck >/dev/null 2>&1; then \
		echo "📦 shellcheck not found, installing..."; \
		case "$$(uname -s)" in \
			Darwin) brew install shellcheck ;; \
			*) sudo apt-get update && sudo apt-get install -y shellcheck ;; \
		esac; \
	fi
	$(call show-tool,shellcheck)

.PHONY: install-bats
install-bats:
	@if ! command -v bats >/dev/null 2>&1; then \
		echo "📦 bats not found, installing..."; \
		case "$$(uname -s)" in \
			Darwin) brew install bats-core ;; \
			*) sudo apt-get update && sudo apt-get install -y bats ;; \
		esac; \
	fi
	$(call show-tool,bats)

.PHONY: install-shfmt
install-shfmt:
	@if ! command -v shfmt >/dev/null 2>&1; then \
		echo "📦 shfmt not found, installing..."; \
		case "$$(uname -s)" in \
			Darwin) brew install shfmt ;; \
			*) \
			if command -v go >/dev/null 2>&1 && go install mvdan.cc/sh/v3/cmd/shfmt@latest; then \
				gobin="$$(go env GOBIN)"; \
				if [ -z "$$gobin" ]; then gobin="$$(go env GOPATH)/bin"; fi; \
					sudo cp "$$gobin/shfmt" /usr/local/bin/shfmt; \
				else \
					arch="$$(uname -m)"; \
					case "$$arch" in \
						x86_64) arch=amd64 ;; \
						aarch64|arm64) arch=arm64 ;; \
					esac; \
					curl -fsSL -o /tmp/shfmt "https://github.com/mvdan/sh/releases/download/$(SHFMT_VERSION)/shfmt_$(SHFMT_VERSION)_linux_$${arch}"; \
					chmod +x /tmp/shfmt; \
					sudo mv /tmp/shfmt /usr/local/bin/shfmt; \
				fi; \
				;; \
		esac; \
	fi
	$(call show-tool,shfmt)

.PHONY: lint-shell
lint-shell: install-shellcheck ## Lint shell scripts with shellcheck
	@echo "🐚 Running shellcheck on shell scripts..."
	@$(call list-files,$(SHELL_LINT_PATH),**/*.sh) | xargs -0 -r shellcheck
	@echo "✅ Shellcheck passed"

.PHONY: format-shell
format-shell: install-shfmt ## Format shell scripts with shfmt
	@echo "🔧 Running shfmt to format shell scripts..."
	@$(call list-files,$(SHELL_FORMAT_PATH),**/*.sh) | xargs -0 -r shfmt -l -w
	@echo "✅ Shell formatting complete"

.PHONY: check-format-shell
check-format-shell: install-shfmt ## Check shell script formatting with shfmt
	@echo "🔍 Checking shell script formatting with shfmt..."
	@$(call list-files,$(SHELL_FORMAT_PATH),**/*.sh) | xargs -0 -r shfmt -d
	@echo "✅ Shell formatting is correct"

endif
