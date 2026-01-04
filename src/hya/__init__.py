r"""Contain the main features of the ``hya`` package."""

from __future__ import annotations

__all__ = ["get_default_registry"]

from importlib.metadata import PackageNotFoundError, version

from hya.default import get_default_registry

try:
    __version__ = version(__name__)
except PackageNotFoundError:  # pragma: no cover
    # Package is not installed, fallback if needed
    __version__ = "0.0.0"
