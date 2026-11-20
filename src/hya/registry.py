r"""Implement the resolver registry to easily register resolvers."""

from __future__ import annotations

__all__ = ["ResolverRegistry"]

import warnings
from collections.abc import Callable, Mapping
from types import MappingProxyType
from typing import Any, TypeVar

from omegaconf import OmegaConf

F = TypeVar("F", bound=Callable[..., Any])


class ResolverRegistry:
    r"""Implement a resolver registry.

    This class manages a collection of resolver functions that can be registered
    with keys and later used with OmegaConf.


    Args:
        state: Optional initial state mapping containing key-resolver pairs.
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

    def __init__(self, state: Mapping[str, Callable[..., Any]] | None = None) -> None:
        self._state: dict[str, Callable[..., Any]] = dict(state) if state else {}
        # The resolvers published to OmegaConf by this registry
        self._published: dict[str, Callable[..., Any]] = {}

    @property
    def state(self) -> Mapping[str, Callable[..., Any]]:
        r"""The state of the registry.

        This is a read-only view: use ``register`` to add a resolver.
        """
        return MappingProxyType(self._state)

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

    def register(self, key: str, *, exist_ok: bool = False) -> Callable[[F], F]:
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

    def register_resolvers(self, *, replace: bool = False) -> None:
        r"""Register the resolvers to OmegaConf.

        This method publishes the registered resolvers to OmegaConf. It is
        idempotent: a resolver already published by this registry is not
        registered again, so calling this method twice changes nothing. A
        resolver is not published, and a warning is emitted, if OmegaConf
        already has a resolver for its key (a resolver published before the
        registry changed, or registered by another source) and ``replace`` is
        ``False``.

        The resolvers are published with ``annotation_validation="off"``: the
        annotations of the resolvers are not a runtime contract.

        Args:
            replace: If ``True``, the resolvers replace the resolvers that
                OmegaConf already has for the same keys. If ``False``, these
                keys are skipped with a warning.

        Notes:
            OmegaConf caches the resolved value of the nodes of a
            configuration. Replacing a resolver does not clear the cache of
            the existing configurations: use ``OmegaConf.clear_cache(cfg)``
            to clear it.

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
        for key, resolver in self._state.items():
            if self._published.get(key) is resolver:
                continue
            if OmegaConf.has_resolver(key) and not replace:
                warnings.warn(
                    f"A resolver is already registered in OmegaConf for '{key}': not replaced. "
                    "Use register_resolvers(replace=True) to replace it.",
                    stacklevel=2,
                )
                continue
            OmegaConf.register_resolver(key, resolver, replace=replace, annotation_validation="off")
            self._published[key] = resolver
