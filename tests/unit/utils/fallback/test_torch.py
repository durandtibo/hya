from __future__ import annotations

from types import ModuleType

from hya.utils.fallback.torch import torch


def test_torch() -> None:
    isinstance(torch, ModuleType)
