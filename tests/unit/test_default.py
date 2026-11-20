from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest

from hya import get_default_registry
from hya.registry import ResolverRegistry

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture(autouse=True)
def _reset_default_registry() -> Generator[None, None, None]:
    """Reset the registry before and after each test."""
    get_default_registry.cache_clear()
    yield
    get_default_registry.cache_clear()


##########################################
#     Tests for get_default_registry     #
##########################################


def test_get_default_registry_returns_resolver_registry() -> None:
    """Test that get_default_registry returns a ResolverRegistry
    instance."""
    assert isinstance(get_default_registry(), ResolverRegistry)


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
    mock_resolver = Mock(return_value=42)
    registry1.register("test_key")(mock_resolver)

    # Get registry again and verify the resolver is still there
    registry2 = get_default_registry()
    assert registry2.has_resolver("test_key")


@pytest.mark.parametrize(
    "name",
    [
        "hya.add",
        "hya.asinh",
        "hya.ceildiv",
        "hya.exp",
        "hya.floordiv",
        "hya.len",
        "hya.iter_join",
        "hya.log",
        "hya.log10",
        "hya.max",
        "hya.min",
        "hya.mul",
        "hya.neg",
        "hya.path",
        "hya.pi",
        "hya.pow",
        "hya.sqrt",
        "hya.sha256",
        "hya.sinh",
        "hya.sub",
        "hya.truediv",
    ],
)
def test_get_default_registry_default_resolvers(name: str) -> None:
    """Test that get_default_registry returns a registry with default
    resolvers."""
    assert get_default_registry().has_resolver(name)


@pytest.mark.parametrize(
    "name", ["hya.braceexpand", "hya.np.array", "hya.torch.tensor", "hya.torch.dtype"]
)
def test_get_default_registry_default_optional_resolvers(name: str) -> None:
    """Test that the optional resolvers are registered, whether or not
    their package is installed."""
    assert get_default_registry().has_resolver(name)


OPTIONAL_KEYS = {
    "hya.braceexpand",
    "hya.np.array",
    "hya.torch.tensor",
    "hya.torch.dtype",
}


BUILTIN_KEYS = {
    "hya.add",
    "hya.asinh",
    "hya.ceildiv",
    "hya.exp",
    "hya.floordiv",
    "hya.iter_join",
    "hya.len",
    "hya.log",
    "hya.log10",
    "hya.max",
    "hya.min",
    "hya.mul",
    "hya.neg",
    "hya.path",
    "hya.pi",
    "hya.pow",
    "hya.sha256",
    "hya.sinh",
    "hya.sqrt",
    "hya.sub",
    "hya.truediv",
}


def test_get_default_registry_keys() -> None:
    assert set(get_default_registry().state) == BUILTIN_KEYS | OPTIONAL_KEYS


def test_get_default_registry_keys_do_not_depend_on_the_installed_packages() -> None:
    with (
        patch("hya.imports.is_braceexpand_available", return_value=False),
        patch("hya.imports.is_numpy_available", return_value=False),
        patch("hya.imports.is_torch_available", return_value=False),
    ):
        keys = set(get_default_registry().state)
    assert keys == BUILTIN_KEYS | OPTIONAL_KEYS


def test_get_default_registry_does_not_look_for_the_optional_packages() -> None:
    with (
        patch("hya.imports.is_braceexpand_available") as braceexpand,
        patch("hya.imports.is_numpy_available") as numpy,
        patch("hya.imports.is_torch_available") as torch,
    ):
        get_default_registry()
    assert (braceexpand.call_count, numpy.call_count, torch.call_count) == (0, 0, 0)


def test_get_default_registry_keys_are_in_the_hya_namespace() -> None:
    assert all(key.startswith("hya.") for key in get_default_registry().state)


def test_get_default_registry_does_not_modify_the_builtins() -> None:
    get_default_registry().register("hya.custom")(Mock())
    get_default_registry.cache_clear()
    assert not get_default_registry().has_resolver("hya.custom")


def test_get_default_registry_registers_nothing_in_omegaconf() -> None:
    with patch("hya.registry.OmegaConf") as omegaconf:
        get_default_registry()
    assert omegaconf.register_resolver.call_count == 0
