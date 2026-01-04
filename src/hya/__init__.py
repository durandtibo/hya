r"""Contain the main features of the ``hya`` package."""

from __future__ import annotations

__all__ = []

from importlib.metadata import PackageNotFoundError, version

from hya import resolvers  # noqa: F401
from hya.default import get_default_registry
from hya.imports import is_braceexpand_available, is_numpy_available, is_torch_available

try:
    __version__ = version(__name__)
except PackageNotFoundError:  # pragma: no cover
    # Package is not installed, fallback if needed
    __version__ = "0.0.0"

if is_braceexpand_available():  # pragma: no cover
    from hya import braceexpand_  # noqa: F401
if is_numpy_available():  # pragma: no cover
    from hya import numpy_  # noqa: F401
if is_torch_available():  # pragma: no cover
    from hya import torch_  # noqa: F401

get_default_registry().register_resolvers()
