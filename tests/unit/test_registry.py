from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import Mock, NonCallableMock

import pytest
from omegaconf import OmegaConf

from hya.registry import (
    ResolverRegistry,
)

if TYPE_CHECKING:
    from collections.abc import Callable


def add_two(value: int) -> int:
    return value + 2


def test_resolver_registry_init_empty() -> None:
    assert ResolverRegistry().state == {}


def test_resolver_registry_init_with_state() -> None:
    initial_state: dict[str, Callable[[...], Any]] = {"add2": add_two}
    registry = ResolverRegistry(initial_state)

    assert "add2" in registry.state
    assert registry.state["add2"] == add_two
    # Verify it's a copy
    initial_state["add1"] = add_two
    assert "add1" not in registry.state


def test_resolver_registry_has_resolver_true() -> None:
    assert ResolverRegistry({"add2": add_two}).has_resolver("add2")


def test_resolver_registry_has_resolver_false() -> None:
    assert not ResolverRegistry().has_resolver("add2")


def test_resolver_registry_register() -> None:
    registry = ResolverRegistry()

    @registry.register("add1")
    def add_one(value: int) -> int:
        return value + 1

    assert registry.state["add1"] == add_one


def test_resolver_registry_register_not_callable() -> None:
    registry = ResolverRegistry()
    with pytest.raises(TypeError, match=r"Resolver must be callable, but received"):
        registry.register("key")(NonCallableMock())


def test_resolver_registry_register_duplicate_exist_ok_false() -> None:
    registry = ResolverRegistry()
    registry.register("key")(Mock())
    with pytest.raises(RuntimeError, match=r"A resolver is already registered for 'key'."):
        registry.register("key")(Mock())


def test_resolver_registry_register_duplicate_exist_ok_true() -> None:
    registry = ResolverRegistry()
    registry.register("key")(Mock())
    registry.register("key", exist_ok=True)(Mock())


def test_resolver_registry_register_resolvers() -> None:
    registry = ResolverRegistry()
    registry.register("hya.custom_resolver")(Mock())
    registry.register_resolvers()
    assert OmegaConf.has_resolver("hya.custom_resolver")


def test_resolver_registry_register_resolvers_idempotent() -> None:
    registry = ResolverRegistry()
    registry.register("hya.custom_resolver")(Mock())
    registry.register_resolvers()
    assert OmegaConf.has_resolver("hya.custom_resolver")
    registry.register_resolvers()
    assert OmegaConf.has_resolver("hya.custom_resolver")
