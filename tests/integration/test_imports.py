from __future__ import annotations

import pytest

from hya.imports import (
    check_braceexpand,
    check_numpy,
    check_torch,
    is_braceexpand_available,
    is_numpy_available,
    is_torch_available,
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
    check_braceexpand()


@braceexpand_not_available
def test_check_braceexpand_without_package() -> None:
    with pytest.raises(RuntimeError, match=r"'braceexpand' package is required but not installed."):
        check_braceexpand()


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
    check_numpy()


@numpy_not_available
def test_check_numpy_without_package() -> None:
    with pytest.raises(RuntimeError, match=r"'numpy' package is required but not installed."):
        check_numpy()


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
    check_torch()


@torch_not_available
def test_check_torch_without_package() -> None:
    with pytest.raises(RuntimeError, match=r"'torch' package is required but not installed."):
        check_torch()


@torch_available
def test_is_torch_available_true() -> None:
    assert is_torch_available()


@torch_not_available
def test_is_torch_available_false() -> None:
    assert not is_torch_available()
