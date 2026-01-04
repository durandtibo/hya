r"""Define the public interface to interact with the default resolver
registry.."""

from __future__ import annotations

__all__ = ["get_default_registry"]


from hya.registry import ResolverRegistry


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
    return get_default_registry._registry
