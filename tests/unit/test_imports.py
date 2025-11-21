from __future__ import annotations

from unittest.mock import patch

import pytest

from hya.imports import (
    check_braceexpand,
    check_numpy,
    check_torch,
    is_braceexpand_available,
    is_numpy_available,
    is_torch_available,
)

#######################
#     braceexpand     #
#######################


def test_check_braceexpand_with_package() -> None:
    with patch("hya.imports.is_braceexpand_available", lambda: True):
        check_braceexpand()


def test_check_braceexpand_without_package() -> None:
    with (
        patch("hya.imports.is_braceexpand_available", lambda: False),
        pytest.raises(RuntimeError, match=r"'braceexpand' package is required but not installed."),
    ):
        check_braceexpand()


def test_is_braceexpand_available() -> None:
    assert isinstance(is_braceexpand_available(), bool)


#################
#     numpy     #
#################


def test_check_numpy_with_package() -> None:
    with patch("hya.imports.is_numpy_available", lambda: True):
        check_numpy()


def test_check_numpy_without_package() -> None:
    with (
        patch("hya.imports.is_numpy_available", lambda: False),
        pytest.raises(RuntimeError, match=r"'numpy' package is required but not installed."),
    ):
        check_numpy()


def test_is_numpy_available() -> None:
    assert isinstance(is_numpy_available(), bool)


#################
#     torch     #
#################


def test_check_torch_with_package() -> None:
    with patch("hya.imports.is_torch_available", lambda: True):
        check_torch()


def test_check_torch_without_package() -> None:
    with (
        patch("hya.imports.is_torch_available", lambda: False),
        pytest.raises(RuntimeError, match=r"'torch' package is required but not installed."),
    ):
        check_torch()


def test_is_torch_available() -> None:
    assert isinstance(is_torch_available(), bool)
