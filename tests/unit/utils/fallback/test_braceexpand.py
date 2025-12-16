from __future__ import annotations

from types import ModuleType

from hya.utils.fallback.braceexpand import braceexpand


def test_braceexpand() -> None:
    isinstance(braceexpand, ModuleType)
