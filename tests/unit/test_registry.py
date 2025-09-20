from __future__ import annotations

from unittest.mock import Mock, NonCallableMock

import pytest
from omegaconf import OmegaConf

from hya.registry import ResolverRegistry, register_resolvers, registry

######################################
#     Tests for ResolverRegistry     #
######################################


def test_resolver_registry_register() -> None:
    register = ResolverRegistry()

    @register.register("add1")
    def add_one(value: int) -> None:
        return value + 1

    assert register.state["add1"] == add_one


def test_resolver_registry_register_not_callable() -> None:
    register = ResolverRegistry()
    with pytest.raises(TypeError, match=r"Each resolver has to be callable but received"):
        register.register("key")(NonCallableMock())


def test_resolver_registry_register_duplicate_exist_ok_false() -> None:
    register = ResolverRegistry()
    register.register("key")(Mock())
    with pytest.raises(RuntimeError, match=r"A resolver is already registered for `key`."):
        register.register("key")(Mock())


def test_resolver_registry_register_duplicate_exist_ok_true() -> None:
    register = ResolverRegistry()
    register.register("key")(Mock())
    register.register("key", exist_ok=True)(Mock())


########################################
#     Tests for register_resolvers     #
########################################


@pytest.mark.parametrize("name", registry.state.keys())
def test_register_resolvers(name: str) -> None:
    register_resolvers()
    assert OmegaConf.has_resolver(name)
