from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest

from hya import get_default_registry
from hya.registry import ResolverRegistry
from hya.testing import braceexpand_available, numpy_available, torch_available

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture(autouse=True)
def _reset_default_registry() -> Generator[None, None, None]:
    if hasattr(get_default_registry, "_registry"):
        del get_default_registry._registry
    yield
    if hasattr(get_default_registry, "_registry"):
        del get_default_registry._registry


def test_get_default_registry_returns_resolver_registry() -> None:
    assert isinstance(get_default_registry(), ResolverRegistry)


def test_get_default_registry_returns_singleton() -> None:
    registry1 = get_default_registry()
    registry2 = get_default_registry()
    assert registry1 is registry2


def test_get_default_registry_modifications_persist() -> None:
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
        "hya.to_path",
        "hya.truediv",
    ],
)
def test_get_default_registry_default_resolvers(name: str) -> None:
    assert get_default_registry().has_resolver(name)


@braceexpand_available
def test_get_default_registry_default_braceexpand_resolvers() -> None:
    assert get_default_registry().has_resolver("hya.braceexpand")


@numpy_available
def test_get_default_registry_default_numpy_resolvers() -> None:
    """Test that get_default_registry returns a registry with default
    resolvers."""
    assert get_default_registry().has_resolver("hya.np.array")


@torch_available
@pytest.mark.parametrize("name", ["hya.torch.tensor", "hya.torch.dtype"])
def test_get_default_registry_default_torch_resolvers(name: str) -> None:
    assert get_default_registry().has_resolver(name)
