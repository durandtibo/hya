ifndef SELF_MK_INCLUDED
SELF_MK_INCLUDED := 1

# Target for syncing the shared-makefiles subtree in a consuming project.
# The subtree is assumed to be unmodified locally: on merge conflicts, the upstream version wins.
#
# Optional variables (set before including this file):
#   SHARED_MAKEFILES_REMOTE_NAME ?= shared-makefiles                                   # git remote name
#   SHARED_MAKEFILES_REMOTE_URL  ?= https://github.com/durandtibo/shared-makefiles.git # git remote URL
#   SHARED_MAKEFILES_BRANCH      ?= main                                               # branch to pull
#   SHARED_MAKEFILES_PREFIX      ?= .make                                              # subtree prefix
#   SHARED_MAKEFILES_CLEANUP     ?= .github testdata .gitignore CONTRIBUTING.md ...   # files removed after sync

SHARED_MAKEFILES_REMOTE_NAME ?= shared-makefiles
SHARED_MAKEFILES_REMOTE_URL ?= https://github.com/durandtibo/shared-makefiles.git
SHARED_MAKEFILES_BRANCH ?= main
SHARED_MAKEFILES_PREFIX ?= .make
SHARED_MAKEFILES_CLEANUP ?= .github testdata tests .gitignore CODE_OF_CONDUCT.md CODEOWNERS CLAUDE.md CONTRIBUTING.md README.md SECURITY.md

.PHONY: update-subtree
update-subtree: ## Deprecated alias of self-update
	@echo "⚠️  'update-subtree' is deprecated and will be removed; use 'make self-update' instead."
	@$(MAKE) --no-print-directory self-update

.PHONY: self-update
self-update: ## Sync the shared-makefiles subtree from upstream
	@echo "🔄 Syncing $(SHARED_MAKEFILES_PREFIX) subtree from $(SHARED_MAKEFILES_REMOTE_URL)..."
	git remote add $(SHARED_MAKEFILES_REMOTE_NAME) $(SHARED_MAKEFILES_REMOTE_URL) || true
	git fetch $(SHARED_MAKEFILES_REMOTE_NAME) $(SHARED_MAKEFILES_BRANCH)
	@if ! git diff --cached --quiet; then \
		echo "❌ index has staged changes; commit or 'git reset' them first"; \
		exit 1; \
	fi
	@set -e; \
	if [ -d "$(SHARED_MAKEFILES_PREFIX)" ] && ! git log --grep="git-subtree-dir: $(SHARED_MAKEFILES_PREFIX)$$" --format=%H -1 | grep -q .; then \
		echo "⚠️  $(SHARED_MAKEFILES_PREFIX) exists but has no subtree history; re-adding it..."; \
		git rm -rq $(SHARED_MAKEFILES_PREFIX); \
		git commit -m "chore: remove $(SHARED_MAKEFILES_PREFIX) before subtree re-add"; \
		git subtree add --prefix=$(SHARED_MAKEFILES_PREFIX) $(SHARED_MAKEFILES_REMOTE_NAME) $(SHARED_MAKEFILES_BRANCH) --squash -m "chore: sync shared Makefile subtree"; \
	elif [ ! -d "$(SHARED_MAKEFILES_PREFIX)" ]; then \
		git subtree add --prefix=$(SHARED_MAKEFILES_PREFIX) $(SHARED_MAKEFILES_REMOTE_NAME) $(SHARED_MAKEFILES_BRANCH) --squash -m "chore: sync shared Makefile subtree"; \
	else \
		if ! git subtree pull --prefix=$(SHARED_MAKEFILES_PREFIX) $(SHARED_MAKEFILES_REMOTE_NAME) $(SHARED_MAKEFILES_BRANCH) --squash -m "chore: sync shared Makefile subtree"; then \
			conflicts=$$(git diff --name-only --diff-filter=U -- $(SHARED_MAKEFILES_PREFIX)); \
			if [ -z "$$conflicts" ]; then \
				echo "❌ subtree pull failed"; \
				exit 1; \
			fi; \
			echo "⚠️  Conflicts in $(SHARED_MAKEFILES_PREFIX); keeping the upstream version..."; \
			for f in $$conflicts; do \
				if git checkout --theirs -- "$$f" 2>/dev/null; then \
					git add -- "$$f"; \
				else \
					git rm -rq --cached -- "$$f"; \
					rm -rf "$$f"; \
				fi; \
			done; \
			git commit -q --no-edit -m "chore: sync shared Makefile subtree"; \
		fi; \
	fi
	@removed=""; \
	for f in $(SHARED_MAKEFILES_CLEANUP); do \
		if [ -e "$(SHARED_MAKEFILES_PREFIX)/$$f" ]; then \
			git rm -rq --ignore-unmatch "$(SHARED_MAKEFILES_PREFIX)/$$f"; \
			rm -rf "$(SHARED_MAKEFILES_PREFIX)/$$f"; \
			removed="$$removed $$f"; \
		fi; \
	done; \
	if [ -n "$$removed" ]; then \
		echo "🧹 Removed from $(SHARED_MAKEFILES_PREFIX):$$removed"; \
		git commit -m "chore: remove unnecessary files from synced subtree" || true; \
	fi
	@echo "✅ Subtree sync complete"

endif
