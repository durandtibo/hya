from __future__ import annotations

from unittest.mock import patch

from pytest import raises

from hya.imports import check_torch, is_torch_available


def test_check_torch_with_package() -> None:
    with patch("hya.imports.is_torch_available", lambda *args: True):
        check_torch()


def test_check_torch_without_package() -> None:
    with patch("hya.imports.is_torch_available", lambda *args: False):
        with raises(RuntimeError, match="`torch` package is required but not installed."):
            check_torch()


def test_is_torch_available() -> None:
    assert isinstance(is_torch_available(), bool)
