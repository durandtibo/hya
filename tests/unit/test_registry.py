from unittest.mock import NonCallableMock

from pytest import raises

from bearface import ResolverRegistry

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
