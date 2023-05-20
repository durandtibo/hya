__all__ = ["register_resolvers"]

from hya import resolvers  # noqa: F401
from hya.imports import is_torch_available
from hya.registry import register_resolvers

if is_torch_available():
    from hya import pytorch  # noqa: F401
