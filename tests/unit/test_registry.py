from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import Mock, NonCallableMock

import pytest
from omegaconf import OmegaConf

from hya.registry import ResolverRegistry, register_resolvers, registry

if TYPE_CHECKING:
    from collections.abc import Callable


def add_two(value: int) -> int:
    return value + 2


######################################
#     Tests for ResolverRegistry     #
######################################


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
    with pytest.raises(TypeError, match=r"Each resolver has to be callable but received"):
        registry.register("key")(NonCallableMock())


def test_resolver_registry_register_duplicate_exist_ok_false() -> None:
    registry = ResolverRegistry()
    registry.register("key")(Mock())
    with pytest.raises(RuntimeError, match=r"A resolver is already registered for `key`."):
        registry.register("key")(Mock())


def test_resolver_registry_register_duplicate_exist_ok_true() -> None:
    registry = ResolverRegistry()
    registry.register("key")(Mock())
    registry.register("key", exist_ok=True)(Mock())


########################################
#     Tests for register_resolvers     #
########################################


@pytest.mark.parametrize("name", registry.state.keys())
def test_register_resolvers(name: str) -> None:
    register_resolvers()
    assert OmegaConf.has_resolver(name)
