from __future__ import annotations

import ast

import pytest
from omegaconf import OmegaConf
from omegaconf.errors import InterpolationResolutionError

from hya.imports import is_torch_available
from hya.testing import torch_available

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
