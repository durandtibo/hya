from __future__ import annotations

__all__ = [
    "register_resolvers",
    "is_torch_available",
    "is_braceexpand_available",
    "register_resolvers",
]

from hya import resolvers  # noqa: F401
from hya.imports import is_braceexpand_available, is_torch_available
from hya.registry import register_resolvers

if is_braceexpand_available():
    from hya import braceexpand_  # noqa: F401
if is_torch_available():
    from hya import torch_  # noqa: F401
