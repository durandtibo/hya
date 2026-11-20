r"""Define the public interface to interact with the default resolver
registry."""

from __future__ import annotations

__all__ = ["get_default_registry"]

import math
import operator
from functools import cache
from typing import TYPE_CHECKING, Any

from hya import resolvers
from hya.imports import is_braceexpand_available, is_numpy_available, is_torch_available
from hya.registry import ResolverRegistry

if TYPE_CHECKING:
    from collections.abc import Callable

_BUILTINS: dict[str, Callable[..., Any]] = {
    "hya.add": resolvers.add_resolver,
    "hya.asinh": math.asinh,
    "hya.ceildiv": resolvers.ceildiv_resolver,
    "hya.exp": math.exp,
    "hya.floordiv": operator.floordiv,
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
    "hya.to_path": resolvers.to_path_resolver,
    "hya.truediv": operator.truediv,
}


@cache
def get_default_registry() -> ResolverRegistry:
    """Get or create the default global resolver registry.

    Returns a singleton registry instance using a simple singleton pattern.
    The registry initially contains the default resolvers and can be
    extended with custom resolvers. The resolvers that need an optional
    package (``braceexpand``, ``numpy`` or ``torch``) are in the registry only
    if the package is installed, and the module of such a resolver is
    imported on its first call, not when ``hya`` is imported.

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
    if is_braceexpand_available():
        registry.register_lazy("hya.braceexpand", "hya.braceexpand:braceexpand_resolver")
    if is_numpy_available():
        registry.register_lazy("hya.np.array", "hya.numpy:to_array_resolver")
    if is_torch_available():
        registry.register_lazy("hya.torch.tensor", "hya.torch:to_tensor_resolver")
        registry.register_lazy("hya.torch.dtype", "hya.torch:torch_dtype_resolver")
    return registry
