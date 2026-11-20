ifndef GITHUB_MK_INCLUDED
GITHUB_MK_INCLUDED := 1

include $(dir $(lastword $(MAKEFILE_LIST)))tool-info.mk

# Targets for working with GitHub Actions runs through the GitHub CLI (`gh`).
#
# `gh` must be authenticated (`gh auth login`) and run inside a clone of the target repository.
#
# Optional variables (set before including this file, or on the command line):
#   GITHUB_RERUN_LIMIT  ?= 5   # number of most recent runs considered by gh-rerun-failed
#   GITHUB_RERUN_BRANCH ?=     # only consider runs of this branch (empty = all branches)

GITHUB_RERUN_LIMIT ?= 5
GITHUB_RERUN_BRANCH ?=

.PHONY: install-gh
install-gh:
	@if ! command -v gh >/dev/null 2>&1; then \
		echo "📦 gh not found, installing..."; \
		case "$$(uname -s)" in \
			Darwin) brew install gh ;; \
			*) \
			if command -v apt-get >/dev/null 2>&1; then \
				sudo apt-get update && sudo apt-get install -y gh; \
			else \
				echo "❌ Please install the GitHub CLI: https://cli.github.com"; exit 1; \
			fi \
				;; \
		esac; \
	fi
	$(call show-tool,gh)

# Equivalent of "Re-run failed jobs" in the web UI, applied to the last runs whose conclusion is
# failure, cancelled or timed_out. Successful, skipped and still-running runs are left untouched.
# A run that cannot be re-run (e.g. too old) only produces a warning; the target does not fail.
.PHONY: gh-rerun-failed
gh-rerun-failed: install-gh ## Re-run failed/cancelled runs among the last GITHUB_RERUN_LIMIT runs (optional GITHUB_RERUN_BRANCH)
	@echo "🔁 Re-running failed/cancelled runs among the last $(GITHUB_RERUN_LIMIT) runs$(if $(GITHUB_RERUN_BRANCH), of branch $(GITHUB_RERUN_BRANCH))..."
	@ids="$$(gh run list --limit '$(GITHUB_RERUN_LIMIT)' $(if $(GITHUB_RERUN_BRANCH),--branch '$(GITHUB_RERUN_BRANCH)') \
		--json databaseId,conclusion \
		--jq '.[] | select(.conclusion == "failure" or .conclusion == "cancelled" or .conclusion == "timed_out") | .databaseId')" \
		|| exit 1; \
	if [ -z "$$ids" ]; then \
		echo "✅ No failed or cancelled runs to re-run"; \
	else \
		ok=0; skipped=0; \
		for id in $$ids; do \
			echo "🔁 Re-running failed jobs of run $$id"; \
			if gh run rerun "$$id" --failed; then \
				ok=$$((ok + 1)); \
			else \
				echo "⚠️ Warning: run $$id could not be re-run, skipping it"; \
				skipped=$$((skipped + 1)); \
			fi; \
		done; \
		echo "✅ Re-triggered $$ok run(s), $$skipped skipped"; \
	fi

endif
