# CLAUDE.md

Guidance for coding agents working in this repository.

## Repository purpose

Shared, reusable Makefiles for formatting and linting common file types (YAML, Markdown, shell,
TOML, Makefiles, GitHub Actions) plus a few housekeeping helpers (git, GitHub CLI, tool checks).
Consumers vendor this repo as a git subtree (conventionally at `.make/`) and `include` the `.mk`
files they need.

- `*.mk` — one self-contained module per file type or concern: `yaml.mk`, `shell.mk`, `toml.mk`,
  `markdown.mk`, `makefile.mk`, `actions.mk`, `uv.mk`, `git.mk`, `github.mk`, `tools.mk`.
- Helpers included by other modules: `prettier.mk`, `tool-info.mk` (`show-tool`, used by the
  `install-*` targets), `files.mk` (`list-files`, `USE_GITIGNORE`: skip git-ignored files),
  `help.mk` (`make help`), `self.mk` (`self-update`).
- `Makefile` — the repo's own entry point; includes every module and defines `install-tools`,
  `format` and `lint`.
- `testdata/` — sample files (`sample.yaml`, `sample.md`, `sample.sh`, `sample.toml`) used by CI to
  exercise each module.
- `tests/` — shell tests, one per module that needs one (`tests/test-<module>-mk.sh`).
- Config for the tools: `bake.toml` (mbake), `checkmake.ini`.

## Environment

- Use the `Makefile`; run `make help` to list documented targets.
- Tools (`prettier`, `yamllint`, `mbake`, `checkmake`, `shellcheck`, `shfmt`, `bats`, `taplo`,
  `markdownlint`, `actionlint`, `zizmor`, `gh`, ...) are installed on demand by `install-*`
  targets; run `make install-tools` to install them all and `make check-tools` to see what is
  installed.
- Run `make format` and `make lint` before committing. Fix what they report instead of disabling
  rules.
- Run the shell test of any module you touch, e.g. `bash tests/test-self-mk.sh` for `self.mk` or
  `bash tests/test-tools-mk.sh` for `tools.mk`. Some workflows cannot be run locally; say so in
  the PR instead of claiming they pass.

## Git workflow

- One branch and one PR per logical change, branched from an up-to-date `main`. Never commit or
  push to `main`.
- Name branches `<type>/<short-description>` in kebab-case, with type one of: `feat`, `bugfix`,
  `hotfix`, `docs`, `refactor`, `perf`, `test`, `chore`, `ci`.
- Write commit messages and PR titles as a short imperative sentence starting with a verb such as
  `Add`, `Fix`, `Update`, `Remove` or `Improve`. Do not use conventional-commit prefixes like
  `docs:` or `feat:` (the type prefix is only for branch names). The squash-merge appends the PR
  number, so do not add one.
- PR descriptions cover what changed, what was deliberately left alone, and any behaviour change
  (renamed targets, changed variable defaults), since consumers depend on them.
- On conflicts with `main`, merge `origin/main` into the branch; do not rebase and force-push.
- Update `README.md` when targets, variables, modules or workflows change.
- Follow `.github/PULL_REQUEST_TEMPLATE.md` and `CONTRIBUTING.md`.

## Makefile rules (`*.mk`)

- Every `.mk` file is include-guarded:
  `ifndef FOO_MK_INCLUDED` / `FOO_MK_INCLUDED := 1` ... `endif`.
- Document optional variables in a header comment and define them with `?=` so consumers can
  override them before including.
- Include sibling modules via `$(dir $(lastword $(MAKEFILE_LIST)))other.mk` so the file works from
  any vendored path.
- Mark every target `.PHONY`.
- Public targets carry a `## description` comment so they appear in `make help`. Internal
  `install-*` targets do not.
- Each `format-*`/`lint-*` target depends on an `install-*` target that installs the tool only if
  it is missing from `PATH` (Homebrew on Darwin, a sensible fallback elsewhere) and ends with
  `$(call show-tool,<tool>)` from `tool-info.mk`.
- Keep modules independent: a consumer must be able to include only the files they need.
- Match the existing output style (emoji-prefixed `@echo` start/finish messages).
- Recipes must work on both macOS and Linux (GNU and BSD tools); avoid GNU-only flags.
- Never hardcode paths to the consumer's layout; expose them as variables.
- Do not rename or remove a public target or variable, or change a default, without flagging it as
  a breaking change.
- When adding or renaming a module or target, update `README.md` and the root `Makefile`
  (`include`, `install-tools`, `format`, `lint`) and `TOOLS` in `tools.mk` if a tool is added.

## Workflow structure (`.github/workflows/`)

Files are prefixed by role:

- `ci.yaml`: entry point for pull requests, pushes to `main`, a nightly schedule and manual runs.
  It holds no steps, only jobs that call the reusable `ci-*.yaml` workflows below.
  - `ci-format.yaml`: runs `make format` and checks that nothing changed; not matrix-based, so
    `ci.yaml` calls it without `test-matrix`.
  - `ci-<module>.yaml` (`ci-yaml`, `ci-makefile`, `ci-shell`, `ci-toml`, `ci-markdown`,
    `ci-actions`, `ci-uv`, `ci-git`, `ci-github`): run the targets of `<module>.mk` against
    `testdata/` on the OS matrix (`ci-uv` also uses the Python matrix).
  - `ci-self.yaml`, `ci-tools.yaml`, `ci-files.yaml`: run `tests/test-self-mk.sh`,
    `tests/test-tools-mk.sh` and `tests/test-files-mk.sh` on the OS matrix.
- `ci-verify-workflows.yaml`: lints the workflow files themselves. It has its own triggers and is
  not called from `ci.yaml`, so it can be a required check.
- `lib-get-test-matrix.yaml`: reusable workflow that loads the OS/Python matrices once from
  `durandtibo/workflow-config-action`; callers pass them down via the `test-matrix` input.
- `bot-*.yaml`: scheduled automation (`bot-format-files`, `bot-pin-action`,
  `bot-cancel-stale-queued-runs`); the first two open PRs using a GitHub App token.
- `security-*.yaml`: dependency review and OSSF Scorecard.

Conventions:

- Every workflow has `permissions: {}` at the workflow level (it grants nothing, never a grant)
  and explicit minimal `permissions` on every job, including jobs that call a reusable workflow.
- Each matrix `ci-<module>` workflow is `workflow_call` only, takes the required `test-matrix`
  string input, and sets `timeout-minutes` and `fail-fast: false`.
- A new module gets its own `ci-<module>.yaml` plus a job (with `needs: get-matrix`) in `ci.yaml`.
- Put `make` targets in the steps rather than duplicating commands, so local runs and CI match.
- Pin third-party actions to commit SHAs with a `# ratchet:<owner>/<repo>@<tag>` comment (see
  `bot-pin-action.yaml`), never to tags or branches.
- Pass inputs to scripts through `env:`, never by interpolating them in `run:`.
- Start each file with a comment saying what it does, and update it when the behaviour changes.

## Tests

- Shell tests live in `tests/test-<module>-mk.sh`. They use temp dirs and fake tools, and must not
  touch the real repo or the network.
- Add a sample file in `testdata/` (if the module processes files), a test script (if it has
  logic), a `ci-<module>.yaml` workflow and a job in `ci.yaml` for every new module.
- Cover success, failure, and edge cases.
- Every bug fix needs a regression test that fails without the fix.
- If a check fails for a real reason, report it rather than weakening the test.

## Reporting

- State which checks ran (`make format`, `make lint`, `bash tests/test-<module>-mk.sh`) and which
  did not.
- Note that CI was not awaited.
- Report failures that already exist on `main` rather than hiding them.
