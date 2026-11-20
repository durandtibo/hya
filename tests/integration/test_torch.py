from __future__ import annotations

import ast

import pytest
from omegaconf import OmegaConf
from omegaconf.errors import InterpolationResolutionError

from hya.testing import torch_available


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
