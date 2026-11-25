ifndef GIT_MK_INCLUDED
GIT_MK_INCLUDED := 1

# Targets for common git housekeeping tasks.
#
# Optional variables (set before including this file, or on the command line):
#   GIT_MAIN_BRANCH ?= main   # branch kept by git-delete-branches

GIT_MAIN_BRANCH ?= main

# Deletes every local branch except GIT_MAIN_BRANCH with `git branch -D` (even if unmerged).
# The checked-out branch cannot be deleted by git: it is reported and skipped.
.PHONY: git-delete-branches
git-delete-branches: ## Delete all local branches except GIT_MAIN_BRANCH (default: main)
	@echo "🧹 Deleting all local branches except $(GIT_MAIN_BRANCH)..."
	@git branch --format='%(refname:short)' | grep -vx -e '$(GIT_MAIN_BRANCH)' -e '(.*)' | \
	while IFS= read -r branch; do \
		git branch -D "$$branch" || echo "⚠️ Warning: could not delete $$branch"; \
	done; \
	echo "✅ Local branches cleaned up"

endif
