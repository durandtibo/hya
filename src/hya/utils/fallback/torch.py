r"""Contain fallback implementations used when ``torch`` dependency is
not available."""

from __future__ import annotations

__all__ = ["torch"]

from types import SimpleNamespace

# Create a fake torch package
torch = SimpleNamespace()
