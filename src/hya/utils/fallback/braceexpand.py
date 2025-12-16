r"""Contain fallback implementations used when ``braceexpand``
dependency is not available."""

from __future__ import annotations

__all__ = ["braceexpand"]

from types import ModuleType

# Create a fake braceexpand package
braceexpand: ModuleType = ModuleType("braceexpand")
