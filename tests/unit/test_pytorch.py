from omegaconf import OmegaConf
from omegaconf.errors import InterpolationResolutionError
from pytest import fixture, mark, raises

from hya import is_torch_available, register_resolvers
from hya.pytorch import get_dtypes

if is_torch_available():
    import torch
    from torch import dtype
else:
    dtype = None

torch_available = mark.skipif(not is_torch_available(), reason="Requires PyTorch")


@fixture(scope="module", autouse=True)
def register() -> None:
    register_resolvers()


@torch_available
def test_to_tensor_resolver_number():
    assert OmegaConf.create({"key": "${hya.to_tensor:1.42}"}).key.equal(torch.tensor(1.42))


@torch_available
def test_to_tensor_resolver_list():
    assert OmegaConf.create({"key": "${hya.to_tensor:[1, 2, 3]}"}).key.equal(
        torch.tensor([1, 2, 3])
    )


@torch_available
def test_torch_dtype_resolver_float():
    assert OmegaConf.create({"key": "${hya.torch_dtype:float}"}).key == torch.float


@torch_available
def test_torch_dtype_resolver_long():
    assert OmegaConf.create({"key": "${hya.torch_dtype:long}"}).key == torch.long


@torch_available
def test_torch_dtype_resolver_bool():
    assert OmegaConf.create({"key": "${hya.torch_dtype:bool}"}).key == torch.bool


@torch_available
def test_torch_dtype_resolver_incorrect_attribute():
    with raises(InterpolationResolutionError):
        OmegaConf.create({"key": "${hya.torch_dtype:bool32}"}).key


@torch_available
def test_torch_dtype_resolver_incorrect_dtype():
    with raises(InterpolationResolutionError):
        OmegaConf.create({"key": "${hya.torch_dtype:ones}"}).key


@torch_available
def test_get_dtypes():
    dtypes = get_dtypes()
    assert len(dtypes) > 1
    assert torch.float in dtypes
    assert torch.long in dtypes
