from __future__ import annotations

import pytest

from hya.imports import (
    is_braceexpand_available,
    is_numpy_available,
    is_torch_available,
    validate_braceexpand,
    validate_numpy,
    validate_torch,
)
from hya.testing import (
    braceexpand_available,
    braceexpand_not_available,
    numpy_available,
    numpy_not_available,
    torch_available,
    torch_not_available,
)

#######################
#     braceexpand     #
#######################


@braceexpand_available
def test_check_braceexpand_with_package() -> None:
    validate_braceexpand()


@braceexpand_not_available
def test_check_braceexpand_without_package() -> None:
    with pytest.raises(RuntimeError, match=r"'braceexpand' package is required but not installed."):
        validate_braceexpand()


@braceexpand_available
def test_is_braceexpand_available_true() -> None:
    assert is_braceexpand_available()


@braceexpand_not_available
def test_is_braceexpand_available_false() -> None:
    assert not is_braceexpand_available()


#################
#     numpy     #
#################


@numpy_available
def test_check_numpy_with_package() -> None:
    validate_numpy()


@numpy_not_available
def test_check_numpy_without_package() -> None:
    with pytest.raises(RuntimeError, match=r"'numpy' package is required but not installed."):
        validate_numpy()


@numpy_available
def test_is_numpy_available_true() -> None:
    assert is_numpy_available()


@numpy_not_available
def test_is_numpy_available_false() -> None:
    assert not is_numpy_available()


#################
#     torch     #
#################


@torch_available
def test_check_torch_with_package() -> None:
    validate_torch()


@torch_not_available
def test_check_torch_without_package() -> None:
    with pytest.raises(RuntimeError, match=r"'torch' package is required but not installed."):
        validate_torch()


@torch_available
def test_is_torch_available_true() -> None:
    assert is_torch_available()


@torch_not_available
def test_is_torch_available_false() -> None:
    assert not is_torch_available()
