r"""Implement the resolver registry to easily register resolvers."""

from __future__ import annotations

__all__ = ["ResolverRegistry", "get_default_registry", "register_resolvers", "registry"]
from typing import TYPE_CHECKING, Any

from omegaconf import OmegaConf

if TYPE_CHECKING:
    from collections.abc import Callable


class ResolverRegistry:
    r"""Implement a resolver registry.

    Example:
        ```pycon
        >>> from hya.registry import ResolverRegistry
        >>> registry = ResolverRegistry()
        >>> @registry.register("my_key")
        ... def my_resolver(value):
        ...     pass
        ...

        ```
    """

    def __init__(self, state: dict[str, Callable[..., Any]] | None = None) -> None:
        self._state: dict[str, Callable[..., Any]] = state.copy() if state else {}

    @property
    def state(self) -> dict[str, Callable[..., Any]]:
        r"""The state of the registry."""
        return self._state

    def register(self, key: str, exist_ok: bool = False) -> Callable[..., Any]:
        r"""Register a resolver to registry with ``key``.

        Args:
            key: Specifies the key used to register the resolver.
            exist_ok: If ``False``, a ``RuntimeError`` is raised if
                you try to register a new resolver with an existing
                key.

        Raises:
            TypeError: if the resolver is not callable
            TypeError: if the key already exists and ``exist_ok=False``

        Example:
            ```pycon
            >>> from hya.registry import registry
            >>> @registry.register("my_key")
            ... def my_resolver(value):
            ...     pass
            ...

            ```
        """

        def wrap(resolver: Callable[..., Any]) -> Callable[..., Any]:
            if not callable(resolver):
                msg = f"Each resolver has to be callable but received {type(resolver)}"
                raise TypeError(msg)
            if key in self._state and not exist_ok:
                msg = (
                    f"A resolver is already registered for `{key}`. You can use another key "
                    "or set `exist_ok=True` to override the existing resolver"
                )
                raise RuntimeError(msg)
            self._state[key] = resolver
            return resolver

        return wrap


registry: ResolverRegistry = ResolverRegistry()


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
        >>> from hya.registry import get_default_registry
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


def register_resolvers() -> None:
    r"""Register the default resolvers.

    Example:
        ```pycon
        >>> from hya import register_resolvers
        >>> register_resolvers()

        ```
    """
    for key, resolver in registry.state.items():
        if not OmegaConf.has_resolver(key):
            OmegaConf.register_new_resolver(key, resolver)
