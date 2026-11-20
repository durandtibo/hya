from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING, Any
from unittest.mock import Mock, NonCallableMock, call, patch

import pytest

from hya.registry import (
    ResolverRegistry,
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
    initial_state: dict[str, Callable[..., Any]] = {"add2": add_two}
    registry = ResolverRegistry(initial_state)

    assert "add2" in registry.state
    assert registry.state["add2"] == add_two
    # Verify it's a copy
    initial_state["add1"] = add_two
    assert "add1" not in registry.state


def test_resolver_registry_init_with_mapping() -> None:
    assert ResolverRegistry(MappingProxyType({"add2": add_two})).state == {"add2": add_two}


def test_resolver_registry_state_is_read_only() -> None:
    state: Any = ResolverRegistry().state
    with pytest.raises(TypeError, match=r"does not support item assignment"):
        state["add2"] = add_two


def test_resolver_registry_state_follows_register() -> None:
    registry = ResolverRegistry()
    state = registry.state
    registry.register("add2")(add_two)
    assert state == {"add2": add_two}


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


def test_resolver_registry_register_exist_ok_is_keyword_only() -> None:
    register: Any = ResolverRegistry().register
    with pytest.raises(TypeError, match=r"takes 2 positional arguments but 3 were given"):
        register("key", True)


def test_resolver_registry_register_returns_resolver() -> None:
    resolver = Mock()
    assert ResolverRegistry().register("key")(resolver) is resolver


def test_resolver_registry_register_duplicate_exist_ok_true_overrides() -> None:
    registry = ResolverRegistry()
    new_resolver = Mock()
    registry.register("key")(Mock())
    registry.register("key", exist_ok=True)(new_resolver)
    assert registry.state == {"key": new_resolver}


def test_resolver_registry_register_does_not_modify_state_on_duplicate() -> None:
    registry = ResolverRegistry()
    resolver = Mock()
    registry.register("key")(resolver)
    with pytest.raises(RuntimeError, match=r"A resolver is already registered for 'key'."):
        registry.register("key")(Mock())
    assert registry.state == {"key": resolver}


#########################################################
#     Tests for ResolverRegistry.register_resolvers     #
#########################################################


def test_resolver_registry_register_resolvers() -> None:
    registry = ResolverRegistry()
    resolver = Mock()
    registry.register("key")(resolver)
    with patch("hya.registry.OmegaConf") as omegaconf:
        omegaconf.has_resolver.return_value = False
        registry.register_resolvers()
    assert omegaconf.register_resolver.call_args_list == [
        call("key", resolver, replace=False, annotation_validation="off")
    ]


def test_resolver_registry_register_resolvers_all_keys() -> None:
    first, second = Mock(), Mock()
    registry = ResolverRegistry({"first": first, "second": second})
    with patch("hya.registry.OmegaConf") as omegaconf:
        omegaconf.has_resolver.return_value = False
        registry.register_resolvers()
    assert omegaconf.register_resolver.call_args_list == [
        call("first", first, replace=False, annotation_validation="off"),
        call("second", second, replace=False, annotation_validation="off"),
    ]


def test_resolver_registry_register_resolvers_empty() -> None:
    with patch("hya.registry.OmegaConf") as omegaconf:
        ResolverRegistry().register_resolvers()
    assert omegaconf.register_resolver.call_count == 0


def test_resolver_registry_register_resolvers_idempotent() -> None:
    registry = ResolverRegistry({"key": Mock()})
    with patch("hya.registry.OmegaConf") as omegaconf:
        omegaconf.has_resolver.return_value = False
        registry.register_resolvers()
        registry.register_resolvers()
    assert omegaconf.register_resolver.call_count == 1


def test_resolver_registry_register_resolvers_twice_is_silent(
    recwarn: pytest.WarningsRecorder,
) -> None:
    registry = ResolverRegistry({"key": Mock()})
    with patch("hya.registry.OmegaConf") as omegaconf:
        omegaconf.has_resolver.return_value = False
        registry.register_resolvers()
        omegaconf.has_resolver.return_value = True
        registry.register_resolvers()
    assert len(recwarn) == 0


def test_resolver_registry_register_resolvers_existing_key_warns() -> None:
    registry = ResolverRegistry({"key": Mock()})
    with patch("hya.registry.OmegaConf") as omegaconf:
        omegaconf.has_resolver.return_value = True
        with pytest.warns(
            UserWarning,
            match=r"A resolver is already registered in OmegaConf for 'key': not replaced. "
            r"Use register_resolvers\(replace=True\) to replace it.",
        ):
            registry.register_resolvers()


def test_resolver_registry_register_resolvers_existing_key_is_skipped() -> None:
    registry = ResolverRegistry({"key": Mock()})
    with patch("hya.registry.OmegaConf") as omegaconf:
        omegaconf.has_resolver.return_value = True
        with pytest.warns(UserWarning, match=r"not replaced"):
            registry.register_resolvers()
    assert omegaconf.register_resolver.call_count == 0


def test_resolver_registry_register_resolvers_existing_key_warns_at_each_call() -> None:
    registry = ResolverRegistry({"key": Mock()})
    with patch("hya.registry.OmegaConf") as omegaconf:
        omegaconf.has_resolver.return_value = True
        with pytest.warns(UserWarning, match=r"not replaced"):
            registry.register_resolvers()
        with pytest.warns(UserWarning, match=r"not replaced"):
            registry.register_resolvers()


def test_resolver_registry_register_resolvers_existing_key_warns_only_for_this_key() -> None:
    first, second = Mock(), Mock()
    registry = ResolverRegistry({"first": first, "second": second})
    with patch("hya.registry.OmegaConf") as omegaconf:
        omegaconf.has_resolver.side_effect = lambda key: key == "first"
        with pytest.warns(UserWarning, match=r"'first'"):
            registry.register_resolvers()
    assert omegaconf.register_resolver.call_args_list == [
        call("second", second, replace=False, annotation_validation="off")
    ]


def test_resolver_registry_register_resolvers_replace() -> None:
    registry = ResolverRegistry()
    resolver = Mock()
    registry.register("key")(resolver)
    with patch("hya.registry.OmegaConf") as omegaconf:
        omegaconf.has_resolver.return_value = True
        registry.register_resolvers(replace=True)
    assert omegaconf.register_resolver.call_args_list == [
        call("key", resolver, replace=True, annotation_validation="off")
    ]


def test_resolver_registry_register_resolvers_replace_is_silent(
    recwarn: pytest.WarningsRecorder,
) -> None:
    registry = ResolverRegistry({"key": Mock()})
    with patch("hya.registry.OmegaConf") as omegaconf:
        omegaconf.has_resolver.return_value = True
        registry.register_resolvers(replace=True)
    assert len(recwarn) == 0


def test_resolver_registry_register_resolvers_replace_is_keyword_only() -> None:
    register_resolvers: Any = ResolverRegistry().register_resolvers
    with pytest.raises(TypeError, match=r"takes 1 positional argument but 2 were given"):
        register_resolvers(True)


def test_resolver_registry_register_resolvers_overridden_key_warns() -> None:
    registry = ResolverRegistry()
    registry.register("key")(Mock())
    with patch("hya.registry.OmegaConf") as omegaconf:
        omegaconf.has_resolver.return_value = False
        registry.register_resolvers()
        omegaconf.has_resolver.return_value = True
        registry.register("key", exist_ok=True)(Mock())
        with pytest.warns(UserWarning, match=r"not replaced"):
            registry.register_resolvers()
    assert omegaconf.register_resolver.call_count == 1


def test_resolver_registry_register_resolvers_overridden_key_replace() -> None:
    registry = ResolverRegistry()
    new_resolver = Mock()
    registry.register("key")(Mock())
    with patch("hya.registry.OmegaConf") as omegaconf:
        omegaconf.has_resolver.return_value = False
        registry.register_resolvers()
        omegaconf.has_resolver.return_value = True
        registry.register("key", exist_ok=True)(new_resolver)
        registry.register_resolvers(replace=True)
    assert omegaconf.register_resolver.call_args_list[-1] == call(
        "key", new_resolver, replace=True, annotation_validation="off"
    )


def test_resolver_registry_register_resolvers_new_key_after_first_call() -> None:
    registry = ResolverRegistry({"first": Mock()})
    second = Mock()
    with patch("hya.registry.OmegaConf") as omegaconf:
        omegaconf.has_resolver.return_value = False
        registry.register_resolvers()
        registry.register("second")(second)
        registry.register_resolvers()
    assert omegaconf.register_resolver.call_args_list[-1] == call(
        "second", second, replace=False, annotation_validation="off"
    )


def test_resolver_registry_register_resolvers_registries_are_independent() -> None:
    first, second = ResolverRegistry({"key": Mock()}), ResolverRegistry({"key": Mock()})
    with patch("hya.registry.OmegaConf") as omegaconf:
        omegaconf.has_resolver.return_value = False
        first.register_resolvers()
        omegaconf.has_resolver.return_value = True
        with pytest.warns(UserWarning, match=r"not replaced"):
            second.register_resolvers()
    assert omegaconf.register_resolver.call_count == 1
