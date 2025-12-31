from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import Mock, NonCallableMock

import pytest
from omegaconf import OmegaConf

from hya.registry import (
    ResolverRegistry,
    get_default_registry,
)

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


##########################################
#     Tests for get_default_registry     #
##########################################


def test_get_default_registry_returns_resolver_registry() -> None:
    """Test that get_default_registry returns a ResolverRegistry
    instance."""
    registry = get_default_registry()
    assert isinstance(registry, ResolverRegistry)


def test_get_default_registry_returns_singleton() -> None:
    """Test that get_default_registry returns the same instance on
    multiple calls."""
    registry1 = get_default_registry()
    registry2 = get_default_registry()
    assert registry1 is registry2


def test_get_default_registry_modifications_persist() -> None:
    """Test that modifications to the registry persist across calls."""
    registry1 = get_default_registry()

    # Register a mock resolver
    mock_resolver = Mock(return_value="test_value")
    registry1.register("test_key")(mock_resolver)

    # Get registry again and verify the resolver is still there
    registry2 = get_default_registry()
    assert registry2.has_resolver("test_key")
