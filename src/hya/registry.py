r"""Implement the resolver registry to easily register resolvers."""

from __future__ import annotations

__all__ = ["ResolverRegistry"]

import re
import warnings
from collections.abc import Callable, Mapping
from importlib import import_module
from types import MappingProxyType
from typing import Any, TypeVar

import omegaconf
from omegaconf import OmegaConf

F = TypeVar("F", bound=Callable[..., Any])

# OmegaConf 2.4 renamed ``register_new_resolver`` to ``register_resolver`` and validates the
# annotations of the resolvers at call time. OmegaConf 2.2 and 2.3 do not validate them.
_HAS_ANNOTATION_VALIDATION: bool = tuple(map(int, omegaconf.__version__.split(".")[:2])) >= (2, 4)

# A key that every supported OmegaConf can interpolate: ASCII identifiers joined by dots.
# OmegaConf 2.3 and later also interpolate "-", which OmegaConf 2.2 does not.
_KEY: re.Pattern[str] = re.compile(r"[A-Za-z_]\w*(\.[A-Za-z_]\w*)*", re.ASCII)


def _publish(key: str, resolver: Callable[..., Any], *, replace: bool) -> None:
    r"""Publish a resolver to OmegaConf.

    This function is the only place that depends on the version of OmegaConf. With OmegaConf
    2.4 and later, the annotations of the resolver are not validated at call time
    (``annotation_validation="off"``); OmegaConf 2.2 and 2.3 never validate them.

    Args:
        key: The key of the resolver.
        resolver: The resolver to publish.
        replace: If ``True``, replace the resolver that OmegaConf has for the key.

    Example:
        ```pycon
        >>> from hya.registry import _publish
        >>> _publish("hya.doc_example", lambda x: x, replace=True)

        ```
    """
    if _HAS_ANNOTATION_VALIDATION:
        OmegaConf.register_resolver(key, resolver, replace=replace, annotation_validation="off")
    else:
        OmegaConf.register_new_resolver(key, resolver, replace=replace)


class ResolverRegistry:
    r"""Implement a resolver registry.

    This class manages a collection of resolver functions that can be registered
    with keys and later used with OmegaConf.


    Args:
        state: Optional initial state mapping containing key-resolver pairs.
            If provided, a copy is made to prevent external modifications.
            Each pair is added with ``register``, so it is validated.

    Raises:
        TypeError: If a key of ``state`` is not a string, or a value is
            not callable.
        ValueError: If a key of ``state`` is not made of names joined
            by dots (see ``register``).

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
        self._state: dict[str, Callable[..., Any]] = {}
        # The resolvers published to OmegaConf by this registry
        self._published: dict[str, Callable[..., Any]] = {}
        for key, resolver in (state or {}).items():
            self.register(key)(resolver)

    @property
    def state(self) -> Mapping[str, Callable[..., Any]]:
        r"""The state of the registry.

        This is a read-only view: use ``register`` to add a resolver.

        Example:
            ```pycon
            >>> from hya.registry import ResolverRegistry
            >>> registry = ResolverRegistry()
            >>> @registry.register("my_key")
            ... def my_resolver(value):
            ...     return value
            ...
            >>> list(registry.state)
            ['my_key']

            ```
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
            key: The key used to register the resolver: names made of ASCII
                letters, digits and ``_`` that do not start with a digit,
                joined by dots (for example ``"my.resolver_2"``). Every
                supported OmegaConf can interpolate such a key. Must be unique
                unless exist_ok is True.
            exist_ok: If False, a RuntimeError is raised if you try to register
                a new resolver with an existing key. If True, the existing
                resolver will be overridden.

        Returns:
            A decorator function that registers the resolver and returns it unchanged.

        Raises:
            TypeError: If the key is not a string (for example
                ``@registry.register`` used without a key), or if the
                resolver is not callable.
            ValueError: If the key is not made of names joined by dots.
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
        if not isinstance(key, str):
            msg = (
                f"The key must be a string, but received {type(key).__name__}. "
                "Use the decorator as @registry.register('my_key')."
            )
            raise TypeError(msg)
        if not _KEY.fullmatch(key):
            msg = (
                f"Invalid resolver key '{key}': use names made of letters, digits and _, "
                "that do not start with a digit, joined by dots"
            )
            raise ValueError(msg)

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

    def register_lazy(self, key: str, target: str, *, exist_ok: bool = False) -> None:
        r"""Register a resolver that is imported on its first call.

        The module of the resolver is not imported when the resolver is
        registered, but the first time OmegaConf calls the resolver. It
        is useful for the resolvers that need a heavy package, because
        the package is not imported if the resolver is never used. The
        registered callable is named after the function of the target and
        its docstring gives the target, so that tracebacks and the state of
        the registry say what it is.

        Args:
            key: The key used to register the resolver, as for ``register``.
                Must be unique unless ``exist_ok`` is ``True``.
            target: The resolver to import, as ``"module:function"``, for
                example ``"hya.numpy:to_array_resolver"``. The function
                is the name of an attribute of the module.
            exist_ok: If ``False``, a ``RuntimeError`` is raised if you try to
                register a new resolver with an existing key. If ``True``,
                the existing resolver will be overridden.

        Raises:
            TypeError: If the key is not a string.
            ValueError: If ``target`` is not formatted as
                ``"module:function"``, or if the key is not made of names
                joined by dots.
            RuntimeError: If the key already exists and ``exist_ok`` is
                ``False``.

        Note:
            A resolver registered lazily cannot receive the special
            parameters of OmegaConf (``_root_``, ``_parent_`` or
            ``_node_``): OmegaConf reads them from the signature, which
            is not known before the import.

        Example:
            ```pycon
            >>> from hya.registry import ResolverRegistry
            >>> registry = ResolverRegistry()
            >>> registry.register_lazy("hya.np.array", "hya.numpy:to_array_resolver")
            >>> registry.has_resolver("hya.np.array")
            True

            ```
        """
        module_name, _, function_name = target.partition(":")
        if not module_name or not function_name.isidentifier():
            msg = f"The target must be formatted as 'module:function', but received '{target}'"
            raise ValueError(msg)

        def resolver(*args: Any) -> Any:
            return getattr(import_module(module_name), function_name)(*args)

        resolver.__name__ = function_name
        resolver.__qualname__ = function_name
        resolver.__doc__ = f"Resolver {target}, imported on its first call."

        self.register(key, exist_ok=exist_ok)(resolver)

    def register_resolvers(self, *, replace: bool = False) -> None:
        r"""Register the resolvers to OmegaConf.

        This method publishes the registered resolvers to OmegaConf. It is
        idempotent: calling it twice changes nothing. A resolver removed
        from OmegaConf (for example with ``OmegaConf.clear_resolvers()``)
        is published again.

        Without ``replace``, a resolver already published by this registry,
        and whose key OmegaConf still knows, is not registered again. A key
        is skipped if OmegaConf already has a resolver for it that this
        registry did not publish (registered by another source), or if the
        registry changed since it was published. One warning lists the
        skipped keys, after the other keys are published, so no key is left
        out when warnings are errors. A resolver that another source
        registers over a published key is not detected: it is kept without
        a warning.

        With ``replace=True``, every key of the registry is published,
        whatever OmegaConf holds.

        The resolvers are published with ``annotation_validation="off"`` when
        OmegaConf validates the annotations (2.4 and later): the annotations of
        the resolvers are not a runtime contract.

        Args:
            replace: If ``True``, the resolvers replace the resolvers that
                OmegaConf already has for the same keys. If ``False``, these
                keys are skipped, with a warning for the ones that this
                registry did not publish.

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
        skipped: list[str] = []
        for key, resolver in self._state.items():
            if not replace and OmegaConf.has_resolver(key):
                if self._published.get(key) is not resolver:
                    skipped.append(key)
                continue
            _publish(key, resolver, replace=replace)
            self._published[key] = resolver
        # The warning is emitted after the loop: as an error, it must not stop the publication
        if skipped:
            keys = ", ".join(f"'{key}'" for key in skipped)
            warnings.warn(
                f"A resolver is already registered in OmegaConf for {keys}: not replaced. "
                "Use register_resolvers(replace=True) to replace it.",
                stacklevel=2,
            )
