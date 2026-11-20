r"""Define the public interface to interact with the default resolver
registry."""

from __future__ import annotations

__all__ = ["get_default_registry"]

import math
import operator
from functools import cache
from typing import TYPE_CHECKING, Any

from hya import resolvers
from hya.registry import ResolverRegistry

if TYPE_CHECKING:
    from collections.abc import Callable

_BUILTINS: dict[str, Callable[..., Any]] = {
    "hya.add": resolvers.add_resolver,
    "hya.asinh": math.asinh,
    "hya.ceildiv": resolvers.ceildiv_resolver,
    "hya.exp": math.exp,
    "hya.float": float,
    "hya.floordiv": operator.floordiv,
    "hya.int": int,
    "hya.iter_join": resolvers.iter_join_resolver,
    "hya.len": len,
    "hya.log": math.log,
    "hya.log10": math.log10,
    "hya.max": max,
    "hya.min": min,
    "hya.mul": resolvers.mul_resolver,
    "hya.neg": operator.neg,
    "hya.path": resolvers.path_resolver,
    "hya.pi": resolvers.pi_resolver,
    "hya.pow": operator.pow,
    "hya.sha256": resolvers.sha256_resolver,
    "hya.sinh": math.sinh,
    "hya.sqrt": math.sqrt,
    "hya.sub": operator.sub,
    "hya.sum": sum,
    "hya.truediv": operator.truediv,
}

# key -> "module:function". The resolvers are always registered: the module (and its package) is
# imported on the first call, and the resolver raises a RuntimeError that says how to install the
# package if it is missing.
_OPTIONAL: dict[str, str] = {
    "hya.braceexpand": "hya.braceexpand:braceexpand_resolver",
    "hya.np.array": "hya.numpy:to_array_resolver",
    "hya.torch.dtype": "hya.torch:torch_dtype_resolver",
    "hya.torch.tensor": "hya.torch:to_tensor_resolver",
}


@cache
def get_default_registry() -> ResolverRegistry:
    """Get or create the default global resolver registry.

    Returns a singleton registry instance using a simple singleton pattern.
    The registry initially contains the default resolvers and can be
    extended with custom resolvers. The registry has the same keys on every
    machine: the resolvers that need an optional package (``braceexpand``,
    ``numpy`` or ``torch``) are always registered. The module of such a
    resolver is imported on its first call, not when ``hya`` is imported, and
    the call raises an error that says how to install the package if it is
    missing.

    This function uses a singleton pattern to ensure the same registry instance
    is returned on subsequent calls, which is efficient and maintains consistency
    across an application.

    Returns:
        A ResolverRegistry instance

    Notes:
        The singleton pattern means modifications to the returned registry
        affect all future calls to this function. If you need an isolated
        registry, create a new ResolverRegistry instance directly.

    Example:
        ```pycon
        >>> from hya import get_default_registry
        >>> registry = get_default_registry()
        >>> @registry.register("my_key")
        ... def my_resolver(value):
        ...     pass
        ...

        ```
    """
    registry = ResolverRegistry(_BUILTINS)
    for key, target in _OPTIONAL.items():
        registry.register_lazy(key, target)
    return registry
