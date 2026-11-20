from __future__ import annotations

import re
from unittest.mock import patch

import pytest
from omegaconf import OmegaConf
from omegaconf.errors import InterpolationResolutionError

from hya.imports import is_torch_available
from hya.testing import torch_available
from hya.torch import _dtype_names, to_tensor_resolver, torch_dtype_resolver

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


def get_incorrect_dtype_message() -> str:
    with pytest.raises(InterpolationResolutionError) as exc_info:
        OmegaConf.create({"key": "${hya.torch.dtype:ones}"}).key  # noqa: B018
    return str(exc_info.value)


@torch_available
def test_torch_dtype_resolver_incorrect_dtype_message_lists_the_names() -> None:
    with (
        patch("hya.torch._dtype_names", return_value=["float32", "int64"]),
        pytest.raises(
            InterpolationResolutionError,
            match=re.escape("Incorrect dtype ones. The available dtypes are ['float32', 'int64']"),
        ),
    ):
        OmegaConf.create({"key": "${hya.torch.dtype:ones}"}).key  # noqa: B018


@torch_available
def test_torch_dtype_resolver_incorrect_dtype_message_is_deterministic() -> None:
    assert get_incorrect_dtype_message() == get_incorrect_dtype_message()


@torch_available
def test_torch_dtype_resolver_direct_call() -> None:
    assert torch_dtype_resolver("float32") == torch.float32


def test_torch_dtype_resolver_missing_package() -> None:
    with (
        patch("hya.torch.validate_torch", side_effect=RuntimeError("missing package")),
        pytest.raises(RuntimeError, match=r"missing package"),
    ):
        torch_dtype_resolver("float32")


@torch_available
def test_dtype_names_is_sorted() -> None:
    names = _dtype_names()
    assert names == sorted(names)


@torch_available
def test_dtype_names_contains_dtypes() -> None:
    names = _dtype_names()
    assert {"bool", "float", "float32", "int64", "long"} <= set(names)


@torch_available
def test_dtype_names_has_no_duplicate() -> None:
    names = _dtype_names()
    assert len(names) == len(set(names))


@torch_available
def test_dtype_names_are_dtypes() -> None:
    assert all(isinstance(getattr(torch, name), torch.dtype) for name in _dtype_names())


@torch_available
def test_dtype_names_does_not_contain_other_attributes() -> None:
    assert "ones" not in _dtype_names()


@torch_available
def test_dtype_names_is_deterministic() -> None:
    assert _dtype_names() == _dtype_names()


@torch_available
def test_to_tensor_resolver_default_dtype() -> None:
    assert to_tensor_resolver([1, 2]).dtype == torch.int64


@torch_available
def test_to_tensor_resolver_dtype_none_is_the_default() -> None:
    assert to_tensor_resolver([1, 2], None).dtype == to_tensor_resolver([1, 2]).dtype


@torch_available
def test_to_tensor_resolver_dtype() -> None:
    assert to_tensor_resolver([1, 2], torch.float32).dtype == torch.float32


@torch_available
def test_to_tensor_resolver_dtype_tensor() -> None:
    assert to_tensor_resolver([1, 2], torch.float32).equal(torch.tensor([1.0, 2.0]))


@torch_available
def test_to_tensor_resolver_resolver_with_dtype() -> None:
    result = OmegaConf.create({"key": "${hya.torch.tensor:[1,2],${hya.torch.dtype:float64}}"}).key
    assert result.dtype == torch.float64


def test_to_tensor_resolver_missing_package() -> None:
    with (
        patch("hya.torch.validate_torch", side_effect=RuntimeError("missing package")),
        pytest.raises(RuntimeError, match=r"missing package"),
    ):
        to_tensor_resolver([1, 2])


@torch_available
def test_to_tensor_resolver_missing_package_with_dtype() -> None:
    with (
        patch("hya.torch.validate_torch", side_effect=RuntimeError("missing package")),
        pytest.raises(RuntimeError, match=r"missing package"),
    ):
        to_tensor_resolver([1, 2], torch.float32)
