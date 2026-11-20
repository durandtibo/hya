from __future__ import annotations

from unittest.mock import patch

import pytest
from omegaconf import OmegaConf

from hya.imports import is_numpy_available
from hya.numpy import to_array_resolver
from hya.testing import numpy_available

if is_numpy_available():
    import numpy as np


@numpy_available
def test_to_array_resolver_number() -> None:
    assert np.array_equal(OmegaConf.create({"key": "${hya.np.array:1.42}"}).key, np.array(1.42))


@numpy_available
def test_to_array_resolver_list() -> None:
    assert np.array_equal(
        OmegaConf.create({"key": "${hya.np.array:[1, 2, 3]}"}).key, np.array([1, 2, 3])
    )


@numpy_available
def test_to_array_resolver_default_dtype() -> None:
    assert to_array_resolver([1, 2]).dtype == np.int64


@numpy_available
def test_to_array_resolver_dtype_none_is_the_default() -> None:
    assert to_array_resolver([1, 2], None).dtype == to_array_resolver([1, 2]).dtype


@numpy_available
def test_to_array_resolver_dtype() -> None:
    assert to_array_resolver([1, 2], "float32").dtype == np.float32


@numpy_available
def test_to_array_resolver_dtype_array() -> None:
    result = to_array_resolver([1, 2], "float32")
    assert np.array_equal(result, np.array([1.0, 2.0], dtype=np.float32))


@numpy_available
def test_to_array_resolver_dtype_does_not_change_the_values() -> None:
    assert to_array_resolver([1, 2], "float32").tolist() == [1.0, 2.0]


@numpy_available
def test_to_array_resolver_incorrect_dtype() -> None:
    with pytest.raises(TypeError, match=r"data type 'nope' not understood"):
        to_array_resolver([1, 2], "nope")


@numpy_available
def test_to_array_resolver_resolver_with_dtype() -> None:
    result = OmegaConf.create({"key": "${hya.np.array:[1, 2],float32}"}).key
    assert result.dtype == np.float32


@pytest.mark.parametrize("dtype", [None, "float32"])
def test_to_array_resolver_missing_package(dtype: str | None) -> None:
    with (
        patch("hya.numpy.validate_numpy", side_effect=RuntimeError("missing package")),
        pytest.raises(RuntimeError, match=r"missing package"),
    ):
        to_array_resolver([1, 2], dtype)
