r"""Define some tasks that are executed with invoke."""

from __future__ import annotations

from typing import TYPE_CHECKING

from invoke import task

if TYPE_CHECKING:
    from invoke.context import Context

NAME = "hya"
SOURCE = f"src/{NAME}"
TESTS = "tests"
UNIT_TESTS = f"{TESTS}/unit"
INTEGRATION_TESTS = f"{TESTS}/integration"
PYTHON_VERSION = "3.13"


@task
def check_format(c: Context) -> None:
    r"""Check code format."""
    c.run("black --check .", pty=True)


@task
def check_lint(c: Context) -> None:
    r"""Check code format."""
    c.run("ruff check --output-format=github .", pty=True)


@task
def create_venv(c: Context) -> None:
    r"""Create a virtual environment."""
    c.run(f"uv venv --python {PYTHON_VERSION} --clear", pty=True)
    c.run("source .venv/bin/activate", pty=True)
    c.run("make install-invoke", pty=True)


@task
def doctest_src(c: Context) -> None:
    r"""Check the docstrings in source folder."""
    c.run(f"python -m pytest --xdoctest {SOURCE}", pty=True)
    c.run(
        'find . -type f -name "*.md" | xargs python -m doctest -o NORMALIZE_WHITESPACE '
        "-o ELLIPSIS -o REPORT_NDIFF",
        pty=True,
    )


@task
def docformat(c: Context) -> None:
    r"""Check the docstrings in source folder."""
    c.run(f"docformatter --config ./pyproject.toml --in-place {SOURCE}", pty=True)


@task
def install(
    c: Context, optional_deps: bool = True, dev_deps: bool = True, docs_deps: bool = False
) -> None:
    r"""Install packages."""
    cmd = ["uv sync --frozen"]
    if optional_deps:
        cmd.append("--all-extras")
    if dev_deps:
        cmd.append("--group dev")
    if docs_deps:
        cmd.append("--group docs")
    c.run(" ".join(cmd), pty=True)


@task
def update(c: Context) -> None:
    r"""Update the dependencies and pre-commit hooks."""
    c.run("uv sync --upgrade", pty=True)
    c.run("uv tool upgrade --all", pty=True)
    c.run("pre-commit autoupdate", pty=True)
    install(c, docs_deps=True)


@task
def all_test(c: Context, cov: bool = False) -> None:
    r"""Run the unit tests."""
    cmd = ["python -m pytest --xdoctest --timeout 10"]
    if cov:
        cmd.append(f"--cov-report html --cov-report xml --cov-report term --cov={NAME}")
    cmd.append(f"{TESTS}")
    c.run(" ".join(cmd), pty=True)


@task
def unit_test(c: Context, cov: bool = False) -> None:
    r"""Run the unit tests."""
    cmd = ["python -m pytest --xdoctest --timeout 10"]
    if cov:
        cmd.append(f"--cov-report html --cov-report xml --cov-report term --cov={NAME}")
    cmd.append(f"{UNIT_TESTS}")
    c.run(" ".join(cmd), pty=True)


@task
def integration_test(c: Context, cov: bool = False) -> None:
    r"""Run the unit tests."""
    cmd = ["python -m pytest --xdoctest --timeout 60"]
    if cov:
        cmd.append(
            f"--cov-report html --cov-report xml --cov-report term  --cov-append --cov={NAME}"
        )
    cmd.append(f"{INTEGRATION_TESTS}")
    c.run(" ".join(cmd), pty=True)


@task
def show_installed_packages(c: Context) -> None:
    r"""Show the installed packages."""
    c.run("uv pip list", pty=True)
    c.run("uv pip check", pty=True)


@task
def show_python_config(c: Context) -> None:
    r"""Show the python configuration."""
    c.run("uv python list --only-installed", pty=True)
    c.run("uv python find", pty=True)
    c.run("which python", pty=True)


@task
def publish_pypi(c: Context) -> None:
    r"""Publish the package to PyPI."""
    c.run("uv build", pty=True)
    c.run(
        f'uv run --with {NAME} --refresh-package {NAME} --no-project -- python -c "import {NAME}"',
        pty=True,
    )
    c.run("uv publish --token ${PYPI_TOKEN}", pty=True)


@task
def publish_doc_dev(c: Context) -> None:
    r"""Publish development (e.g. unstable) docs."""
    # delete previous version if it exists
    c.run("mike delete --config-file docs/mkdocs.yml main", pty=True, warn=True)
    c.run("mike deploy --config-file docs/mkdocs.yml --push --update-aliases main dev", pty=True)


@task
def publish_doc_latest(c: Context) -> None:
    r"""Publish latest (e.g. stable) docs."""
    from feu.git import get_last_version_tag_name  # noqa: PLC0415
    from packaging.version import Version  # noqa: PLC0415

    try:
        version = Version(get_last_version_tag_name())
        tag = f"{version.major}.{version.minor}"
    except RuntimeError:
        tag = "0.0"

    # delete previous version if it exists
    c.run(f"mike delete --config-file docs/mkdocs.yml {tag}", pty=True, warn=True)
    c.run(
        f"mike deploy --config-file docs/mkdocs.yml --push --update-aliases {tag} latest", pty=True
    )
    c.run("mike set-default --config-file docs/mkdocs.yml --push --allow-empty latest", pty=True)
