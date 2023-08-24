from __future__ import annotations

__all__ = ["ResolverRegistry", "registry"]

from collections.abc import Callable

from omegaconf import OmegaConf


class ResolverRegistry:
    r"""Implementation of a resolver registry.

    Example usage:

    .. code-block:: pycon

        >>> from hya.registry import ResolverRegistry
        >>> registry = ResolverRegistry()
        >>> @registry.register("my_key")
        ... def my_resolver(value):
        ...     pass
        ...
    """

    def __init__(self) -> None:
        self._state: dict[str, Callable] = dict()

    @property
    def state(self) -> dict[str, Callable]:
        r"""``dict``: The state of the registry."""
        return self._state

    def register(self, key: str, exist_ok: bool = False) -> Callable:
        r"""Registers a resolver to registry with ``key``

        Args:
        ----
            key (str): Specifies the key used to register the resolver.
            exist_ok (bool, optional): If ``False``, a ``RuntimeError``
                is raised if you try to register a new resolver with
                an existing key. Default: ``False``

        Raises:
        ------
            TypeError if the resolver is not callable
            TypeError if the key already exists and ``exist_ok=False``

        Example usage:

        .. code-block:: pycon

            >>> from hya.registry import registry
            >>> @registry.register("my_key")
            ... def my_resolver(value):
            ...     pass
            ...
        """

        def wrap(resolver: Callable) -> Callable:
            if not callable(resolver):
                raise TypeError(f"Each resolver has to be callable but received {type(resolver)}")
            if key in self._state and not exist_ok:
                raise RuntimeError(
                    f"A resolver is already registered for `{key}`. You can use another key "
                    "or set `exist_ok=True` to override the existing resolver"
                )
            self._state[key] = resolver
            return resolver

        return wrap


registry = ResolverRegistry()


def register_resolvers() -> None:
    r"""Registers the resolvers.

    Example usage:

    .. code-block:: pycon

        >>> from hya import register_resolvers
        >>> register_resolvers()
    """
    for key, resolver in registry.state.items():
        if not OmegaConf.has_resolver(key):
            OmegaConf.register_new_resolver(key, resolver)
