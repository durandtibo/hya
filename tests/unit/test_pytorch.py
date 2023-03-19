from omegaconf import OmegaConf
from pytest import fixture, mark

from hya import is_torch_available, register_resolvers
from hya.pytorch import DTYPE_MAPPING

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
def test_dtype_mapping():
    assert len(DTYPE_MAPPING) > 1


@torch_available
def test_torch_dtype_resolver_float():
    assert OmegaConf.create({"key": "${hya.torch_dtype:float}"}).key == torch.float


@torch_available
@mark.parametrize("target,dtype", DTYPE_MAPPING.items())
def test_torch_dtype_resolver_list(target: str, dtype: dtype):
    assert OmegaConf.create({"key": "${hya.torch_dtype:" + f"{target}" + "}"}).key == dtype
