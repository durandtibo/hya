r"""Define some tasks that are executed with invoke."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from invoke.tasks import task

if TYPE_CHECKING:
    from invoke.context import Context


logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


NAME = "hya"
SOURCE = f"src/{NAME}"
TESTS = "tests"
UNIT_TESTS = f"{TESTS}/unit"
INTEGRATION_TESTS = f"{TESTS}/integration"
FUNCTIONAL_TESTS = f"{TESTS}/functional"
PYTHON_VERSION = "3.13"


@task
def check_format(c: Context) -> None:
    r"""Check code format with black.

    This task verifies that all Python code follows Black's formatting rules
    without modifying any files. Use the 'format' task to automatically fix
    formatting issues.

    Args:
        c: The invoke context.
    """
    logger.info("🎨 Checking code format with black...")
    c.run("black --check .", pty=True)
    logger.info("✅ Code format check passed")


@task
def check_lint(c: Context) -> None:
    r"""Check code linting with ruff.

    This task runs Ruff linter to identify code quality issues, potential bugs,
    and style violations. Output is formatted for GitHub Actions compatibility.

    Args:
        c: The invoke context.
    """
    logger.info("🔍 Checking code linting with ruff...")
    c.run("ruff check --output-format=github .", pty=True)
    logger.info("✅ Linting check passed")


@task
def check_types(c: Context) -> None:
    r"""Check type hints with pyright.

    This task uses Pyright to perform static type checking on the source code,
    ensuring type safety and catching potential type-related errors.

    Args:
        c: The invoke context.
    """
    logger.info("🔬 Checking type hints with pyright...")
    c.run(f"pyright --verifytypes {NAME} --ignoreexternal", pty=True)
    logger.info("✅ Type check passed")


@task
def create_venv(c: Context) -> None:
    r"""Create a virtual environment and install invoke.

    This task creates a fresh virtual environment using uv with the specified
    Python version, activates it, and installs the invoke package for task
    management.

    Args:
        c: The invoke context.

    Note:
        The virtual environment will be created in the .venv directory and any
        existing environment will be cleared.
    """
    logger.info(f"🐍 Creating virtual environment with Python {PYTHON_VERSION}...")
    c.run(f"uv venv --python {PYTHON_VERSION} --clear", pty=True)
    c.run("source .venv/bin/activate", pty=True)
    logger.info("📦 Installing invoke...")
    c.run("make install-invoke", pty=True)
    logger.info("✅ Virtual environment created successfully")


@task
def doctest_src(c: Context) -> None:
    r"""Run doctests on source code and validate markdown code examples.

    This function performs two types of validation:
    1. Runs doctests on Python source code files using xdoctest
    2. Validates code examples embedded in markdown files (via check_markdown.sh
       which internally uses doctest)

    Args:
        c: The invoke context.
    """
    logger.info("📚 Running doctests on source code...")
    c.run(f"python -m pytest --xdoctest {SOURCE}", pty=True)
    logger.info("📝 Validating markdown code examples...")
    c.run("dev/check_markdown.sh", pty=True)
    logger.info("✅ Doctest validation complete")


@task
def docformat(c: Context) -> None:
    r"""Format docstrings in source code.

    This task uses docformatter to automatically format all docstrings in the
    source code according to PEP 257 conventions and project-specific settings
    defined in pyproject.toml.

    Args:
        c: The invoke context.

    Note:
        This modifies files in place. Ensure your work is committed before
        running this task.
    """
    logger.info("📖 Formatting docstrings...")
    c.run(f"docformatter --config ./pyproject.toml --in-place {SOURCE}", pty=True)
    logger.info("✅ Docstring formatting complete")


@task
def format_shell(c: Context) -> None:
    r"""Format and validate shell scripts.

    This task performs two operations on all shell scripts:
    1. Runs shellcheck to identify potential bugs and style issues
    2. Formats scripts using shfmt for consistent style

    Args:
        c: The invoke context.

    Raises:
        SystemExit: If shellcheck or shfmt fails.
    """
    logger.info("🐚 Running shellcheck on shell scripts...")
    c.run("shellcheck -- **/*.sh", pty=True)
    logger.info("✅ Shellcheck passed\n")

    logger.info("🔧 Running shfmt to format shell scripts...")
    c.run("shfmt -l -w -- **/*.sh", pty=True)
    logger.info("✅ Shell formatting complete")


@task
def install(
    c: Context, optional_deps: bool = True, dev_deps: bool = True, docs_deps: bool = False
) -> None:
    r"""Install project dependencies and the package in editable mode.

    This task synchronizes dependencies from the lock file and installs the
    package in editable mode, allowing you to test changes without reinstalling.

    Args:
        c: The invoke context.
        optional_deps: If True, install all optional dependencies defined in
            the project extras. Default is True.
        dev_deps: If True, install development dependencies (testing, linting,
            formatting tools). Default is True.
        docs_deps: If True, install documentation generation dependencies
            (mkdocs, themes, plugins). Default is False.

    Example:
        # Install with all dependencies except docs
        invoke install

        # Install only core and dev dependencies
        invoke install --no-optional-deps

        # Install everything including docs dependencies
        invoke install --docs-deps
    """
    logger.info("📦 Installing project dependencies...")
    cmd = ["uv sync --frozen"]
    if optional_deps:
        cmd.append("--all-extras")
    if dev_deps:
        cmd.append("--group dev")
    if docs_deps:
        cmd.append("--group docs")
    c.run(" ".join(cmd), pty=True)
    logger.info("🔧 Installing package in editable mode...")
    c.run("uv pip install -e .", pty=True)
    logger.info("✅ Installation complete")


@task
def update(c: Context) -> None:
    r"""Update dependencies and pre-commit hooks to their latest
    versions.

    This task performs a comprehensive update of the project's tooling:
    1. Updates all locked dependencies to their latest compatible versions
    2. Upgrades all uv tools to their latest versions
    3. Updates pre-commit hook versions
    4. Reinstalls the project with updated documentation dependencies

    Args:
        c: The invoke context.

    Warning:
        This may introduce breaking changes. Review the changes and run tests
        after updating.
    """
    logger.info("🔄 Updating dependencies...")
    c.run("uv sync --upgrade", pty=True)
    logger.info("🛠️  Upgrading uv tools...")
    c.run("uv tool upgrade --all", pty=True)
    logger.info("🪝 Updating pre-commit hooks...")
    c.run("pre-commit autoupdate", pty=True)
    logger.info("📦 Reinstalling with docs dependencies...")
    install(c, docs_deps=True)
    logger.info("✅ Update complete")


@task
def all_test(c: Context, cov: bool = False) -> None:
    r"""Run all tests (unit and integration).

    This task executes the complete test suite including unit tests, integration
    tests, and doctests with a 10-second timeout per test.

    Args:
        c: The invoke context.
        cov: If True, generate coverage reports in HTML, XML, and terminal
            formats. Default is False.

    Example:
        # Run all tests without coverage
        invoke all-test

        # Run all tests with coverage reports
        invoke all-test --cov
    """
    logger.info("🧪 Running all tests (unit and integration)...")
    cmd = ["python -m pytest --xdoctest --timeout 10"]
    if cov:
        cmd.append(f"--cov-report html --cov-report xml --cov-report term --cov={NAME}")
        logger.info("📊 Coverage reports will be generated")
    cmd.append(f"{TESTS}")
    c.run(" ".join(cmd), pty=True)
    logger.info("✅ All tests complete")


@task
def unit_test(c: Context, cov: bool = False) -> None:
    r"""Run unit tests.

    This task executes only the unit tests (fast, isolated tests) with doctests
    and a 10-second timeout per test. Unit tests are located in the tests/unit
    directory.

    Args:
        c: The invoke context.
        cov: If True, generate coverage reports in HTML, XML, and terminal
            formats. Default is False.

    Example:
        # Run unit tests without coverage
        invoke unit-test

        # Run unit tests with coverage reports
        invoke unit-test --cov
    """
    logger.info("🧪 Running unit tests...")
    cmd = ["python -m pytest --xdoctest --timeout 10"]
    if cov:
        cmd.append(f"--cov-report html --cov-report xml --cov-report term --cov={NAME}")
        logger.info("📊 Coverage reports will be generated")
    cmd.append(f"{UNIT_TESTS}")
    c.run(" ".join(cmd), pty=True)
    logger.info("✅ Unit tests complete")


@task
def integration_test(c: Context, cov: bool = False) -> None:
    r"""Run integration tests.

    Args:
        c: The invoke context.
        cov: If True, generate coverage reports.
    """
    logger.info("🧪 Running integration tests...")
    cmd = ["python -m pytest --xdoctest --timeout 60"]
    if cov:
        cmd.append(
            f"--cov-report html --cov-report xml --cov-report term --cov-append --cov={NAME}"
        )
        logger.info("📊 Coverage reports will be generated (appending)")
    cmd.append(f"{INTEGRATION_TESTS}")
    c.run(" ".join(cmd), pty=True)
    logger.info("✅ Integration tests complete")


@task
def show_installed_packages(c: Context) -> None:
    r"""Show the installed packages.

    Args:
        c: The invoke context.
    """
    logger.info("📦 Listing installed packages...")
    c.run("uv pip list", pty=True)


@task
def show_python_config(c: Context) -> None:
    r"""Show the python configuration.

    Args:
        c: The invoke context.
    """
    logger.info("🐍 Python configuration:")
    c.run("uv python list --only-installed", pty=True)
    c.run("uv python find", pty=True)
    c.run("which python", pty=True)


@task
def publish_pypi(c: Context) -> None:
    r"""Publish the package to PyPI.

    Args:
        c: The invoke context.
    """
    logger.info("📦 Building package...")
    c.run("uv build", pty=True)
    logger.info("🔍 Verifying package installation...")
    c.run(
        f'uv run --with {NAME} --refresh-package {NAME} --no-project -- python -c "import {NAME}"',
        pty=True,
    )
    logger.info("🚀 Publishing to PyPI...")
    c.run("uv publish --token ${PYPI_TOKEN}", pty=True)
    logger.info("✅ Package published successfully")


@task
def publish_doc_dev(c: Context) -> None:
    r"""Publish development (e.g. unstable) docs."""
    logger.info("📚 Publishing development documentation...")
    logger.info("🗑️  Deleting previous 'main' version if it exists...")
    c.run("mike delete --config-file docs/mkdocs.yml main", pty=True, warn=True)
    logger.info("🚀 Deploying 'main' and 'dev' aliases...")
    c.run("mike deploy --config-file docs/mkdocs.yml --push --update-aliases main dev", pty=True)
    logger.info("✅ Development documentation published")


@task
def publish_doc_latest(c: Context) -> None:
    r"""Publish latest (e.g. stable) docs."""
    from feu.git import get_last_version_tag_name  # noqa: PLC0415
    from packaging.version import Version  # noqa: PLC0415

    logger.info("📚 Publishing latest documentation...")

    try:
        version = Version(get_last_version_tag_name())
        tag = f"{version.major}.{version.minor}"
        logger.info(f"📌 Using version tag: {tag}")
    except RuntimeError:
        tag = "0.0"
        logger.warning("⚠️  No version tag found, using default: 0.0")

    logger.info(f"🗑️  Deleting previous '{tag}' version if it exists...")
    c.run(f"mike delete --config-file docs/mkdocs.yml {tag}", pty=True, warn=True)
    logger.info(f"🚀 Deploying '{tag}' and 'latest' aliases...")
    c.run(
        f"mike deploy --config-file docs/mkdocs.yml --push --update-aliases {tag} latest", pty=True
    )
    logger.info("🎯 Setting 'latest' as default...")
    c.run("mike set-default --config-file docs/mkdocs.yml --push --allow-empty latest", pty=True)
    logger.info("✅ Latest documentation published")
