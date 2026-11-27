from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING, Any
from unittest.mock import Mock, NonCallableMock, call, patch

import pytest

from hya.registry import _KEY, ResolverRegistry, _publish

if TYPE_CHECKING:
    from collections.abc import Callable, Generator


def add_two(value: int) -> int:
    return value + 2


@pytest.fixture(autouse=True)
def _annotation_validation() -> Generator[None, None, None]:
    # The tests assert the calls of the API of OmegaConf 2.4; _publish is tested separately
    with patch("hya.registry._HAS_ANNOTATION_VALIDATION", new=True):
        yield


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


VALID_KEYS = ["a", "_", "_a", "A1", "a_b", "a.b", "a.b_2.c", "_a._b", "oc.env", "hya.np.array"]
INVALID_KEYS = [
    "",
    " ",
    "a b",
    " a",
    "a ",
    "a\n",
    "1a",
    "a.1",
    ".a",
    "a.",
    "a..b",
    "a-b",
    "a:b",
    "a,b",
    "a/b",
    "${a}",
    "\u00e9",
    "a\u00e9",
]


@pytest.mark.parametrize("key", VALID_KEYS)
def test_resolver_registry_register_valid_key(key: str) -> None:
    registry = ResolverRegistry()
    registry.register(key)(add_two)
    assert registry.state == {key: add_two}


@pytest.mark.parametrize("key", INVALID_KEYS)
def test_resolver_registry_register_invalid_key(key: str) -> None:
    registry = ResolverRegistry()
    with pytest.raises(ValueError, match=r"Invalid resolver key"):
        registry.register(key)
    assert registry.state == {}


def test_resolver_registry_register_invalid_key_with_exist_ok() -> None:
    with pytest.raises(ValueError, match=r"Invalid resolver key 'a-b'"):
        ResolverRegistry().register("a-b", exist_ok=True)


@pytest.mark.parametrize(("key", "name"), [(1, "int"), (None, "NoneType"), (b"a", "bytes")])
def test_resolver_registry_register_key_not_a_string(key: Any, name: str) -> None:
    with pytest.raises(TypeError, match=rf"The key must be a string, but received {name}"):
        ResolverRegistry().register(key)


def test_resolver_registry_register_without_a_key() -> None:
    registry = ResolverRegistry()
    register: Any = registry.register
    with pytest.raises(TypeError, match=r"Use the decorator as @registry.register\('my_key'\)"):
        register(add_two)
    assert registry.state == {}


def test_resolver_registry_init_with_a_non_callable_value() -> None:
    state: Any = {"key": 1}
    with pytest.raises(TypeError, match=r"Resolver must be callable, but received int"):
        ResolverRegistry(state)


@pytest.mark.parametrize("key", ["a-b", ""])
def test_resolver_registry_init_with_an_invalid_key(key: str) -> None:
    with pytest.raises(ValueError, match=r"Invalid resolver key"):
        ResolverRegistry({key: add_two})


def test_resolver_registry_init_with_a_key_that_is_not_a_string() -> None:
    state: Any = {1: add_two}
    with pytest.raises(TypeError, match=r"The key must be a string, but received int"):
        ResolverRegistry(state)


def test_resolver_registry_init_does_not_modify_the_state_on_error() -> None:
    state: Any = {"add2": add_two, "key": 1}
    with pytest.raises(TypeError, match=r"Resolver must be callable"):
        ResolverRegistry(state)
    assert state == {"add2": add_two, "key": 1}


def test_resolver_registry_init_keeps_the_order_of_the_state() -> None:
    assert list(ResolverRegistry({"b": add_two, "a": add_two}).state) == ["b", "a"]


##########################
#     Tests for _KEY     #
##########################


@pytest.mark.parametrize("key", VALID_KEYS)
def test_key_pattern_match(key: str) -> None:
    assert _KEY.fullmatch(key)


@pytest.mark.parametrize("key", INVALID_KEYS)
def test_key_pattern_no_match(key: str) -> None:
    assert not _KEY.fullmatch(key)


####################################################
#     Tests for ResolverRegistry.register_lazy     #
####################################################


def test_resolver_registry_register_lazy() -> None:
    registry = ResolverRegistry()
    registry.register_lazy("key", "package.module:function")
    assert registry.has_resolver("key")


def test_resolver_registry_register_lazy_resolver_has_the_name_of_the_function() -> None:
    registry = ResolverRegistry()
    registry.register_lazy("key", "package.module:function")
    resolver: Any = registry.state["key"]
    assert resolver.__name__ == "function"


def test_resolver_registry_register_lazy_resolver_has_the_qualified_name_of_the_function() -> None:
    registry = ResolverRegistry()
    registry.register_lazy("key", "package.module:function")
    resolver: Any = registry.state["key"]
    assert resolver.__qualname__ == "function"


def test_resolver_registry_register_lazy_resolver_documents_the_target() -> None:
    registry = ResolverRegistry()
    registry.register_lazy("key", "package.module:function")
    assert registry.state["key"].__doc__ == (
        "Resolver package.module:function, imported on its first call."
    )


def test_resolver_registry_register_lazy_does_not_import_the_module() -> None:
    registry = ResolverRegistry()
    with patch("hya.registry.import_module") as import_module:
        registry.register_lazy("key", "package.module:function")
    assert import_module.call_count == 0


def test_resolver_registry_register_lazy_imports_the_module_on_the_first_call() -> None:
    registry = ResolverRegistry()
    registry.register_lazy("key", "package.module:function")
    with patch("hya.registry.import_module") as import_module:
        registry.state["key"](1, 2)
    assert import_module.call_args_list == [call("package.module")]


def test_resolver_registry_register_lazy_calls_the_function_with_the_arguments() -> None:
    registry = ResolverRegistry()
    registry.register_lazy("key", "package.module:function")
    with patch("hya.registry.import_module") as import_module:
        registry.state["key"](1, 2)
    assert import_module.return_value.function.call_args_list == [call(1, 2)]


def test_resolver_registry_register_lazy_returns_the_output_of_the_function() -> None:
    registry = ResolverRegistry()
    registry.register_lazy("key", "package.module:function")
    with patch("hya.registry.import_module") as import_module:
        import_module.return_value.function.return_value = 42
        assert registry.state["key"]() == 42


def test_resolver_registry_register_lazy_imports_the_module_at_each_call() -> None:
    registry = ResolverRegistry()
    registry.register_lazy("key", "package.module:function")
    with patch("hya.registry.import_module") as import_module:
        registry.state["key"]()
        registry.state["key"]()
    assert import_module.call_count == 2


def test_resolver_registry_register_lazy_target_with_nested_module() -> None:
    registry = ResolverRegistry()
    registry.register_lazy("key", "a.b.c:f")
    with patch("hya.registry.import_module") as import_module:
        registry.state["key"]()
    assert import_module.call_args_list == [call("a.b.c")]


def test_resolver_registry_register_lazy_module_not_found() -> None:
    registry = ResolverRegistry()
    registry.register_lazy("key", "hya_missing_module:function")
    with pytest.raises(ModuleNotFoundError, match=r"No module named 'hya_missing_module'"):
        registry.state["key"]()


def test_resolver_registry_register_lazy_function_not_found() -> None:
    registry = ResolverRegistry()
    registry.register_lazy("key", "json:missing_function")
    with pytest.raises(AttributeError, match=r"missing_function"):
        registry.state["key"]()


@pytest.mark.parametrize(
    "target",
    [
        "",
        "module",
        "module:",
        ":function",
        ":",
        "a:b:c",
        "module::function",
        "module:a.b",
        "module:1f",
        "module:f g",
        "module:function ",
    ],
)
def test_resolver_registry_register_lazy_invalid_target(target: str) -> None:
    registry = ResolverRegistry()
    with pytest.raises(ValueError, match=r"The target must be formatted as 'module:function'"):
        registry.register_lazy("key", target)


def test_resolver_registry_register_lazy_invalid_target_does_not_register() -> None:
    registry = ResolverRegistry()
    with pytest.raises(ValueError, match=r"must be formatted as"):
        registry.register_lazy("key", "module")
    assert registry.state == {}


def test_resolver_registry_register_lazy_invalid_key() -> None:
    registry = ResolverRegistry()
    with pytest.raises(ValueError, match=r"Invalid resolver key 'a-b'"):
        registry.register_lazy("a-b", "package.module:function")
    assert registry.state == {}


def test_resolver_registry_register_lazy_key_not_a_string() -> None:
    key: Any = 1
    with pytest.raises(TypeError, match=r"The key must be a string, but received int"):
        ResolverRegistry().register_lazy(key, "package.module:function")


def test_resolver_registry_register_lazy_duplicate_exist_ok_false() -> None:
    registry = ResolverRegistry({"key": Mock()})
    with pytest.raises(RuntimeError, match=r"A resolver is already registered for 'key'."):
        registry.register_lazy("key", "package.module:function")


def test_resolver_registry_register_lazy_duplicate_exist_ok_true() -> None:
    old_resolver = Mock()
    registry = ResolverRegistry({"key": old_resolver})
    registry.register_lazy("key", "package.module:function", exist_ok=True)
    assert registry.state["key"] is not old_resolver


def test_resolver_registry_register_lazy_exist_ok_is_keyword_only() -> None:
    register_lazy: Any = ResolverRegistry().register_lazy
    with pytest.raises(TypeError, match=r"takes 3 positional arguments but 4 were given"):
        register_lazy("key", "package.module:function", True)


def test_resolver_registry_register_lazy_register_resolvers() -> None:
    registry = ResolverRegistry()
    registry.register_lazy("key", "package.module:function")
    with patch("hya.registry.OmegaConf") as omegaconf:
        omegaconf.has_resolver.return_value = False
        registry.register_resolvers()
    assert omegaconf.register_resolver.call_args_list == [
        call("key", registry.state["key"], replace=False, annotation_validation="off")
    ]


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
        omegaconf.has_resolver.return_value = True
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


def test_resolver_registry_register_resolvers_republishes_a_cleared_resolver() -> None:
    registry = ResolverRegistry({"key": Mock()})
    with patch("hya.registry.OmegaConf") as omegaconf:
        omegaconf.has_resolver.return_value = False
        registry.register_resolvers()
        registry.register_resolvers()
    assert omegaconf.register_resolver.call_count == 2


def test_resolver_registry_register_resolvers_republishes_a_cleared_resolver_silently(
    recwarn: pytest.WarningsRecorder,
) -> None:
    registry = ResolverRegistry({"key": Mock()})
    with patch("hya.registry.OmegaConf") as omegaconf:
        omegaconf.has_resolver.return_value = False
        registry.register_resolvers()
        registry.register_resolvers()
    assert len(recwarn) == 0


def test_resolver_registry_register_resolvers_registries_are_independent() -> None:
    first, second = ResolverRegistry({"key": Mock()}), ResolverRegistry({"key": Mock()})
    with patch("hya.registry.OmegaConf") as omegaconf:
        omegaconf.has_resolver.return_value = False
        first.register_resolvers()
        omegaconf.has_resolver.return_value = True
        with pytest.warns(UserWarning, match=r"not replaced"):
            second.register_resolvers()
    assert omegaconf.register_resolver.call_count == 1


#############################
#     Tests for _publish    #
#############################


def test_publish_with_annotation_validation() -> None:
    with patch("hya.registry.OmegaConf") as omegaconf:
        _publish("key", add_two, replace=True)
    assert omegaconf.register_resolver.call_args_list == [
        call("key", add_two, replace=True, annotation_validation="off")
    ]


def test_publish_without_annotation_validation() -> None:
    with (
        patch("hya.registry._HAS_ANNOTATION_VALIDATION", new=False),
        patch("hya.registry.OmegaConf") as omegaconf,
    ):
        _publish("key", add_two, replace=False)
    assert omegaconf.register_new_resolver.call_args_list == [call("key", add_two, replace=False)]


def test_publish_without_annotation_validation_does_not_use_register_resolver() -> None:
    with (
        patch("hya.registry._HAS_ANNOTATION_VALIDATION", new=False),
        patch("hya.registry.OmegaConf") as omegaconf,
    ):
        _publish("key", add_two, replace=False)
    assert omegaconf.register_resolver.call_count == 0
