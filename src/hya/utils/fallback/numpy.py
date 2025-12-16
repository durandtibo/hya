r"""Contain fallback implementations used when ``numpy`` dependency is
not available."""

from __future__ import annotations

__all__ = ["numpy"]

from types import ModuleType

# Create a fake numpy package
numpy: ModuleType = ModuleType("numpy")
