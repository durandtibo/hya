# GitHub Actions workflows

This directory holds every workflow for the repository. There are no
subdirectories: GitHub only discovers workflows placed directly under
`workflows`, so reusable workflows live here too, alongside the
top-level ones that trigger on events.

## Naming convention

Every file is prefixed by what it does:

| Prefix      | Purpose                                                                                                                                                              |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ci-`       | Quality/test checks, most of them reusable workflows called from `workflows/ci.yaml`.                                                                                |
| `lib-`      | Reusable workflows with no event trigger of their own; they only expose `workflow_call` outputs (e.g. reading a JSON config file) and are `needs:`-ed by other jobs. |
| `bot-`      | Scheduled automation that pushes commits / opens PRs as the `ci-bot` GitHub App.                                                                                     |
| `nightly-`  | Scheduled checks against the _published_ PyPI package (as opposed to `ci-*`, which checks the repo's source).                                                        |
| `release-`  | Publishing: PyPI package, GitHub release assets, documentation.                                                                                                      |
| `security-` | Supply-chain/security scanning (Scorecard, dependency review).                                                                                                       |

`workflows/ci.yaml` is the entry point for pull requests/pushes to `main`; it fans out
to the `ci-*.yaml` reusable workflows so each check can also be run/dispatched
on its own. Job ids in `ci.yaml` and in the workflows it calls are
load-bearing for branch protection (see the comment at the top of `ci.yaml`)
— keep them in sync if you rename either side.

One `ci-*` workflow is deliberately _not_ called from `ci.yaml`, with its own trigger instead:
`ci-verify-workflows.yaml` lints `.github/workflows/*` itself, so it triggers on every pull request
and push to `main` rather than being part of `ci.yaml`.

## Catalogue of the workflows

The trigger of a reusable workflow is `workflow_call`: it runs when another workflow calls it
(`ci.yaml` for the `ci-*` ones, `nightly-package.yaml` for the `nightly-test-*` ones).

| Workflow                             | Trigger                                | Purpose                                                                                                    |
| ------------------------------------ | -------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `ci.yaml`                            | pull request, push to `main`, nightly  | Entry point: calls the `ci-*` checks below.                                                                |
| `ci-build.yaml`                      | called by `ci.yaml`                    | Build the package and check that the built package installs.                                               |
| `ci-cyclic-imports.yaml`             | called by `ci.yaml`, manual            | Check that there is no circular import (`inv imports.check-cycles`).                                       |
| `ci-doctest.yaml`                    | called by `ci.yaml`, manual            | Run the doctests (`inv test.doctest`) and check that the documentation builds.                             |
| `ci-format.yaml`                     | called by `ci.yaml`, manual            | Check the formatting and the linting of the Python and shell files.                                        |
| `ci-pre-commit.yaml`                 | called by `ci.yaml`, manual            | Run all the pre-commit hooks.                                                                              |
| `ci-test.yaml`                       | called by `ci.yaml`                    | Unit and integration tests, with all the dependencies and with the required ones only.                     |
| `ci-test-deps.yaml`                  | called by `ci.yaml`                    | One job per dependency (`omegaconf` and each optional dependency), to test it with its supported versions. |
| `ci-test-code-dep.yaml`              | called by `ci-test-deps.yaml`          | Test the code with the supported versions of one dependency.                                               |
| `ci-type-checking.yaml`              | called by `ci.yaml`, manual            | Type check the package with `ty`.                                                                          |
| `ci-verify-workflows.yaml`           | pull request, push to `main`, manual   | Lint the files of `.github/workflows`.                                                                     |
| `lib-get-test-matrix.yaml`           | called by other workflows, manual      | Load the Python versions and the operating systems to test.                                                |
| `lib-get-package-extras.yaml`        | called by other workflows, manual      | Read the names of the optional dependencies from `pyproject.toml`.                                         |
| `lib-get-package-versions.yaml`      | called by other workflows, manual      | Read the versions of the optional dependencies to test from `dev/config`.                                  |
| `lib-get-package-deps.yaml`          | called by other workflows, manual      | Combine the two previous workflows.                                                                        |
| `nightly-package.yaml`               | nightly (10:30 UTC), manual            | Test the package published on PyPI: calls the three `nightly-test-*` workflows.                            |
| `nightly-test-package.yaml`          | called by `nightly-package.yaml`       | Run the tests against the installed PyPI package.                                                          |
| `nightly-test-package-dep.yaml`      | called by `nightly-package.yaml`       | Test the installed PyPI package with the supported versions of one dependency.                             |
| `nightly-test-package-extras.yaml`   | called by `nightly-package.yaml`       | Check that each extra of the PyPI package installs.                                                        |
| `release-pypi.yaml`                  | version tag `v*.*.*`, manual           | Build and publish the package to PyPI.                                                                     |
| `release-docs.yaml`                  | version tag `v*.*.*`, manual           | Deploy the documentation of the stable version (with `mike`).                                              |
| `release-docs-dev.yaml`              | push to `main`, manual                 | Deploy the documentation of the development version.                                                       |
| `release-docs-publish.yaml`          | called by the two previous workflows   | Build and deploy the documentation (shared logic).                                                         |
| `security-dependency-review.yaml`    | pull request                           | Review the dependencies added by the pull request.                                                         |
| `security-scorecard.yaml`            | weekly, push, branch protection change | OSSF Scorecard supply-chain analysis.                                                                      |
| `bot-cancel-stale-queued-runs.yaml`  | hourly                                 | Cancel the runs that have been queued for too long.                                                        |
| `bot-format-files.yaml`              | weekly (Friday)                        | Format the YAML, Makefile, shell and Markdown files and open a pull request.                               |
| `bot-generate-package-versions.yaml` | weekly (Thursday)                      | Update `dev/config/package_versions.json` and open a pull request.                                         |
| `bot-pin-action.yaml`                | weekly (Wednesday)                     | Pin the actions to a commit SHA (`ratchet`) and open a pull request.                                       |
| `bot-pre-commit-autoupdate.yaml`     | weekly (Tuesday)                       | Update the pre-commit hooks and open a pull request.                                                       |
| `bot-sync-shared-makefile.yaml`      | weekly (Wednesday)                     | Sync the shared Makefile subtree and open a pull request.                                                  |
| `bot-update-deps.yaml`               | weekly (Saturday)                      | Update the dependencies (`uv.lock`) and open a pull request.                                               |

All the workflows can also be triggered manually (`workflow_dispatch`), except the reusable ones
that need inputs and the pull request security review.

## Composite actions vs. reusable workflows

- **`.github/actions/*`** (composite actions): used when the shared unit is a
  handful of _steps_ inside a single job (e.g. checkout + `uv` setup,
  generating a bot token + checking out, or opening the resulting PR as
  ci-bot). Composite actions cannot produce a job-level output usable in a
  `strategy.matrix`.
- **`.github/workflows/lib-*.yaml`** (reusable workflows called with `uses:
./.github/workflows/lib-....yaml`): used when the output needs to feed a
  matrix, or when the shared logic is naturally a whole job (e.g. reading
  the supported Python versions and operating systems once and handing the JSON down to several
  jobs via `needs:`).

When adding new duplication, prefer extending an existing composite
action/reusable workflow over copy-pasting steps.

## Conventions applied to every workflow

- **Action pinning**: every third-party (and first-party `actions/*`) step is
  pinned to a full commit SHA with a trailing `# ratchet:owner/repo@vX.Y.Z`
  comment, added and refreshed automatically by
  [`ratchet`](https://github.com/sethvargo/ratchet) via `workflows/bot-pin-action.yaml`.
  Never hand-pin a SHA without that comment — the next `bot-pin-action` run
  would otherwise silently downgrade or drift it. Local composite actions
  (`uses: ./.github/actions/...`) are referenced by path, not pinned. Any
  runtime tool invoked outside of a pinned action (e.g. `npx <pkg>`) should
  also pin an explicit version, so a bot-authored PR can't pick up an
  unreviewed upstream release.
- **Permissions**: top-level `permissions:` is always the least the workflow
  needs — `contents: read` or `{}` — and any job that needs more (e.g.
  `contents: write` to push, `id-token: write` for OIDC) declares it on that
  job only, never widening the workflow default.
- **Timeouts**: every job sets `timeout-minutes`, sized to what the job
  actually does (2 for a config-read job, 5 for most checks, 10 for slower
  jobs like Scorecard or benchmarks) so a hung step can't occupy a runner
  indefinitely.
- **Runners**: `ubuntu-slim` for lightweight jobs that only run a small
  action or a couple of shell commands (no Python/build tooling); otherwise
  `ubuntu-latest`, or the OS matrix under test for `workflows/ci-test.yaml` /
  `nightly-test-package.yaml`.
- **`workflow_dispatch`**: added to every workflow (checks and automation
  alike) so it can be re-run manually without waiting for its normal trigger.

## Shared configuration

Values that would otherwise be duplicated across workflows are centralized in
`../dev/config`:

- The supported Python versions / OS matrix is not in this directory: it is the default
  config of `durandtibo/workflow-config-action`, read once per run by
  `lib-get-test-matrix.yaml`.
- `../dev/config/package_versions.json` — version ranges to test optional
  dependencies against, read by `lib-get-package-versions.yaml` and kept
  current by `bot-generate-package-versions.yaml`.

Optional-dependency _names_ are never duplicated in config: they're read
directly from `../pyproject.toml`'s `[project.optional-dependencies]` by the
`durandtibo/extract-pyproject-metadata-action` composite action /
`lib-get-package-extras.yaml`, so a
new extra only needs to be added in one place.

## Validating changes to this directory

`workflows/ci-verify-workflows.yaml` runs `durandtibo/verify-github-workflow-action` on
every PR/push that touches `.github/workflows/*`, checking pinning and
general workflow correctness. Locally, `actionlint` (run from this
directory) and a YAML syntax check are good pre-flight checks before pushing:

```bash
cd .github/workflows && actionlint
python3 -c "import yaml, glob; [yaml.safe_load(open(f)) for f in glob.glob('*.yaml')]"
```
