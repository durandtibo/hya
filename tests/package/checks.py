r"""Check that the installed ``hya`` package works.

The script is run by the CI against a package that is *installed* (built
from the source distribution or the wheel, or downloaded from PyPI), not
against the source tree. It is a standalone script, not a pytest module:
it must run in an environment where only ``hya`` (and the requested
extras) are installed, so it does not import ``pytest`` or
``hya.testing``, and it does not import an optional library at module
level.

Usage::

    python tests/package/checks.py                  # no extra
    python tests/package/checks.py --extra numpy    # numpy is required
    python tests/package/checks.py --extra all      # every extra is required

A check on an optional library is skipped (and reported as skipped) when
the library is not installed, unless the extra that provides it was
requested with ``--extra``: then a missing library is a failure.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import importlib.util
import json
import logging
import pkgutil
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from omegaconf import OmegaConf

import hya

if TYPE_CHECKING:
    from collections.abc import Sequence
    from types import FunctionType

logger = logging.getLogger(__name__)

PACKAGE = "hya"

# Extra name -> module that the extra installs. The extras that are only
# installed on some platforms are in ``PLATFORM_DEPENDENT_EXTRAS``.
EXTRA_MODULES = {
    "braceexpand": "braceexpand",
    "numpy": "numpy",
    "torch": "torch",
}

# These extras have environment markers (OS, architecture, Python version) in
# ``pyproject.toml``: on an unsupported platform the extra installs nothing,
# so a missing library is not a failure.
PLATFORM_DEPENDENT_EXTRAS = frozenset({"torch"})

# Modules that must not be imported by ``import hya``.
LAZY_MODULES = ("pytest", *sorted(EXTRA_MODULES.values()))

# First minor release that imports the optional libraries lazily. The nightly
# workflow also runs this script against older releases published on PyPI.
FIRST_LAZY_VERSION = (0, 5)

# ``hya.testing`` imports ``pytest``, which the other extras do not install.
IMPORT_EXCLUDED = ("hya.testing",)

REQUIRED_EXTRAS: set[str] = set()


class SkipCheckError(Exception):
    r"""Raised by a check that cannot run in this environment."""


def is_installed(module: str) -> bool:
    r"""Indicate if a module can be imported, without importing it."""
    return importlib.util.find_spec(module) is not None


def require(extra: str) -> None:
    r"""Make sure a check can run with the library of an extra.

    Args:
        extra: The name of the extra.

    Raises:
        SkipCheckError: If the library is not installed and the extra
            was not requested, or the extra depends on the platform.
        ModuleNotFoundError: If the library is not installed and the
            extra was requested.
    """
    module = EXTRA_MODULES[extra]
    if is_installed(module):
        return
    if extra in REQUIRED_EXTRAS and extra not in PLATFORM_DEPENDENT_EXTRAS:
        msg = f"the extra {extra!r} was requested but {module!r} is not installed"
        raise ModuleNotFoundError(msg)
    msg = f"{module!r} is not installed"
    raise SkipCheckError(msg)


#################################
#     Checks of the package     #
#################################


def is_editable_install() -> bool:
    r"""Indicate if ``hya`` is installed in editable mode (PEP 610)."""
    text = importlib.metadata.distribution(PACKAGE).read_text("direct_url.json")
    return bool(text) and bool(json.loads(text or "{}").get("dir_info", {}).get("editable"))


def check_install_location() -> None:
    r"""Check that ``hya`` is imported from the installed package, not
    from the source tree.

    An editable install is imported from the source tree by design, so
    the check is skipped.
    """
    if is_editable_install():
        msg = "editable install"
        raise SkipCheckError(msg)

    location = Path(hya.__file__).resolve()
    source_tree = Path(__file__).resolve().parents[2] / "src"
    assert source_tree not in location.parents, f"hya is imported from the source tree: {location}"


def check_metadata() -> None:
    r"""Check the metadata of the installed distribution."""
    metadata = importlib.metadata.metadata(PACKAGE)
    assert metadata["Name"] == PACKAGE
    assert metadata["Requires-Python"], "Requires-Python is missing"
    assert metadata["License-Expression"] or metadata["License"], "the license is missing"
    installed = importlib.metadata.version(PACKAGE)
    assert installed != "0.0.0", "the version is the fallback of an uninstalled package"
    assert hya.__version__ == installed, f"{hya.__version__!r} != {installed!r}"


def check_distribution_files() -> None:
    r"""Check that the typing marker and the license are shipped."""
    assert (Path(hya.__file__).parent / "py.typed").is_file(), "py.typed is missing"
    files = {str(f) for f in importlib.metadata.files(PACKAGE) or []}
    assert any(f.endswith("LICENSE") for f in files), "LICENSE is missing"


def check_extras_installed() -> None:
    r"""Check that the distribution of each requested extra is
    installed."""
    missing = []
    for extra in sorted(REQUIRED_EXTRAS - PLATFORM_DEPENDENT_EXTRAS):
        try:
            importlib.metadata.version(extra)
        except importlib.metadata.PackageNotFoundError:
            missing.append(extra)
    assert not missing, f"the packages of the extras are not installed: {missing}"


def check_lazy_imports() -> None:
    r"""Check that ``import hya`` does not import the optional libraries
    (nor ``pytest``)."""
    version = importlib.metadata.version(PACKAGE)
    if tuple(int(part) for part in version.split(".")[:2]) < FIRST_LAZY_VERSION:
        msg = f"hya {version} imports the optional libraries eagerly"
        raise SkipCheckError(msg)
    imported = [name for name in LAZY_MODULES if name in sys.modules]
    assert not imported, f"imported by the package at import time: {imported}"


def check_import_all_modules() -> None:
    r"""Check that every module of the package can be imported.

    This catches a module that is missing from the sdist or the wheel. A
    module may fail with ``ModuleNotFoundError`` if it needs an optional
    library that is not installed and whose extra was not requested.
    """
    package = importlib.import_module(PACKAGE)
    required = {EXTRA_MODULES[e] for e in REQUIRED_EXTRAS - PLATFORM_DEPENDENT_EXTRAS}
    failures = []
    for info in pkgutil.walk_packages(package.__path__, prefix=f"{PACKAGE}."):
        if info.name.startswith(IMPORT_EXCLUDED):
            continue
        try:
            importlib.import_module(info.name)
        except ModuleNotFoundError as exc:
            missing = (exc.name or "").split(".")[0]
            if missing not in EXTRA_MODULES.values() or missing in required:
                failures.append(f"{info.name}: {type(exc).__name__}: {exc}")
        except Exception as exc:  # noqa: BLE001  an import can raise anything
            failures.append(f"{info.name}: {type(exc).__name__}: {exc}")
    assert not failures, "failed to import:\n" + "\n".join(failures)


def check_imports() -> None:
    r"""Check that all main package objects can be imported
    correctly."""
    objects_to_import = [
        "hya.get_default_registry",
        "hya.default.get_default_registry",
        "hya.registry.ResolverRegistry",
    ]
    for a in objects_to_import:
        module_path, name = a.rsplit(".", maxsplit=1)
        module = importlib.import_module(module_path)
        assert getattr(module, name, None) is not None, f"Failed to import {a}"


################################
#     Checks of the features   #
################################


def check_native_resolvers() -> None:
    r"""Check the resolvers that only need the required dependencies."""
    assert OmegaConf.create({"key": "${hya.add:1,4}"}).key == 5
    assert OmegaConf.create({"key": "${hya.ceildiv:11,4}"}).key == 3
    assert OmegaConf.create({"key": "${hya.len:[1,2,3]}"}).key == 3
    assert OmegaConf.create({"key": "${hya.max:3,4}"}).key == 4
    assert OmegaConf.create({"key": "${hya.min:3,4}"}).key == 3
    assert OmegaConf.create({"key": "${hya.mul:3,4}"}).key == 12
    assert OmegaConf.create({"key": "${hya.path:/my/path}"}).key == Path("/my/path")
    assert OmegaConf.create({"key": "${hya.sub:1,4}"}).key == -3
    assert OmegaConf.create({"key": "${hya.truediv:11,4}"}).key == 2.75


def check_braceexpand_resolvers() -> None:
    r"""Check the resolvers that need ``braceexpand``."""
    require("braceexpand")

    assert list(OmegaConf.create({"key": r"${hya.braceexpand:\{1..4\}}"}).key) == [
        "1",
        "2",
        "3",
        "4",
    ]


def check_numpy_resolvers() -> None:
    r"""Check the resolvers that need NumPy."""
    require("numpy")
    np = importlib.import_module("numpy")

    assert np.array_equal(
        OmegaConf.create({"key": "${hya.np.array:[1, 2, 3]}"}).key, np.array([1, 2, 3])
    )


def check_torch_resolvers() -> None:
    r"""Check the resolvers that need PyTorch."""
    require("torch")
    torch = importlib.import_module("torch")

    assert OmegaConf.create({"key": "${hya.torch.tensor:[1, 2, 3]}"}).key.equal(
        torch.tensor([1, 2, 3])
    )
    assert OmegaConf.create({"key": "${hya.torch.dtype:float}"}).key == torch.float


# ``check_lazy_imports`` must run before the checks that import the optional
# libraries.
CHECKS: tuple[FunctionType, ...] = (
    check_install_location,
    check_metadata,
    check_distribution_files,
    check_extras_installed,
    check_lazy_imports,
    check_import_all_modules,
    check_imports,
    check_native_resolvers,
    check_braceexpand_resolvers,
    check_numpy_resolvers,
    check_torch_resolvers,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    r"""Parse the command line arguments.

    Args:
        argv: The arguments. ``None`` means ``sys.argv[1:]``.

    Returns:
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument(
        "--extra",
        action="append",
        default=[],
        help="extra installed with the package: its library must be importable. "
        "Can be repeated or comma-separated; 'all' means every extra; '' means none.",
    )
    return parser.parse_args(argv)


def get_required_extras(values: Sequence[str]) -> set[str]:
    r"""Get the extras whose library is required.

    Args:
        values: The values of ``--extra``.

    Returns:
        The names of the extras.
    """
    extras = {e.strip() for value in values for e in value.split(",") if e.strip()}
    if "all" in extras:
        extras = (extras - {"all"}) | set(EXTRA_MODULES)
    # An extra without an optional library (for example ``testing``) has nothing to check.
    extras &= set(EXTRA_MODULES)
    return extras


def main(argv: Sequence[str] | None = None) -> int:
    r"""Run all the package checks.

    Args:
        argv: The command line arguments.

    Returns:
        The exit code: ``0`` if no check failed, ``1`` otherwise.
    """
    REQUIRED_EXTRAS.update(get_required_extras(parse_args(argv).extra))
    logger.info("Required extras: %s", sorted(REQUIRED_EXTRAS) or "none")
    failed, skipped = [], []
    for check in CHECKS:
        name = check.__name__
        try:
            check()
        except SkipCheckError as exc:
            skipped.append(name)
            logger.info("⏭️  %s skipped: %s", name, exc)
        except Exception:
            failed.append(name)
            logger.exception("❌ %s failed", name)
        else:
            logger.info("✅ %s passed", name)
    passed = len(CHECKS) - len(failed) - len(skipped)
    logger.info("%d passed, %d skipped, %d failed", passed, len(skipped), len(failed))
    if failed:
        logger.error("❌ Package check failed: %s", ", ".join(failed))
        return 1
    logger.info("✅ All package checks passed successfully!")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    sys.exit(main())
