r"""Define the public interface to interact with the default resolver
registry."""

from __future__ import annotations

__all__ = ["get_default_registry"]

from typing import TYPE_CHECKING, Any

from hya import resolvers
from hya.imports import is_braceexpand_available, is_numpy_available, is_torch_available
from hya.registry import ResolverRegistry

if TYPE_CHECKING:
    from collections.abc import Callable


def get_default_registry() -> ResolverRegistry:
    """Get or create the default global resolver registry.

    Returns a singleton registry instance using a simple singleton pattern.
    The registry is initially empty and can be populated with custom resolvers.

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
    if not hasattr(get_default_registry, "_registry"):
        get_default_registry._registry = ResolverRegistry()
        _register_default_resolvers(get_default_registry._registry)
    return get_default_registry._registry


def _register_default_resolvers(registry: ResolverRegistry) -> None:
    """Register default resolvers.

    Args:
        registry: The registry to populate with default resolvers

    Notes:
        This function is called internally by get_default_registry() and should
        not typically be called directly by users.
    """
    res = {
        "hya.add": resolvers.add_resolver,
        "hya.asinh": resolvers.asinh_resolver,
        "hya.ceildiv": resolvers.ceildiv_resolver,
        "hya.exp": resolvers.exp_resolver,
        "hya.floordiv": resolvers.floordiv_resolver,
        "hya.len": resolvers.len_resolver,
        "hya.iter_join": resolvers.iter_join_resolver,
        "hya.log": resolvers.log_resolver,
        "hya.log10": resolvers.log10_resolver,
        "hya.max": resolvers.max_resolver,
        "hya.min": resolvers.min_resolver,
        "hya.mul": resolvers.mul_resolver,
        "hya.neg": resolvers.neg_resolver,
        "hya.path": resolvers.path_resolver,
        "hya.pi": resolvers.pi_resolver,
        "hya.pow": resolvers.pow_resolver,
        "hya.sqrt": resolvers.sqrt_resolver,
        "hya.sha256": resolvers.sha256_resolver,
        "hya.sinh": resolvers.sinh_resolver,
        "hya.sub": resolvers.sub_resolver,
        "hya.to_path": resolvers.to_path_resolver,
        "hya.truediv": resolvers.truediv_resolver,
    }
    _add_braceexpand_resolvers(res)
    _add_numpy_resolvers(res)
    _add_torch_resolvers(res)
    for key, resolver in res.items():
        registry.register(key)(resolver)


def _add_braceexpand_resolvers(resolvers: dict[str, Callable[[...], Any]]) -> None:
    r"""Add the default braceexpand resolvers.

    Args:
        resolvers: The dictionary to populate with default
            braceexpand resolvers if braceexpand is installed.

    Notes:
        This function is called internally by get_default_registry() and should
        not typically be called directly by users.
    """
    if not is_braceexpand_available():  # pragma: no cover
        return

    # Local import because it is an optional resolver
    from hya.braceexpand import braceexpand_resolver  # noqa: PLC0415

    resolvers["hya.braceexpand"] = braceexpand_resolver


def _add_numpy_resolvers(resolvers: dict[str, Callable[[...], Any]]) -> None:
    r"""Add the default numpy resolvers.

    Args:
        resolvers: The dictionary to populate with default
            numpy resolvers if numpy is installed.

    Notes:
        This function is called internally by get_default_registry() and should
        not typically be called directly by users.
    """
    if not is_numpy_available():  # pragma: no cover
        return

    # Local import because it is an optional resolver
    from hya.numpy import to_array_resolver  # noqa: PLC0415

    resolvers["hya.np.array"] = to_array_resolver


def _add_torch_resolvers(resolvers: dict[str, Callable[[...], Any]]) -> None:
    r"""Add the default torch resolvers.

    Args:
        resolvers: The dictionary to populate with default
            torch resolvers if torch is installed.

    Notes:
        This function is called internally by get_default_registry() and should
        not typically be called directly by users.
    """
    if not is_torch_available():  # pragma: no cover
        return

    # Local import because it is an optional resolver
    from hya.torch import to_tensor_resolver, torch_dtype_resolver  # noqa: PLC0415

    resolvers["hya.torch.tensor"] = to_tensor_resolver
    resolvers["hya.torch.dtype"] = torch_dtype_resolver


# Register the available resolvers
get_default_registry().register_resolvers()
