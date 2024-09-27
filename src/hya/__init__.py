r"""Contain the main features of the ``hya`` package."""

from __future__ import annotations

__all__ = [
    "is_braceexpand_available",
    "is_torch_available",
    "register_resolvers",
    "register_resolvers",
]

from hya import resolvers  # noqa: F401
from hya.imports import is_braceexpand_available, is_numpy_available, is_torch_available
from hya.registry import register_resolvers

if is_braceexpand_available():  # pragma: no cover
    from hya import braceexpand_  # noqa: F401
if is_numpy_available():  # pragma: no cover
    from hya import numpy_  # noqa: F401
if is_torch_available():  # pragma: no cover
    from hya import torch_  # noqa: F401
