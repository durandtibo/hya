from unittest.mock import Mock, NonCallableMock

from omegaconf import OmegaConf
from pytest import mark, raises

from hya.registry import ResolverRegistry, register_resolvers, registry

######################################
#     Tests for ResolverRegistry     #
######################################


def test_resolver_registry_register():
    register = ResolverRegistry()

    @register.register("add1")
    def add_one(value: int):
        return value + 1

    assert register.state["add1"] == add_one


def test_resolver_registry_register_not_callable():
    register = ResolverRegistry()
    with raises(TypeError):
        register.register("key")(NonCallableMock())


def test_resolver_registry_register_duplicate_exist_ok_false():
    register = ResolverRegistry()
    register.register("key")(Mock())
    with raises(RuntimeError):
        register.register("key")(Mock())


def test_resolver_registry_register_duplicate_exist_ok_true():
    register = ResolverRegistry()
    register.register("key")(Mock())
    register.register("key", exist_ok=True)(Mock())


########################################
#     Tests for register_resolvers     #
########################################


@mark.parametrize("name", registry.state.keys())
def test_register_resolvers(name: str):
    register_resolvers()
    assert OmegaConf.has_resolver(name)
