r"""Define some PyTest fixtures."""

from __future__ import annotations

__all__ = [
    "braceexpand_available",
    "braceexpand_not_available",
    "numpy_available",
    "numpy_not_available",
    "torch_available",
    "torch_not_available",
]

import pytest

from hya.imports import is_braceexpand_available, is_numpy_available, is_torch_available

braceexpand_available = pytest.mark.skipif(
    not is_braceexpand_available(), reason="Require braceexpand"
)
braceexpand_not_available = pytest.mark.skipif(
    is_braceexpand_available(), reason="Skip if braceexpand is available"
)
numpy_available = pytest.mark.skipif(not is_numpy_available(), reason="Require numpy")
numpy_not_available = pytest.mark.skipif(is_numpy_available(), reason="Skip if numpy is available")
torch_available = pytest.mark.skipif(not is_torch_available(), reason="Require torch")
torch_not_available = pytest.mark.skipif(is_torch_available(), reason="Skip if torch is available")
