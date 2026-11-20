# noqa: INP001
r"""Script to create or update the package versions."""

from __future__ import annotations

import logging
from pathlib import Path

from feu.utils.io import save_json
from feu.utils.mapping import sort_by_keys
from feu.version import (
    fetch_latest_minor_versions_map,
    read_pyproject_dependencies,
    read_pyproject_optional_dependencies,
)

logger: logging.Logger = logging.getLogger(__name__)


def fetch_package_versions(base_dir: Path) -> dict[str, list[str]]:
    r"""Get the versions for each package.

    Args:
        base_dir: Path to the base directory.

    Returns:
        A dictionary with the versions for each package.
    """
    pyproject_path = base_dir.joinpath("pyproject.toml")

    deps = read_pyproject_dependencies(pyproject_path) + read_pyproject_optional_dependencies(
        pyproject_path
    )
    return sort_by_keys(fetch_latest_minor_versions_map(deps, include_lower_bound=True))


def main() -> None:
    r"""Generate the package versions and save them in a JSON file."""
    base_dir = Path(__file__).parent.parent
    versions = fetch_package_versions(base_dir)
    logger.info("versions=%s", versions)
    path = base_dir.joinpath("dev/config").joinpath("package_versions.json")
    logger.info("Saving package versions to %s", path)
    save_json(versions, path, exist_ok=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
