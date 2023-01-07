from unittest.mock import Mock, NonCallableMock

from pytest import raises

from bearface.registry import ResolverRegistry

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
