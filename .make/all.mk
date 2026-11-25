ifndef ALL_MK_INCLUDED
ALL_MK_INCLUDED := 1

# One-stop entry point: `include <path>/all.mk` makes every target of this repo available.
#
# It includes every module (`yaml`, `makefile`, `shell`, `toml`, `markdown`, `actions`, `uv`, `git`,
# `github`, `tools`, `self` and `help`), sets `help` as the default goal and defines the aggregate
# `format` and `lint` targets. Set the optional variables of the modules before including it, and
# override `.DEFAULT_GOAL` after it if `help` is not the goal you want. A consumer that needs only
# some modules should include those directly instead.
#
# `format` runs `format-yaml`, `format-makefile`, `format-shell`, `format-toml` and
# `format-markdown`; `lint` runs `lint-yaml`, `lint-makefile`, `lint-shell`, `lint-markdown` and
# `lint-actions`.

_ALL_MK_DIR := $(dir $(lastword $(MAKEFILE_LIST)))

include $(_ALL_MK_DIR)yaml.mk
include $(_ALL_MK_DIR)makefile.mk
include $(_ALL_MK_DIR)shell.mk
include $(_ALL_MK_DIR)toml.mk
include $(_ALL_MK_DIR)markdown.mk
include $(_ALL_MK_DIR)actions.mk
include $(_ALL_MK_DIR)uv.mk
include $(_ALL_MK_DIR)git.mk
include $(_ALL_MK_DIR)github.mk
include $(_ALL_MK_DIR)tools.mk
include $(_ALL_MK_DIR)self.mk
include $(_ALL_MK_DIR)help.mk

.DEFAULT_GOAL := help

.PHONY: format
format: format-yaml format-makefile format-shell format-toml format-markdown ## Format all files

.PHONY: lint
lint: lint-yaml lint-makefile lint-shell lint-markdown lint-actions ## Lint all files

endif
