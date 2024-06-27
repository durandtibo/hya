r"""Implement the resolver registry to easily register resolvers."""

from __future__ import annotations

__all__ = ["ResolverRegistry", "registry"]

from typing import TYPE_CHECKING

from omegaconf import OmegaConf

if TYPE_CHECKING:
    from collections.abc import Callable


class ResolverRegistry:
    r"""Implement a resolver registry.

    Example usage:

    ```pycon

    >>> from hya.registry import ResolverRegistry
    >>> registry = ResolverRegistry()
    >>> @registry.register("my_key")
    ... def my_resolver(value):
    ...     pass
    ...

    ```
    """

    def __init__(self) -> None:
        self._state: dict[str, Callable] = {}

    @property
    def state(self) -> dict[str, Callable]:
        r"""The state of the registry."""
        return self._state

    def register(self, key: str, exist_ok: bool = False) -> Callable:
        r"""Register a resolver to registry with ``key``.

        Args:
            key: Specifies the key used to register the resolver.
            exist_ok: If ``False``, a ``RuntimeError`` is raised if
                you try to register a new resolver with an existing
                key.

        Raises:
            TypeError: if the resolver is not callable
            TypeError: if the key already exists and ``exist_ok=False``

        Example usage:

        ```pycon
        >>> from hya.registry import registry
        >>> @registry.register("my_key")
        ... def my_resolver(value):
        ...     pass
        ...

        ```
        """

        def wrap(resolver: Callable) -> Callable:
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


registry = ResolverRegistry()


def register_resolvers() -> None:
    r"""Register the resolvers.

    Example usage:

    ```pycon

    >>> from hya import register_resolvers
    >>> register_resolvers()

    ```
    """
    for key, resolver in registry.state.items():
        if not OmegaConf.has_resolver(key):
            OmegaConf.register_new_resolver(key, resolver)
