ifndef HELP_MK_INCLUDED
HELP_MK_INCLUDED := 1

# Target that prints all documented targets in the included Makefiles.
#
# Add a `## description` comment after a target's prerequisites to have it
# show up in `make help`, e.g.:
#   .PHONY: format
#   format: format-yaml ## Format all files

.PHONY: help
help:
	@grep -Eh '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

endif
