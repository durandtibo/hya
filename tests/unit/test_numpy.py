from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest
from omegaconf import OmegaConf
from omegaconf.errors import MissingMandatoryValue

from hya.imports import is_numpy_available, is_torch_available
from hya.numpy import to_array_resolver
from hya.testing import numpy_available, torch_available

if is_numpy_available():
    import numpy as np

if is_torch_available():
    import torch


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


@numpy_available
@pytest.mark.parametrize("data", [OmegaConf.create({"a": 1}), {"a": 1}])
def test_to_array_resolver_mapping(data: Any) -> None:
    assert to_array_resolver(data).item() == {"a": 1}


@numpy_available
def test_to_array_resolver_mapping_node_is_an_object_array() -> None:
    assert to_array_resolver(OmegaConf.create({"a": 1})).dtype == object


@numpy_available
def test_to_array_resolver_mapping_node_is_not_modified() -> None:
    conf = OmegaConf.create({"a": 1, "x": {"b": "${a}"}})
    to_array_resolver(conf.x)
    assert OmegaConf.to_container(conf.x) == {"b": "${a}"}


@numpy_available
def test_to_array_resolver_list_node() -> None:
    result = to_array_resolver(OmegaConf.create([[1, 2], [3, 4]]))
    assert result.tolist() == [[1, 2], [3, 4]]


@numpy_available
def test_to_array_resolver_empty_list_node() -> None:
    assert to_array_resolver(OmegaConf.create([])).shape == (0,)


@numpy_available
def test_to_array_resolver_nested_interpolation() -> None:
    conf = OmegaConf.create({"a": 1, "x": [["${a}"]]})
    assert to_array_resolver([conf.x]).tolist() == [[[1]]]


@numpy_available
@pytest.mark.parametrize(
    "data",
    [
        OmegaConf.create(["???"]),
        OmegaConf.create({"a": "???"}),
        [OmegaConf.create({"a": "???"})],
        {"a": OmegaConf.create(["???"])},
    ],
)
def test_to_array_resolver_missing_value(data: Any) -> None:
    with pytest.raises(MissingMandatoryValue, match=r"Missing mandatory value"):
        to_array_resolver(data)


@numpy_available
@pytest.mark.parametrize("dtype", [None, "int64"])
def test_to_array_resolver_array_is_copied(dtype: str | None) -> None:
    data = np.array([1, 2], dtype=np.int64)
    assert not np.shares_memory(to_array_resolver(data, dtype), data)


@numpy_available
def test_to_array_resolver_array_is_not_modified() -> None:
    data = np.array([1, 2])
    to_array_resolver(data)[0] = 5
    assert data.tolist() == [1, 2]


@numpy_available
def test_to_array_resolver_keeps_the_memory_order() -> None:
    result = to_array_resolver(np.asfortranarray([[1, 2], [3, 4]]))
    assert result.flags.f_contiguous


@numpy_available
@torch_available
def test_to_array_resolver_tensor() -> None:
    result = to_array_resolver(torch.tensor([1.0, 2.0]))
    assert np.array_equal(result, np.array([1.0, 2.0], dtype=np.float32))


@numpy_available
@torch_available
def test_to_array_resolver_tensor_with_dtype() -> None:
    result = to_array_resolver(torch.tensor([1, 2]), "float64")
    assert result.dtype == np.float64


@numpy_available
@torch_available
@pytest.mark.parametrize("dtype", [None, "int64"])
def test_to_array_resolver_tensor_is_copied(dtype: str | None) -> None:
    data = torch.tensor([1, 2])
    to_array_resolver(data, dtype)[0] = 5
    assert data.tolist() == [1, 2]


@numpy_available
@torch_available
def test_to_array_resolver_tensor_with_gradient() -> None:
    with pytest.raises(RuntimeError, match=r"Can't call numpy\(\) on Tensor that requires grad"):
        to_array_resolver(torch.tensor([1.0], requires_grad=True))


@pytest.mark.parametrize("dtype", [None, "float32"])
def test_to_array_resolver_missing_package(dtype: str | None) -> None:
    with (
        patch("hya.numpy.validate_numpy", side_effect=RuntimeError("missing package")),
        pytest.raises(RuntimeError, match=r"missing package"),
    ):
        to_array_resolver([1, 2], dtype)
