from __future__ import annotations

import pytest
from omegaconf import OmegaConf
from omegaconf.errors import InterpolationResolutionError

from hya.imports import is_torch_available
from hya.testing import torch_available
from hya.torch import get_dtypes

if is_torch_available():
    import torch


@torch_available
def test_to_tensor_resolver_number() -> None:
    assert OmegaConf.create({"key": "${hya.torch.tensor:1.42}"}).key.equal(torch.tensor(1.42))


@torch_available
def test_to_tensor_resolver_list() -> None:
    assert OmegaConf.create({"key": "${hya.torch.tensor:[1, 2, 3]}"}).key.equal(
        torch.tensor([1, 2, 3])
    )


@torch_available
def test_torch_dtype_resolver_float() -> None:
    assert OmegaConf.create({"key": "${hya.torch.dtype:float}"}).key == torch.float


@torch_available
def test_torch_dtype_resolver_long() -> None:
    assert OmegaConf.create({"key": "${hya.torch.dtype:long}"}).key == torch.long


@torch_available
def test_torch_dtype_resolver_bool() -> None:
    assert OmegaConf.create({"key": "${hya.torch.dtype:bool}"}).key == torch.bool


@torch_available
def test_torch_dtype_resolver_incorrect_attribute() -> None:
    with pytest.raises(InterpolationResolutionError, match=r"Incorrect dtype bool32."):
        OmegaConf.create({"key": "${hya.torch.dtype:bool32}"}).key  # noqa: B018


@torch_available
def test_torch_dtype_resolver_incorrect_dtype() -> None:
    with pytest.raises(InterpolationResolutionError, match=r"Incorrect dtype ones."):
        OmegaConf.create({"key": "${hya.torch.dtype:ones}"}).key  # noqa: B018


@torch_available
def test_get_dtypes() -> None:
    dtypes = get_dtypes()
    assert len(dtypes) > 1
    assert torch.float in dtypes
    assert torch.long in dtypes
