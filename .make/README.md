# shared-makefiles

[![CI](https://github.com/durandtibo/shared-makefiles/actions/workflows/ci.yaml/badge.svg)](https://github.com/durandtibo/shared-makefiles/actions/workflows/ci.yaml)
[![Nightly](https://github.com/durandtibo/shared-makefiles/actions/workflows/nightly.yaml/badge.svg)](https://github.com/durandtibo/shared-makefiles/actions/workflows/nightly.yaml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/durandtibo/shared-makefiles/badge)](https://scorecard.dev/viewer/?uri=github.com/durandtibo/shared-makefiles)
[![License](https://img.shields.io/badge/license-BSD--3--Clause-blue)](LICENSE)
[![Latest release](https://img.shields.io/github/v/tag/durandtibo/shared-makefiles?label=release)](https://github.com/durandtibo/shared-makefiles/tags)

Shared/reusable Makefiles for formatting and linting common file types across projects.

Each file is self-contained, include-guarded, and configurable via variables — pull in only what
you need.

## Usage

Include `all.mk` to get every target (`format`, `lint`, `install-tools`, `help`, ...), or include
only the files you need:

```makefile
include .make/all.mk
```

Required tools (`prettier`, `yamllint`, `mbake`, `checkmake`, `shellcheck`, `shfmt`, `markdownlint`,
`actionlint`) are installed on demand — each `format-*`/`lint-*` target depends on an `install-*`
target that installs the tool if it isn't already on `PATH`, then prints the tool's name, version
and path. Run `make install-tools` (from `tools.mk`) to install every tool of `TOOLS` upfront;
include the modules of those tools, or narrow `TOOLS`.

Run `make help` to list every target that has a `## description` comment (see `help.mk` below).

## Adding as a git subtree

This repo is meant to be vendored into consuming projects as a git subtree (conventionally at
`.make/`), rather than being added as a submodule or copy-pasted:

```shell
git remote add shared-makefiles https://github.com/durandtibo/shared-makefiles.git
git fetch shared-makefiles main

git subtree add --prefix=.make shared-makefiles main --squash
```

Then `include` the files you need from `.make/` in your project's `Makefile`, e.g.
`include .make/yaml.mk`.

To pull in upstream changes later, `include .make/self.mk` and run `make self-update` — see
[`self.mk`](#selfmk) below. It fetches the latest commits and runs `git subtree pull`, so you
don't need to remember the raw `git subtree`/`git remote` invocations yourself.

## Available files

| File           | Targets                                                               | Tools                      | Description                                                                                                         |
| -------------- | --------------------------------------------------------------------- | -------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `yaml.mk`      | `format-yaml`, `lint-yaml`                                            | `prettier`, `yamllint`     | Format and lint YAML files                                                                                          |
| `makefile.mk`  | `format-makefile`, `lint-makefile`                                    | `mbake`, `checkmake`       | Format and lint Makefiles and `.mk` files                                                                           |
| `shell.mk`     | `format-shell`, `lint-shell`                                          | `shfmt`, `shellcheck`      | Format and lint shell scripts                                                                                       |
| `toml.mk`      | `format-toml`                                                         | `taplo`                    | Format TOML files                                                                                                   |
| `markdown.mk`  | `format-markdown`, `lint-markdown`                                    | `prettier`, `markdownlint` | Format and lint Markdown files                                                                                      |
| `actions.mk`   | `lint-actions`, `lint-actions-security`                               | `actionlint`, `zizmor`     | Lint GitHub Actions workflow files; audit workflows and composite actions for security issues                       |
| `git.mk`       | `git-delete-branches`                                                 | `git`                      | Delete all local branches except `main`                                                                             |
| `github.mk`    | `gh-rerun-failed`                                                     | `gh`                       | Re-run failed/cancelled GitHub Actions runs                                                                         |
| `uv.mk`        | `install-invoke`, `update-uv`, `setup-venv`                           | `uv`                       | Manage Python virtual environments with `uv`                                                                        |
| `prettier.mk`  | `install-prettier`                                                    | `prettier`                 | Shared `install-prettier` target, included by `yaml.mk`/`markdown.mk`                                               |
| `files.mk`     | —                                                                     | —                          | Shared helpers that make the format/lint targets skip the files ignored by `.gitignore` (`USE_GITIGNORE`)           |
| `tool-info.mk` | —                                                                     | —                          | Shared `show-tool` helper used by the `install-*` targets to print a tool's version and path                        |
| `self.mk`      | `self-update`, `update-subtree` (deprecated)                          | `git`                      | Sync the `.make` shared-makefiles subtree                                                                           |
| `tools.mk`     | `install-tools`, `check-tools`, `check-tool-releases`, `update-tools` | —                          | Show which tools are installed and which are missing, and when their versions were released; update installed tools |
| `all.mk`       | `format`, `lint`                                                      | —                          | Include every module, make `help` the default goal, and define `format` and `lint`                                  |
| `help.mk`      | `help`                                                                | —                          | List all documented (`## ...`) targets                                                                              |

### Ignored files

By default every format/lint target skips the files ignored by `.gitignore`, in addition to the
tools' own ignore files (`.prettierignore`, `.markdownlintignore`, the `ignore` key of
`.yamllint.yaml`, ...). `files.mk` lists the files with `git ls-files` (tracked files and untracked
files that are not ignored) and falls back to `find` outside a git work tree. `prettier` gets
`--ignore-path .gitignore --ignore-path .prettierignore`, and `markdownlint` gets an ignore file
combining the root `.gitignore` and `.markdownlintignore`.

| Variable        | Default | Description                                                                |
| --------------- | ------- | -------------------------------------------------------------------------- |
| `USE_GITIGNORE` | `1`     | `1` skips the files ignored by `.gitignore`; any other value does not skip |

Set it before `include`, or on the command line (`make lint USE_GITIGNORE=0`). It applies to
`yaml.mk`, `makefile.mk`, `shell.mk`, `toml.mk`, `markdown.mk` and `actions.mk`.

### `yaml.mk`

Optional variables (set before `include`):

| Variable           | Default | Description                                                   |
| ------------------ | ------- | ------------------------------------------------------------- |
| `YAML_FORMAT_PATH` | `.`     | Root path globbed for `**/*.{yml,yaml}`, passed to `prettier` |
| `YAML_LINT_PATH`   | `.`     | Path passed to `yamllint`                                     |

```makefile
include yaml.mk

YAML_LINT_PATH = .github/workflows
```

### `makefile.mk`

Optional variables (set before `include`):

| Variable                | Default | Description                                                                  |
| ----------------------- | ------- | ---------------------------------------------------------------------------- |
| `MAKEFILE_PATH`         | `.`     | Directory searched recursively for `Makefile`, `GNUmakefile` and `*.mk`      |
| `MAKEFILE_FORMAT_FILES` | (empty) | If set, shell globs passed to `mbake format` instead of the recursive search |
| `MAKEFILE_LINT_FILES`   | (empty) | If set, shell globs passed to `checkmake` instead of the recursive search    |

Files in nested directories are included; git-ignored files and vendored `.make` directories are
skipped (see `USE_GITIGNORE`).

```makefile
include makefile.mk

MAKEFILE_LINT_FILES = Makefile makefile.mk yaml.mk
```

### `shell.mk`

Optional variables (set before `include`):

| Variable            | Default | Description                                           |
| ------------------- | ------- | ----------------------------------------------------- |
| `SHELL_FORMAT_PATH` | `.`     | Path passed to `shfmt` (walked recursively)           |
| `SHELL_LINT_PATH`   | `.`     | Path searched for `*.sh` files passed to `shellcheck` |

```makefile
include shell.mk

SHELL_LINT_PATH = scripts
```

### `toml.mk`

Optional variables (set before `include`):

| Variable           | Default | Description                                        |
| ------------------ | ------- | -------------------------------------------------- |
| `TOML_FORMAT_PATH` | `.`     | Path searched for `*.toml` files passed to `taplo` |

```makefile
include toml.mk

TOML_FORMAT_PATH = config
```

### `markdown.mk`

Optional variables (set before `include`):

| Variable               | Default   | Description                                           |
| ---------------------- | --------- | ----------------------------------------------------- |
| `MARKDOWN_FORMAT_PATH` | `.`       | Root path globbed for `**/*.md`, passed to `prettier` |
| `MARKDOWN_LINT_GLOB`   | `**/*.md` | Glob passed to `markdownlint`                         |

```makefile
include markdown.mk

MARKDOWN_LINT_GLOB = docs/**/*.md
```

### `actions.mk`

Optional variables (set before `include`):

| Variable            | Default | Description                                                                                                                                   |
| ------------------- | ------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `ACTIONS_LINT_PATH` | `.`     | Path searched for `.github/workflows/*.{yml,yaml}` files (`actionlint`, `zizmor`) and `.github/actions/**/action.{yml,yaml}` files (`zizmor`) |

```makefile
include actions.mk

ACTIONS_LINT_PATH = .
```

### `git.mk`

`make git-delete-branches` runs `git branch -D` on every local branch except `GIT_MAIN_BRANCH`.
Unmerged work is lost. The checked-out branch cannot be deleted by git, so it is skipped with a warning.

Optional variables (set before `include`):

| Variable          | Default | Description                          |
| ----------------- | ------- | ------------------------------------ |
| `GIT_MAIN_BRANCH` | `main`  | Branch kept by `git-delete-branches` |

### `github.mk`

Requires an authenticated GitHub CLI (`gh auth login`). `gh-rerun-failed` is the equivalent of "Re-run
failed jobs" in the web UI, applied to the last runs that failed, were cancelled or timed out;
successful and still-running runs are left alone.

Optional variables (set before `include`, or on the command line):

| Variable              | Default | Description                                              |
| --------------------- | ------- | -------------------------------------------------------- |
| `GITHUB_RERUN_LIMIT`  | `5`     | Number of most recent runs considered                    |
| `GITHUB_RERUN_BRANCH` | empty   | Only consider runs of this branch (empty = all branches) |

```makefile
include github.mk
```

```bash
make gh-rerun-failed                                   # last 5 runs, any branch
make gh-rerun-failed GITHUB_RERUN_LIMIT=10 GITHUB_RERUN_BRANCH=main
```

### `uv.mk`

Optional variables (set before `include`):

| Variable         | Default | Description                                 |
| ---------------- | ------- | ------------------------------------------- |
| `PYTHON_VERSION` | `3.14`  | Python version passed to `uv venv --python` |

```makefile
include uv.mk

PYTHON_VERSION = 3.12
```

`install-invoke` installs `uv` on demand and then `invoke>=3.0` and `invoke-tasklib>=0.0.8` via
`uv pip install` into the active virtual environment (create one first, e.g. with `uv venv`).
`update-uv` runs `uv self update`. `setup-venv` updates `uv`, creates a fresh `.venv`
(`uv venv --python $(PYTHON_VERSION) --clear`), installs `invoke` into it, and runs
`uv run inv env.create-venv` and `uv run inv env.install` — it assumes the project's
`tasks.py` exposes the `invoke-tasklib` tasks (`from invoke_tasklib import ns`).

### `self.mk`

For projects that vendor this repo as a subtree (e.g. at `.make/`), `self.mk` provides a target
to pull in upstream changes.

Optional variables (set before `include`):

| Variable                       | Default                                              | Description     |
| ------------------------------ | ---------------------------------------------------- | --------------- |
| `SHARED_MAKEFILES_REMOTE_NAME` | `shared-makefiles`                                   | Git remote name |
| `SHARED_MAKEFILES_REMOTE_URL`  | `https://github.com/durandtibo/shared-makefiles.git` | Git remote URL  |
| `SHARED_MAKEFILES_BRANCH`      | `main`                                               | Branch to pull  |
| `SHARED_MAKEFILES_PREFIX`      | `.make`                                              | Subtree prefix  |

```makefile
include self.mk
```

`self-update` adds the `$(SHARED_MAKEFILES_REMOTE_NAME)` remote if missing, fetches
`$(SHARED_MAKEFILES_BRANCH)`, and runs `git subtree pull --prefix=$(SHARED_MAKEFILES_PREFIX)
$(SHARED_MAKEFILES_REMOTE_NAME) $(SHARED_MAKEFILES_BRANCH) --squash` to sync the subtree. It then
removes the `.github/`, `testdata/` and `tests/` folders and files such as `CODEOWNERS` from within
`$(SHARED_MAKEFILES_PREFIX)` (not needed in consuming projects) and commits the removal.

`update-subtree` is a deprecated alias kept for backward compatibility: it prints a warning and runs
`self-update`. Migrate to `self-update`; the alias may be removed in a future release.

### `tools.mk`

`make check-tools` looks up each tool of `TOOLS` on the `PATH`, prints one aligned line per tool
(✅ with its version and path, or ❌ if missing) and exits with code 127 if any is missing.

`make check-tool-releases` does the same and adds the release date of each installed version. The
date is looked up online (GitHub releases, npm or PyPI, per `TOOL_SOURCES`) with `curl`, so it is
slower than `check-tools`, which stays instant and offline. A date that cannot be found is shown as
`?` and does not fail the target; set `GITHUB_TOKEN` to avoid GitHub rate limits.

`make update-tools` upgrades the installed tools of `TOOLS` to their latest version, using the package
manager that installed each one (Homebrew, npm, pipx, uv, pip or apt). Tools that are not installed
are skipped, as are tools installed another way (`go install`, a downloaded binary). It carries on
after a failed upgrade and exits with 1 at the end.

Optional variables (set before `include`):

| Variable          | Default                                                                                           | Description                                                                                 |
| ----------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| `TOOLS`           | `actionlint bats checkmake gh markdownlint mbake prettier shellcheck shfmt taplo yamllint zizmor` | Space-separated tools to check                                                              |
| `TOOL_SOURCES`    | one entry per default tool                                                                        | `<tool>=<kind>:<id>` entries (`github:owner/repo`, `npm:pkg`, `pypi:pkg`) for release dates |
| `TOOL_BREW_NAMES` | `bats=bats-core`                                                                                  | `<tool>=<name>` when the Homebrew/apt name differs from the tool (`update-tools`)           |
| `TOOL_NPM_NAMES`  | `markdownlint=markdownlint-cli taplo=@taplo/cli`                                                  | `<tool>=<package>` when the npm package differs from the tool (`update-tools`)              |

### `help.mk`

```makefile
include help.mk

.PHONY: format
format: format-yaml ## Format all files
```

`help` scans every included Makefile (`$(MAKEFILE_LIST)`) for lines matching
`target: ... ## description` and prints them, sorted, as `target` / `description` pairs. Only
targets with a trailing `## ...` comment show up — add one to any target you want documented. Every
target defined in this repo's own `.mk` files is already annotated this way, so `include`-ing any
of them and running `make help` lists them for free.

## Design

- **Include guards** — each file defines an `_MK_INCLUDED` variable so it's safe to `include`
  more than once (e.g. transitively from multiple project Makefiles).
- **On-demand install** — every lint/format target depends on an `install-<tool>` target that
  checks `command -v` before installing, so CI and local runs don't need the tool preinstalled.
- **Configurable paths** — variables default to sensible project-wide values but can be
  overridden per project or per target invocation.
- **`.make/` excluded by default** — this repo is meant to be vendored as a subtree at `.make/`
  in consuming projects, so every formatter/linter skips that folder by default:
  [`.prettierignore`](.prettierignore) and [`.markdownlintignore`](.markdownlintignore) exclude
  it, `.yamllint.yaml` sets `ignore: .make/`, and `shell.mk`'s `find` commands `-prune` it.

## Testing

[`.github/workflows/ci.yaml`](.github/workflows/ci.yaml) exercises every module (one reusable
`ci-<module>.yaml` workflow each) against the Unix OS matrix (Ubuntu and macOS runners) and, for
`uv.mk`, the Python versions, resolved dynamically via
[`durandtibo/workflow-config-action`](https://github.com/durandtibo/workflow-config-action) in
[`lib-get-test-matrix.yaml`](.github/workflows/lib-get-test-matrix.yaml). It runs on every push/PR
to `main`, nightly and on demand, running both the lint and format targets (including on-demand
tool installation) to make sure the rules stay portable across platforms.

## License

This repo is licensed under BSD 3-Clause "New" or "Revised" license available in [LICENSE](LICENSE)
file.
