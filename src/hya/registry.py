r"""Implement the resolver registry to easily register resolvers."""

from __future__ import annotations

__all__ = ["ResolverRegistry"]
from collections.abc import Callable
from typing import Any, TypeVar

from omegaconf import OmegaConf

F = TypeVar("F", bound=Callable[..., Any])


class ResolverRegistry:
    r"""Implement a resolver registry.

    This class manages a collection of resolver functions that can be registered
    with keys and later used with OmegaConf.


    Args:
        state: Optional initial state dictionary containing key-resolver pairs.
            If provided, a copy is made to prevent external modifications.

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

    def has_resolver(self, key: str) -> bool:
        """Check if a resolver is explicitly registered for the given
        key.

        Args:
            key: The key to check.

        Returns:
            True if a resolver is registered for this key,
            False otherwise

        Example:
            ```pycon
            >>> from hya.registry import ResolverRegistry
            >>> registry = ResolverRegistry()
            >>> @registry.register("my_key")
            ... def my_resolver(value):
            ...     pass
            ...
            >>> registry.has_resolver("my_key")
            True
            >>> registry.has_resolver("missing")
            False

            ```
        """
        return key in self._state

    def register(self, key: str, exist_ok: bool = False) -> Callable[[F], F]:
        """Register a resolver to registry with the specified key.

        This method returns a decorator that can be used to register resolver functions.

        Args:
            key: The key used to register the resolver. Must be unique unless
                exist_ok is True.
            exist_ok: If False, a RuntimeError is raised if you try to register
                a new resolver with an existing key. If True, the existing
                resolver will be overridden.

        Returns:
            A decorator function that registers the resolver and returns it unchanged.

        Raises:
            TypeError: If the resolver is not callable.
            RuntimeError: If the key already exists and exist_ok is False.

        Example:
            ```pycon
            >>> from hya.registry import ResolverRegistry
            >>> registry = ResolverRegistry()
            >>> @registry.register("my_key")
            ... def my_resolver(value):
            ...     return value * 2
            ...
            >>> my_resolver(5)
            10

            ```
        """

        def wrap(resolver: F) -> F:
            if not callable(resolver):
                msg = f"Resolver must be callable, but received {type(resolver).__name__}"
                raise TypeError(msg)

            if key in self._state and not exist_ok:
                msg = (
                    f"A resolver is already registered for '{key}'. "
                    "Use a different key or set exist_ok=True to override."
                )
                raise RuntimeError(msg)

            self._state[key] = resolver
            return resolver

        return wrap

    def register_resolvers(self) -> None:
        r"""Register the resolvers to OmegaConf.

        This method iterates through all registered resolvers and registers them
        with OmegaConf if they haven't been registered already.

        Example:
            ```pycon
            >>> from hya.registry import ResolverRegistry
            >>> registry = ResolverRegistry()
            >>> @registry.register("multiply")
            ... def multiply_resolver(x, y):
            ...     return x * y
            ...
            >>> registry.register_resolvers()

            ```
        """
        for key, resolver in self.state.items():
            if not OmegaConf.has_resolver(key):
                OmegaConf.register_new_resolver(key, resolver)
