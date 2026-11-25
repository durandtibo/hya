ifndef ACTIONS_MK_INCLUDED
ACTIONS_MK_INCLUDED := 1

include $(dir $(lastword $(MAKEFILE_LIST)))tool-info.mk
include $(dir $(lastword $(MAKEFILE_LIST)))files.mk

# Targets for linting GitHub Actions workflow files and composite actions.
#
# Optional variables (set before including this file):
#   ACTIONS_LINT_PATH ?= .   # path searched for workflow files passed to actionlint, and for workflow and
#                              action files passed to zizmor
#   USE_GITIGNORE ?= 1   # 1: skip the files ignored by .gitignore (see files.mk)

ACTIONS_LINT_PATH ?= .

.PHONY: install-actionlint
install-actionlint:
	@if ! command -v actionlint >/dev/null 2>&1; then \
		echo "📦 actionlint not found, installing..."; \
		case "$$(uname -s)" in \
			Darwin) brew install actionlint ;; \
			*) \
			if command -v go >/dev/null 2>&1 && go install github.com/rhysd/actionlint/cmd/actionlint@latest; then \
				gobin="$$(go env GOBIN)"; \
				if [ -z "$$gobin" ]; then gobin="$$(go env GOPATH)/bin"; fi; \
					sudo cp "$$gobin/actionlint" /usr/local/bin/actionlint; \
				else \
					curl -fsSL https://raw.githubusercontent.com/rhysd/actionlint/main/scripts/download-actionlint.bash | bash -s -- latest /tmp; \
					sudo mv /tmp/actionlint /usr/local/bin/actionlint; \
				fi \
				;; \
		esac; \
	fi
	$(call show-tool,actionlint)

.PHONY: install-zizmor
install-zizmor:
	@if ! command -v zizmor >/dev/null 2>&1; then \
		echo "📦 zizmor not found, installing..."; \
		case "$$(uname -s)" in \
			Darwin) brew install zizmor ;; \
			*) \
			if command -v uv >/dev/null 2>&1; then \
				uv tool install zizmor; \
			elif command -v pipx >/dev/null 2>&1; then \
				pipx install zizmor; \
			elif command -v cargo >/dev/null 2>&1; then \
				cargo install --locked zizmor; \
			else \
				echo "❌ Please install zizmor: https://docs.zizmor.sh/installation/"; exit 1; \
			fi \
				;; \
		esac; \
	fi
	$(call show-tool,zizmor)

.PHONY: lint-actions
lint-actions: install-actionlint ## Lint GitHub Actions workflow files with actionlint
	@echo "⚙️ Running actionlint on GitHub Actions workflow files..."
	@{ $(call list-files,$(ACTIONS_LINT_PATH),**/.github/workflows/*.yml); \
	$(call list-files,$(ACTIONS_LINT_PATH),**/.github/workflows/*.yaml); } | xargs -0 -r actionlint -color
	@echo "✅ Actionlint passed"

.PHONY: lint-actions-security
lint-actions-security: install-zizmor ## Audit GitHub Actions workflows and actions with zizmor
	@echo "⚙️ Running zizmor on GitHub Actions workflow and action files..."
	@{ $(call list-files,$(ACTIONS_LINT_PATH),**/.github/workflows/*.yml); \
	$(call list-files,$(ACTIONS_LINT_PATH),**/.github/workflows/*.yaml); \
	$(call list-files,$(ACTIONS_LINT_PATH),**/.github/actions/**/action.yml); \
	$(call list-files,$(ACTIONS_LINT_PATH),**/.github/actions/**/action.yaml); } | xargs -0 -r zizmor --no-progress
	@echo "✅ Zizmor passed"

endif
