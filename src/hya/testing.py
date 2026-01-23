r"""Define PyTest fixtures for testing optional dependencies.

This module provides pytest markers and fixtures that help with testing
the hya library under different dependency configurations. The fixtures
allow tests to be conditionally skipped based on whether optional
packages (braceexpand, numpy, torch) are available in the test
environment.

These fixtures are useful for ensuring tests only run when the required
dependencies are present, avoiding import errors and test failures when
optional packages are not installed.
"""

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

braceexpand_available: pytest.MarkDecorator = pytest.mark.skipif(
    not is_braceexpand_available(), reason="Require braceexpand"
)
braceexpand_not_available: pytest.MarkDecorator = pytest.mark.skipif(
    is_braceexpand_available(), reason="Skip if braceexpand is available"
)
numpy_available: pytest.MarkDecorator = pytest.mark.skipif(
    not is_numpy_available(), reason="Require numpy"
)
numpy_not_available: pytest.MarkDecorator = pytest.mark.skipif(
    is_numpy_available(), reason="Skip if numpy is available"
)
torch_available: pytest.MarkDecorator = pytest.mark.skipif(
    not is_torch_available(), reason="Require torch"
)
torch_not_available: pytest.MarkDecorator = pytest.mark.skipif(
    is_torch_available(), reason="Skip if torch is available"
)
