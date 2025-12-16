r"""Contain fallback implementations used when ``torch`` dependency is
not available."""

from __future__ import annotations

__all__ = ["torch"]

from types import ModuleType

# Create a fake torch package
torch: ModuleType = ModuleType("torch")
