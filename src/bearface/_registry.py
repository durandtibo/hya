__all__ = ["ResolverRegistry", "registry"]

from collections.abc import Callable


class ResolverRegistry:
    r"""Implementation of the resolver registry."""

    state = dict()

    @classmethod
    def register(cls, key: str, exist_ok: bool = False) -> Callable:
        r"""Register a resolver to registry with ``key``

        Args:
            key (str): Specifies the key used to register the resolver.

        Example usage:

        .. code-block:: python

            >>> from bearface import registry
            >>> @registry.register('my_key')
            >>> def my_resolver(value):
            ...     pass
        """

        def wrap(resolver: Callable) -> Callable:
            print(resolver, callable(resolver))
            if not callable(resolver):
                raise TypeError(f"Each resolver has to be callable but received {type(resolver)}")
            cls.state[key] = resolver
            return resolver

        return wrap


registry = ResolverRegistry()
