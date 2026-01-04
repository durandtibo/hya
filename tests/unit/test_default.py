from __future__ import annotations

from unittest.mock import Mock

from hya import get_default_registry
from hya.registry import ResolverRegistry

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
