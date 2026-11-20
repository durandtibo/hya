# Instructions for coding agents

## Environment

- Use the virtual environment in `.venv`: `.venv/bin/python`, `.venv/bin/pytest`, `.venv/bin/ruff`.
  There is no `python` on the `PATH`.
- Lint and format before committing: `.venv/bin/ruff check src tests` and
  `.venv/bin/ruff format src tests`. Fix the issues raised by ruff. Ignoring an issue (`noqa`, a
  changed rule set) is not fixing it.
- Type check with `.venv/bin/inv types.check` (ty) and
  `.venv/bin/pyright --verifytypes hya --ignoreexternal`. Fix the issues raised by the checkers.
  Ignoring an issue (`type: ignore`, `pyright: ignore`, a cast that hides the problem) is not
  fixing it.
- Run the unit tests of the modules you changed (for example
  `.venv/bin/pytest tests/unit/test_registry.py -q`). Some tests fail on `main`; check with
  `git stash` before blaming your change.
- The docstring examples are run as doctests: `.venv/bin/python -m pytest --xdoctest src/hya`.

## Workflow

- One branch and one pull request per logical change (one feature, one bug fix, one refactor).
  Branch from an up to date `main`.
- Name the branch `<type>/<short-description>` in lowercase kebab-case, for example
  `feat/add-resolver` or `bugfix/handle-empty-input`. Use one of these types:
  `feat` (new feature), `bugfix` (bug fix), `hotfix` (urgent fix), `docs` (documentation),
  `refactor` (no behaviour change), `perf` (performance), `test` (tests only),
  `chore` (maintenance, dependencies, tooling), `ci` (CI configuration).
- Do not commit or push to `main`.
- When working on several sequential PRs where one depends on the previous one, use stacked PRs:
  branch each PR from the branch of the previous one (not from `main`) and open it with the
  previous branch as its base. Keep each PR small and reviewable on its own. Once a PR of the stack
  is merged, retarget the next PR to `main` and merge `origin/main` into it.
- Write commit messages and PR titles as a short imperative sentence starting with a verb such as
  `Add`, `Fix`, `Update`, `Remove` or `Improve`. Do not use conventional-commit prefixes like
  `docs:` or `feat:` (the type prefix is only for branch names). The squash-merge appends the PR
  number, so do not add one.
- In the PR description, say what was changed, what was deliberately not changed, and any
  behaviour change (for example a changed output, or a breaking change of the signature). Follow
  `.github/PULL_REQUEST_TEMPLATE.md`.
- Do not escape special characters such as the backtick (`` ` ``) in the PR title or description
  (no `\``): the backslash is not rendered well. Write the characters as is.
- When a PR conflicts with `main`, merge `origin/main` into the branch and resolve the conflicts
  (do not rebase and force-push). Most conflicts are two PRs appending tests at the end of the
  same test file: keep both. Check what `main` already contains before choosing a side.
- Update any tracking document (documentation in `docs/`, issue) affected by the change.

## Code

- Match the surrounding code: comment density, naming, docstring style (Google style with
  `Args:`, `Returns:`, `Raises:` and a `pycon` example that runs as a doctest).
- Follow the current style of the repository in everything you add (source, tests, docs, commit
  messages, PR descriptions). Look at a few neighbouring files first, and do not introduce a new
  convention or reformat code you do not otherwise change.
- Every module starts with `from __future__ import annotations` and defines `__all__`.
- Shared helpers belong in `hya.utils` as public functions (no leading underscore) with their
  own tests, not as private functions imported across modules.
- Check optional packages with the functions of `hya.imports` (`check_numpy`,
  `is_torch_available`, ...); do not write a custom `try`/`except ImportError` or a
  `raise RuntimeError` for a missing package.
- Do not add a validator that is one `isinstance` or one comparison; raise the error inline with
  a clear message, as the existing code does.
- Keep new options keyword-only (`*`).
- Optional libraries (numpy, torch, braceexpand) are imported lazily or guarded with
  `is_*_available()` and a fallback from `hya.utils.fallback`; do not import them
  unconditionally at module level in `src`. Add a fallback when you add a new optional package.
- New resolvers are registered with the `ResolverRegistry` of their module (`hya.numpy`,
  `hya.torch`, `hya.default`, ...) and documented in `docs/`.
- Every function, public or private (leading underscore), needs a docstring and its own unit
  tests. Private functions are not exempt. An override that adds nothing to the docstring of the
  method it overrides (same behaviour, arguments and exceptions) has no docstring: it inherits the
  parent's. Document an override only when it adds something (for example a `Raises:` section).
- Document the constructor arguments (`Args:`, `Raises:`) in the class docstring, not in a
  docstring of `__init__`, as the existing classes do. Do not add a docstring to `__init__`
  or to the other dunder methods (`__repr__`, `__str__`, `__eq__`, ...).
- Keep docstrings and documentation up to date and comprehensive: update them whenever the
  behaviour, signature or options of the code change.

## Tests

- Always write tests for the code in `src/`, including every private function. Unit tests must be
  fast and efficient; move big or slow tests to `tests/integration/` if needed.
- Unit tests mirror the source tree (`tests/unit/test_<module>.py`, and
  `tests/unit/<package>/test_<module>.py` for subpackages such as `hya.utils`). Tests that exercise
  the real OmegaConf resolution end to end go in `tests/integration/`.
- Do not use local imports inside tests (for example `import torch` in a test body). Import
  at the top of the module; use the markers from `hya.testing` (`numpy_available`,
  `torch_available`, `braceexpand_available` and their `*_not_available` counterparts) for
  optional libraries.
- One behaviour per test: a test has one `assert` or one `pytest.raises`. Split a test that checks
  several things (equal, different, negative, ...) into several tests.
- Keep the unit tests simple and fast: no sleeps, no large data, no real network or heavy I/O,
  and no logic (loops, branches) in the test body. Anything slow belongs in
  `tests/integration/`.
- Add the missing tests to get 100% coverage of the code you add or change
  (`.venv/bin/pytest <tests> --cov=hya --cov-report=term-missing`). Do not use
  `# pragma: no cover` to skip a line that can be tested.
- Use `pytest.mark.parametrize` for the same check on several values.
- Every `pytest.raises` (and `pytest.warns`) must define `match` with a regular expression for the
  message (raw string if it has metacharacters), so a test does not pass on an unrelated error of
  the same type. An exception raised by a patched stand-in needs an explicit message for the same
  reason (`side_effect=KeyboardInterrupt("interrupted")`, not `side_effect=KeyboardInterrupt`).
- Add a regression test for every bug fixed, and check that it fails without the fix (revert the
  `src` change with `git stash push src` and run it).
- Do not add tests for the exports of `__all__` or other trivial structure.
- Section headers in the tests have three lines. The second line is `#`, 5 spaces, the name,
  5 spaces and `#`. The first and third lines repeat `#` to match the length of the second line:

  ```python
  ######################################
  #     Tests for ResolverRegistry     #
  ######################################
  ```

- Seed random data (`torch.manual_seed(0)`, `numpy.random.default_rng(0)`); no unseeded randomness
  in tests.
- Patching (`monkeypatch`, `unittest.mock.patch`) is fine in unit tests: it keeps them fast and
  simple and isolates the logic under test (for example to simulate a missing optional package).
  But a patched test only proves the logic works against the patched stand-in, which may not match
  the real collaborator (signature, return type, behaviour). A passing patched unit test does not
  mean the feature works. Every patched behaviour needs an integration test in
  `tests/integration/` that exercises the real thing without patching. The two kinds of test have
  different purposes; do not drop one because the other exists.

### Test assertions

- When asserting an expected value, write the final computed number, not the arithmetic
  expression that produces it (for example `0.6666666666666666`, not `1.0 * 0.4 + 0.0 * 0.2`).
  If the derivation is not obvious, keep the expression as a comment above the assertion.
- When a function returns a composite value (a dict, a list, ...), include at least one test that
  asserts the entire output against a fully-specified literal, not only individual keys or fields.
  This catches unexpected extra or missing entries that per-field assertions miss:

  ```python
  result = compute(...)
  assert result == {...}
  ```

### Test coverage

When implementing or modifying a function, write comprehensive unit tests, not just a happy-path
check. Cover, where applicable:

- Typical inputs.
- Edge cases: empty inputs, single-element inputs, duplicate inputs.
- Boundary values (0, negative numbers, min/max of a valid range).
- Error conditions: inputs that should raise, with the right exception type and message
  (including errors raised by collaborators the function calls).
- Interactions between parameters, for example a cross-product of two input lists, or the order
  of output keys or entries.
- Side effects: the function does not mutate its inputs, is deterministic across repeated calls,
  and does not leak state when given reused or stateful collaborators.
- Behaviour with and without each optional package (numpy, torch, braceexpand) installed.

Prefer many small, precisely named tests (one behavior per test) over a few broad ones, so a
failure points at the specific behavior that broke.

## GitHub Actions workflows

The workflows are in `.github/workflows/`. Read `.github/GUIDELINES.md` first: it lists every
workflow and the conventions (naming prefixes, action pinning, permissions, timeouts, runners).
The workflows follow those of [coola](https://github.com/durandtibo/coola).

- File names start with a prefix: `ci-` (checks of the source), `lib-` (reusable workflows that
  only expose outputs), `bot-` (scheduled automation that opens pull requests), `nightly-` (checks
  of the _published_ PyPI package), `release-` (PyPI and documentation publishing) and `security-`.
- `ci.yaml` is the single entry point of the checks (pull request, push to `main`, nightly,
  `workflow_call` for the release). It calls the reusable `ci-*.yaml` workflows. To add a check,
  create a reusable `ci-<name>.yaml` workflow and add a job in `ci.yaml`.
- The Python versions and the operating systems to test come from `lib-get-test-matrix.yaml`
  (`durandtibo/workflow-config-action`), and the optional dependencies from `pyproject.toml`
  (`lib-get-package-extras.yaml`, `durandtibo/extract-pyproject-metadata-action`). Do not hardcode
  them in a workflow.
- Every action is pinned to a commit SHA with a `# ratchet:owner/repo@vX.Y.Z` comment. Copy the pin
  of an existing workflow; `bot-pin-action.yaml` refreshes them.
- Conventions: a header comment that says what the workflow does and when it runs; `permissions: {}`
  at the top and the minimum `permissions` per job; `timeout-minutes` on every job;
  `workflow_dispatch` when it makes sense. Look at an existing workflow and copy its conventions.
- `ci-verify-workflows.yaml` lints the workflows: check your changes with `make lint-actions`
  (`actionlint`) and `make lint` when available.

## Releases

- Releases are immutable exact version tags (`v0.4.0`, ...). Do not create or move floating tags
  (`v0`, `latest`) and do not document them as an option.

## Reporting

- Report faithfully: say which tests were run, which were not, and that CI was not awaited.
- Mention test failures that already exist on `main` instead of hiding them.
