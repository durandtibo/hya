from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest

from hya import get_default_registry
from hya.registry import ResolverRegistry
from hya.testing import braceexpand_available, numpy_available, torch_available

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


@braceexpand_available
def test_get_default_registry_default_braceexpand_resolvers() -> None:
    """Test that get_default_registry returns a registry with default
    resolvers."""
    assert get_default_registry().has_resolver("hya.braceexpand")


@numpy_available
def test_get_default_registry_default_numpy_resolvers() -> None:
    """Test that get_default_registry returns a registry with default
    resolvers."""
    assert get_default_registry().has_resolver("hya.np.array")


@torch_available
@pytest.mark.parametrize("name", ["hya.torch.tensor", "hya.torch.dtype"])
def test_get_default_registry_default_torch_resolvers(name: str) -> None:
    """Test that get_default_registry returns a registry with default
    resolvers."""
    assert get_default_registry().has_resolver(name)


OPTIONAL_KEYS = {
    "hya.braceexpand",
    "hya.np.array",
    "hya.torch.tensor",
    "hya.torch.dtype",
}


def get_keys(*, braceexpand: bool, numpy: bool, torch: bool) -> set[str]:
    with (
        patch("hya.default.is_braceexpand_available", return_value=braceexpand),
        patch("hya.default.is_numpy_available", return_value=numpy),
        patch("hya.default.is_torch_available", return_value=torch),
    ):
        return set(get_default_registry().state)


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


def test_get_default_registry_keys_all_packages() -> None:
    assert get_keys(braceexpand=True, numpy=True, torch=True) == BUILTIN_KEYS | OPTIONAL_KEYS


def test_get_default_registry_keys_no_optional_package() -> None:
    assert get_keys(braceexpand=False, numpy=False, torch=False) == BUILTIN_KEYS


def test_get_default_registry_keys_braceexpand_only() -> None:
    assert get_keys(braceexpand=True, numpy=False, torch=False) == BUILTIN_KEYS | {
        "hya.braceexpand"
    }


def test_get_default_registry_keys_numpy_only() -> None:
    assert get_keys(braceexpand=False, numpy=True, torch=False) == BUILTIN_KEYS | {"hya.np.array"}


def test_get_default_registry_keys_torch_only() -> None:
    assert get_keys(braceexpand=False, numpy=False, torch=True) == BUILTIN_KEYS | {
        "hya.torch.tensor",
        "hya.torch.dtype",
    }


def test_get_default_registry_keys_are_in_the_hya_namespace() -> None:
    keys = get_keys(braceexpand=True, numpy=True, torch=True)
    assert all(key.startswith("hya.") for key in keys)


def test_get_default_registry_does_not_modify_the_builtins() -> None:
    get_default_registry().register("hya.custom")(Mock())
    get_default_registry.cache_clear()
    assert not get_default_registry().has_resolver("hya.custom")


def test_get_default_registry_registers_nothing_in_omegaconf() -> None:
    with patch("hya.registry.OmegaConf") as omegaconf:
        get_default_registry()
    assert omegaconf.register_resolver.call_count == 0
