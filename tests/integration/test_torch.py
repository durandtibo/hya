from __future__ import annotations

import ast

import pytest
from omegaconf import OmegaConf
from omegaconf.errors import InterpolationResolutionError

from hya.imports import is_torch_available
from hya.testing import numpy_available, torch_available

if is_torch_available():
    import torch


@torch_available
def test_tensor_resolver() -> None:
    assert OmegaConf.has_resolver("hya.torch.tensor")


@torch_available
def test_dtype_resolver() -> None:
    assert OmegaConf.has_resolver("hya.torch.dtype")


@torch_available
def test_dtype_resolver_error_lists_the_sorted_names() -> None:
    conf = OmegaConf.create({"key": "${hya.torch.dtype:ones}"})
    with pytest.raises(InterpolationResolutionError) as exc_info:
        _ = conf.key
    names = ast.literal_eval(
        str(exc_info.value).split("The available dtypes are ")[1].split("\n")[0]
    )
    assert names == sorted(names)


@torch_available
def test_dtype_resolver_error_lists_real_dtypes() -> None:
    conf = OmegaConf.create({"key": "${hya.torch.dtype:ones}"})
    with pytest.raises(InterpolationResolutionError, match=r"'float32'"):
        _ = conf.key


@torch_available
def test_tensor_resolver_dtype() -> None:
    conf = OmegaConf.create({"key": "${hya.torch.tensor:[1,2],${hya.torch.dtype:float32}}"})
    assert conf.key.dtype == torch.float32


@torch_available
def test_tensor_resolver_dtype_tensor() -> None:
    conf = OmegaConf.create({"key": "${hya.torch.tensor:[1,0,1],${hya.torch.dtype:bool}}"})
    assert conf.key.equal(torch.tensor([True, False, True]))


@torch_available
def test_tensor_resolver_dtype_does_not_modify_the_config() -> None:
    conf = OmegaConf.create(
        {"x": [1, 2], "key": "${hya.torch.tensor:${x},${hya.torch.dtype:float64}}"}
    )
    assert conf.key.dtype == torch.float64
    assert conf.x == [1, 2]


@torch_available
@pytest.mark.filterwarnings("error")
def test_tensor_resolver_of_a_tensor() -> None:
    conf = OmegaConf.create({"key": "${hya.torch.tensor:${hya.torch.tensor:[1,2]}}"})
    assert conf.key.equal(torch.tensor([1, 2]))


@torch_available
def test_tensor_resolver_of_a_tensor_with_a_dtype() -> None:
    conf = OmegaConf.create(
        {"key": "${hya.torch.tensor:${hya.torch.tensor:[1,2]},${hya.torch.dtype:float64}}"}
    )
    assert conf.key.dtype == torch.float64


@torch_available
def test_tensor_resolver_of_a_tensor_of_the_configuration_does_not_share_memory() -> None:
    data = torch.tensor([1, 2])
    conf = OmegaConf.create(
        {"x": data, "key": "${hya.torch.tensor:${x}}"}, flags={"allow_objects": True}
    )
    conf.key[0] = 10
    assert data.tolist() == [1, 2]


@numpy_available
@torch_available
def test_tensor_resolver_of_an_array() -> None:
    conf = OmegaConf.create({"key": "${hya.torch.tensor:${hya.np.array:[1,2]}}"})
    assert conf.key.equal(torch.tensor([1, 2]))


@torch_available
def test_tensor_resolver_of_a_literal_list_of_a_node() -> None:
    conf = OmegaConf.create({"a": 1, "x": ["${a}"], "key": "${hya.torch.tensor:[${x},[2]]}"})
    assert conf.key.equal(torch.tensor([[1], [2]]))


@torch_available
def test_tensor_resolver_missing_value_in_a_list() -> None:
    conf = OmegaConf.create({"x": ["???"], "key": "${hya.torch.tensor:${x}}"})
    with pytest.raises(InterpolationResolutionError, match=r"MissingMandatoryValue"):
        _ = conf.key


@torch_available
@pytest.mark.parametrize(
    ("expression", "dtype"),
    [
        ("${hya.torch.tensor:[1,2],float32}", "float32"),
        ("${hya.torch.tensor:[1,2],${name}}", "float32"),
        ("${hya.torch.tensor:[1,2],null}", "int64"),
        ("${hya.torch.tensor:${hya.torch.tensor:[1,2]},float32}", "float32"),
    ],
)
def test_tensor_resolver_dtype_name(expression: str, dtype: str) -> None:
    conf = OmegaConf.create({"name": "float32", "key": expression})
    assert conf.key.dtype == getattr(torch, dtype)


@torch_available
def test_tensor_resolver_unknown_dtype_name() -> None:
    conf = OmegaConf.create({"key": "${hya.torch.tensor:[1,2],bool32}"})
    with pytest.raises(InterpolationResolutionError, match=r"Incorrect dtype bool32\."):
        _ = conf.key
