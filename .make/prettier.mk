ifndef PRETTIER_MK_INCLUDED
PRETTIER_MK_INCLUDED := 1

include $(dir $(lastword $(MAKEFILE_LIST)))tool-info.mk
include $(dir $(lastword $(MAKEFILE_LIST)))files.mk

# Shared target for installing prettier, used by yaml.mk and markdown.mk, and `PRETTIER_IGNORE_ARGS`,
# the flags that make prettier skip the files ignored by `.gitignore` (unless `USE_GITIGNORE` is not
# 1, see files.mk) and `.prettierignore`.

PRETTIER_IGNORE_ARGS = $(if $(filter 1,$(USE_GITIGNORE)),--ignore-path .gitignore )--ignore-path .prettierignore

.PHONY: install-prettier
install-prettier:
	@if ! command -v prettier >/dev/null 2>&1; then \
		echo "📦 prettier not found, installing..."; \
		npm install -g prettier; \
	fi
	$(call show-tool,prettier)

endif
